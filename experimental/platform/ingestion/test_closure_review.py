"""Independent closure checks for snapshots, transaction rollback and process death.

All provider traffic is replaced by deterministic fixtures. WAL is used only in
the reader tests to allow a writer commit at an exact read boundary without
timing-based assertions or blocking SQLite's rollback-journal reader lock.
"""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import nomad_incremental as inc
from test_nomad_batch import fixture
from test_nomad_incremental import BOUNDARY, Crash, QueueTransport, attribution, response


class ClosureReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def init(self, **kwargs):
        inc.init_store(self.root, boundary=BOUNDARY, **kwargs)

    def update(self, *responses):
        return inc.update(self.root, transport=QueueTransport(*responses))

    def baseline(self):
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db:
            return json.loads(db.execute("SELECT value FROM metadata WHERE key='baseline'").fetchone()[0])

    def paused_two_page_cycle(self):
        self.init(pages=2, page_size=1)
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db:
            self.assertEqual(db.execute('PRAGMA journal_mode=WAL').fetchone()[0], 'wal')
        result = self.update(response([fixture('a', 'material_a')], total=2, after='a'),
                             attribution('a'), OSError('Synthetic second-page interruption'))
        self.assertEqual(result['status'], 'paused')
        return result

    def read_across_writer_commit(self, reader):
        original_latest = inc.latest
        committed = []

        def select_then_complete(db):
            selected = original_latest(db)
            if not committed:
                committed.append(True)
                finished = self.update(response([fixture('b', 'material_b')], total=2), attribution('b'))
                self.assertEqual(finished['status'], 'complete')
            return selected

        with patch.object(inc, 'latest', side_effect=select_then_complete):
            result = reader(self.root)
        self.assertEqual(len(committed), 1)
        self.assertEqual(inc.status(self.root)['cycle']['status'], 'complete')
        return result

    def test_report_retains_one_snapshot_across_concurrent_commit(self):
        before = self.paused_two_page_cycle()
        during = self.read_across_writer_commit(inc.report)
        self.assertEqual(during['input_changes'], before['input_changes'])
        self.assertEqual(during, before)

    def test_status_retains_one_snapshot_across_concurrent_commit(self):
        self.paused_two_page_cycle()
        before = inc.status(self.root)
        during = self.read_across_writer_commit(inc.status)
        self.assertEqual(during['cycle']['status'], during['history'][-1]['status'])
        self.assertEqual(during, before)

    def test_completion_checkpoint_rolls_back_baseline_and_replays_cache(self):
        self.init()
        previous = self.baseline()
        original_save = inc.save_cycle

        def crash_before_complete_state(db, cycle):
            if cycle['status'] == 'complete':
                raise Crash('Synthetic death after baseline write, before cycle write')
            original_save(db, cycle)

        with patch.object(inc, 'save_cycle', side_effect=crash_before_complete_state):
            with self.assertRaises(Crash):
                self.update(response([fixture()]), attribution('entry_1'))
        self.assertEqual(self.baseline(), previous)
        self.assertNotEqual(inc.status(self.root)['cycle']['status'], 'complete')
        finished = self.update()
        self.assertEqual(finished['status'], 'complete')
        self.assertEqual(finished['budget']['requests'], 2)
        self.assertEqual(finished['input_changes'][0]['change'], 'new')
        self.assertEqual(inc.report(self.root), finished)

    def test_hard_process_death_preserves_inflight_reservation(self):
        self.init(retries=1, max_response=3000)
        script = """
import os, sys
import nomad_incremental as inc
def die_without_finally(endpoint, body, limit):
    os._exit(27)
inc.update(sys.argv[1], transport=die_without_finally)
"""
        child = subprocess.run([sys.executable, '-B', '-c', script, str(self.root)],
                               cwd=Path(__file__).resolve().parent, capture_output=True, timeout=15)
        self.assertEqual(child.returncode, 27, child.stderr.decode(errors='replace'))
        state = inc.status(self.root)['cycle']
        self.assertEqual(state['requests'], 1)
        self.assertEqual(state['bytes_charged'], 3000)
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db:
            stored, raw = db.execute('SELECT record,raw FROM attempts').fetchone()
        self.assertEqual(json.loads(stored)['status'], 'reserved')
        self.assertIsNone(raw)
        finished = self.update(response([fixture()]), attribution('entry_1'))
        self.assertEqual(finished['status'], 'complete')
        self.assertEqual(finished['budget']['requests'], 3)
        self.assertEqual(finished['budget']['retries_used'], 1)
        self.assertGreaterEqual(finished['budget']['bytes_charged'], 3000)

    def test_real_process_lock_is_released_after_termination(self):
        self.init()
        script = """
from pathlib import Path
import sys
import nomad_incremental as inc
with inc.locked(Path(sys.argv[1])):
    print('locked', flush=True)
    sys.stdin.read()
"""
        child = subprocess.Popen([sys.executable, '-B', '-c', script, str(self.root)],
                                 cwd=Path(__file__).resolve().parent, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'locked')
            with self.assertRaisesRegex(ValueError, 'already being updated'):
                self.update()
            child.terminate()
            child.communicate(timeout=15)
            finished = self.update(response([fixture()]), attribution('entry_1'))
            self.assertEqual(finished['status'], 'complete')
            self.assertEqual(finished['budget']['requests'], 2)
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=15)
            for pipe in (child.stdin, child.stdout, child.stderr):
                if pipe is not None:
                    pipe.close()

    def test_overflowing_json_exponents_are_rejected_before_caching(self):
        for exponent in (b'1e400', b'-1e400'):
            with self.subTest(exponent=exponent), tempfile.TemporaryDirectory() as directory:
                inc.init_store(directory, boundary=BOUNDARY)
                raw = response([fixture()])[2].replace(b'"mass_density":8000',
                                                       b'"mass_density":' + exponent)
                result = inc.update(directory, transport=QueueTransport((200, {}, raw)))
                self.assertEqual(result['status'], 'blocked')
                self.assertEqual(result['candidate_packet']['candidates'], [])
                with closing(sqlite3.connect(Path(directory) / inc.DB_NAME)) as db:
                    self.assertIsNone(db.execute('SELECT raw FROM attempts').fetchone()[0])
                self.assertEqual(inc.report(directory), result)
                self.assertEqual(inc.abandon(directory, 'Reviewed synthetic invalid source')['status'], 'abandoned')

    def test_huge_integer_density_is_quarantined_without_breaking_recovery(self):
        self.init()
        row = fixture()
        row['archive']['results']['properties']['structures']['structure_original']['mass_density'] = 10 ** 400
        result = self.update(response([row]), attribution('entry_1'))
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertEqual(result['gate_exclusions'][0]['reason'], 'invalid_density')
        self.assertEqual(inc.report(self.root), result)
        repeated = self.update(response([row]), attribution('entry_1'))
        self.assertEqual(repeated['status'], 'complete')
        self.assertEqual(repeated['input_changes'], [])
        self.assertEqual(repeated['candidate_changes'], [])

    def test_source_and_method_fields_require_nonempty_text(self):
        fields = ('nomad_version', 'nomad_commit', 'last_processing_time', 'mainfile', 'program_name')
        for field in fields:
            for value in (True, 123, {'wrong': 'shape'}, ['wrong shape'], '   '):
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                    inc.init_store(directory, boundary=BOUNDARY)
                    row = fixture()
                    target = (row['archive']['results']['method']['simulation'] if field == 'program_name'
                              else row['archive']['metadata'])
                    target[field] = value
                    result = inc.update(directory, transport=QueueTransport(response([row]), attribution('entry_1')))
                    self.assertEqual(result['status'], 'complete')
                    self.assertEqual(result['candidate_packet']['candidates'], [])
                    self.assertEqual(result['admitted_delta'], 0)
                    expected = 'unsupported_method' if field == 'program_name' else 'missing_provenance_version'
                    self.assertEqual(result['gate_exclusions'][0]['reason'], expected)


if __name__ == '__main__':
    unittest.main()
