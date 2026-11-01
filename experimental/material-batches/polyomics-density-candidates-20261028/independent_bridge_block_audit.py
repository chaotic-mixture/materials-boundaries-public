
from rdkit import Chem
from pathlib import Path
from collections import defaultdict,Counter
import json,sys
sys.path.insert(0,str(Path('experimental/material-batches/quota1000-polyomics-source-audit-20261027').resolve()))
import periodic_repeat_graph as producer

def block_word(smiles):
 m=Chem.MolFromSmiles(smiles)
 assert m is not None and len(Chem.GetMolFrags(m))==1
 ports=[a.GetIdx() for a in m.GetAtoms() if a.GetAtomicNum()==0]
 assert len(ports)==2 and all(m.GetAtomWithIdx(i).GetDegree()==1 for i in ports)
 for a in m.GetAtoms():
  a.SetAtomMapNum(0);a.SetIntProp('_audit_orig',a.GetIdx())
  if a.GetAtomicNum()==0:a.SetIsotope(0)
 head,tail=ports;path=list(Chem.GetShortestPath(m,head,tail));position={a:i for i,a in enumerate(path)}
 adjacency={a.GetIdx():[] for a in m.GetAtoms()}
 for bond in m.GetBonds():
  a,b=bond.GetBeginAtomIdx(),bond.GetEndAtomIdx();adjacency[a].append((b,bond.GetIdx()));adjacency[b].append((a,bond.GetIdx()))
 tin,low,bridges={},{},set();tick=[0]
 def dfs(v,parent_bond=-1):
  tin[v]=low[v]=tick[0];tick[0]+=1
  for other,bid in adjacency[v]:
   if bid==parent_bond:continue
   if other in tin:low[v]=min(low[v],tin[other])
   else:
    dfs(other,bid);low[v]=min(low[v],low[other])
    if low[other]>tin[v]:bridges.add(bid)
 dfs(head)
 cuts=[]
 for a,b in zip(path[1:-2],path[2:-1]):
  bond=m.GetBondBetweenAtoms(a,b)
  if bond.GetIdx() in bridges:cuts.append((bond.GetIdx(),a,b))
 fragmented=Chem.FragmentOnBonds(m,[x[0] for x in cuts],addDummies=True,dummyLabels=[(i+1,i+1) for i in range(len(cuts))]) if cuts else Chem.Mol(m)
 words=[]
 for part in Chem.GetMolFrags(fragmented,asMols=True,sanitizeFrags=True):
  ordinal=min(position[a.GetIntProp('_audit_orig')] for a in part.GetAtoms() if a.HasProp('_audit_orig') and a.GetIntProp('_audit_orig') in position)
  roles=[]
  for a in part.GetAtoms():
   if a.GetAtomicNum()!=0:continue
   if a.HasProp('_audit_orig'):
    original=a.GetIntProp('_audit_orig');role=1 if original==head else 2;assert original in (head,tail)
   else:
    _,left,right=cuts[a.GetIsotope()-1];neighbor=a.GetNeighbors()[0].GetIntProp('_audit_orig');assert neighbor in (left,right);role=2 if neighbor==left else 1
   a.SetIsotope(0);a.SetAtomMapNum(role);roles.append(role)
  assert sorted(roles)==[1,2]
  forward=Chem.MolToSmiles(part,canonical=True,isomericSmiles=True)
  for a in part.GetAtoms():
   if a.GetAtomicNum()==0:a.SetAtomMapNum(3-a.GetAtomMapNum())
  reverse=Chem.MolToSmiles(part,canonical=True,isomericSmiles=True)
  words.append((ordinal,forward,reverse))
 words.sort();forward=tuple(w[1] for w in words);reverse=tuple(w[2] for w in reversed(words))
 def primitive(seq):
  for length in range(1,len(seq)+1):
   if len(seq)%length==0 and seq==seq[:length]*(len(seq)//length):return seq[:length]
 def rotations(seq):
  seq=primitive(seq);return [seq[i:]+seq[:i] for i in range(len(seq))]
 canonical=min(rotations(forward)+rotations(reverse))
 return canonical,forward

def assemble(sequence):
 fragments=[Chem.MolFromSmiles(s) for s in sequence];boundaries=[];combined=None;offset=0
 for m in fragments:
  heads=[a for a in m.GetAtoms() if a.GetAtomicNum()==0 and a.GetAtomMapNum()==1]
  tails=[a for a in m.GetAtoms() if a.GetAtomicNum()==0 and a.GetAtomMapNum()==2]
  assert len(heads)==len(tails)==1
  h,t=heads[0],tails[0];hn,tn=h.GetNeighbors()[0],t.GetNeighbors()[0]
  hb=m.GetBondBetweenAtoms(h.GetIdx(),hn.GetIdx()).GetBondType();tb=m.GetBondBetweenAtoms(t.GetIdx(),tn.GetIdx()).GetBondType()
  boundaries.append((offset+h.GetIdx(),offset+t.GetIdx(),offset+hn.GetIdx(),offset+tn.GetIdx(),hb,tb))
  combined=Chem.Mol(m) if combined is None else Chem.CombineMols(combined,m);offset+=m.GetNumAtoms()
 edit=Chem.RWMol(combined);removed=[]
 for left,right in zip(boundaries,boundaries[1:]):
  assert left[5]==right[4];edit.AddBond(left[3],right[2],left[5]);removed.extend([left[1],right[0]])
 for i in sorted(removed,reverse=True):edit.RemoveAtom(i)
 result=edit.GetMol();Chem.SanitizeMol(result)
 for a in result.GetAtoms():a.SetAtomMapNum(0)
 return Chem.MolToSmiles(result,canonical=True,isomericSmiles=True)

cache=Path('F:/材料边界/growth-source-cache/polyomics-7475')
index=json.loads((cache/'periodic-graph-prototype-r1/periodic-graph-index.json').read_bytes())
word_cache={};word_to_producer=defaultdict(set);producer_to_words={};bad_source_groups=[]
for key,g in index['groups'].items():
 own=set()
 for row in g['source_records']:
  s=row['source_smiles_1']
  if s not in word_cache:word_cache[s]=block_word(s)
  word=word_cache[s][0];own.add(word);word_to_producer[word].add(key)
 producer_to_words[key]=own
 if len(own)!=1:bad_source_groups.append(key)
selected=json.loads(Path('experimental/material-batches/polyomics-density-candidates-20261028/source-fact-candidates.json').read_bytes())['candidates']
nonminimal=[];transformation_failures=[];single_block=0;counts=Counter();selected_words=set()
for row in selected:
 s=row['selected_source_record']['source_smiles_1'];key=row['operational_graph_key_sha256'];word,full=word_cache[s];selected_words.add(word)
 minimum_atoms=sum(Chem.MolFromSmiles(token).GetNumAtoms()-2 for token in word)
 if minimum_atoms!=row['unreviewed_periodic_graph']['primitive_non_dummy_atoms']:nonminimal.append(key)
 # Rebuild an independently minimal single-bond-boundary representation.
 rotations=[word[i:]+word[:i] for i in range(len(word))]
 valid=[]
 for seq in rotations:
  m=Chem.MolFromSmiles(seq[0]);h=next(a for a in m.GetAtoms() if a.GetAtomicNum()==0 and a.GetAtomMapNum()==1)
  if h.GetBonds()[0].GetBondType()==Chem.BondType.SINGLE:valid.append(seq)
 assert valid
 sequence=valid[-1]  # usually shifts the producer's source boundary
 variants=[('primitive_shift',assemble(sequence)),('nonprimitive_double',assemble(sequence*2))]
 for label,variant in variants:
  counts[label]+=1
  try:
   actual=producer.normalize(variant)['periodic_graph_key_sha256']
   if actual!=key:transformation_failures.append((label,key,actual,variant))
  except Exception as error:transformation_failures.append((label,key,str(error),variant))
print(json.dumps({'source_literals':len(word_cache),'source_index_groups':len(index['groups']),'independent_block_necklace_groups':len(word_to_producer),'producer_false_merges':len(bad_source_groups),'producer_extra_split_groups':sum(len(v)-1 for v in word_to_producer.values()),'selected_independent_distinct':len(selected_words),'selected_nonminimal':len(nonminimal),'transformations':dict(counts),'transformation_failures':len(transformation_failures),'failure_examples':transformation_failures[:5]}))
