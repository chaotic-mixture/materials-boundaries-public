# 材料边界 · Materials Boundaries

Current software release: **v0.21.0** · **Six additional Ni11X predictions** · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)

A condition-aware, source-traceable materials-mechanics catalog and offline Python toolkit. It separates conditional mathematical bounds, model relations, published observations, computational predictions and synthetic demonstrations. Python 3.10+; no third-party runtime dependencies.

Repository: [chaotic-mixture/materials-boundaries-public](https://github.com/chaotic-mixture/materials-boundaries-public)

## Public-release scope

- **36 mechanics claims**, **51 source records**, **6 observations from three studies**, **12 published computational predictions in 2 scientific families and 3 explicit groups**, and **5 synthetic temperature demos with 7 branches**
- Exactly **8 executable composite calculation rules**: HS/Reuss/Voigt bulk and shear bounds plus conservative derived Young's-modulus and Poisson-ratio envelopes
- Other mechanics records, including bulk elastic waves, hydrostatic compressibility, directional Poisson ratio, anisotropy, fatigue, fracture, stability and porous relations, are catalog-only
- The 51 sources comprise 50 bibliographic/source records plus one original synthetic-demo provenance record; a source record is not a redistribution of its publication or dataset
- All five temperature demos use intentionally invented coefficients and ranges. They do not describe real materials, measured properties or engineering allowables

Version **0.21.0** appends exactly six **Ni11X periodic-model ideal-shear predictions** from Shimanek et al., arXiv:2108.06412v2, Table 2, p. 27: **Cr 4.90, Mn 5.12, Fe 5.20, Cu 4.51, Si 4.17 and Ti 4.24 GPa**. They form the new explicit group `shimanek_v2_table2_cr_mn_fe_cu_si_ti`; the original Ni/Ni11Al/Ni11Co default remains three points, and the separate three-point silicon first-instability group is unchanged. No source or scientific schema is added or changed. These are published-method-only predictions for 12-atom Ni11X cells, not pure-X strengths, commercial grades, experiments or universal bounds. Unknown temperature, pressure, magnetism and uncertainty remain unknown; bare table labels do not identify the PAW datasets or valence configurations. Perdew et al. (1992) GGA is not silently relabeled PBE; 0.08 GPa peak convergence is not an error bar. [Prediction evidence and limits](docs/COMPUTATIONAL_PREDICTIONS.md) · [v0.21.0 migration](docs/MIGRATION_v0.21.0.md)

Version **0.20.0** previously added source-ordered offline **observation inspection cards/tables** for the existing six summaries. It changes no scientific record or evaluator: normalized catalog values, original source strings, source-specific warnings, uncertainty evidence, scoped sample counts and unknown conditions remain separate and traceable. Exact filters and study/quantity grouping export auditable JSON, CSV, wide/narrow SVG and script-free HTML in en/zh/ja/de. There are no quantitative axes, uncertainty endpoints, aggregation, ranking, overlays or matched-condition comparisons. The new inspection schema is **1.0.0**; existing scientific schemas stay unchanged. [Inspection guide](docs/OBSERVATION_INSPECTION.md) · [v0.20.0 migration](docs/MIGRATION_v0.20.0.md)

Version **0.16.0** was the first public-release baseline; earlier version labels describe development milestones. Version **0.19.0** previously appended exactly two catalog-only monolayer hBN observations and one Falin et al. (2017) source, preserving all earlier records. At that release, observations schema advanced **1.1.0 → 1.2.0** with a separate closed hBN method family; claims stay **1.11.0**, sources **1.0.0**, and evaluation **1.1.0**. Scientific schema versions are independent of the software version. [Migration and unchanged contracts](docs/MIGRATION_v0.19.0.md)

The hBN values are source-printed **289 ± 24 N/m in-plane stiffness** and **23.6 ± 1.8 N/m breaking strength**. Their SD meaning comes from the publisher-linked peer-review author response, PDF p. 8, rather than the main text's ± notation alone. **N=11 is tested sheets explicitly associated with the stiffness average**, not a verified curve or failure-event count. Stiffness uses a membrane fit; strength uses nonlinear FEM **volume-averaged stresses beneath the finite-radius indenter**, distinct from Supplementary Fig. S5's maximum Von Mises diagnostic. Finite-strain stress/strain measures remain unknown. Ambient conditions and **0.5 μm/s probe translation velocity** do not supply numerical environment values or strain rate. The source formula q=1/(1.049−0.15ν−0.16ν²), ν=0.211 gives **0.9898768854482001 by curator arithmetic only**; no separately printed numerical q or actual fit constant is verified, so no hBN q discrepancy is asserted. No thickness conversion, refit, comparison or ranking is added. [Full source, method and statistical limits](docs/OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)

Version **0.18.0** previously added the two bulk elastic-wave claims and two sources, with claims schema **1.10.0 → 1.11.0**. [Its migration notes](docs/MIGRATION_v0.18.0.md) and scientific distinctions remain applicable.

For finite positive isotropic K, G and density ρ, c_L²=(K+4G/3)/ρ and c_T²=G/ρ. The material-class ratio is **c_L/c_T ∈ (√(4/3),∞)**: the lower infimum is unattained and no finite class-wide upper bound exists. Each fixed material has finite direction-independent speeds and twofold transverse degeneracy. The canonical acoustic tensor **Q_ik=C_ijkl n_j n_l** has pressure units; **Γ=Q/ρ** has speed-squared units. Strict strong ellipticity means every directional Q is SPD; full symmetric-strain energy SPD implies it, but the converse fails. Phase normal and polarization are distinct, and no generic anisotropic exact L/T ordering, ray/group-speed claim or automatic static/isothermal-modulus substitution is made. [Definitions, original proofs, source/version limits and exclusions](docs/BULK_ELASTIC_WAVES.md)

Version **0.17.0** previously added one MoS2 study and two catalog-only 2D summaries, with observations schema **1.0.0 → 1.1.0**. [Its migration notes](docs/MIGRATION_v0.17.0.md) remain applicable.

The retained monolayer MoS2 summaries are **180 ± 60 N/m in-plane stiffness** and **15 ± 3 N/m breaking strength**, with source-reported standard deviations. They retain a flagged inconsistency between the printed q formula and stated q = 0.95; the actual fit constant remains unresolved. The inspected EPFL artifact is proof-formatted (A–G); final publisher text and the supplement are unverified. No refit, plot, comparison, ranking or thickness conversion is added. [Observation evidence and limits](docs/OBSERVATIONS.md#monolayer-mos2-bertolazzi-et-al-2011-new-records)

Original project code, documentation and original curation are MIT-licensed under the maintainer handle **chaotic-mixture**. This does not relicense third-party publications, source datasets or scientific facts, or imply their authors' endorsement. See [Third-party notices](THIRD_PARTY_NOTICES.md) and [source provenance](docs/SOURCES.md).

The five NIST cryogenic coefficient datasets and all derived examples are omitted conservatively while reuse terms are clarified. This is not a finding that redistribution is prohibited. Bibliographic records and official links remain. The collection is currently listed by NIST as a curated collection, formerly SRD 152; reclassification alone does not establish an express redistribution grant. [Details and official sources](THIRD_PARTY_NOTICES.md#nist-cryogenic-material-properties)

Formula checks and software tests do not constitute independent scientific peer review or validate a real specimen. Scientific and native-language review remain incomplete; the catalog is not comprehensive.

## Quick start

```sh
python -m pip install -e .
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang en
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang en
python -m materials_boundaries catalog claims --query compressibility --text --lang en
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang en
python -m materials_boundaries observation inspect --output /tmp/observations --lang en
python -m materials_boundaries catalog predictions --text --lang en
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six --lang en
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-50k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-overlap-50k.json --lang en
python -m materials_boundaries temperature plot --output /tmp/temperature-demo --lang en
```

The synthetic linear temperature demo returns **15 GPa at 50 K**. The overlap demo returns **25 and 32.5 GPa at 50 K**, retaining both artificial branches. These are invented demonstration outputs, not NIST results or material-property data. Outside the authored ranges, no value is extrapolated. [Temperature API and demo contract](docs/TEMPERATURE_MODELS.md)

[English](docs/GETTING_STARTED.en.md) · [中文](docs/GETTING_STARTED.zh.md) · [日本語](docs/GETTING_STARTED.ja.md) · [Deutsch](docs/GETTING_STARTED.de.md)

The scientific guides retain source-specific qualifications for the graphene, monolayer MoS2 and monolayer hBN observations, Ni-family ideal-shear predictions, silicon first-instability predictions and literature-model example. These brief numerical facts are not removed merely because their publications have separate rights. No paper PDFs, figures, full text or raw measurement collections are bundled.

中文：当前 **0.21.0** 新增 Ni11X 周期模型的六条理想剪切预测：Cr 4.90、Mn 5.12、Fe 5.20、Cu 4.51、Si 4.17、Ti 4.24 GPa，共 12 条预测、2 个科学方法族、3 个显式比较组。须用 `--group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti` 选择新组；原 Ni／Al／Co 三点默认组与独立硅三点组不变。仅在已发表方法层面比较，不是纯 X、商业牌号、实验测量或普适上界。温度、压力、磁态和不确定性未知；无 pv／sv 后缀不能证明 PAW 数据集、价电子配置或不含半芯态。Perdew（1992）不改称 PBE，0.08 GPa 收敛不是误差棒。[完整说明](docs/GETTING_STARTED.zh.md)

中文：此前 **0.20.0** 新增六条现有观测的离线查阅卡片／表格；精确筛选与按研究／量分组可导出 JSON、CSV、宽／窄 SVG 和无脚本 HTML。规范化目录显示与来源原始字符串分开，警告先于数值，来源及未知条件保留。不新增科学记录、求值器、数值坐标轴、误差棒、排名、聚合或匹配条件比较。[查阅说明](docs/GETTING_STARTED.zh.md)

中文：历史 0.19.0 只新增 Falin 等（2017）单层 hBN 的两条观测和一条来源，共 36 条论断、51 条来源、三项研究六条观测；观测 schema 为 1.2.0。刚度 289 ± 24 N/m、破坏强度 23.6 ± 1.8 N/m 均为来源明示值，标准差定义来自公开审稿作者回复第 8 页。11 张试验薄膜只明确对应刚度平均值，不是失效事件数；强度是压头下应力的 FEM 体积平均，不是 S5 的最大 Von Mises 应力。有限应变度量及数值环境未知；0.5 μm/s 是探针位移速度。q 的 0.9898768854482001 仅为公式算术核对，没有另报 q 可供判定矛盾。文章 CC BY 4.0 不自动扩展到许可未核实的补充材料或审稿文件；不再分发来源媒体。[hBN 完整说明](docs/OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)

中文：0.16.0 是首个公开版本的基线；0.17.0 曾新增一项 MoS2 研究的两项二维观测，此前 0.18.0 新增两条仅目录体弹性波关系和两条来源，共 36 条力学论断、50 条来源。有限正 K、G、ρ 的各向同性比值 c_L/c_T∈(√(4/3),∞) 是跨材料类别的范围；单一材料的速度有限且与方向无关，横波二重简并。严格强椭圆性弱于完整对称应变能正定性；相位法向不等于偏振方向，也不声称一般各向异性的精确纵横波排序、群速度或静态／等温模量自动适用。详见[体弹性波](docs/BULK_ELASTIC_WAVES.md)。原创代码、文档及策展内容采用 MIT 许可证，第三方作品及科学事实不因此被重新许可。温度目录仅含五个人为构造的演示模型（七个分支），不能当作真实材料数据。NIST 低温系数及其推导示例暂不收录，这是一项谨慎的发布选择，并非已证明禁止再分发。八条复合材料计算规则及其他科学目录保留；独立科学审查和母语审校尚未完成。

日本語：現在の **0.21.0** は Ni11X 周期モデルの理想せん断予測6件を追加します。Cr 4.90、Mn 5.12、Fe 5.20、Cu 4.51、Si 4.17、Ti 4.24 GPa、合計12予測・2方法ファミリー・3明示的比較グループです。新グループは `--group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti` で選択し、既定の Ni／Al／Co 3点と独立したシリコン3点は不変です。比較は公表された方法の範囲に限り、純粋な X、市販材、実測値、普遍的上限を表しません。温度・圧力・磁気状態・不確かさは不明です。pv／sv 接尾辞がないことから PAW データセット、価電子配置、半内殻状態の不在を確定できません。Perdew（1992）を PBE とせず、0.08 GPa の収束基準を誤差棒としません。[詳細](docs/GETTING_STARTED.ja.md)

日本語：以前の **0.20.0** は既存観測6件のオフライン閲覧カード／表を追加します。完全一致の選択と研究／量のグループ分けから JSON、CSV、広幅／狭幅 SVG、スクリプト不要の HTML を出力します。正規化表示と原文を分け、警告を数値より先に示し、出典と不明条件を保持します。科学的記録、計算器、数値軸、誤差棒、順位、集計、条件一致比較は追加しません。[閲覧説明](docs/GETTING_STARTED.ja.md)

日本語：以前の 0.19.0 は Falin ら（2017）の単層 hBN 観測2件と出典1件のみを追加し、論断36件・出典51件・3研究の観測6件、観測スキーマ1.2.0です。剛性289 ± 24 N/mと破壊強さ23.6 ± 1.8 N/mは出典の記載値で、標準偏差の定義は公開査読の著者回答8頁に由来します。試験シート11枚は剛性平均との対応のみ明示され、破壊事象数ではありません。強さは圧子下応力のFEM体積平均で、S5の最大Von Mises応力とは異なります。有限ひずみ尺度・数値環境は不明、0.5 μm/sは探針移動速度です。q=0.9898768854482001は式の算術確認だけで、別記のqとの不整合は主張しません。論文のCC BY 4.0を、権利未確認の補足・査読ファイルへ自動適用せず、出典媒体は再配布しません。[hBNの詳細](docs/OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)

日本語：0.16.0 は初の公開版の基準です。0.17.0 は MoS2 の一研究から二つの二次元観測を追加しました。以前の 0.18.0 はカタログ専用のバルク弾性波関係2件と出典2件を追加し、論断36件・出典50件です。有限正値 K、G、ρ に対する等方的速度比 c_L/c_T∈(√(4/3),∞) は材料集合の範囲であり、固定材料の速度は有限・方向非依存で横波は二重縮退します。厳密な強楕円性は全対称ひずみエネルギーの正定値性より弱い条件です。位相法線と偏極は別で、一般異方性の厳密な縦横波順序、群速度、静的・等温弾性率の自動適用は主張しません。[バルク弾性波](docs/BULK_ELASTIC_WAVES.md)を参照してください。独自のコード、文書、キュレーションには MIT ライセンスを適用しますが、第三者の著作物や科学的事実を再許諾するものではありません。温度カタログは人工的なデモ5件（7分岐）のみで、実材料のデータではありません。NIST の低温係数と派生例は確認待ちのため慎重に除外しており、再配布禁止が確定したという意味ではありません。独立した科学的・母語レビューは未実施です。

Deutsch: Die aktuelle Version **0.21.0** ergänzt sechs ideale Scherfestigkeiten periodischer Ni11X-Modelle: Cr 4.90, Mn 5.12, Fe 5.20, Cu 4.51, Si 4.17 und Ti 4.24 GPa. Insgesamt sind es 12 Vorhersagen, 2 Methodenfamilien und 3 explizite Vergleichsgruppen. Die neue Gruppe wird mit `--group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti` gewählt; die drei Ni/Al/Co-Standardpunkte und die separate Siliziumgruppe bleiben unverändert. Vergleichbarkeit gilt nur für das veröffentlichte Verfahren, nicht für reines X, Handelslegierungen, Messungen oder universelle Grenzen. Temperatur, Druck, Magnetismus und Unsicherheit bleiben unbekannt. Fehlende pv/sv-Suffixe belegen weder PAW-Datensätze noch Valenzkonfigurationen oder das Fehlen von Semicore-Zuständen. Perdew (1992) wird nicht zu PBE; 0.08 GPa Konvergenz ist kein Fehlerbalken. [Details](docs/GETTING_STARTED.de.md)

Deutsch: Die frühere Version **0.20.0** ergänzt Offline-Karten/Tabellen für sechs bestehende Beobachtungen. Exakte Filter und Studien-/Größengruppen exportieren JSON, CSV, breite/schmale SVG und skriptfreies HTML. Normalisierte Kataloganzeige und Originalwortlaut bleiben getrennt; Warnungen stehen vor Werten, Quellen und unbekannte Bedingungen bleiben erhalten. Keine neuen wissenschaftlichen Einträge, Rechner, numerischen Achsen, Fehlerbalken, Rangfolgen, Aggregation oder Vergleiche bei nachgewiesen gleichen Bedingungen. [Anleitung](docs/GETTING_STARTED.de.md)

Deutsch: Die frühere Version 0.19.0 ergänzte genau zwei einlagige hBN-Beobachtungen aus Falin et al. (2017) und eine Quelle: 36 Aussagen, 51 Quellen, sechs Beobachtungen aus drei Studien; Beobachtungsschema 1.2.0. Steifigkeit 289 ± 24 N/m und Bruchfestigkeit 23.6 ± 1.8 N/m sind gedruckte Quellenwerte; die SD-Definition stammt aus der öffentlichen Autorenantwort zur Begutachtung, PDF S. 8. Elf getestete Schichten sind ausdrücklich dem Steifigkeitsmittel zugeordnet, nicht einer Zahl von Bruchereignissen. Die Festigkeit ist ein FEM-Volumenmittel der Spannungen unter dem Eindringkörper, nicht das Maximum der Von-Mises-Spannung aus S5. Finite Verzerrungsmaße und numerische Umgebungswerte bleiben unbekannt; 0.5 μm/s ist die Sondentranslationsgeschwindigkeit. q=0.9898768854482001 ist nur eine Rechenkontrolle; kein separat gedrucktes q begründet einen Widerspruch. CC BY 4.0 des Artikels wird nicht auf Supplement oder Begutachtungsdatei mit ungeklärter Lizenz übertragen; Quellenmedien werden nicht weitergegeben. [hBN-Details](docs/OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)

Deutsch: 0.16.0 war die Basis der ersten öffentlichen Version. Version 0.17.0 ergänzte zwei zweidimensionale Beobachtungen aus einer MoS2-Studie. Version 0.18.0 ergänzte zwei reine Katalogrelationen für elastische Volumenwellen und zwei Quellen: insgesamt 36 Aussagen und 50 Quellen. Für endliche positive K, G, ρ gilt über die isotrope Materialklasse c_L/c_T∈(√(4/3),∞); ein festes Material hat endliche richtungsunabhängige Geschwindigkeiten und zweifach entartete Transversalmoden. Strikte starke Elliptizität ist schwächer als positive Energie aller symmetrischen Verzerrungen. Phasennormale und Polarisation sind verschieden; allgemeine anisotrope L/T-Reihenfolge, Gruppengeschwindigkeit oder automatische Verwendung statischer/isothermer Moduln werden nicht behauptet. Siehe [Volumenwellen](docs/BULK_ELASTIC_WAVES.md). Eigener Code, eigene Dokumentation und eigenständige Kuration stehen unter MIT; fremde Werke und wissenschaftliche Fakten werden damit nicht neu lizenziert. Die Temperaturmodelle sind fünf künstliche Demos mit sieben Zweigen, keine realen Materialdaten. NIST-Tieftemperaturkoeffizienten und abgeleitete Beispiele bleiben vorsorglich bis zur Klärung ausgenommen; daraus folgt kein nachgewiesenes Weitergabeverbot. Unabhängige wissenschaftliche und muttersprachliche Prüfung steht noch aus.

## 立即运行

Python 3.10+，运行时无第三方依赖。在仓库根目录：

```sh
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang zh
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang en
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang ja
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang de
```

也可安装命令行入口：

```sh
python -m pip install -e .
materials-boundaries evaluate examples/synthetic-two-phase.json --lang zh
```

同一份公式、单位、数据标识符和原始引用供四种语言共用。`--lang` 只改变可读标签/说明；JSON、错误代码、条件标识符及 CLI 参数保持稳定英文。`--lang` 可放在命令前或命令后，重复指定时以最后一次为准；`--help` 的标签/说明也随之切换，命令语法和标识符不变。翻译尚未经过独立科学或母语审校。

[English](docs/GETTING_STARTED.en.md) · [中文](docs/GETTING_STARTED.zh.md) · [日本語](docs/GETTING_STARTED.ja.md) · [Deutsch](docs/GETTING_STARTED.de.md) · [术语对照](docs/TERMINOLOGY.md) · [语言与回退规则](docs/I18N.md)

## 合成示例的预期结果

输入全为人为构造的演示数值，**不是测量结果、文献材料参数或 Materials Project 记录**：

- 第一相：K₁ = 10 GPa，G₁ = 5 GPa，体积分数 f₁ = 0.5
- 第二相：K₂ = 30 GPa，G₂ = 15 GPa，体积分数 f₂ = 0.5
- 体积模量 K：HS 为 16.25–17.5 GPa；Reuss / Voigt 为 15 / 20 GPa
- 剪切模量 G：HS 约为 8.37837837838–9.04761904762 GPa；Reuss / Voigt 为 7.5 / 10 GPa
- 杨氏模量 E 推导外包络：约 21.4488468362–23.1528046422 GPa
- 泊松比 ν 推导外包络：约 0.265190525232–0.293562708102，无量纲单位 `1`

这些结果是数值近似，不是某个具体微结构的性能预测，也不是区间算术认证的端点。E/ν 是由分别成立的 K/G 界推导的**保守外包络，不是紧的联合可达界**；两个 HS 端点不一定能由同一微结构同时达到。

E = 9KG/(3K+G)，ν = (3K−2G)/(2(3K+G))。E 下/上端点分别使用 (Klow,Glow)/(Khigh,Ghigh)，ν 下/上端点使用 (Klow,Ghigh)/(Khigh,Glow)。推导仅使用同一输入体系的 HS 体积/剪切模量结果，并保留依赖论断与实例 ID；前提未知或不满足时不输出数值，相排序不一致时不回退到 Reuss/Voigt。

## 首个文献模型示例

`examples/literature-epoxy-glass-model.json` 使用 [Genin–Birman 2009](https://doi.org/10.1016/j.ijsolstr.2008.08.010) 的环氧/玻璃组分模型参数。它与仓库中的合成示例分开标记为 `literature_model`，并非测量材料或已报告试样。

原始 E/ν、K/G 换算方法和文献定位均保留；玻璃 20% / 环氧 80% 是计算示例的选择。宏观各向同性、理想粘结等作为计算器假设记录，温度、牌号、固化状态和测量不确定性保持未知。条件成立时体积模量 HS 约为 5.59472–9.40776 GPa，Reuss / Voigt 约为 5.30327 / 13.6 GPa。v0.2.0 同时输出剪切界和有效 E/ν 外包络；这些有效材料输出与原始组分 E/ν 不是同一物理记录。

```sh
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --lang zh
```

[完整来源、假设与换算说明](docs/LITERATURE_EXAMPLE.md)。该来源保留所有版权；仓库不附论文全文、PDF 或图。

## 复合材料计算器支持的条件

- 三维、小应变、静态、线性弹性
- **组分各向同性** `constituent_symmetry` 与**宏观有效各向同性** `effective_symmetry` 分别声明；后者不能代替前者
- 理想粘结 `perfectly_bonded`
- 两相描述，已知体积分数；活动相 K > 0 且 G > 0
- HS 及依赖 HS 的 E/ν 外包络额外要求 well-ordered：K 与 G 的相排序一致；排序保留每相 K/G/体积分数配对，包含相等模量极限
- 允许 f = 0 / 1 的纯相极限；不存在相的未知参数不参与计算

Reuss / Voigt 比较使用同一保守条件集合，但不要求 well-ordered。更一般定理可适用的情况，不代表本实现也支持。负刚度、活动孔隙/零刚度相、各向异性组分、非理想界面、动态/有限应变、强度/失效/塑性数值评价和联合可达域均未实现。断裂、稳定性、孔隙论断及独立观测记录只保存目录知识，不扩大该计算器的适用范围。

## 三态与输入验证

- `satisfied`：提供的声明/数值满足本实现条件；不表示已验证实际材料
- `violated`：至少一个已知条件不匹配；不表示这种材料不可能存在
- `unknown`：没有已知冲突，但至少一个必要条件/参数未知

缺失观察量或 `null` 保持未知，绝不替换成 0 或无穷大。`violated` 优先于 `unknown`，输出保留所有逐条件证据。仅 `satisfied` 的 claim 产生数值。非有限值、错误单位、重复键/相 ID、非法类型和不一致体积分数会报输入错误。

```sh
python -m materials_boundaries validate examples/synthetic-two-phase.json
python -m materials_boundaries evaluate examples/unknown-isotropy.json --lang zh
python -m materials_boundaries evaluate examples/anisotropic-constituent.json --json
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --unit MPa --json
python -m materials_boundaries catalog claims
python -m materials_boundaries catalog sources
```

退出码：0 = 完成验证/评价（包括 unknown / violated）或目录查询（包括空结果），2 = 无效输入/CLI 用法或未知记录 ID，3 = 数值输出范围错误。模量输出单位支持 `Pa`、`kPa`、`MPa`、`GPa`；每个输入模量独立带单位，内部统一为 Pa。泊松比始终以无量纲单位 `1` 输出，不随 `--unit` 换算，也不能把 `1` 用作该参数值。ν 必须严格满足 −1 < ν < 0.5；负值与零值可有效。若浮点舍入落在任一不包含的边界，返回 `numerical_range_error` 和 null，不裁剪为物理端点。依赖的 HS 结果发生数值错误时，推导结果也不可用。

## 只读目录检索

`catalog claims`、`catalog sources` 和新增 `catalog observations` 默认输出规范 JSON，兼容现有调用；`--json` 显式选择相同格式。使用 `--text --lang zh|en|ja|de` 阅读本地化标签和证据状态说明，原始标题、证据文字及规范 ID 保留。搜索仅检查仓库随附的人工策展记录，不联网、不修改记录，也不评价材料输入。

```sh
python -m materials_boundaries catalog claims --id hs_bulk_3d_two_phase --text --lang zh
python -m materials_boundaries --lang ja catalog claims --direction interval --text
python -m materials_boundaries catalog claims --query "bulk kochmann" --source-id kochmann_milton_2014 --json
python -m materials_boundaries catalog sources --query "Milton moduli" --year 2014 --text --lang de
python -m materials_boundaries catalog sources --role changed_assumption_comparison --license CC-BY-4.0 --text --lang en
python -m materials_boundaries catalog observations --source-id lee_wei_kysar_hone_2008 --text --lang zh
python -m materials_boundaries catalog observations --quantity breaking_strength_2d --json
python -m materials_boundaries --lang zh catalog --help
```

- `--id` 精确匹配记录 ID，区分大小写；未知 ID 报错并以 2 退出
- `--query` 按空白拆词，经 Unicode `casefold` 后做字面子串匹配，所有词均须命中。检索 ID、标题/名称，以及来源的作者、DOI、用途；论断还检索物理量、方向、`claim_type`、规则 ID 和证据来源 ID。观测检索 ID、名称、物理量、`observation_type`、`study_id`、`material.name` 和证据来源 ID；十八条 v0.4.0–v0.6.0、v0.8.0 与 v0.9.0 论断及六条观测的人工策展四语言显示名称也作为字面搜索别名；它不搜索论文全文，不做词干化、排名、模糊匹配或自动翻译
- `claims` 专用筛选：`--direction interval|lower|upper|prediction|relation|constraint`、`--claim-type theoretical_bound|derived_outer_envelope|model_estimate|model_relation|stability_criterion`
- 论断与观测共用 `--source-id`（精确匹配证据引用的来源 ID）；观测专用 `--quantity` 和 `--observation-type experiment_derived_model_dependent`
- `sources` 专用筛选：`--role`（用途）、`--year`（整数）、`--license`（许可证标识符或许可证状态）。除查询文字外，字符串筛选均精确匹配并区分大小写
- 所有筛选条件按 AND 组合，结果保持原目录顺序；空结果是成功查询，退出码为 0。把筛选用于不支持的目录种类，是用法错误，退出码为 2

阅读记录、核对公式或软件测试均不构成独立科学证明，也不授予来源内容的再使用许可。许可证筛选仅匹配已记录的元数据。检索到一条论断不代表它适用于某个材料；检索不到也不代表不存在相关文献或定理。

完整 CLI / Python 约定与安全录入检查表见 [Catalog reference](docs/CATALOG.md)。

## v0.8.0：四方／菱方严格稳定性模板

四条新记录沿用来源的 I／II 名称与 Laue 类：`tetragonal_i_born_stability`（4/mmm，6 个独立常数）、`tetragonal_ii_born_stability`（4/m，7 个）、`rhombohedral_i_born_stability`（−3m，6 个）、`rhombohedral_ii_born_stability`（−3，7 个）。菱方在此也称三方；不是要求使用非正交原胞坐标。

四条判据共同要求 C11 > |C12|、C33(C11+C12) − 2C13² > 0、C44 > 0，另分别要求：

- 四方 I：C66 > 0
- 四方 II：C66(C11−C12) − 2C16² > 0
- 菱方 I：C44(C11−C12) − 2C14² > 0
- 菱方 II：C44(C11−C12) − 2(C14²+C15²) > 0

四方两类的 C66 独立；菱方两类必须满足 C66=(C11−C12)/2。采用右手正交 Cartesian 坐标、z 沿主四重／三重轴；I 类 x 沿基面 Laue 二重轴，II 类保留固定基面方向中的允许耦合。Voigt 次序为 (xx,yy,zz,yz,xz,xy)，应变剪切项乘 2，应力剪切项不乘 2。完整矩阵与符号约定必须匹配，不能删去破坏对称性的项或单独改耦合符号。

这些严格不等式仅在**无应力平衡态、均匀无穷小应变、谐波二次能量**及对应完整实对称模板内为充要条件。菱方 II 的两个耦合须合并检查，分别通过不够；菱方行列式含耦合余量的平方，正行列式也不够。等号不满足严格稳定性；只有整个矩阵半正定且存在零模态时，才可称为谐波临界情况。它们不证明全声子稳定性、预应力／有限载荷稳定性或强度，近零不确定值也不自动分类。

```sh
python -m materials_boundaries catalog claims --id tetragonal_ii_born_stability --text --lang zh
python -m materials_boundaries catalog claims --query "rhombohedral" --text --lang en
```

[八条判据、完整矩阵与来源](docs/ELASTIC_STABILITY.md) · [v0.8.0 迁移](docs/MIGRATION_v0.8.0.md)。原始公式视觉核对与原创合成算例的代数／数值交叉检查不等于独立科学同行评审；译文仍未经过独立科学或母语审校。

## 历史 v0.7.0：独立、可追溯的观测目录

同一研究报告二维面内刚度 **340 ± 50 N/m** 和由非线性膜模型／有限元推断的二维破坏强度 **42 ± 4 N/m**。两项 ± 的统计类型与覆盖水平均未核实，不能标为标准差、置信区间或理论界。另有刚度拟合分布：均值 342 N/m、标准差 30 N/m，共 67 次拟合、23 张膜、2 片石墨烯；这些不是破坏试验样本数，也不替代 ±50 N/m。

AFM 中央压入的刚度拟合采用夹持各向同性圆膜、可忽略弯曲刚度及假定 ν=0.165。强度推断采用第二 Piola–Kirchhoff 应力与 Lagrangian 应变的非线性约定，不是直接测得的均匀拉应力。温度、气氛、湿度和加载速率保持未知；已核查作者 PDF 的正文段落，补充材料不可访问、未阅读。只保存 N/m，不设默认厚度、不换算为 GPa、不生成观测叠加图。©2008 AAAS，保留所有权利；不附 PDF、图或原始数据。

```sh
python -m materials_boundaries catalog observations --id lee_2008_graphene_in_plane_stiffness_2d --text --lang zh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang en
```

[观测、方法与证据](docs/OBSERVATIONS.md) · [v0.7.0 迁移](docs/MIGRATION_v0.7.0.md) · [四语言科学区别](docs/TERMINOLOGY.md)

## 历史 v0.6.0：各向同性固体＋孔隙界

新增 `hs_porous_bulk_3d_solid_void`、`hs_porous_shear_3d_solid_void` 和 `hs_porous_youngs_outer_3d_solid_void`。Ks、Gs 为正的固体模量，p 为孔隙体积分数；Roberts–Garboczi 原文的 p 是固相分数，须换为 1−p。完整有限孔隙率上界为：

- Kupper = 4 Ks Gs (1−p)/(4 Gs + 3 Ks p)
- Gupper = Gs (1−p)(9 Ks + 8 Gs)/(9 Ks + 8 Gs + 6 p(Ks + 2 Gs))
- Eupper = Es (1−p)/(1 + C p)，Es = 9 Ks Gs/(3 Ks + Gs)，νs = (3 Ks−2 Gs)/(2(3 Ks+Gs))，C = (1+νs)(13−15νs)/(2(7−5νs))

几何可包含不连通固体，因此 0<p<1 时三个下界为零；p=0 必须收缩为纯固体值；p=1 仅表示形式上的空域零刚度，不定义泊松比或比模量。孔隙极限采用保持宏观各向同性的正刚度趋零论证，不能直接把零代入奇异项。杨氏模量式是保守外包络，不保证同一微结构同时达到 K/G 上端点。

只有固定固体密度 ρs 且孔隙无质量时，才有 ρeff=(1−p)ρs。低密度一阶渐近式不能替代完整公式成为有限密度严格上界。来源保留精确定位、分数约定和 NIST 封面／期刊页版权声明差异，不推断普遍再使用权。

```sh
python -m materials_boundaries catalog claims --query porous --direction interval --text --lang zh
python -m materials_boundaries catalog sources --id roberts_garboczi_2002_porous --text --lang zh
```

[公式、端点与证据](docs/POROUS_BOUNDS.md) · [v0.6.0 迁移](docs/MIGRATION_v0.6.0.md) · [仅用于文档的合成数值](examples/catalog/porous-synthetic.json)。该 JSON 不属于 `validate`、`evaluate` 或对比绘图输入，也不是测量或文献材料数据。

## 历史 v0.5.0：四条弹性稳定性判据

新增 `general_stiffness_positive_definite`、`cubic_born_stability`、`hexagonal_born_stability` 和 `orthorhombic_born_stability`，来源为 Mouhat–Coudert 2014 已发表论文。它们要求无应力平衡态、均匀无穷小应变、谐波近似和对应对称性，明确工程 Voigt 剪切因子与符号矩阵。每项不等式都必须严格大于零；等号不满足严格稳定性，不能自动判为临界稳定。

新类型为 `stability_criterion` / `direction: constraint`，逻辑谓词的 `quantity_dimension` 为 `logical_predicate`，`si_unit` 为 null（不适用）；刚度参数仍为 Pa，二／三次不等式为 Pa²／Pa³。全部为 `catalog_only`，不产生材料适用性判断、特征值或绘图。论断 schema 为 1.4.0；原有 15 条论断、17 条来源与八条评价保留。目录不把各向同性泊松比范围泛化为各向异性响应的普适约束。

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang zh
python -m materials_boundaries catalog claims --query "正交晶系" --text --lang zh
```

[判据、来源与适用边界](docs/ELASTIC_STABILITY.md) · [v0.5.0 迁移](docs/MIGRATION_v0.5.0.md)

## 历史 v0.4.0：五条强度／断裂知识记录

- Frenkel：tau_ideal = G_slip b/(2πh)，保留特定滑移系刚度和 b/h 比值，不能直接套用多晶平均剪切模量
- UBER：sigma_max = W_sep/(e lambda)，由有来源的内聚能量模型求导；W_sep 为正分离功，局部张开量不能直接用超胞伸长量替代
- 中央裂纹：K_I = sigma sqrt(πa)，a 是完整裂纹 2a 的一半；K_I 不是断裂韧度或体积模量 K
- I 型能量关系：G_I = K_I²/E_prime；G_I 不是剪切模量 G，也不是自动给定的临界 Gc
- 有限宽度：Y = sqrt(sec(πa/W))，W 为完整板宽，采用有第二来源核对的 0 < 2a/W ≤ 0.8 范围；原来源的宽度比歧义明确保留

前两条是 `model_estimate`；后三条是新增的 `model_relation` / `direction: relation`，均为 `catalog_only`，不冒充严格理论上界，不增加数值计算器。论断目录升为 schema 1.3.0，评价仍为 schema 1.1.0。原有十条论断和十一条来源的内容保持不变。

```sh
python -m materials_boundaries catalog claims --claim-type model_relation --text --lang zh
python -m materials_boundaries catalog claims --query "理想剪切" --text --lang zh
python -m materials_boundaries catalog claims --query "Sekanskorrekturfaktor" --text --lang de
```

新模型显示名称有 en/zh/ja/de 版本，可跨语言字面检索；原名、原始论文标题和 DOI 原样保留，译文仍待独立科学／母语审校。[完整模型、条件与来源差异](docs/MECHANICS_CATALOG.md) · [v0.4.0 迁移](docs/MIGRATION_v0.4.0.md)

## 历史 v0.3.0：仅目录的断裂模型

新增 `griffith_central_crack_plane_stress` 和 `griffith_central_crack_plane_strain`，分别记录平面应力／平面应变下中央贯穿裂纹的临界远场拉应力模型。两者为 `claim_type: model_estimate`、`direction: prediction`、`bound_kind: null`、`evaluation_support: catalog_only`。六条 K/G 界标为 `theoretical_bound`，E/ν 标为 `derived_outer_envelope`；旧记录的 `bound_kind` 保持不变。

σc = sqrt(E_prime Gc/(πa))，平面应力取 E_prime = E，平面应变取 E_prime = E/(1−ν²)。E 为杨氏模量（Pa），Gc 为临界能量释放率（J/m²），a 为裂纹总长 2a 的一半（m），ν 为无量纲泊松比。每条模型的 `parameters` 保存符号、物理量、量纲、SI 单位及含义。Gc 不自动等于 2γ；只有形成两个新表面是唯一耗散的理想纯脆性特例才可作此替换。

这些模型要求均匀各向同性线弹性材料、足够宽／无限大板中的中央贯穿裂纹、远场 I 型拉伸，以及足够小的屈服区／断裂过程区。它们不是普适抗拉强度上界或工程许用应力，不能外推至原子尺度或 a → 0。目录记录不证明实际前提成立，不产生实例适用性状态，也不计算应力；前提未知或违反时不能据此使用公式。

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --direction prediction --text --lang zh
python -m materials_boundaries catalog claims --id griffith_central_crack_plane_strain --json
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --text --lang en
```

v0.3.0 的十条论断目录使用 schema 1.2.0，每条包含 `claim_type`、`quantity_dimension`、`si_unit` 和 `evaluation_support`；`evaluate()` 仍只输出既有八条复合材料评价，schema 保持 1.1.0。所有筛选值和标识符在四种语言中均不翻译。Griffith 的历史来源与现代 LEFM 公式核对分开记录，不声称现代公式逐字来自 1921 年论文。详见[模型与证据](docs/FRACTURE_MODELS.md)、[来源核验](docs/SOURCES.md)及 [v0.3.0 迁移检查表](docs/MIGRATION_v0.3.0.md)。

## 离线对比可视化

可对既有八条复合材料评价进行保留来源与条件信息的多案例绘图，见[可视化使用说明](docs/VISUALIZATION.md)。目录中的七条强度／断裂模型、八条稳定性判据、三条孔隙论断和三项研究的六条观测不会被绘成已计算的预测或叠加到复合材料曲线上；未知、不满足和数值失败也不能用伪造数值代替。

## 历史 v0.2.0 输出迁移

v0.2.0 将评价结果从 3 条扩展到 8 条；原有三个体积模量 claim ID、rule ID、数值形状和顺序保持不变，新条目追加其后。所有评价新增 `quantity` 和 `bound_kind`；E/ν 使用 `derived_outer_envelope` 并附带 HS 依赖信息。请按 ID/物理量读取，不要假定只有三条记录或所有结果都有压力单位。当时评价与论断目录 schema 升为 1.1.0，输入 schema 不变，来源目录仍为 1.0.0。v0.3.0 仅将论断目录升为 1.2.0，评价输出保持 1.1.0。[迁移说明及下游检查表](docs/MIGRATION_v0.2.0.md)。

## 结构与证据

- `materials_boundaries/data/claims.json`：可复用 claim、条件、固定 rule ID、公式展示、逐 claim 核验缺口
- `materials_boundaries/data/sources.json`：人工策展的来源、阅读范围、许可证状态及用途
- `materials_boundaries/data/observations.json`：单独保存模型依赖实验摘要、同一研究关联、方法、不确定性及未知条件
- `examples/*.json`：四份独立评价输入，不与 claim 定义混用；`examples/catalog/porous-synthetic.json` 与 `examples/catalog/crystal-stability-synthetic.json` 仅为文档／测试合成示例，不是评价输入
- `schemas/*.schema.json`：JSON Schema 2020-12；运行时还检查跨字段约束
- `materials_boundaries/engine.py`：固定可执行规则表；不会执行输入或资料中的任意公式字符串
- `docs/CATALOG.md`：只读目录检索、筛选、Python API 与录入检查表
- `docs/BULK_ELASTIC_WAVES.md`：体弹性波速度、精确类别比值范围、声学张量归一化、严格强椭圆性及原创能量反例
- `docs/OBSERVATION_INSPECTION.md`：六条现有观测的离线查阅、精确筛选及审计导出；不是匹配条件比较
- `docs/MIGRATION_v0.21.0.md`：六条 Ni11X 预测、12 条预测与三个显式组；原默认三点、科学协议及 schema 不变
- `docs/MIGRATION_v0.20.0.md`：新查阅 schema 1.0.0，科学记录与八条计算规则不变
- `docs/MIGRATION_v0.19.0.md`：单层 hBN 两条观测、来源与统计边界，观测 schema 1.2.0；共 36 条论断、51 条来源、三项研究六条观测
- `docs/MIGRATION_v0.18.0.md`：历史 36 条论断、50 条来源、论断 schema 1.11.0 与不变的八条可执行规则
- `docs/MODEL.md`：体积/剪切界、推导 E/ν 外包络、数值策略与边界情况
- `docs/OBSERVATIONS.md`：石墨烯、单层 MoS2 和单层 hBN 三项研究的六项观测、模型依赖、统计区别、单位及核验边界
- `docs/MIGRATION_v0.17.0.md`：观测 schema 1.1.0、窄范围 MoS2 扩展、打印 q 矛盾及不变的旧记录
- `docs/MIGRATION_v0.7.0.md`：独立观测目录、筛选与不变的论断／评价约定
- `docs/MIGRATION_v0.2.0.md`：历史八条输出、类型信息、依赖和单位迁移
- `docs/MIGRATION_v0.3.0.md`：十条目录记录、论断分类、量纲及仅目录支持标识
- `docs/MECHANICS_CATALOG.md`：v0.4.0 五条新模型、条件、推导与来源差异
- `docs/MIGRATION_v0.4.0.md`：十五条论断、十七条来源、模型关系分类与新量纲
- `docs/ELASTIC_STABILITY.md`：八条严格均匀弹性判据、四方／菱方完整模板、Voigt 约定、范围与来源
- `docs/MIGRATION_v0.8.0.md`：二十六条论断、schema 1.6.0、四条新增仅目录判据与不变的八条评价
- `docs/MIGRATION_v0.5.0.md`：十九条论断、十八条来源、逻辑谓词与不等式元数据
- `docs/POROUS_BOUNDS.md`：v0.6.0 固体＋孔隙有限孔隙率界、端点、密度及来源约定
- `docs/MIGRATION_v0.6.0.md`：二十二条论断、十九条来源、仅目录区间与不变的运行时约定
- `docs/FRACTURE_MODELS.md`：Griffith/LEFM 模型、参数、几何前提与来源边界
- `docs/VISUALIZATION.md`：既有复合材料评价的离线多案例对比可视化
- `docs/SOURCES.md`：来源核验、历史争议与许可证边界
- `docs/LITERATURE_EXAMPLE.md`：文献模型参数、换算与计算假设的逐项区分

HS 实现与 [Kochmann–Milton 2014, arXiv v1](https://arxiv.org/html/1401.4142v1) 的体积模量式 (117)/(134) 及剪切模量式 (118)/(135) 核对。E/ν 恒等式与 [Meille–Garboczi 2001 式 (3)，第 2.2 节，印刷页 374 / PDF 第 4 页](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860321)的提取文本核对；截图/渲染核验失败，因此不声称已完成视觉核验。该文献只支持恒等式；外包络是基于这些恒等式和单调性的项目推导，不构成紧联合界的新定理，也不验证本复合材料的适用前提。v0.2.0 新增的第 9 条来源仅含元数据和原创注记，不附 PDF；未核实开放再使用许可证。原始 [Hashin–Shtrikman 1963](https://doi.org/10.1016/0022-5096(63)90060-7) 当前仅读到出版商摘要，原文公式定位仍未知。

## 测试

```sh
# 完整开发检查要求 jsonschema 及格式校验支持；运行时仍无第三方依赖
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -p test_release_metadata.py -v
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
```

测试涵盖合成基准、文献模型原始参数/换算/证据一致性、独立有理数算例、相标号交换、单位/尺度变换、相等模量、纯相、未知/冲突条件、极端对比度、数值溢出/下溢、推导依赖及无量纲泊松比边界、JSON schema、来源引用一致性和四语言输出一致性。v0.8.1 的完整开发流程不允许静默跳过目录校验：缺少 `jsonschema` 或所需格式校验器会失败；无第三方依赖的运行时输入校验仍有效。CI 配置针对 Python 3.11/3.12。新增目录录入与合成追加测试见 [贡献指南](CONTRIBUTING.md)。

下一步应先做独立科学复核、补齐原始文献核验，再考虑经独立审查的孔隙数值评价、联合可达域或更广的外部数据导入。不要把增加记录数当作验证质量。
