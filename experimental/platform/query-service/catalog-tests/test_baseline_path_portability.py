"""Exercise the actual baseline validator with both filesystem path flavors."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import unittest
from unittest.mock import patch

from materials_query import computed_registry as registry


class Resource:
    def __init__(self, path, flavor, change=None, extra=False):
        self.path, self.flavor, self.change, self.extra = path, flavor, change, extra

    def __lt__(self, other):
        return self.path.as_posix() < other.path.as_posix()

    @property
    def suffix(self):
        return self.path.suffix

    def is_file(self):
        return self.extra or self.path.is_file()

    def relative_to(self, root):
        return self.flavor(*self.path.relative_to(root).parts)

    def read_bytes(self):
        if self.extra:
            return b'{}'
        raw = self.path.read_bytes()
        return raw + b' ' if self.change == 'alter' and self.path.name == 'materials.json' else raw


class Tree:
    def __init__(self, root, flavor, change=None):
        self.root, self.flavor, self.change = Path(root), flavor, change

    def rglob(self, pattern):
        rows = [Resource(path, self.flavor, self.change) for path in self.root.rglob(pattern)
                if not (self.change == 'missing' and path.name == 'materials.json')]
        if self.change == 'extra':
            rows.append(Resource(self.root / 'data' / 'unexpected.json', self.flavor, extra=True))
        return rows


class BaselinePathPortability(unittest.TestCase):
    def validate_flavor(self, flavor, change=None):
        # Patch only filesystem traversal. The real pins, resource bytes, hash
        # calculations and exact-manifest comparison all remain in force.
        with patch.object(registry, 'Path', lambda root: Tree(root, flavor, change)):
            return registry.baseline_digest()

    def test_identical_files_have_one_baseline_on_both_path_flavors(self):
        expected = self.validate_flavor(PurePosixPath)
        self.assertEqual(self.validate_flavor(PureWindowsPath), expected)
        self.assertEqual(registry.baseline_digest(), expected)

    def test_changed_bytes_rejected_on_both_path_flavors(self):
        for flavor in (PurePosixPath, PureWindowsPath):
            with self.subTest(flavor=flavor.__name__):
                with self.assertRaisesRegex(ValueError, 'Installed legacy baseline differs'):
                    self.validate_flavor(flavor, 'alter')

    def test_extra_file_rejected_on_both_path_flavors(self):
        for flavor in (PurePosixPath, PureWindowsPath):
            with self.subTest(flavor=flavor.__name__):
                with self.assertRaisesRegex(ValueError, 'Installed legacy baseline differs'):
                    self.validate_flavor(flavor, 'extra')

    def test_missing_file_rejected_on_both_path_flavors(self):
        for flavor in (PurePosixPath, PureWindowsPath):
            with self.subTest(flavor=flavor.__name__):
                with self.assertRaisesRegex(ValueError, 'Installed legacy baseline differs'):
                    self.validate_flavor(flavor, 'missing')


if __name__ == '__main__':
    unittest.main()
