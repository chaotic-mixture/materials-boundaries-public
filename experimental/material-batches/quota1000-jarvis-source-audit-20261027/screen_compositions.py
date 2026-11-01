"""Audit a pinned JARVIS release without admitting or reclassifying materials.

The buckets are screening predicates, not approved taxonomy or identity keys.
One reduced atom-count ratio is counted once regardless of polymorph/JID count.
"""
import argparse
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import TextIOWrapper
import json
from math import gcd
from pathlib import Path
import re
from zipfile import ZipFile

ARCHIVE_SHA256 = 'f9e0a3309f0000d5de1ec9e49c93963109ea45e63f451103f8f6595d2eabf7f5'
MEMBER = 'jdft_3d-9-24-2025.json'
METALS = frozenset('Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv'.split())
ELEMENTS = METALS | frozenset('H He B C N O F Ne Si P S Cl Ar Ge As Se Br Kr Sb Te I Xe Po At Rn Ts Og'.split())

class NumberToken(str):
    """Retain the exact JSON numeric token without conflating JSON strings."""

class SourceNonfiniteToken(str):
    """Preserve this release's non-JSON missing-data token; never a number."""

def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object key: ' + key)
        result[key] = value
    return result

DECODER = json.JSONDecoder(object_pairs_hook=unique_pairs, parse_int=NumberToken,
                           parse_float=NumberToken, parse_constant=SourceNonfiniteToken)

def source_nonfinite_paths(value, prefix=''):
    if isinstance(value, SourceNonfiniteToken):
        yield prefix, str(value)
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from source_nonfinite_paths(child, prefix + '.' + key if prefix else key)
    elif isinstance(value, list):
        for child in value:
            yield from source_nonfinite_paths(child, prefix + '[*]')

def array_objects(stream, chunk_size=1048576):
    """Read a single strict JSON array; reject truncation and trailing content."""
    buffer, position, eof = '', 0, False
    def fill():
        nonlocal buffer, position, eof
        buffer = buffer[position:]
        position = 0
        chunk = stream.read(chunk_size)
        eof = not chunk
        buffer += chunk
    def skip_space():
        nonlocal position
        while True:
            while position < len(buffer) and buffer[position] in ' \t\r\n':
                position += 1
            if position < len(buffer) or eof:
                return
            fill()
    skip_space()
    if position >= len(buffer) or buffer[position] != '[':
        raise ValueError('Expected a JSON array')
    position += 1
    skip_space()
    if position < len(buffer) and buffer[position] == ']':
        position += 1
    else:
        while True:
            while True:
                try:
                    value, end = DECODER.raw_decode(buffer, position)
                except json.JSONDecodeError:
                    if eof:
                        raise
                    fill()
                    continue
                break
            if not isinstance(value, dict):
                raise ValueError('Each source row must be a JSON object')
            raw = buffer[position:end]
            position = end
            yield value, raw
            skip_space()
            if position >= len(buffer):
                raise ValueError('Truncated array')
            delimiter = buffer[position]
            position += 1
            if delimiter == ']':
                break
            if delimiter != ',':
                raise ValueError('Expected array comma or closing bracket')
            skip_space()
            if position < len(buffer) and buffer[position] == ']':
                raise ValueError('Trailing comma')
    skip_space()
    if position != len(buffer):
        raise ValueError('Trailing JSON content')

def ratio_key(amounts):
    if not amounts or not set(amounts) <= ELEMENTS:
        raise ValueError('Unknown or empty elemental composition')
    values = {element: Fraction(value) for element, value in amounts.items()}
    if any(value <= 0 for value in values.values()):
        raise ValueError('Nonpositive composition amount')
    scale = 1
    for value in values.values():
        scale = scale * value.denominator // gcd(scale, value.denominator)
    integers = {element: int(value * scale) for element, value in values.items()}
    common = 0
    for value in integers.values():
        common = gcd(common, value)
    return '|'.join(f'{element}:{integers[element]//common}' for element in sorted(integers))

def formula_key(formula):
    if not isinstance(formula, str) or not formula or len(formula) > 512:
        raise ValueError('Missing/oversize formula')
    position, amounts = 0, Counter()
    for match in re.finditer(r'([A-Z][a-z]?)([0-9]+(?:\.[0-9]+)?)?', formula):
        if match.start() != position:
            raise ValueError('Unsupported formula syntax')
        amounts[match[1]] += Fraction(match[2] or '1')
        position = match.end()
    if position != len(formula):
        raise ValueError('Unsupported formula suffix')
    return ratio_key(amounts)

def row_facts(row):
    jid = row.get('jid')
    if not isinstance(jid, str) or not re.fullmatch(r'JVASP-[1-9][0-9]*', jid):
        raise ValueError('Invalid source JID')
    atoms = row.get('atoms')
    if not isinstance(atoms, dict) or not isinstance(atoms.get('elements'), list):
        raise ValueError('Missing source atom elements')
    elements = atoms['elements']
    if not elements or any(type(e) is not str or e not in ELEMENTS for e in elements):
        raise ValueError('Invalid source atom element')
    if not isinstance(atoms.get('coords'), list) or len(atoms['coords']) != len(elements):
        raise ValueError('Atom and coordinate counts differ')
    lattice = atoms.get('lattice_mat')
    if (not isinstance(lattice,list) or len(lattice)!=3
            or any(not isinstance(vector,list) or len(vector)!=3 for vector in lattice + atoms['coords'])
            or any(type(n) is not NumberToken or not Decimal(n).is_finite()
                   for vector in lattice + atoms['coords'] for n in vector)):
        raise ValueError('Missing/nonfinite source geometry')
    if type(row.get('nat')) is not NumberToken or not re.fullmatch('[1-9][0-9]*', row['nat']) or int(row['nat']) != len(elements):
        raise ValueError('Source nat differs from atomic element count')
    key = ratio_key(Counter(elements))
    if formula_key(row.get('formula')) != key:
        raise ValueError('Source formula and atom-count ratios disagree')
    density = row.get('density')
    if type(density) is not NumberToken or len(density) > 64:
        raise ValueError('Density is not a bounded source JSON number')
    number = Decimal(density)
    if not number.is_finite() or number <= 0:
        raise ValueError('Nonpositive/nonfinite density')
    if row.get('func') != 'OptB88vdW':
        raise ValueError('Functional is not the selected OptB88vdW workflow')
    if row.get('dimensionality') != '3D-bulk' or row.get('typ') != 'bulk':
        raise ValueError('Not explicitly 3D-bulk')
    element_set = set(elements)
    bucket = ('all_metal_elements' if element_set <= METALS else
              'oxygen_containing_no_C_H' if 'O' in element_set and not {'C','H'} & element_set else
              'other_requires_classification')
    return {'jid':jid, 'formula':row['formula'], 'ratio_key':key,
            'screening_bucket':bucket, 'source_density_token':str(density),
            'functional':row['func'],'dimensionality':row['dimensionality'],
            'space_group_number':str(row.get('spg_number')),
            'parent_structure_reference':row.get('reference')}

def screen(archive, output_dir):
    raw_sha = sha256(archive.read_bytes()).hexdigest()
    if raw_sha != ARCHIVE_SHA256:
        raise ValueError('Unreviewed release bytes')
    counters, exclusions, examples, nonfinite = Counter(), Counter(), [], Counter()
    groups, source_ids = {}, set()
    output_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as container:
        if container.namelist() != [MEMBER]:
            raise ValueError('Unexpected archive member list')
        internal_sha = sha256()
        with container.open(MEMBER) as member:
            for chunk in iter(lambda:member.read(1048576), b''):
                internal_sha.update(chunk)
        with container.open(MEMBER) as member, TextIOWrapper(member, encoding='utf8') as stream:
            for index, (row, text) in enumerate(array_objects(stream)):
                counters['source_rows'] += 1
                constants = list(source_nonfinite_paths(row))
                if constants:
                    counters['rows_with_source_nonfinite_tokens'] += 1
                nonfinite.update(path + ':' + value for path,value in constants)
                jid = row.get('jid')
                if jid in source_ids:
                    raise ValueError('Repeated source JID: ' + str(jid))
                source_ids.add(jid)
                try:
                    facts = row_facts(row)
                except ValueError as error:
                    exclusions[str(error)] += 1
                    if len(examples) < 30:
                        examples.append({'index':index,'jid':jid,'reason':str(error)})
                    continue
                facts['source_row_index'] = index
                facts['source_row_text_sha256'] = sha256(text.encode('utf8')).hexdigest()
                key = facts['ratio_key']
                counters['eligible_rows'] += 1
                counters[facts['screening_bucket'] + '_rows'] += 1
                if key not in groups:
                    groups[key] = {'source_row_count':0, 'representative':facts}
                groups[key]['source_row_count'] += 1
                if int(facts['jid'].split('-')[1]) < int(groups[key]['representative']['jid'].split('-')[1]):
                    groups[key]['representative'] = facts
    group_counts = Counter(g['representative']['screening_bucket'] for g in groups.values())
    output = {'schema':'jarvis-composition-screen/1','status':'source_audit_only_no_admission',
              'source_archive_sha256':raw_sha, 'source_member':MEMBER,
              'source_member_sha256':internal_sha.hexdigest(), 'counts':dict(counters),
              'reduced_composition_groups':len(groups),'groups_by_screening_bucket':dict(group_counts),
              'exclusions_by_reason':dict(exclusions),'exclusion_examples':examples,
              'source_nonfinite_token_counts':dict(nonfinite),
              'identity_overlap_with_project':'not_yet_resolved',
              'approved_unique_material_count':None, 'admitted_increment':0,
              'density_basis':'source-reported computed density; unit attribution requires pinned source-code and methods evidence',
              'selection_policy':'Smallest numeric JID per reduced atom-count ratio is an index representative, not the most stable phase or a material admission.',
              'limitations':['Screening buckets are not independently approved taxonomy.',
                             'The source contains non-JSON NaN/Infinity tokens. They are retained as typed source sentinels for audit; any such selected density/geometry is rejected, never converted to a runtime number.',
                             'Reduced stoichiometry does not establish structure, phase or material identity equivalence.',
                             'Source rows, polymorphs and simulation states do not independently increase quota.',
                             'No experimental density, measured uncertainty, specimen count or engineering allowable is inferred.',
                             'No full parent crystal coordinates are exported by this screen.']}
    index = {'schema':'jarvis-composition-index/1', 'groups':groups}
    index_raw = (json.dumps(index,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    output['composition_index_sha256'] = sha256(index_raw).hexdigest()
    (output_dir / 'composition-index.json').write_bytes(index_raw)
    (output_dir / 'screening-summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(output,ensure_ascii=False),flush=True)
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    screen(args.archive,args.output_dir)
