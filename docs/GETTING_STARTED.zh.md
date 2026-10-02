# 快速开始：材料边界

## 当前 v0.18.0：仅目录的体弹性波

本版只新增两条关系和两条来源：共 **36 条力学论断、50 条来源**，论断 schema
为 **1.11.0**。两项研究的四条观测、六条计算预测、五个合成温度演示（七个分支）
以及八条可执行复合材料规则不变。不新增波速计算器、材料输入、张量特征值求解器或波图。

在无应力平衡态、均匀无界三维经典局部线弹性无耗散介质中，若各向同性 K、G
及标量密度 ρ 均为有限正值，则 **c_L²=(K+4G/3)/ρ**、**c_T²=G/ρ**，且
**c_L/c_T∈(√(4/3),∞)**。这是有限正应变能材料类别之间的比值范围：下确界不达到，
不存在共同的有限上界，无穷大也不是可达到的材料值。每个固定材料的 c_L、c_T
均有限且与方向无关，横波具有二重简并。

在所声明的实刚度张量对称性下，**Q_ik=C_ijkl n_j n_l** 的单位为 Pa，
**Γ=Q/ρ** 的单位为 m² s⁻²，满足 Q a=ρc²a。相位法向 n 与位移偏振 a
是不同变量。严格强椭圆性要求每个单位 n 的 Q(n) 均正定，等价于每个方向的
三个波速平方均严格为正。完整对称应变能正定性蕴含强椭圆性，反之不成立：
项目原创反例 **K=−G/3、G>0** 给出 Q=GI，三个波速平方相等且为正，但静水
应变能为负。这不是真实稳定材料的提案；既有完整应变能稳定性判据保留较强含义。

一般各向异性模态不一定是精确纵波或横波，也没有普适的“纵波最快”排序。
相速度不等于关于射线／群速度的结论；不能自动代入静态或等温模量，也未提供
热力学转换、预应力或有限应变推广。Chevrot–van der Hilst（2003）印刷页 498
式 (1)–(4) 及 Xiang–Qi–Wei arXiv v2 第 2、4–5 页支持基础方程；区间和能量
证明为项目原创推导。不附来源图或全文；独立科学与母语审校尚未完成。
详见[完整假设、证明、版本与排除范围](BULK_ELASTIC_WAVES.md)及
[v0.18.0 迁移](MIGRATION_v0.18.0.md)。

```sh
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang zh
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang zh
```

**历史 v0.17.0** 新增一项研究的两条仅目录单层 MoS2 记录：当时共有 **2 项研究的 4 条观测、48 条来源**，观测 schema 为 **1.1.0**。原有石墨烯记录不变。MoS2 面内刚度 **180 ± 60 N/m** 与破坏强度 **15 ± 3 N/m** 的 ± 表示来源报告的标准差。**打印的 q 公式与所写 q=0.95 不一致；实际拟合常数仍未确定，未重新拟合。** 详见[标准差含义、来源证据与 q 限制](OBSERVATIONS.md#monolayer-mos2-bertolazzi-et-al-2011-new-records)。

**首个公开版本基线（0.16.0）当时的目录：**34 条力学论断、47 条来源记录、2 条观测、6 条计算预测，以及 5 个合成温度演示模型（7 个分支）。八条复合材料计算规则不变。当时的论断 schema 为 1.10.0；科学 schema 版本独立于软件版本。

原创代码、文档和原创策展内容采用 [MIT 许可证](../LICENSE)，不重新许可第三方作品或科学事实。NIST 低温系数及推导示例出于谨慎暂不收录，等待复用条款澄清；这不表示已经证实禁止再分发。书目信息和链接保留，见[第三方说明](../THIRD_PARTY_NOTICES.md)。

温度模型的系数和区间均为人为构造，不是真实材料或测量数据。线性示例在 50 K 返回 15 GPa；重叠示例在 50 K 同时返回 25 和 32.5 GPa。不选择分支、不平均、不外推，也不绘制不确定性带。[温度模型说明](TEMPERATURE_MODELS.md)

```sh
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-50k.json --lang zh
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-overlap-50k.json --lang zh
python -m materials_boundaries temperature plot --output /tmp/temperature-demos --lang zh
```

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Bulk elastic waves](BULK_ELASTIC_WAVES.md) · [Release scope](MIGRATION_v0.18.0.md)

## 本地运行

需要 Python 3.10 或更高版本。在仓库根目录执行以下命令，无需第三方运行时软件包或网络访问：

```sh
python -m materials_boundaries validate examples/synthetic-two-phase.json --lang zh
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang zh --unit GPa
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang zh --json
```

可用 `--lang en`、`--lang ja` 或 `--lang de` 切换显示语言。JSON 键、枚举值、公式、数值和单位标识符保持不变。缺失的译文回退为英文；英文中也没有的键会显示明确的缺失标记。

## 理解合成示例

示例仅供说明，并非实测材料数据：

- 相 1：`f1 = 0.5`，`K1 = 10 GPa`，`G1 = 5 GPa`
- 相 2：`f2 = 0.5`，`K2 = 30 GPa`，`G2 = 15 GPa`
- 体积模量 K：Reuss `15 GPa`；HS `16.25–17.5 GPa`；Voigt `20 GPa`
- 剪切模量 G：Reuss `7.5 GPa`；HS 约 `8.37837837838–9.04761904762 GPa`；Voigt `10 GPa`
- 杨氏模量 E 推导外包络：约 `21.4488468362–23.1528046422 GPa`
- 泊松比 ν 推导外包络：约 `0.265190525232–0.293562708102`，无量纲单位 `1`

HS 区间是理论约束，不是模型预测、测量不确定性区间或工程验收限值。输出数值为浮点近似值，未通过区间运算认证。

## 正确理解推导外包络

同一材料体系满足 E = 9KG/(3K+G)、ν = (3K−2G)/(2(3K+G))。E 下/上端点分别取 (Klow,Glow)/(Khigh,Ghigh)；ν 下/上端点分别取 (Klow,Ghigh)/(Khigh,Glow)。分别成立的两个 HS 区间，其端点不一定可同时达到：这些结果是保守外包络，不是紧的联合界。前提未知或不满足时不输出数值；相排序不一致时，E/ν 不回退到 Reuss/Voigt 界。

`--unit` 仅改变 K/G/E 单位；ν 始终使用单位 `1`，须满足 −1 < ν < 0.5。负值和零值均可有效。浮点舍入达到任一不包含的边界时，结果为 `numerical_range_error` 且数值为 null，不能裁剪成伪造的物理端点。任一依赖的 HS 结果出现数值错误时，推导外包络也不可用。Decimal 计算不等于向外舍入认证。

评价输出自 v0.2.0 起包含八条记录，v0.8.0 保留这八条科学评价。请按 `claim_id` 与 `quantity` 选择，不要假定列表长度。既有体积模量 ID、规则 ID 和数值结果形状保持不变，类型元数据和评价输出 schema 1.1.0 均在 v0.2.0 引入。输入 schema 和示例仍有效。参见 [v0.2.0 迁移说明](MIGRATION_v0.2.0.md)与[模型及公式](MODEL.md)。

## 使用界限前先检查适用性

- `satisfied`（满足）：在已实现的检查范围内，提供的输入和声明支持所有必要前提
- `violated`（不满足）：至少一个前提与输入冲突，不得使用受影响的界限
- `unknown`（未知）：缺少评估至少一个前提所需的证据，不能假定界限适用

组成相各向同性与等效介质各向同性是不同的前提。所有活动相的 K/G 必须为正。HS 与推导的 E/ν 还要求两相可同时满足 `K1 <= K2` 和 `G1 <= G2`，排序时必须保留各相 K/G 与体积分数的配对关系；Reuss/Voigt 不要求这一排序。完整假设见论断目录；程序不会独立验证试样的微观结构。评价器仍不进行强度、失效或塑性的数值计算。下述断裂模型仅作为目录记录。

```sh
python -m materials_boundaries evaluate examples/unknown-isotropy.json --lang zh
python -m materials_boundaries evaluate examples/anisotropic-constituent.json --lang zh
python -m materials_boundaries catalog claims
python -m materials_boundaries catalog sources
```

使用自己的输入时，可复制示例并保留模式规定的规范键和枚举值。未知的可选观测可写为 `null` 或省略；不要编造数值，也不要将缺失的证据写成 `satisfied`。单位标识符区分大小写：`Pa`、`kPa`、`MPa`、`GPa`。JSON 数字使用小数点。先执行 `validate`，再执行 `evaluate`；结构合法并不等于物理前提满足。

四类科学表述的区别见[术语表](TERMINOLOGY.md)，翻译约定与质量检查见[语言支持说明](I18N.md)。

## 检索只读目录

目录仅检索随附的人工策展记录，不联网，也不修改数据。原有 `catalog claims` 和 `catalog sources` 命令仍返回规范 JSON；`--json` 显式选择相同输出。使用 `--text` 可显示本地化标签及核心证据状态说明，同时保留原始文献标题、证据文字和规范 ID。

```sh
python -m materials_boundaries catalog claims --id hs_bulk_3d_two_phase --text --lang zh
python -m materials_boundaries --lang zh catalog claims --direction interval --text
python -m materials_boundaries catalog claims --query "bulk kochmann" --source-id kochmann_milton_2014 --json
python -m materials_boundaries catalog sources --query "Milton moduli" --year 2014 --text --lang zh
python -m materials_boundaries catalog sources --role changed_assumption_comparison --license CC-BY-4.0 --text --lang zh
python -m materials_boundaries --lang zh catalog --help
```

`--lang` 可位于命令前或命令后；重复指定时以最后一次为准。帮助信息中的标签和说明随之切换，命令语法与 ID 保持规范形式。

`--id` 精确匹配且区分大小写。`--query` 按空白拆词，经 Unicode `casefold` 后逐词做字面子串匹配，所有词均须命中。检索字段为 ID、标题/名称，以及来源的作者、DOI、用途，或论断的物理量、方向、`claim_type`、规则 ID、证据来源 ID。十六条 v0.4.0–v0.6.0 与 v0.8.0 记录的四语言显示名称也作为字面搜索别名。不做词干化、排名、模糊匹配、自动翻译或网络搜索。

论断筛选为 `--direction interval|lower|upper|prediction|relation|constraint`、`--claim-type theoretical_bound|derived_outer_envelope|model_estimate|model_relation|stability_criterion` 和 `--source-id`（精确匹配证据引用）。来源筛选为 `--role`、整数 `--year` 和 `--license`（精确匹配许可证标识符或状态）。字符串筛选区分大小写；全部条件按 AND 组合，保留目录顺序。空结果是有效查询（退出码 0）；未知 `--id`、无效筛选或用于错误目录类型的筛选报错（退出码 2）。

阅读来源、核对公式或通过软件测试不等于独立科学证明，也不授予内容再使用许可。搜索命中不能证明物理适用性，许可证筛选仅匹配已记录的元数据。原创代码采用 MIT 许可证，第三方作品不因此被重新许可。Python API 和来源/论断录入检查表见 [Catalog reference](CATALOG.md)。

## 仅供目录检索的断裂模型

v0.3.0 新增两条 Griffith / 线弹性断裂力学（LEFM）临界远场拉应力模型记录：`griffith_central_crack_plane_stress`（平面应力）和 `griffith_central_crack_plane_strain`（平面应变）。两者均为 `claim_type: model_estimate`、`direction: prediction`、`bound_kind: null` 和 `evaluation_support: catalog_only`。它们记录模型及前提，不是新增的数值评价。

公式为 σc = sqrt(E_prime Gc/(πa))，平面应力取 E_prime = E，平面应变取 E_prime = E/(1−ν²)。E 是杨氏模量（Pa），Gc 是临界能量释放率（J/m²），a 是中央贯穿裂纹总长 2a 的一半（m）；平面应变还需要无量纲泊松比 ν。`parameters` 数组逐项保留符号、物理量、量纲、SI 单位及含义。Gc 不能自动替换为 2γ；只有在形成两个新表面是唯一耗散的理想纯脆性特例中，才有 Gc = 2γ。

前提包括均匀各向同性线弹性材料、足够宽／无限大板中的中央贯穿裂纹、远场 I 型拉伸，以及足够小的屈服区／断裂过程区。其他裂纹几何或大范围塑性不适用此模型。临界应力不是普适的抗拉强度上界，也不是工程许用应力；不能把连续介质公式外推至原子尺度裂纹或 a → 0。

目录检索不证明某试样满足前提，不产生 `satisfied`/`violated`/`unknown` 实例状态，也不计算应力。前提未知或违反时，不能据此使用公式。`evaluate()` 仍按 schema 1.1.0 返回原有八条复合材料评价；v0.3.0 将十条记录的论断目录升级至 schema 1.2.0；历史 v0.4.0 为十五条记录、schema 1.3.0。每条论断新增明确的 `claim_type`、`quantity_dimension`、`si_unit` 和 `evaluation_support`。

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --direction prediction --text --lang zh
python -m materials_boundaries catalog claims --id griffith_central_crack_plane_strain --json
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --text --lang zh
```

这些规范代码在四种语言中完全相同，搜索不会翻译显示标签。六条 K/G 界标为 `theoretical_bound`，E/ν 标为 `derived_outer_envelope`。Griffith 的历史归属与现代公式核对是不同的证据角色。参见[断裂模型及证据](FRACTURE_MODELS.md)、[来源说明](SOURCES.md)与 [v0.3.0 迁移说明](MIGRATION_v0.3.0.md)。v0.3.0 断裂扩展没有新增论文全文、出版商 PDF、测量数据或再使用许可；原创代码采用 MIT 许可证，第三方作品不因此被重新许可，独立科学审校尚待完成。

## 一个文献模型示例

独立的[环氧/玻璃示例](LITERATURE_EXAMPLE.md)保留文献模型 E/ν 与本项目换算的 K/G。玻璃 20%、宏观各向同性和理想粘结是计算器假设，并非试样测量结果。温度和材料背景仍未知。

```sh
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --lang zh
```

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang zh
```

```sh
python -m materials_boundaries catalog claims --query porous --direction interval --text --lang zh
```

## 检索观测

`catalog observations` 同样默认输出规范 JSON，并用 `--text` 选择本地化显示。观测查询检索 ID、名称、`quantity`、`observation_type`、`study_id`、`material.name`、证据来源 ID 和四语言策展显示名称，沿用字面、所有词均命中的规则。`--source-id` 由论断与观测共用；`--quantity` 和 `--observation-type experiment_derived_model_dependent` 仅供观测，精确匹配并区分大小写。所有筛选按 AND 组合，不支持的目录／筛选组合报错。同一研究 ID 下的两个性质记录仍只代表一项研究。

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang zh
```

## 已发表的理想剪切预测（v0.12.0）

运行 `catalog predictions --text --lang zh` 查询三个已核对来源的周期模型；
`prediction plot --output /tmp/ideal-shear --lang zh` 导出离散点比较。
Ni / Ni11Al / Ni11Co：5.13 / 4.58 / 5.46 GPa。只在同一研究所述方法层面比较，
不是商业合金测量值或普适上界。物理温度、标量压力、磁态与不确定性保持未知；
0.08 GPa 收敛判据不是误差棒。[方法、来源与局限](COMPUTATIONAL_PREDICTIONS.md)。
