# 快速开始：材料边界

## 当前 v0.23.0：显式 PA12 CF15 温度观测图

新独立路径只显示**同一来源报告协议下表 3 的完整六个已接纳单元格**，是已发表摘要
的描述性转录，不是材料预测或独立科学验证。科学目录不变：**12 条观测、52 条来源、
36 条论断、12 条预测、五个合成温度模型、七个分支、八条可执行规则**；观测仍为
`catalog_only`。

```sh
python -m materials_boundaries observation plot-temperature --dataset-id ciganas-2026-pa12-cf15-fff-uts-temperature --output /tmp/pa12-temperature-plot-zh --lang zh
python -m materials_boundaries observation plot-temperature --help --lang zh
```

上述精确数据集 ID 与输出目录均**必需**；不默认绘制全部记录，不接受子集、任意压力
形状记录或自动分组。`--lang en|zh|ja|de` 仍以最后一次出现为准。新绘图 schema
**1.0.0** 独立于不变的观测 **1.3.0** 和通用查阅 **1.1.0**。`observation inspect`
仍是无数值轴的文本视图，原筛选及目录顺序保持不变。

六个不连接、同样式的点表示**报告的中心 UTS 值，不断定为均值**；横轴是数值试验箱
温度（°C），纵轴是来源 MPa。带端帽的竖向须线表示 **±报告的标准差 SD**，不是 SEM、
置信区间、观测最小／最大值、硬界或覆盖声明。**每条件三次拉伸试验**的原始重复数据
及独立性未核实。试验箱稳定 30 分钟不证明直接试样温度；无横向须线意味着**温度不确定性
未报告，而非零**。固定的 15–125 °C／0–55 MPa 显示范围只是边距／基线，不是材料极限。
不连线、不拟合、不插值或外推、不排名或叠加，也不提供许用值或安全声明。

精确来源表保留字符串及尾零；Pa 仅为独立的精确单位元数据，**1 MPa = 1000000 Pa**，
不增加精度或重算几何。中心统计量／聚合方式、应力／面积依据、含水量／湿度和局部
应变率仍未知。水平 ±45° FFF、干燥、声明的 15 wt.%、100% 填充设置、标称几何与
1 mm/min 横梁协议是具体条件，不能证明实测组分、零孔隙或各向同性。

五类文件采用 `observation-temperature-plot` 前缀：JSON、CSV、宽／窄 SVG、无脚本
响应式 HTML。紧凑 SVG 保持六项核心警告、图例、精确来源表／记录 ID、共享协议／几何／
未知条件摘要、精确来源定位及版本／权利归属可见。完整元数据字典、逐条重复的来源信息和
六组 SI 值仍无损保存在 JSON／CSV 及无脚本 HTML 详情中；核心解释警告不会隐藏于此。JSON／CSV 确定且不随语言变化；将来源、ID 和 JSON 列按文本导入，因为
公式式前缀保持原样。新规范验证在写入前从当前目录重建；无效输入不改变输出，但后续
磁盘／权限错误不保证全部文件原子回滚。绘图恢复表 3 来源顺序；通用查阅仍用目录顺序。

HTML 版本、PDF 未检查、未选表 4 差异、CC BY 4.0 归属及离散绘图改编说明保留。
不新增来源媒体或原始数据。机器辅助翻译不是独立科学／母语审校；浏览器 QA 未验证。
[完整绘图／API／CSV 合同](OBSERVATION_TEMPERATURE_PLOT.md) · [迁移](MIGRATION_v0.23.0.md)。

## 此前 v0.22.0：六个试验箱条件下的 PA12 CF15 拉伸摘要

新增 Ciganas、Kalinauskis 和 Cigane（2026）表 3 的六个 UTS／SD 单元格，
报告的试验箱条件为 **23、40、60、80、100、120 °C**。当前共 **四项研究的
12 条观测、52 条来源**；**36 条论断、12 条预测、五个合成温度模型、七个分支
及八条可执行复合材料规则**不变。

材料为水平 FFF 打印的 Fiberlogy PA12 CF15，交替 +45°／−45° 光栅，
试验箱稳定 30 分钟后以 1 mm/min 横梁位移速率测试。这不是实测局部应变率，
也不证明直接试样温度或温度稳定公差。干燥不能证明实际含水量；15 wt.% 是声明
配方，100% 填充是打印设置，不代表实测纤维含量或零孔隙率。应力定义、应力面积
依据、确切中心统计量和聚合方式仍未知。每条件报告三次试验；± 是报告的标准差，
不是标准误、置信区间、硬界或通用工程许用值。

新类型为 `experiment_derived_tensile_test_summary`，物理量为
`ultimate_tensile_strength_as_reported_3d`。**MPa 来源字符串**及 SD 与
**精确 Pa 单位换算**分开，1 MPa = 1000000 Pa 不增加测量精度或进行几何重算。
旧二维 N/m 记录不变。不插值、不拟合连续温度规律、不排名或跨量纲比较。

观测 schema 为 **1.3.0**，查阅 schema 为 **1.1.0**。旧查阅包须重新生成，不能只改
版本号。默认返回 12 张文本卡片，核心警告先于性质值；CSV 明确区分报告单位与 SI／
归一化列。完整目录拒绝同一来源单元格的重复别名；科学内容不变的子集及改名身份可用，
其他既有方法族的追加能力保留。

保留所检 HTML 的更新版本、PDF 未检查和未选表 4 的缓存／实时差异。六个所选表 3
单元格通过当前 HTML、视觉核对及第二次独立转录一致，不代表独立实验重复。文章的
CC BY 4.0 及作者／题名／DOI 归属保留；厂家表 1 排除，不再分发来源媒体或长段正文。
翻译及软件检查不是独立科学审查或母语审校。

```sh
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang zh
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15-zh --lang zh
python -m materials_boundaries observation inspect --id ciganas2026-pa12cf15-uts-60c --output /tmp/pa12-cf15-60c-zh --lang zh
```

[PA12 CF15](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) · [v0.22.0](MIGRATION_v0.22.0.md) · [Inspection](OBSERVATION_INSPECTION.md)

## 此前 v0.21.0：新增六条 Ni11X 模型预测

本版只新增六条已发表的理想剪切预测：**Ni11Cr 4.90、Ni11Mn 5.12、
Ni11Fe 5.20、Ni11Cu 4.51、Ni11Si 4.17、Ni11Ti 4.24 GPa**，来源为
Shimanek 等的 arXiv:2108.06412v2，表 2，PDF／印刷页码 27。
在 v0.21.0 时，共 **12 条预测、2 个科学方法族、3 个显式比较组**；36 条论断、51 条来源、
三项研究的 6 条观测、5 个合成温度演示（7 个分支）及 8 条可执行复合材料规则不变。
不改变运行时、科学 schema 或已有来源记录。

新组名称为 **Ni11X 周期模型：Cr、Mn、Fe、Cu、Si 和 Ti**，必须显式选择。
原 Ni／Ni11Al／Ni11Co 默认组仍为三点，独立的硅首次失稳三点组不变。
Ni11Si 的剪切预测不是纯硅拉伸首次失稳强度。无筛选目录返回 12 条记录；
按 Shimanek 来源筛选返回 9 条，但这不会建立新的绘图比较组。

这些模型为由 fcc Ni 构建的 12 原子、三层周期晶胞，平面内一个 Ni 位点由 X 取代；
使用 (111)[1,1,-2] 正向 pure-alias 剪切，固定规定剪切角，弛豫原子位置与其余晶胞参数。
比较仅限于**已发表方法层面**，不能证明原始输入或未知条件相同；
不是纯 X 强度、商业合金牌号、实验测量或普适上界。

六个表格标签未打印 pv／sv 后缀，但这不能确认 PAW 数据集、价电子配置或不含半芯态。
物理温度、标量压力、磁态／自旋极化及统计／总不确定性仍未知。
来源的 GGA 对应 **Perdew 等（1992），不能推定为 PBE**。
**0.08 GPa 峰值收敛不是误差棒**；4.90、5.20 保留原打印精度，不表示不确定性。
不再分发来源 PDF、全文或图像；来源核对及翻译检查不是独立科学或母语审校。

```sh
python -m materials_boundaries catalog predictions --query shimanek_v2_table2_cr_mn_fe_cu_si_ti --text --lang zh
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-zh --lang zh
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_ni_al_co --output /tmp/ni-original-zh --lang zh
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability-zh --lang zh
```

[方法、来源与局限](COMPUTATIONAL_PREDICTIONS.md) · [迁移说明](MIGRATION_v0.21.0.md)

## 此前 v0.20.0：离线观测查阅视图

以按来源排序的卡片／表格查阅三项研究的六条现有模型相关摘要。科学记录不变：
36 条论断、51 条来源、六条观测、六条计算预测及五个合成温度演示（七个分支）。
仍只有八条可执行复合材料规则。新增查阅包 schema 1.0.0；观测 schema 仍为 1.2.0。

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang zh
python -m materials_boundaries observation inspect --output /tmp/hbn --source-id falin_et_al_2017_hbn_mechanical_properties --group-by quantity --lang zh
python -m materials_boundaries observation inspect --output /tmp/selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d --lang zh
python -m materials_boundaries observation inspect --help --lang zh
```

可重复 `--id` 选择精确 ID；`--source-id` 和 `--quantity` 区分大小写并精确匹配。
筛选按 AND 组合；可选量为 `in_plane_stiffness_2d`、`breaking_strength_2d`。
默认按 `study` 分组，`quantity` 仅改变导航。保留目录顺序，绝不按数值排序。
未知、重复或格式错误的 ID、不支持的筛选／科学方法族及空结果均在写文件前拒绝。

导出 `observation-inspection.json`、`.csv`、`.zh.svg`、`.narrow.zh.svg` 和 `.zh.html`。
HTML 可本地打开，无脚本且自包含；仅在读者点击来源链接时访问网络。
JSON／CSV、来源措辞、数值、ID 和摘要哈希不随语言变化。“规范化目录显示”
与来源原始字符串分开，不是逐字引文或新的厚度换算。

警告先于数值：MoS2 保留打印 q 矛盾、实际拟合 q 未知且未重拟合／更正；
石墨烯 ± 的统计含义未经核实；hBN 强度为压头下应力的 FEM 体积平均，
确切中心统计量及应力分量未指定。hBN 标准差及薄膜计数的证据仍是公开审稿作者
回复 PDF 第 8 页；刚度样本数不能变成强度失效次数。未知条件不构成条件相同的证据。

不新增观测求值器、匹配条件比较、数值坐标轴、误差棒、聚合、排名或叠加。
旧查阅包需重新生成，不能仅改版本号。不附来源 PDF、图或原始数据。
翻译尚未经过独立科学或母语审校。
[查阅指南](OBSERVATION_INSPECTION.md) · [迁移说明](MIGRATION_v0.20.0.md)

## 历史 v0.19.0：仅目录的单层 hBN 观测

只新增 Falin 等（2017）的两条记录和一条来源：共 **36 条力学论断、51 条来源、
3 项研究的 6 条观测**。观测 schema **1.1.0 → 1.2.0**，hBN 使用独立封闭方法族。
六条计算预测、五个合成温度演示（七个分支）及八条可执行复合材料规则不变；
论断 schema 仍为 1.11.0。

来源明示 **面内刚度 289 ± 24 N/m** 与 **破坏强度 23.6 ± 1.8 N/m**。
标准差定义来自出版商链接的**公开审稿作者回复 PDF 第 8 页、审稿人 #1 问题 3**，
不能仅凭正文的 ± 符号得出。这不是标准误、置信区间、硬界或完整不确定性预算，
确切重复试验权重未知。**N=11 是试验薄膜张数，且仅明确对应刚度平均值**；
曲线总数及失效事件数未知。每张薄膜通常压入五次，不等于恰好 55 条曲线，
也不能证明有 11 个强度重复样本。

刚度由圆形膜 AFM 拟合推断。强度来自非线性 FEM 中**有限半径压头下膜单元应力的
体积平均**，不是补充图 S5 的**最大 Von Mises 应力**诊断，也不是直接测量的均匀
拉伸强度。有限应变应力／应变度量未知。来源公式 **q=1/(1.049−0.15ν−0.16ν²)**、
**ν=0.211** 的 **0.9898768854482001 仅为策展算术核对**；未核实来源另报的数值 q
或实际拟合常数，因此不声称 hBN 存在 q 矛盾或需更正。

“环境条件（ambient）”不提供数值温度、压力、气体组成或湿度。**0.5 μm/s**
是加载／卸载探针平移速度，不是应变率。两个 N/m 摘要都是来源明示值；**0.334 nm**
只是来源的模型厚度约定。不新增厚度换算、重拟合、排名、比较、图或复合材料叠加。
原有石墨烯和 MoS2 记录保留，包括下文醒目的 MoS2 打印 q 矛盾。

文章采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)；补充材料与审稿文件的
独立许可范围未核实。不附来源 PDF、全文、图、截图、审稿报告或原始数据集合。
转录核对和软件测试不等于独立科学或母语审校。详见 [hBN 证据与边界](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
及 [v0.19.0 迁移](MIGRATION_v0.19.0.md)。

```sh
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang zh
python -m materials_boundaries catalog observations --query "hBN stiffness" --json
```

## 历史 v0.18.0：仅目录的体弹性波

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

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Bulk elastic waves](BULK_ELASTIC_WAVES.md) · [Release scope](MIGRATION_v0.23.0.md)

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

`catalog observations` 同样默认输出规范 JSON，并用 `--text` 选择本地化显示。观测查询检索 ID、名称、`quantity`、`observation_type`、`study_id`、`material.name`、证据来源 ID 和四语言策展显示名称，沿用字面、所有词均命中的规则。`--source-id` 由论断与观测共用；`--quantity` 和 `--observation-type` (`experiment_derived_model_dependent`, `experiment_derived_tensile_test_summary`) 仅供观测，精确匹配并区分大小写。所有筛选按 AND 组合，不支持的目录／筛选组合报错。同一研究 ID 下的两个性质记录仍只代表一项研究。

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang zh
```

## 已发表的理想剪切预测（v0.12.0）

运行 `catalog predictions --query shimanek_v2_table2_ni_al_co --text --lang zh` 查询三个已核对来源的周期模型；
`prediction plot --output /tmp/ideal-shear --lang zh` 导出离散点比较。
Ni / Ni11Al / Ni11Co：5.13 / 4.58 / 5.46 GPa。只在同一研究所述方法层面比较，
不是商业合金测量值或普适上界。物理温度、标量压力、磁态与不确定性保持未知；
0.08 GPa 收敛判据不是误差棒。[方法、来源与局限](COMPUTATIONAL_PREDICTIONS.md)。
