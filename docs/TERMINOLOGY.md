# Scientific terminology / 科学术语 / 科学用語 / Wissenschaftliche Begriffe

Machine-assisted terminology, not independently scientifically or linguistically reviewed. All translations refer to the same canonical keys in `materials_boundaries/data/locales.json`; formulas and unit IDs remain unchanged.

机器辅助术语，尚未经独立科学审校或语言审校。各语言共用同一组规范键，公式和单位标识符保持不变。

機械支援で作成した用語集であり、独立した科学的・言語的な校閲は受けていません。各言語で同じ正規キーを使用し、数式と単位 ID は変更しません。

Maschinell unterstützte Terminologie ohne unabhängige fachliche oder sprachliche Prüfung. Alle Sprachen verwenden dieselben kanonischen Schlüssel; Formeln und Einheiten-IDs bleiben unverändert.

## Aligned labels

| Canonical key | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `theoretical_bound` | Theoretical bound | 理论界限 | 理論的な上下界 | Theoretische Schranke |
| `model_prediction` | Model prediction | 模型预测 | モデル予測 | Modellvorhersage |
| `experimental_record` | Experimental record | 实验记录 | 実験記録 | Experimenteller Datensatz |
| `engineering_limit` | Engineering limit | 工程限值 | 工学的制約値 | Technischer Grenzwert |
| `uncertainty` | Uncertainty | 不确定性 | 不確かさ | Unsicherheit |
| `applicability_unknown` | Applicability unknown | 适用性未知 | 適用条件の充足状況が不明 | Anwendbarkeit unbekannt |
| `bulk_modulus` | Bulk modulus | 体积模量 | 体積弾性率 | Kompressionsmodul |
| `shear_modulus` | Shear modulus | 剪切模量 | せん断弾性率 | Schubmodul |
| `youngs_modulus` | Young’s modulus | 杨氏模量 | ヤング率 | Elastizitätsmodul |
| `poissons_ratio` | Poisson’s ratio | 泊松比 | ポアソン比 | Poissonzahl |
| `youngs_modulus_outer` | Young’s modulus derived outer envelope | 杨氏模量推导外包络 | ヤング率の導出した外側包絡 | Abgeleitete äußere Einhüllung des Elastizitätsmoduls |
| `poissons_ratio_outer` | Poisson’s ratio derived outer envelope | 泊松比推导外包络 | ポアソン比の導出した外側包絡 | Abgeleitete äußere Einhüllung der Poissonzahl |
| `volume_fraction` | Volume fraction | 体积分数 | 体積分率 | Volumenanteil |
| `constituent_symmetry` | Constituent symmetry | 组成相的对称性 | 構成相の対称性 | Symmetrie der Einzelphasen |
| `effective_symmetry` | Effective-medium symmetry | 等效介质的对称性 | 有効媒質の対称性 | Symmetrie des effektiven Mediums |
| `lower_bound` | Lower bound | 下界 | 下界 | Untere Schranke |
| `upper_bound` | Upper bound | 上界 | 上界 | Obere Schranke |
| `premise` | Premise | 前提条件 | 前提条件 | Voraussetzung |
| `well_ordered` | Well-ordered phases | 良序相 | 弾性率の大小関係が揃った相 | Gleichsinnig geordnete Phasen |

Here, `K` denotes bulk modulus, `G` denotes shear modulus, and `f` denotes volume fraction. For the supported ordering, phases can be labeled so that `K1 <= K2` and `G1 <= G2` simultaneously. The phase with the lower `K` must not have the higher `G`. Constituent isotropy and effective-medium isotropy are separate premises; one must not silently substitute for the other.

这里，`K` 为体积模量，`G` 为剪切模量，`f` 为体积分数。“良序”指两相可同时满足 `K1 <= K2` 和 `G1 <= G2`，即两种模量的排序一致。组成相各向同性与等效介质各向同性是不同的前提，不能相互替代。

`K` は体積弾性率、`G` はせん断弾性率、`f` は体積分率です。対応する順序は、`K1 <= K2` と `G1 <= G2` が同時に成立することを意味します。構成相の等方性と有効媒質の等方性は別の前提であり、一方を他方の代わりに用いてはいけません。

`K` bezeichnet den Kompressionsmodul, `G` den Schubmodul und `f` den Volumenanteil. Die unterstützte Ordnung verlangt gleichzeitig `K1 <= K2` und `G1 <= G2`. Die Isotropie der Einzelphasen und die des effektiven Mediums sind getrennte Voraussetzungen und dürfen nicht gleichgesetzt werden.

## Four different kinds of statement

### English

- **Theoretical bound:** a mathematical lower or upper constraint under explicit premises. It does not select a unique property value or guarantee attainability for a specified specimen
- **Model prediction:** a value or distribution estimated by a specified model for specified inputs; it is not automatically a rigorous bound
- **Experimental record:** a measurement record with specimen, method, conditions, and uncertainty when available; it is not a universal material limit
- **Engineering limit:** a design, operating, manufacturing, or acceptance constraint for a particular use; it is not automatically a mathematical theorem

### 简体中文

- **理论界限：** 在明确前提下成立的数学下界或上界，不确定唯一的性能值，也不保证指定试样能够达到该界限
- **模型预测：** 指定模型针对指定输入估计的数值或分布，不会自动构成严格的数学界限
- **实验记录：** 包括试样、方法、条件及可获取的不确定性信息的测量记录，不是普适的材料极限
- **工程限值：** 针对特定用途的设计、运行、制造或验收约束，不会自动构成数学定理

### 日本語

- **理論的な上下界：** 明示された前提の下で成り立つ数学的な下界または上界。特性値を一意に決めるものではなく、特定の試験片での到達可能性も保証しません
- **モデル予測：** 指定したモデルが指定した入力に対して推定する値または分布。それだけで厳密な上下界になるわけではありません
- **実験記録：** 試験片、方法、条件、入手可能な不確かさの情報を含む測定記録。普遍的な材料限界を示すものではありません
- **工学的制約値：** 特定の用途における設計、運用、製造、受入れの制約。それだけで数学的な定理になるわけではありません

### Deutsch

- **Theoretische Schranke:** eine mathematische untere oder obere Schranke unter ausdrücklichen Voraussetzungen. Sie bestimmt keinen eindeutigen Eigenschaftswert und garantiert keine Erreichbarkeit für eine bestimmte Probe
- **Modellvorhersage:** ein von einem bestimmten Modell für bestimmte Eingaben geschätzter Wert oder eine Verteilung; nicht automatisch eine mathematisch gesicherte Schranke
- **Experimenteller Datensatz:** eine Messaufzeichnung mit Probe, Methode, Bedingungen und, soweit verfügbar, Unsicherheitsangaben; keine allgemeingültige Materialgrenze
- **Technischer Grenzwert:** eine Vorgabe für Auslegung, Betrieb, Herstellung oder Abnahme in einer bestimmten Anwendung; nicht automatisch ein mathematischer Satz

## Applicability is not uncertainty

| Canonical status | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `satisfied` | Satisfied | 满足 | 充足 | Erfüllt |
| `violated` | Violated | 不满足 | 不充足 | Verletzt |
| `unknown` | Unknown | 未知 | 不明 | Unbekannt |

- **English:** `satisfied` means the supplied inputs support every implemented premise. `violated` means at least one premise conflicts with them. `unknown` means evidence is missing. These are logical applicability states, not confidence levels or uncertainty intervals. This MVP does not quantify or propagate uncertainty
- **简体中文：** `satisfied` 表示提供的输入支持所有已实现检查的前提；`violated` 表示至少一个前提与输入冲突；`unknown` 表示缺少证据。这些是逻辑上的适用性状态，不是置信水平或不确定性区间。本 MVP 不量化或传播不确定性
- **日本語：** `satisfied` は入力が実装されたすべての前提を支持すること、`violated` は少なくとも一つの前提と矛盾すること、`unknown` は証拠の不足を意味します。論理的な適用状態であり、信頼度や不確かさ区間ではありません。この MVP は不確かさの定量化や伝播計算を行いません
- **Deutsch:** `satisfied` bedeutet, dass die Eingaben alle implementierten Voraussetzungen stützen. `violated` zeigt einen Widerspruch zu mindestens einer Voraussetzung an. `unknown` bedeutet fehlende Belege. Dies sind logische Anwendbarkeitszustände, keine Konfidenzniveaus oder Unsicherheitsintervalle. Dieses MVP quantifiziert Unsicherheiten nicht und berechnet keine Unsicherheitsfortpflanzung

## Derived outer envelope / 推导外包络 / 導出した外側包絡 / Abgeleitete äußere Einhüllung

- **English:** The E/ν envelopes come from separate compatible HS K/G intervals for the same system. E = 9KG/(3K+G) increases in K and G; ν = (3K−2G)/(2(3K+G)) increases in K and decreases in G. Combining interval corners gives a conservative outer envelope, not necessarily a tight or jointly attainable bound. ν uses dimensionless unit `1`, may be negative or zero, and must satisfy −1 < ν < 0.5. A rounded boundary is a numerical error, not a valid physical endpoint
- **简体中文：** E/ν 外包络由同一体系分别成立、条件兼容的 HS K/G 区间推导。E = 9KG/(3K+G) 随 K、G 增加而增加；ν = (3K−2G)/(2(3K+G)) 随 K 增加而增加，随 G 增加而减小。组合区间端点得到保守外包络，不保证界紧或联合可达。ν 使用无量纲单位 `1`，可为负或零，须满足 −1 < ν < 0.5。舍入到边界是数值错误，不是有效物理端点
- **日本語：** E/ν の外側包絡は、同一系で条件が整合する個別の HS K/G 区間から導きます。E = 9KG/(3K+G) は K・G の両方に対して増加し、ν = (3K−2G)/(2(3K+G)) は K に対して増加、G に対して減少します。区間の端点の組合せで得られる保守的な外側包絡は、厳密な同時到達領域の限界や同時到達可能性を保証しません。ν は無次元の単位 `1` で負値やゼロも可能ですが、−1 < ν < 0.5 が必要です。境界への丸めは数値エラーであり、有効な物理的端点ではありません
- **Deutsch:** Die E/ν-Einhüllungen entstehen aus getrennten, miteinander vereinbaren HS-K/G-Intervallen desselben Systems. E = 9KG/(3K+G) steigt mit K und G; ν = (3K−2G)/(2(3K+G)) steigt mit K und fällt mit G. Die Kombination von Intervallendpunkten liefert eine konservative äußere Einhüllung, nicht zwingend eine scharfe oder gleichzeitig erreichbare Schranke. ν hat die dimensionslose Einheit `1`, darf negativ oder null sein und muss −1 < ν < 0.5 erfüllen. Ein gerundeter Randwert ist ein numerischer Fehler, kein gültiger physikalischer Endpunkt

Across all four languages, `scalar_modulus_bound` and `derived_outer_envelope` remain canonical bound-kind IDs. Unknown or violated prerequisites suppress numerical results; derived records use only HS dependencies and do not fall back to Reuss/Voigt for unordered phases. None of these elastic-modulus statements is a bound on strength, failure or plasticity.

## Catalog classification in v0.3.0

The four conceptual statement categories above are not a claim that all four are implemented as catalog types. In v0.3.0, the `claim_type` enum had exactly three values:

| Canonical `claim_type` | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `theoretical_bound` | Theoretical bound | 理论界限 | 理論的な上下界 | Theoretische Schranke |
| `derived_outer_envelope` | Derived outer envelope | 推导外包络 | 導出した外側包絡 | Abgeleitete äußere Einhüllung |
| `model_estimate` | Model estimate | 模型估计 | モデル推定 | Modellschätzung |

`model_prediction` above is a conceptual/display term, not an accepted `claim_type` filter value. The six K/G records are `theoretical_bound`; the two E/ν records are `derived_outer_envelope`; the two fracture records are `model_estimate`. Legacy `bound_kind` remains `scalar_modulus_bound` or `derived_outer_envelope` for the original eight records and is null for the fracture models. A model's `direction: prediction` does not make it an upper/lower bound.

| Canonical metadata | Meaning |
| --- | --- |
| `evaluation_support: composite_evaluate` | The current composite evaluator supports the record |
| `evaluation_support: catalog_only` | Read-only model metadata; no runtime applicability check or numerical result |
| `quantity_dimension: pressure`, `si_unit: Pa` | Pressure-valued output quantity, including critical remote tensile stress |
| `quantity_dimension: dimensionless`, `si_unit: 1` | Dimensionless output quantity, including Poisson's ratio |

## Critical remote tensile stress / 临界远场拉应力 / 臨界遠方引張応力 / Kritische Fernzugspannung

- **English:** The two catalog-only Griffith/LEFM estimates describe a central through-crack in a homogeneous isotropic linear-elastic body under remote mode-I tension, in a sufficiently wide/infinite plate with a small yielding/process zone. σc = sqrt(E_prime Gc/(πa)); E_prime = E for plane stress and E/(1−ν²) for plane strain. a is half the total crack length 2a. Gc is critical energy release rate, distinct from shear modulus G; Gc = 2γ only for ideal pure brittle fracture with surface creation as the sole dissipation. This is not a universal tensile-strength upper bound or engineering allowable, and the continuum expression does not apply at atomic scales or as a → 0
- **简体中文：** 两条仅目录的 Griffith/LEFM 模型描述足够宽／无限大板中，均匀各向同性线弹性材料的中央贯穿裂纹在远场 I 型拉伸及小屈服区／过程区前提下的临界应力。σc = sqrt(E_prime Gc/(πa))；平面应力 E_prime = E，平面应变 E_prime = E/(1−ν²)。a 为裂纹总长 2a 的一半。Gc 是临界能量释放率，不是剪切模量 G；只有表面生成是唯一耗散的理想纯脆性情况才有 Gc = 2γ。模型不是普适抗拉强度上界或工程许用应力；原子尺度和 a → 0 不在连续介质公式的适用范围内
- **日本語：** 二つのカタログ専用 Griffith/LEFM モデルは、十分に広い／無限大の板で、均質・等方線形弾性材料の中央貫通き裂に遠方モード I 引張りが作用し、降伏域／プロセスゾーンが小さい場合を記述します。σc = sqrt(E_prime Gc/(πa)) で、平面応力では E_prime = E、平面ひずみでは E_prime = E/(1−ν²) です。a は全き裂長 2a の半分です。Gc は臨界エネルギー解放率であり、せん断弾性率 G とは異なります。Gc = 2γ は表面形成のみが散逸となる理想的な完全脆性の場合に限ります。普遍的な引張強さの上界や設計許容応力ではなく、原子スケールや a → 0 に連続体の式を適用してはいけません
- **Deutsch:** Die beiden katalogbasierten Griffith-/LEFM-Schätzungen beschreiben einen mittigen Durchriss im homogen-isotropen linear-elastischen Körper bei Mode-I-Fernzug, in einer ausreichend breiten/unendlichen Platte und bei kleiner plastischer Zone/Prozesszone. σc = sqrt(E_prime Gc/(πa)); E_prime = E bei ebenem Spannungszustand und E/(1−ν²) bei ebenem Verzerrungszustand. a ist die halbe Gesamtrisslänge 2a. Gc bezeichnet die kritische Energiefreisetzungsrate, nicht den Schubmodul G; Gc = 2γ gilt nur im ideal rein spröden Fall mit Oberflächenbildung als einziger Dissipation. Dies ist keine universelle obere Zugfestigkeitsschranke oder zulässige Bemessungsspannung; die Kontinuumsformel gilt nicht auf atomarer Skala oder für a → 0

A catalog entry does not supply or verify specimen conditions and does not produce `satisfied`, `violated`, or `unknown` instance states. Unknown or violated premises cannot justify applying the model. Preserve this distinction in every language. See [fracture models](FRACTURE_MODELS.md) and [catalog migration](MIGRATION_v0.3.0.md).

## v0.5.0 stability catalog terms

| Canonical | English | 中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| stability_criterion | Elastic stability criterion | 弹性稳定性判据 | 弾性安定性の判定条件 | Elastisches Stabilitätskriterium |
| logical_predicate | Logical predicate | 逻辑谓词 | 論理述語 | Logisches Prädikat |
| constraint | Strict constraint | 严格约束 | 厳密な制約 | Strikte Bedingung |

Predicates have no physical output SI unit; stiffness coefficients use Pa, quadratic/cubic margins use Pa^2/Pa^3. These terms do not denote a computed material stability assessment. Translations await independent review.


## v0.6.0 porous solid/void terminology

These explanatory terms describe catalog metadata, not new accepted input keys or calculated results.

| Concept | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `p` | Porosity / void volume fraction | 孔隙率／孔隙体积分数 | 空隙率／空隙体積分率 | Porosität / Hohlraumvolumenanteil |
| `1-p` | Solid volume fraction | 固相体积分数 | 固相体積分率 | Feststoffvolumenanteil |
| `Ks`, `Gs` | Solid bulk and shear moduli | 固体体积与剪切模量 | 固体の体積・せん断弾性率 | Kompressions- und Schubmodul des Feststoffs |
| Finite-porosity envelope | Full formula at specified porosity | 指定孔隙率下的完整包络 | 指定空隙率での完全な包絡 | Vollständige Einhüllung bei gegebener Porosität |
| Disconnected solid | Solid without a macroscopic load path | 无宏观承载通路的不连通固体 | 巨視的な荷重経路を持たない非連結固体 | Nicht zusammenhängender Feststoff ohne makroskopischen Lastpfad |

- **English:** The porous catalog uses p for void fraction; Roberts–Garboczi uses solid fraction. For 0<p<1 the geometry-unrestricted lower endpoints are zero; p=0 collapses to pure-solid values. p=1 is formal empty stiffness with no Poisson ratio or specific moduli. Preserve isotropy during zero-phase regularization. Density requires a fixed solid and massless void; low-density asymptotes are not finite-density upper bounds. Separate K/G bounds and the Young outer envelope promise no joint attainment or runtime evaluation
- **简体中文：** 孔隙目录的 p 是孔隙体积分数，Roberts–Garboczi 原文使用固相分数。0<p<1 的任意几何下界为零；p=0 收缩为纯固体值。p=1 是形式上的空域零刚度，不定义泊松比或比模量。正刚度趋零过程须保持各向同性。密度关系要求固定固体与无质量孔隙；低密度渐近式不是有限密度上界。分别成立的 K/G 界及杨氏模量外包络不保证联合可达，也不提供运行时评价
- **日本語：** 空隙カタログの p は空隙体積分率ですが、Roberts–Garboczi の原文では固相分率です。0<p<1 で形状を制限しない下界はゼロ、p=0 では純固体の値に一致します。p=1 は形式的な空領域のゼロ剛性で、ポアソン比や比弾性率は定義しません。ゼロ剛性への正則化では等方性を維持します。密度の関係には一定の固体密度と質量のない空隙が必要で、低密度漸近式は有限密度の上界ではありません。個別の K/G 上下界とヤング率の外側包絡は同時到達や実行時評価を保証しません
- **Deutsch:** Im porösen Katalog ist p der Hohlraumanteil, bei Roberts–Garboczi der Feststoffanteil. Für 0<p<1 sind die geometrieunabhängigen unteren Endpunkte null; bei p=0 gelten die reinen Feststoffwerte. p=1 bezeichnet formal einen leeren Bereich ohne Steifigkeit, Poissonzahl oder spezifische Moduln. Die Nullphasen-Regularisierung muss die Isotropie erhalten. Die Dichtebeziehung setzt unveränderten Feststoff und masselosen Hohlraum voraus; Niedrigdichte-Asymptoten sind keine oberen Schranken bei endlicher Dichte. Getrennte K/G-Schranken und die äußere Einhüllung für E behaupten weder gemeinsame Erreichbarkeit noch ausführbare Auswertung

The current five `claim_type` values are `theoretical_bound`, `derived_outer_envelope`, `model_estimate`, `model_relation` and `stability_criterion`. v0.6.0 reuses the first two with `evaluation_support: catalog_only`; classification alone must not select an evaluator. All three porous intervals have pressure dimension and Pa. Their p parameter uses dimensionless unit `1`; this does not introduce an effective Poisson-ratio record. See [scientific definitions](POROUS_BOUNDS.md).

## v0.7.0 model-dependent observations

The observations catalog is separate from the five-value `claim_type` enum. These are source-reported property summaries, not new claim types or executable rules. The word “experimental” does not erase model dependence.

| Canonical concept | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `experiment_derived_model_dependent` | Experiment-derived, model-dependent observation | 实验导出、模型依赖的观测 | 実験から導いたモデル依存の観測 | Experimentell abgeleitete, modellabhängige Beobachtung |
| `in_plane_stiffness_2d` | Two-dimensional in-plane stiffness | 二维面内刚度 | 二次元面内剛性 | Zweidimensionale Steifigkeit in der Ebene |
| `breaking_strength_2d` | Two-dimensional breaking strength | 二维破坏强度 | 二次元破壊強さ | Zweidimensionale Bruchfestigkeit |
| `force_per_length` | Force per length | 力／长度 | 単位長さあたりの力 | Kraft pro Länge |
| `reported_plus_minus_unspecified` | Reported ± with unverified type/coverage | 类型／覆盖未核实的报告 ± 值 | 種類・包含水準が未確認の報告 ± 値 | Berichtete ±-Angabe mit ungeprüfter Art/Überdeckung |
| `study_id` | Shared study identity | 同一研究标识 | 同一研究の識別子 | Gemeinsame Studienkennung |

- **English:** The 340 ± 50 N/m stiffness and model-inferred 42 ± 4 N/m breaking strength are distinct 2D properties from one Lee–Wei–Kysar–Hone (2008) AFM study, not two confirmations, universal bounds or engineering allowables. Neither ± has verified type/coverage; do not call it SD, standard error, a confidence interval or bound endpoints. Separate stiffness statistics are mean 342 N/m, SD 30 N/m and 67 fits on 23 membranes from 2 flakes, never breaking-test counts. Preserve the assumed ν=0.165 and nonlinear strength inference with second Piola–Kirchhoff stress/Lagrangian strain. Temperature, atmosphere, humidity and loading rate are unknown; the supplement is unread. N/m has no default thickness or GPa conversion. No observation execution or overlays are provided
- **简体中文：** 刚度 340 ± 50 N/m 与模型推断的破坏强度 42 ± 4 N/m 是 Lee、Wei、Kysar、Hone（2008）同一项 AFM 研究的两种二维性质，不是两次确认、普适界或工程许用值。两项 ± 的类型／覆盖均未核实，不能称为标准差、标准误、置信区间或界限端点。另有刚度分布均值 342 N/m、标准差 30 N/m，以及来自 2 片石墨烯、23 张膜的 67 次拟合；这些绝不是破坏试验样本数。保留假定 ν=0.165 及非线性强度推断的第二 Piola–Kirchhoff 应力／Lagrangian 应变约定。温度、气氛、湿度和加载速率未知，补充材料未读。N/m 不设默认厚度或 GPa 换算；不提供观测执行或叠加图
- **日本語：** 剛性340 ± 50 N/mとモデル推定の破壊強さ42 ± 4 N/mは、Lee、Wei、Kysar、Hone（2008）の同じ AFM 研究の異なる二次元物性です。二つの独立した確認、普遍的な上下界、設計許容値ではありません。両 ± の種類・包含水準は未確認で、標準偏差、標準誤差、信頼区間、上下界の端点とは呼べません。別の剛性統計は平均342 N/m、標準偏差30 N/m、2片から得た23枚の膜に対する67回のフィットで、破壊試験の標本数ではありません。仮定ν=0.165と、非線形強さ推定の第二 Piola–Kirchhoff 応力／Lagrange ひずみ規約を保持します。温度、雰囲気、湿度、負荷速度は不明、補足資料は未読です。N/mには既定の厚さやGPa換算はなく、観測の実行や重ね描きもありません
- **Deutsch:** Steifigkeit 340 ± 50 N/m und modellgestützt abgeleitete Bruchfestigkeit 42 ± 4 N/m sind verschiedene 2D-Größen derselben AFM-Studie von Lee, Wei, Kysar und Hone (2008), keine zwei Bestätigungen, universellen Schranken oder Bemessungswerte. Art/Überdeckung beider ±-Angaben sind ungeprüft; sie sind nicht als Standardabweichung, Standardfehler, Konfidenzintervall oder Schrankenendpunkte auszugeben. Getrennte Steifigkeitsstatistiken sind Mittelwert 342 N/m, Standardabweichung 30 N/m und 67 Fits an 23 Membranen aus 2 Flocken, niemals Bruchversuchs-Stichprobenzahlen. ν=0.165 bleibt eine Annahme; die nichtlineare Festigkeitsableitung verwendet zweite Piola–Kirchhoff-Spannung und Lagrange-Dehnung. Temperatur, Atmosphäre, Feuchte und Belastungsrate sind unbekannt, Zusatzmaterial ungelesen. Keine Standarddicke, GPa-Umrechnung, Beobachtungsauswertung oder Überlagerung

**Rights and review / 权利与审校 / 権利と校閲 / Rechte und Prüfung:** ©2008 AAAS, all rights reserved / 保留所有权利 / 全権利留保 / alle Rechte vorbehalten. No PDF, figures or raw data are bundled / 不附 PDF、图或原始数据 / PDF・図・生データは同梱しません / Keine PDF, Abbildungen oder Rohdaten werden mitgeliefert. The explanations and translations have not received independent scientific or native-language review / 表述与译文尚未经独立科学或母语审校 / 科学的記述と翻訳の独立した科学的・母語校閲は未実施です / Eine unabhängige fachliche oder muttersprachliche Prüfung steht aus.

See [observations, exact locators and uncertainty distinctions](OBSERVATIONS.md).

## v0.8.0 tetragonal / rhombohedral labels

The source's I/II labels and exact Laue classes are part of the scientific identity. These authored display names match the locale dictionary; they remain independently scientifically and linguistically unreviewed.

| Claim ID | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `tetragonal_i_born_stability` | Tetragonal I (4/mmm) elastic stability | 四方晶系 I（4/mmm）弹性稳定性 | 正方晶系 I（4/mmm）の弾性安定性 | Elastische Stabilität: tetragonal I (4/mmm) |
| `tetragonal_ii_born_stability` | Tetragonal II (4/m) elastic stability | 四方晶系 II（4/m）弹性稳定性 | 正方晶系 II（4/m）の弾性安定性 | Elastische Stabilität: tetragonal II (4/m) |
| `rhombohedral_i_born_stability` | Rhombohedral I / trigonal (-3m) elastic stability | 菱方 / 三方晶系 I（-3m）弹性稳定性 | 菱面体晶系 / 三方晶系 I（-3m）の弾性安定性 | Elastische Stabilität: rhomboedrisch / trigonal I (-3m) |
| `rhombohedral_ii_born_stability` | Rhombohedral II / trigonal (-3) elastic stability | 菱方 / 三方晶系 II（-3）弹性稳定性 | 菱面体晶系 / 三方晶系 II（-3）の弾性安定性 | Elastische Stabilität: rhomboedrisch / trigonal II (-3) |

- **English:** C66 is independent in tetragonal I/II and dependent, (C11−C12)/2, in rhombohedral I/II. Rhombohedral/trigonal names do not require a nonorthogonal primitive basis. Preserve the full Cartesian engineering-Voigt template, coupling signs, factor 2 and combined C14²+C15². Strict stress-free homogeneous harmonic stability is not phonon/prestressed stability or strength. Equality fails strict stability; harmonic marginality requires full PSD with a zero mode. A positive determinant alone is insufficient
- **简体中文：** 四方 I／II 的 C66 独立，菱方 I／II 的 C66=(C11−C12)/2 为从属量。菱方／三方名称不要求非正交原胞坐标。保留完整 Cartesian 工程 Voigt 模板、耦合符号、因子 2 与 C14²+C15² 的合并条件。无应力均匀谐波严格稳定性不等于声子／预应力稳定性或强度。等号不满足严格稳定性，谐波临界须整个矩阵半正定且有零模态；仅正行列式不够
- **日本語：** 正方晶 I／II の C66 は独立ですが、菱面体晶 I／II では (C11−C12)/2 に従属します。菱面体晶／三方晶という名称は非直交原始基底を要求しません。完全な Cartesian 工学 Voigt テンプレート、結合符号、係数2と C14²+C15² の合算条件を保持します。無応力・一様ひずみ・調和近似での厳密な安定性は、フォノン／初期応力下の安定性や強度とは異なります。等号は厳密な安定性を満たさず、限界状態には全体の半正定値性とゼロモードが必要です。正の行列式だけでは不十分です
- **Deutsch:** C66 ist in Tetragonal I/II unabhängig und in Rhomboedrisch I/II durch (C11−C12)/2 bestimmt. Rhomboedrisch/trigonal verlangt keine nichtorthogonale primitive Basis. Vollständige kartesische technische Voigt-Vorlage, Kopplungsvorzeichen, Faktor 2 und gemeinsame Summe C14²+C15² bleiben erhalten. Strikte spannungsfreie homogene harmonische Stabilität bedeutet weder Phononen-/Vorspannungsstabilität noch Festigkeit. Gleichheit erfüllt keine strikte Stabilität; harmonische Grenzfälle benötigen insgesamt PSD mit Nullmode. Eine positive Determinante allein genügt nicht

All full conditions and source locators are in [Elastic stability](ELASTIC_STABILITY.md); the [four getting-started guides](I18N.md) explain the unchanged eight-output calculator and current 36-claim catalog. None of these translated labels supplies runtime specimen classification.

## v0.16.0 hydrostatic compressibility terminology

These terms describe the two new catalog-only relations, not accepted tensor
inputs or computed material results. Scientific symbols and canonical codes are
language-neutral; independent scientific/native-language review remains pending.

| Concept | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| `directional_linear_compressibility`, β(n) | Directional hydrostatic linear compressibility | 静水加载下的方向线压缩率 | 静水圧下の方向別線圧縮率 | Richtungsabhängige lineare Kompressibilität unter hydrostatischem Druck |
| κ=I:S:I | Hydrostatic volumetric compressibility | 静水体积压缩率 | 静水圧下の体積圧縮率 | Hydrostatische Volumenkompressibilität |
| `normalized_directional_linear_compressibility`, β/κ | Normalized directional linear compressibility | 归一化方向线压缩率 | 規格化された方向別線圧縮率 | Normierte richtungsabhängige lineare Kompressibilität |
| `inverse_pressure`, `Pa^-1` | Inverse pressure | 压力的倒数量纲 | 圧力の逆数の次元 | Inverser Druck |
| NLC, β(n)<0 | Negative linear compressibility | 负线压缩率 | 負の線圧縮率 | Negative lineare Kompressibilität |
| Principal β values | Eigenvalues of B=S:I | B=S:I 的特征值／主值 | B=S:I の固有値／主値 | Eigenwerte / Hauptwerte von B=S:I |
| Fixed-tensor range | Finite attained spectral interval | 固定张量的有限可达谱区间 | 固定テンソルの有限で達成される固有値区間 | Endliches angenommenes Eigenwertintervall eines festen Tensors |
| Unrestricted tensor-class range | All finite real normalized values | 不受额外对称性限制的张量类中全部有限归一化实数值 | 対称性を追加制限しないテンソル集合での全有限実数の規格化値 | Alle endlichen reellen normierten Werte über die uneingeschränkte Tensorklasse |

- **English:** Compression-positive p means σ=−pI; tensile stress and extensional strain are positive. β<0 is extension under hydrostatic pressure while κ stays positive. At most two negative principal values does not mean at most two negative directions. For g=S_eng h, B's off-diagonals are (g4,g5,g6)/2. β²<κ/E is strict, same-tensor, necessary and not sufficient; cubic/isotropic β/κ=1/3. These are original project derivations from inspected definitions, with no tensor evaluator or independent scientific review
- **简体中文：** 压缩为正的 p 对应 σ=−pI，应力以拉伸、应变以伸长为正。β<0 是静水压力下的方向伸长，κ 仍为正。至多两个负主值不等于至多两个负方向。g=S_eng h 时，B 的非对角项为 (g4,g5,g6)/2。同一张量的 β²<κ/E 是严格必要条件，不是充分条件；立方／各向同性 β/κ=1/3。项目原创推导依据已核对的定义，不提供张量计算器，也未经独立科学同行评审
- **日本語：** 圧縮を正とする p では σ=−pI、引張応力と伸長ひずみを正とする。β<0 は静水圧での方向別伸長で、κ は正のまま。負の主値が最大二つでも、負の方向が最大二つとは限らない。g=S_eng h から B の非対角項を得る際は (g4,g5,g6)/2 を使う。同じテンソルの β²<κ/E は厳密な必要条件であり十分条件ではなく、立方晶／等方弾性は β/κ=1/3。確認した定義に基づく独自導出で、テンソル計算機能や独立した科学的査読はない
- **Deutsch:** Kompressionspositives p bedeutet σ=−pI; Zugspannung und Verlängerung sind positiv. β<0 bezeichnet richtungsabhängige Verlängerung unter hydrostatischem Druck, während κ positiv bleibt. Höchstens zwei negative Hauptwerte bedeuten nicht höchstens zwei negative Richtungen. Für g=S_eng h sind B-Nebendiagonalen (g4,g5,g6)/2. β²<κ/E ist strikt, für denselben Tensor notwendig und nicht hinreichend; kubisch/isotrop gilt β/κ=1/3. Eigenständige Projektherleitungen auf Grundlage geprüfter Definitionen, kein Tensorrechner und keine unabhängige wissenschaftliche Begutachtung

Ortiz's relevant published pages were visually checked; Miller's institutional
manuscript equations were text-checked only. The inspection distinction must
survive translation. No source PDF, image or full text is bundled, and source
access confers no reuse license. For complete translated scope and exclusions,
see [the four-language scientific summaries](DIRECTIONAL_COMPRESSIBILITY.md#four-language-scientific-summary).

## Monolayer hBN observation terms (v0.19.0)

These labels belong to the Falin et al. (2017) family; they do not change the
older graphene or MoS2 conventions. Full evidence and limits are in the
[observation guide](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records).

| Concept | English | 简体中文 | 日本語 | Deutsch |
| --- | --- | --- | --- | --- |
| Selected specimen | Suspended monolayer hexagonal boron nitride (hBN) | 悬空单层六方氮化硼（hBN） | 懸架した単層六方晶窒化ホウ素（hBN） | Freitragendes einlagiges hexagonales Bornitrid (hBN) |
| Stiffness result | In-plane stiffness, 289 ± 24 N/m | 面内刚度，289 ± 24 N/m | 面内剛性、289 ± 24 N/m | Steifigkeit in der Ebene, 289 ± 24 N/m |
| Strength result | Breaking strength, 23.6 ± 1.8 N/m | 破坏强度，23.6 ± 1.8 N/m | 破壊強さ、23.6 ± 1.8 N/m | Bruchfestigkeit, 23.6 ± 1.8 N/m |
| Strength reduction | Volume-averaged stresses beneath the indenter | 压头下应力的体积平均 | 圧子直下の応力の体積平均 | Volumengemittelte Spannungen unter dem Eindringkörper |
| S5 diagnostic | Maximum Von Mises stress, distinct from the strength statistic | 最大 Von Mises 应力，与强度统计量不同 | 最大 Von Mises 応力、強さの統計量とは別 | Maximale Von-Mises-Spannung, getrennt vom Festigkeitskennwert |
| Rate | Probe translation velocity, not strain rate | 探针平移速度，不是应变率 | 探針移動速度、ひずみ速度ではない | Sondentranslationsgeschwindigkeit, keine Verzerrungsrate |
| Count | Tested sheets, not a verified failure-event count | 试验薄膜张数，不是已核实的失效事件数 | 試験シート枚数、確認済み破壊事象数ではない | Getestete Schichten, keine verifizierte Bruchereigniszahl |
| SD basis | Peer-review author response, PDF p. 8; not main-text notation alone | 审稿作者回复 PDF 第 8 页；非仅据正文符号 | 査読著者回答 PDF 8頁、本文記号のみではない | Autorenantwort zur Begutachtung, PDF S. 8; nicht allein Haupttextnotation |

The source's **0.5 μm/s** translation velocity and qualitative ambient descriptor
do not establish strain rate or numeric temperature/pressure/humidity/gas
composition. Eleven tested sheets are explicitly linked to stiffness only;
unknown curves and failures are not zero or eleven by default. “Typically five”
is not an exact count. Both ± values have source-clarified SD meaning with
unknown coverage and weighting, rather than a confidence interval or bound.
The finite-strain stress/strain measures remain unknown.

The q arithmetic **0.9898768854482001** follows the source formula with
**1.049** and **ν=0.211**; it is neither a printed/fitted q value nor evidence
of an hBN mismatch. Keep the separate MoS2 q inconsistency visible. N/m is
source-printed, with no automatic thickness conversion. Article CC BY 4.0 does
not establish the separate supplement/peer-review-file license scope. These
translations do not claim independent scientific or native-language review.
