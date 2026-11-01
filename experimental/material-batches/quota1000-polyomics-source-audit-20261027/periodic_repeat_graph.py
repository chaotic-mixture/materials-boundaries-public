"""Experimental, unreviewed periodic graph screening; never a material admission API.

Requires an explicitly supplied external RDKit installation. Real isotopes and
chemical bonds are retained. Explicit stereochemistry, ions and non-single port
bonds are held rather than silently erased. Keys need independent scientific and
identity review before any use in quota accounting.
"""
from hashlib import sha256
from rdkit import Chem, rdBase

METHOD = 'unreviewed-linear-two-port-four-repeat-graph/1'

def key(molecule):
    return Chem.MolToSmiles(molecule,canonical=True,isomericSmiles=True)

def ports(molecule):
    result=[a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum()==0]
    if len(result)!=2 or any(molecule.GetAtomWithIdx(i).GetDegree()!=1 for i in result):
        raise ValueError('Requires exactly two degree-one attachment atoms')
    if any(molecule.GetBondBetweenAtoms(i,molecule.GetAtomWithIdx(i).GetNeighbors()[0].GetIdx()).GetBondType()!=Chem.BondType.SINGLE for i in result):
        raise ValueError('Non-single attachment bonds require separate review')
    return result

def clean(molecule):
    molecule=Chem.Mol(molecule)
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
        if atom.GetAtomicNum()==0:
            atom.SetIsotope(0)
    Chem.SanitizeMol(molecule)
    return molecule

def parse(smiles):
    if not isinstance(smiles,str) or not smiles or len(smiles)>10000:
        raise ValueError('Missing/oversize repeat-unit text')
    with rdBase.BlockLogs():
        molecule=Chem.MolFromSmiles(smiles)
    if molecule is None or len(Chem.GetMolFrags(molecule))!=1:
        raise ValueError('Invalid or disconnected repeat-unit graph')
    if Chem.GetFormalCharge(molecule)!=0:
        raise ValueError('Ionic repeat units require separate review')
    if any(a.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED for a in molecule.GetAtoms()):
        raise ValueError('Explicit atom stereochemistry requires separate review')
    if any(b.GetStereo()!=Chem.BondStereo.STEREONONE for b in molecule.GetBonds()):
        raise ValueError('Explicit bond stereochemistry requires separate review')
    molecule=clean(molecule)
    ports(molecule)
    if molecule.GetNumAtoms()<=2:
        raise ValueError('No real repeat-unit atom')
    return molecule

def repeat(molecule,count,*,cyclic=False,reverse=False):
    """Connect identical explicit port graphs, without generating coordinates."""
    if type(count) is not int or count<1 or (cyclic and count<3):
        raise ValueError('Invalid graph repeat count')
    head,tail=ports(molecule)
    if reverse:
        head,tail=tail,head
    head_neighbor=molecule.GetAtomWithIdx(head).GetNeighbors()[0].GetIdx()
    tail_neighbor=molecule.GetAtomWithIdx(tail).GetNeighbors()[0].GetIdx()
    size=molecule.GetNumAtoms()
    combined=Chem.Mol(molecule)
    for _ in range(count-1):
        combined=Chem.CombineMols(combined,molecule)
    edit=Chem.RWMol(combined)
    removed=set()
    seams=range(count) if cyclic else range(count-1)
    for index in seams:
        following=(index+1)%count
        edit.AddBond(index*size+tail_neighbor,following*size+head_neighbor,Chem.BondType.SINGLE)
        removed.update([index*size+tail,following*size+head])
    for index in sorted(removed,reverse=True):
        edit.RemoveAtom(index)
    result=edit.GetMol()
    Chem.SanitizeMol(result)
    return result

def primitive(molecule):
    """Accept a smaller repeat only when exact open-chain rebuilding succeeds."""
    head,tail=ports(molecule)
    backbone=list(Chem.GetShortestPath(molecule,head,tail))[1:-1]
    original=key(molecule)
    for length in range(1,len(backbone)//2+1):
        if len(backbone)%length:
            continue
        cut=[molecule.GetBondBetweenAtoms(backbone[i-1],backbone[i]) for i in range(length,len(backbone),length)]
        if any(b.IsInRing() or b.GetBondType()!=Chem.BondType.SINGLE for b in cut):
            continue
        fragmented=Chem.FragmentOnBonds(molecule,[b.GetIdx() for b in cut],addDummies=True)
        try:
            pieces=[clean(p) for p in Chem.GetMolFrags(fragmented,asMols=True,sanitizeFrags=True)]
            if len(pieces)!=len(backbone)//length:
                continue
            for piece in pieces:
                ports(piece)
            if len({key(p) for p in pieces})!=1:
                continue
            for reverse in (False,True):
                if key(repeat(pieces[0],len(pieces),reverse=reverse))==original:
                    return pieces[0]
        except (ValueError,RuntimeError):
            continue
    return molecule

def normalize(smiles):
    molecule=parse(smiles)
    minimal=primitive(molecule)
    cyclic=key(repeat(minimal,4,cyclic=True))
    old_atoms=molecule.GetNumAtoms()-2
    new_atoms=minimal.GetNumAtoms()-2
    if old_atoms%new_atoms:
        raise ValueError('Reduced graph does not divide source atom count')
    return {'method':METHOD,'rdkit_version':rdBase.rdkitVersion,
            'source_port_graph_smiles':key(molecule),'primitive_repeat_smiles':key(minimal),
            'source_non_dummy_atoms':old_atoms,'primitive_non_dummy_atoms':new_atoms,
            'repeat_factor':old_atoms//new_atoms,'four_repeat_cyclic_graph_smiles':cyclic,
            'periodic_graph_key_sha256':sha256(cyclic.encode('utf8')).hexdigest(),
            'independent_identity_review':'not_run','admitted':False}
