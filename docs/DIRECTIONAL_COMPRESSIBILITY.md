# Directional hydrostatic compressibility: definitions, range and energy constraint

v0.16.0 adds exactly two **catalog-only** `model_relation` / `relation` records:

- `directional_linear_compressibility_hydrostatic_relation`: directional linear
  compressibility β(n), quantity `directional_linear_compressibility`, dimension
  `inverse_pressure`, SI unit `Pa^-1`
- `normalized_directional_compressibility_range`: r(n)=β(n)/κ, quantity
  `normalized_directional_linear_compressibility`, dimension `dimensionless`,
  SI unit `1`; its definition dependency is the first record

Both have `bound_kind: null` and `evaluation_support: catalog_only`. These are
conditional mathematical relations, not measurements, specimen predictions,
engineering allowables or evidence that every permitted tensor is physically
realizable. Claims schema 1.10.0 gives them a dedicated closed
`hydrostatic_compressibility_contract`. Formula strings and contract metadata
are never executed. The eight executable composite claim/rule pairs are unchanged.

## Scope and sign convention

Assume classical local, finite real, three-dimensional, infinitesimal linear
elasticity at fixed temperature about a stress-free equilibrium. Stiffness C
has minor and major symmetries and is **strictly positive definite on all nonzero
symmetric strains**. Compliance S is the full inverse C⁻¹ on symmetric tensors;
equivalently the full engineering compliance is SPD. Full inversion, rather than
componentwise reciprocation, is required. Definitions and necessary constraints
need no additional elastic symmetry. Directions are unit vectors in orthonormal
Cartesian axes; crystallographic lattice vectors need not form such a basis.

Positive p means compressive pressure; tensile stress and extensional strain are
positive. Apply static hydrostatic **stress** σ=−pI with p>0 sufficiently small.
Then ε=S:σ=−p(S:I). This is an isothermal elastic derivative, not a temperature
change or thermal-expansion response. Anisotropic hydrostatic loading may produce
shear strain. No zero-shear-strain condition, imposed isotropic strain, constrained
volume or prescribed displacement is substituted for hydrostatic stress.

Let B=S:I, that is B_ij=S_ijkk, and let nn=n⊗n. At the reference state,

- β(n)=−dεnn/dp=nn:S:I=nᵀBn
- κ=−d(tr ε)/dp=I:S:I=tr B
- ε=−pB, and to first order ΔV/V=tr ε
- E(n)=1/(nn:S:nn)>0 is the uniaxial-stress Young modulus for **the same S**

S, B, β and κ have units Pa⁻¹; C, E and p have units Pa; β/κ is dimensionless.
The canonical unit is `Pa^-1`: 1 GPa⁻¹=10⁻⁹ Pa⁻¹ and 1 TPa⁻¹=10⁻¹² Pa⁻¹.
These conversions document units, not a new numeric input or conversion API.

β(n)<0 means extension along n under positive hydrostatic pressure. It is
**negative linear compressibility**, not negative volume compressibility,
negative thermal expansion, auxeticity (a uniaxial-stress Poisson response), or
uniaxial strain. A negative isotropic Poisson ratio does not imply β<0.

## Engineering shear convention: recover B before taking extrema

Use engineering-Voigt order (11,22,33,23,13,12):

- e=(ε11,ε22,ε33,2ε23,2ε13,2ε12)
- s=(σ11,σ22,σ33,σ23,σ13,σ12)
- e=S_eng s; s=C_eng e; S_eng=(C_eng)⁻¹
- S_eng,IJ=dI dJ S_ijkl with d=(1,1,1,2,2,2); C_eng,IJ=C_ijkl
- energy density is sᵀS_eng s/2=eᵀC_eng e/2

Thus S_eng,44=4S2323 and S_eng,41=2S2311. Kelvin/Mandel scaling differs and
must be converted consistently. Put h=(1,1,1,0,0,0)ᵀ and g=S_eng h. Then

```text
    [ g1    g6/2  g5/2 ]
B = [ g6/2  g2    g4/2 ]
    [ g5/2  g4/2  g3   ]
```

In particular, **(B23,B13,B12)=(g4,g5,g6)/2**, not (g4,g5,g6). With
v(n)=(n1²,n2²,n3²,n2n3,n1n3,n1n2)ᵀ,

- β(n)=v(n)ᵀS_eng h
- β(n)=n1²g1+n2²g2+n3²g3+n2n3g4+n1n3g5+n1n2g6
- κ=hᵀS_eng h=S11+S22+S33+2(S12+S13+S23), using engineering S

The g4,g5,g6 terms vanish for an orthotropic tensor in its symmetry frame, but
not for a general lower-symmetry tensor or arbitrary rotated frame. The
engineering strain vector itself is not a symmetric 3×3 tensor; its shear
components cannot be used as B's off-diagonal entries without halving.

## P1: positive volume response and the orthonormal sum

This is an **original project derivation** from the stated definitions. Full SPD
gives X:S:X>0 for every nonzero symmetric stress X. Taking X=I gives κ>0;
zero and negative κ are excluded. The symmetric second-order tensor B need not
be positive definite: positive quadratic energy on symmetric stresses does not
make S a positivity-preserving map on positive-definite second-order matrices.

For any orthonormal triad n1,n2,n3, Σa na⊗na=I, so

β(n1)+β(n2)+β(n3)=I:S:I=κ>0.

All three responses in such a triad cannot be nonpositive. This restriction
concerns a triad within the **same tensor**, not unrelated directional values
from different specimens. If the hydrostatic stress-response bulk modulus is
named, K_h=1/κ>0. An imposed isotropic-strain modulus or a generic Voigt/Hill
average is not a substitute for K_h, and no executable composite-rule dependency
is introduced.

## P2: one fixed tensor has a finite, attained spectral interval

This is an **original project derivation**. Finite real symmetric B has real
finite eigenvalues λ1≤λ2≤λ3 and an orthonormal eigenbasis. Its Rayleigh quotient
on the unit sphere has the exact range

β(n) ∈ [λ1,λ3], with β_min=λ1 and β_max=λ3.

Both extrema are attained at associated eigenvectors, and every intervening
value occurs. Since λ1+λ2+λ3=κ>0,

β_min≤κ/3≤β_max, with β_max>0.

At least one principal β is positive; at most two principal values can be
negative (or nonpositive). Zero principal values are allowed even though the
**full fourth-order compliance** is strictly positive definite. This is not
“at most two negative directions”: if a negative value occurs, continuity gives
an open set of negative directions on the unit sphere.

All directional values are equal if and only if B=(κ/3)I. That is isotropy of
the hydrostatic response, not necessarily full elastic isotropy. Dividing the
fixed tensor's interval by its positive κ gives finite attained extrema of r.
The uniform spherical mean is β̄=κ/3, from the mean of ni nj being δij/3;
this explanatory consequence does not add a catalog claim.

## P3: every finite real normalized value, even at fixed positive κ

The following explicit construction is **original project algebra**, not a
numbered theorem or proof transcribed from Ortiz or Miller. Choose any finite
real dimensionless q, any prescribed s0>0 in Pa⁻¹, and any finite dimensionless
t>0. Define the three-vectors and projector

u=(1,1,1)ᵀ, a=(q,(1−q)/2,(1−q)/2)ᵀ, P=I3−uuᵀ/3.

Here uᵀa=1 and P projects orthogonally onto the plane perpendicular to u.
Use the block-diagonal engineering compliance

S_eng=s0 diag_blocks(aaᵀ+tP, I3),

with zero normal–shear couplings. For a real normal-stress vector x,

xᵀ(aaᵀ+tP)x=(a·x)²+t‖Px‖².

If this is zero, Px=0 implies x=cu. Then a·x=c because a·u=1, so c=0
and x=0. Thus the normal block is SPD. The positive shear block makes the
entire six-dimensional compliance SPD. Every entry and the inverse stiffness
are finite for finite q,s0,t. Engineering conversion yields a classical tensor
with the required symmetries and **at least orthotropic** symmetry in this frame;
no exact-symmetry claim is needed at special q. The normal-block determinant is
s0³t²/3>0.

Multiplying by h gives S_eng h=s0(a,0,0,0)ᵀ. Therefore

- B=s0 diag(a)
- κ=s0, independently of q and t
- β(e1)=s0 q, hence β(e1)/κ=q

Every finite real normalized value is therefore attained, **even for any fixed
positive κ chosen in advance**. Over varying finite full-SPD 3D tensors, the
range is all finite real numbers, unbounded below and above. Neither infinity
is attained. This does not give an infinite response or unbounded directional
extrema for one fixed finite tensor.

Under pressure p>0, ε=−p s0 diag(a). For any sufficiently small dimensionless
η>0 choose p=η/(s0‖a‖). Then ‖ε‖F=η. Large |q| is compatible with the
infinitesimal model by reducing pressure consistently; it supplies no useful
finite operating-pressure range for an actual material.

Any finite triplet a with sum 1 works in the same proof. Synthetic examples
(−1,1,1), (−1,−1,3) and (1,0,0) give one negative principal response, two
negative principal responses and two zero principal responses, respectively.
They are mathematical constructions, not measured material data. This existence
proof establishes no atomic structure, microstructure, manufacturing route or
microscopic realizability for any prescribed q.

## P4: strict energy inequality, necessary and not sufficient

This is an **original project derivation**. Major symmetry and full SPD make
⟨X,Y⟩S=X:S:Y an inner product on symmetric tensors. N=n⊗n has rank one
and I rank three, so they are linearly independent in three dimensions.
Strict Cauchy–Schwarz gives

(N:S:I)²<(N:S:N)(I:S:I),

or, equivalently,

**β(n)²<κ/E(n)** and **r(n)²<1/[κE(n)]**.

Every quantity must use the **same S and n**. Equality is impossible under the
stated premises; β=0 is allowed. The constraint is necessary, not sufficient
for full SPD: checking this two-tensor subspace does not establish positive
energy on every symmetric stress. Nor does it impose a universal finite
numerical bound, because κE(n) varies over the unrestricted tensor class.
For P3, E(e1)=1/[s0(q²+2t/3)], so the normalized inequality is
q²<q²+2t/3, with a strictly positive gap.

## P5: cubic and isotropic elasticity give exactly 1/3

This specialization is project algebra corroborated by the inspected cubic
formula in Ortiz et al. For cubic stiffness,

C:I=(C11+2C12)I, with C11+2C12>0 under full SPD.

Hence B=I/(C11+2C12), β(n)=1/(C11+2C12)>0,
κ=3/(C11+2C12), and **β(n)/κ=1/3 for every direction**. A cubic tensor need
not be elastically isotropic to have this isotropic hydrostatic response.

For isotropic elasticity, β=1/(3K)=(1−2ν)/E and κ=1/K=3(1−2ν)/E,
again giving r=1/3. Negative isotropic ν does not produce negative β.
Unboundedness over the unrestricted tensor class cannot be transferred to
every symmetry subclass. In particular, the earlier cubic directional-Poisson
unboundedness is a different loading/response statement and gives no cubic NLC.
No classification of all crystal-symmetry subclasses is asserted here.

## Exclusions and scientific limits

Exclude prestress, finite-strain tangents, two-dimensional elasticity,
plane-stress/plane-strain constitutive reductions, complex viscoelasticity,
nonlocal/Cosserat models, singular/positive-semidefinite/indefinite tensors,
internal instabilities, phase transitions and branch switching. Also exclude
metastable or constrained negative-bulk systems, pressure-medium infiltration
or mass exchange, swelling, and active/nonconservative systems.

Full homogeneous elastic SPD is a mathematical premise, not proof of complete
phonon, thermodynamic, finite-amplitude, strength or finite-temperature stability.
There is no tensor-input API, inversion service, eigenvalue solver, extremum
search, material-specific prediction, compressibility plot or new executable
composite rule. The construction, exact algebra checks and software validation
do not replace independent scientific peer review. Independent scientific and
native-language review remain unperformed.

## Source-specific evidence and rights

- [Ortiz, Boutin, Fuchs and Coudert (2012), Physical Review Letters 109, 195502](https://doi.org/10.1103/PhysRevLett.109.195502),
  “Anisotropic Elastic Properties of Flexible Metal-Organic Frameworks: How Soft
  are Soft Porous Crystals?” Source ID `ortiz_2012_anisotropic_mof_elasticity`.
  The relevant [author-hosted published PDF](https://www.coudert.name/papers/10.1103_PhysRevLett.109.195502.pdf)
  pages were visually checked: printed 195502-2, Eqs. (2)–(3), for E(n), β(n)
  and full compliance; printed 195502-4, left column, for cubic β, and the
  final long paragraph for the local elastic-region caveat. Publisher metadata
  and rights were checked. ©2012 American Physical Society; no general reuse
  license verified. Source material values, phase transitions and unrelated
  averaging/shear wording are not imported.
- [Miller, Evans and Marmier (2015), Applied Physics Letters 106(23), 231903](https://doi.org/10.1063/1.4922460),
  “Negative linear compressibility in common materials.” Source ID
  `miller_evans_marmier_2015_linear_compressibility`. The
  [institutional author manuscript](https://uwe-repository.worktribe.com/index.php/preview/843503/NLC_CommMat.pdf)
  was checked **as text only**: manuscript p. 4, Eq. (1) and adjoining isothermal
  definitions for volume compressibility, and Eq. (2) for the explicitly
  orthorhombic/orthotropic specialization; p. 5 distinguishes small-strain
  elastic estimates from higher-pressure behavior. Canonical bibliographic
  metadata was checked through Crossref. Page-image verification failed and
  direct download returned HTTP 403; this denial was respected. No visual
  inspection or equivalence to published pagination is claimed. No general
  reuse license was verified; the repository index reports ©2015 AIP Publishing
  LLC, and the Crossref license field was absent.

Neither source is credited with the original all-real normalized-range theorem,
its fixed-κ construction, the full general strict inequality proof or independent
review of this catalog. Only bibliographic facts, mathematical formulas and
original curation/derivation notes are included. No source PDF, page image,
figure or extracted article full text enters the repository or package. Access
is not a redistribution license. Original project code, documentation and
curation use MIT; third-party works retain their own rights. NIST cryogenic
coefficients are omitted conservatively, with current curated-collection status
and reuse uncertainty described in [the notices](../THIRD_PARTY_NOTICES.md).

## Lookup and contribution boundary

```sh
python -m materials_boundaries catalog claims --id directional_linear_compressibility_hydrostatic_relation --text --lang en
python -m materials_boundaries catalog claims --id normalized_directional_compressibility_range --json
python -m materials_boundaries catalog claims --query compressibility --text --lang de
python -m materials_boundaries catalog sources --id ortiz_2012_anisotropic_mof_elasticity --text --lang zh
```

The closed contract separates the definition/trace/fixed-tensor family from the
normalized-class-range/necessary-energy family. Same-family additions require
the exact scientific contract, compatible definition dependency, evidence and
authored names in all four languages; different scope requires scientific and
schema review. `inverse_pressure` is paired with `Pa^-1` for dimensional
compressibility and compliance, never Pa or dimensionless `1`. Catalog lookup
adds no evaluation or material-applicability state. See [migration](MIGRATION_v0.16.0.md)
and [contributing](../CONTRIBUTING.md).

## Four-language scientific summary

### English

At fixed temperature, apply σ=−pI with compression-positive p>0 to finite real,
full-SPD, stress-free 3D classical small-strain elasticity. With the full inverse
S, β(n)=nn:S:I may be negative although κ=I:S:I>0; every orthonormal triad
sums to κ. For one fixed tensor the range is the finite attained eigenvalue
interval of B=S:I. At most two principal values may be negative, not at most two
directions. In engineering order (11,22,33,23,13,12), g=S_eng(1,1,1,0,0,0)ᵀ
has B's off-diagonals (g4,g5,g6)/2. Across unrestricted tensors every finite
β/κ is attainable, even at fixed positive κ; cubic and isotropic tensors instead
have β/κ=1/3. The strict same-tensor inequality β²<κ/E is necessary, not
sufficient for full SPD. NLC is extension under hydrostatic pressure, not negative
volume/thermal response or auxeticity. The exclusions above apply; no evaluator
or material prediction is added. Ortiz equation pages were visually checked;
Miller manuscript equations were text-checked only. The project proofs and
translations have no independent scientific or native-language review.

### 中文

固定温度下，在无初始应力、有限实数、完整弹性张量严格正定的三维经典
线性小应变范围内，施加静水应力 σ=−pI，p>0 以压缩为正，应力以拉伸为正，
应变以伸长为正。S 是完整刚度的逆；β(n)=nn:S:I 可为负，但 κ=I:S:I>0。
任意正交归一方向三元组的 β 之和为 κ。固定张量的方向范围是 B=S:I 的
有限且可取到的最小、最大特征值区间。“至多两个负主值”不是“至多两个负方向”；
负响应可覆盖球面上的开集。工程 Voigt 顺序为 (11,22,33,23,13,12)，
g=S_eng(1,1,1,0,0,0)ᵀ 时，(B23,B13,B12)=(g4,g5,g6)/2。
β、κ 和 S 的单位为 Pa⁻¹，β/κ 无量纲。

在不额外限定对称性的有限全正定张量类中变化张量时，即使固定任意正 κ，
β/κ 也可取任意有限实数；无穷大不取到。立方与各向同性张量则恒有 β/κ=1/3。
同一 S、同一方向的严格约束 β²<κ/E 是必要条件，不足以判定完整张量正定，
不能与其他材料的 E 或 κ 拼接。负线压缩率表示正静水压力下沿某方向伸长，
不同于负体积压缩率、负热膨胀或负泊松比；静水应力不等于施加各向同性应变。
各向异性静水加载可能引起剪切应变，不能强制其为零。

排除预应力、有限应变切线、二维及平面应力／应变约化、复黏弹性、非局域／
Cosserat 理论、奇异／半正定／不定张量、内部失稳、相变及分支跳转，也排除
受约束或亚稳负体积系统、压力介质渗入／质量交换、溶胀和主动非保守系统。
全正定不证明完整声子、热力学、有限振幅、强度或有限温度稳定性。仅供目录查询，
无张量求逆、特征值／极值求解器或材料预测。Ortiz 相关出版页已视觉核对；
Miller 作者稿公式仅核对文本，不能标成视觉核验。全实数范围与其他项目证明
均为原创推导，软件和代数检查不是独立科学同行评审；译文尚未经母语审校。
不附来源 PDF、图像或全文，不推断再分发许可。

### 日本語

一定温度で、無応力の基準状態にある有限実数・完全正定値の三次元古典的
微小ひずみ線形弾性を考える。圧縮を正とする p>0 に対し σ=−pI を加え、
引張応力と伸長ひずみを正とする。完全な逆テンソル S を使うと β(n)=nn:S:I
は負になり得るが、κ=I:S:I>0 である。任意の正規直交三方向の和は κ。
固定テンソルでは B=S:I の最小・最大固有値が有限かつ達成され、方向範囲の
両端になる。「負の主値は最大二つ」は「負の方向は最大二つ」ではなく、
負の応答を持つ方向は球面上の開集合になり得る。工学 Voigt 順序
(11,22,33,23,13,12) で g=S_eng(1,1,1,0,0,0)ᵀ とすると、
(B23,B13,B12)=(g4,g5,g6)/2。β、κ、S の単位は Pa⁻¹、β/κ は無次元である。

対称性を追加制限せず有限完全正定値テンソル全体を変化させれば、任意の
正の κ を固定しても β/κ は任意の有限実数を実現する。無限大は達成しない。
一方、立方晶・等方弾性ではすべての方向で β/κ=1/3。同じ S と方向に対する
厳密な不等式 β²<κ/E は必要条件であり、完全な正定値性の十分条件ではない。
異なる材料の E や κ を混用してはいけない。負の線圧縮率は静水圧による方向別
伸長であり、負の体積圧縮率、負の熱膨張、負のポアソン比とは異なる。
静水応力を等方ひずみの拘束に置き換えず、誘起されるせん断ひずみも禁止しない。

初期応力、有限ひずみ接線、二次元・平面応力／ひずみ縮約、複素粘弾性、
非局所／Cosserat 理論、特異・半正定値・不定値テンソル、内部不安定性、相転移、
分枝の切替えは対象外。準安定・拘束された負の体積応答、圧力媒体の浸入・質量交換、
膨潤、能動的・非保存系も除外する。完全正定値性は全フォノン、熱力学、有限振幅、
強度、有限温度での安定性を保証しない。カタログのみで、逆行列・固有値・極値の
計算機能や材料予測は追加しない。Ortiz の関連出版ページは画像で確認したが、
Miller の著者原稿の式はテキスト確認のみ。全実数範囲などの証明は本プロジェクトの
独自導出であり、代数・ソフトウェア検査は独立した科学的査読ではない。母語校閲も
未実施。出典 PDF、画像、全文を同梱せず、再配布許諾を推定しない。

### Deutsch

Bei fester Temperatur gilt für endliche reelle, vollständig positiv definite
klassische 3D-Elastizität mit kleinen Dehnungen um einen spannungsfreien Zustand:
σ=−pI mit kompressionspositivem p>0; Zugspannung und Verlängerung sind positiv.
Mit dem vollständigen inversen Tensor S darf β(n)=nn:S:I negativ sein, während
κ=I:S:I>0 bleibt. Für jedes orthonormale Richtungstripel ist die Summe κ.
Ein fester Tensor besitzt das endliche, angenommene Eigenwertintervall von B=S:I
als Richtungsbereich. Höchstens zwei negative Hauptwerte bedeuten nicht höchstens
zwei negative Richtungen; eine offene Richtungsmenge kann β<0 haben. In der
technischen Voigt-Reihenfolge (11,22,33,23,13,12), mit g=S_eng(1,1,1,0,0,0)ᵀ,
gilt (B23,B13,B12)=(g4,g5,g6)/2. β, κ und S haben die Einheit Pa⁻¹;
β/κ ist dimensionslos.

Über die uneingeschränkte endliche SPD-Tensorklasse ist jeder endliche reelle
Wert von β/κ erreichbar, sogar bei beliebig vorgegebenem festem κ>0. Unendliche
Werte werden nicht angenommen. Kubische und isotrope Elastizität liefert dagegen
stets β/κ=1/3. Die strikte Ungleichung β²<κ/E muss denselben Tensor und dieselbe
Richtung verwenden; sie ist notwendig, aber nicht hinreichend für vollständige
SPD. Negative lineare Kompressibilität bedeutet Verlängerung unter hydrostatischem
Druck, nicht negative Volumenkompressibilität, negative Wärmeausdehnung oder
Auxetik. Hydrostatische Spannung darf nicht durch vorgeschriebene isotrope
Dehnung ersetzt werden; induzierte Scherdehnung ist zulässig.

Ausgeschlossen sind Vorspannung, Tangenten bei endlicher Dehnung, 2D- und ebene
Spannungs-/Dehnungsreduktionen, komplexe Viskoelastizität, nichtlokale/Cosserat-
Theorien, singuläre/semidefinite/indefinite Tensoren, innere Instabilitäten,
Phasenübergänge und Zweigwechsel. Ebenso ausgeschlossen: metastabile oder
zwangsgeführte negative Volumenantworten, Eindringen des Druckmediums/Massenaustausch,
Quellung und aktive/nichtkonservative Systeme. Vollständige SPD beweist keine
vollständige Phononen-, thermodynamische, endliche-Amplituden-, Festigkeits- oder
Finite-Temperatur-Stabilität. Nur Katalogangaben, kein Tensor-, Eigenwert- oder
Extremwertlöser und keine Materialvorhersage. Ortiz-Seiten wurden visuell geprüft;
Miller-Manuskriptgleichungen nur als Text. Die Beweise sind eigenständige
Projektherleitungen ohne unabhängige wissenschaftliche Begutachtung; auch eine
muttersprachliche Prüfung steht aus. Keine Quellen-PDFs, Bilder oder Volltexte
werden gebündelt, und keine Weiterverwendungsrechte werden unterstellt.
