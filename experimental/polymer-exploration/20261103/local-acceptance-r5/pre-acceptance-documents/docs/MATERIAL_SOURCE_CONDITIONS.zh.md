# 已有材料的来源、条件与使用说明

本页整理已有配方参考属性，并说明 JARVIS、PolyOmics 计算来源参考密度的阅读方式。
前三组配方说明以实验提交 `f13586759af6a391635fa81da20c73eb6a6c1c6c` 中的规范目录及原有集成说明为背景；
计算来源按各自固定版本与记录字段限定，接纳及发布以对应验收决定为准。
本页只解释已有字段与使用边界，不新增材料、属性、来源或接纳决定。
原有配方和计算说明不重新核实标准符合性或补齐未知实验/轨迹条件；
以下 2026-11-02 小节单独记录本轮实际原文复核范围。

需要查询命令和字段解释时，先读[材料参考检索教程](MATERIAL_REFERENCE_WALKTHROUGH.zh.md)。

## 2026-11-02：已有密度记录的原文复核（有限数据审核通过）

后续针对剩余 14 项调湿条件的[逐项复查清单](../experimental/data-updates/nbs-conditioning-followup-20261102/README.zh.md)
已在本地整理：没有发现可确认的新密度专属调湿协议，14 项继续未知；10 项已有的相关制备说明
与调湿严格分开。本次后续整理不改原生三表，也不继承此前批次的独立审核结论。

本轮更正 15 条既有性质记录的来源检查范围、条件状态及说明，涉及 2 个来源，
材料身份数、性质数、原始数值、单位、样本量及数值不确定度均不变。
记录保留原 ID，修订号从 `1.0.0` 改为 `1.0.1`；表格式仍为 `1.0.0`。
[逐项检查清单](../experimental/data-updates/source-conditions-20261102/source-review.json)
保留更正前后字段和精确数据指纹。2026-11-02 11:40:41（北京时间），
独立审阅者 `/root/review_source_conditions` 批准本批有限数据更正及修订号实现；
见[具名独立审核记录](../experimental/data-updates/source-conditions-20261102/INDEPENDENT_REVIEW.json)。
审核不认证独立科学真实性、软件稳定发布或来源标准符合性。

### NBS：密度参考温度与衍射条件分别读取

直接检查 [NBS Circular 539 Volume I 官方扫描本](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf)
的引言、14 条既有记录对应的样品和密度段落。原文 PDF 指纹与目录已有指纹一致：
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`。

- 14 个试验标准字段改为“所检段落未报告密度试验标准”，不再仅记为交接中未核实。
  ASTM 衍射卡和 ACS 试剂规格不构成密度试验标准符合性证明。
- 14 个密度专属调湿字段仍为 `not_verified`。样品退火、干燥或重结晶不能自动证明
  计算密度时的含水量、相对湿度或独立调湿程序；原有样品制备说明继续保留在状态中。
- 按性质的温度字段阅读密度参考温度。引言明确区分文字中的晶格常数参考温度
  与衍射表中的实验温度。NaF 记录仍保留密度参考温度未知，不从相邻表头代填。
- 这些值由实验晶格信息导出，不是松装／压实密度，也不自动代表当前采购样品。
  本轮不重新计算密度，不从末位数字制造误差区间。

```sh
python -m materials_boundaries.database query --source swanson_tatge_1953_nbs_circ539v1 --query mat_nbs1953_naf
python -m materials_boundaries.database summary --source swanson_tatge_1953_nbs_circ539v1
```

关键词也会匹配状态中的杂质说明，例如 sodium fluoride 会同时找到含相关杂质说明的 KF。
因此先发现候选，再核对 `record_id`、身份和来源；上例使用 NaF 的稳定身份 ID 定位。

### 铌：室温密度与高温热物性程序分别读取

直接复查 [Watanabe 论文](https://doi.org/10.1007/s10765-026-03765-z)的出版社正文
第 2.1.1、2.1.2 节及文章许可说明。只补充密度标准、方向和加载速率的限定缺失说明。
加热程序不补作密度测量条件；已有样本量和误差未知值不变。
补充材料仍沿用原交接的检查范围，本轮未重新检查。文章字节指纹仍不可用，
直接下载未取得有效 PDF，不使用访问响应的哈希冒充文章哈希。
许可说明现直接对应文章的 CC BY 4.0 声明，保留署名、许可链接、修改说明和第三方例外；
不扩大为法律认证，也不分发原文资产。

```sh
python -m materials_boundaries.database query --source watanabe2026_niobium_thermophysical
```

两条来源记录的说明变化会传播至 42 条关联导出记录，其中只有 15 条性质对象实际修订；
另外 27 条仅关联来源元数据变化。快照差异不应误报为新增材料或新增测量。
三表、专项、安装及快照差异的实际结果见[本批验证记录](../experimental/data-updates/source-conditions-20261102/VALIDATION.json)。
冻结候选输入与生产者验证记录中的“待审核”状态保留为当时的记录；后续状态由具名审核记录建立。
本批统一交付及托管 CI 以实际提交为准，不沿用旧提交的 CI 状态。

## PLA/PCL：有 SD，不代表中心值一定是均值

来源标识：`delgado_aguilar_2020_pla_pcl`。
Delgado-Aguilar 等（2020）的配方关联来自 Table 1，Young's modulus 数值来自 Table 2；
SD 的解释来自第 3.2 节式 (6) 后的段落。
目录保留官方 HTML/XML 的有限检查范围和 CC BY 4.0 归属说明。
原始 PDF 字节、页图以及 PDF 与 HTML 的等价性仍未核实。

| 来源配方 | 标称 PLA:PCL 质量配比 | Young's modulus，GPa | 单独报告的 SD，GPa |
| --- | --- | ---: | ---: |
| B95/5 | 95:5 | 3.70 | 0.13 |
| B90/10 | 90:10 | 3.60 | 0.26 |
| B85/15 | 85:15 | 3.38 | 0.27 |
| B80/20 | 80:20 | 3.20 | 0.19 |
| B60/40 | 60:40 | 2.55 | 0.09 |
| B40/60 | 40:60 | 1.86 | 0.11 |
| B20/80 | 20:80 | 1.13 | 0.05 |

中心统计量与样本数未报告。因此，上表不标注为“均值 ± SD”，也不推算 SEM、
置信区间或独立重复数。标称配方不是最终组成分析；表中没有接纳纯 PLA/PCL 端点。

| 条件项目 | 目录已有内容 | 使用边界 |
| --- | --- | --- |
| 试样与方法 | 注塑试样；Instron 1122；5 kN 传感器 | 不推断未说明的试样尺寸或取向 |
| 试验标准 | 来源引用 ISO 527-1:2012 | 不表示独立核实了标准符合性 |
| 运动参数 | 横梁速度 2 mm/min；夹具间距 115 mm | 间距不是引伸计标距；不据此计算局部应变率 |
| 制备信息 | 干燥、混合和注塑条件见原有集成说明 | 加工温度、压力不能代替拉伸试验温度、压力 |
| 未知项 | 试验温度、湿度、压力、调湿、加载方向、模量拟合区间及样本数 | 保留未知，不套用所谓标准默认值 |

查询这一个来源的已接纳模量记录：

```sh
python -m materials_boundaries catalog reference-properties --source-id delgado_aguilar_2020_pla_pcl --quantity youngs_modulus --text --lang zh
```

使用时保留研究、配方和注塑状态限定。即使标称配比相同，也不能将这些值自动赋给另一个
供应商、牌号、加工方法或试验温度下的材料。
详见[原有 PLA/PCL 证据与条件说明](MATERIAL_GROWTH_DELGADO_PLA_PCL_20261026.md#source-and-measurement-scope)。

## 反应型 PBS/木质素：拉伸重复数与生产批次数分开

来源标识：`ewurum_mcdonald_2025_pbs_lignin`。
Ewurum 与 McDonald（2025）的 Table 6 记录以下 R 系列模量。
该来源已被多个目录条目复用；同一个来源 ID 下的 B 系列物理共混物、原料及 R 系列
记录不是同一个材料状态。本节只整理 R10、R20、R30、R45 四项。

| 来源配方 | 标称木质素质量载量 | Young's modulus 均值，MPa | SD，MPa | 拉伸重复数 |
| --- | --- | ---: | ---: | ---: |
| R10 | 10 wt% | 751 | 40 | 10 |
| R20 | 20 wt% | 716 | 49 | 10 |
| R30 | 30 wt% | 910 | 85 | 10 |
| R45 | 45 wt% | 1256 | 162 | 10 |

木质素载量相对于总聚合物质量。10 次拉伸重复不等于 10 个已知独立生产批次。
来源报告添加 0.25 wt% DCP，但其质量分母、最终残留、最终化学组成和网络结构未解决；
不能据此补写最终交联密度。PBS 的 FZ91PM/FZ91PB 牌号记载存在未解决的不一致，
目录没有为成品创建牌号。

| 条件项目 | 目录已有内容 | 使用边界 |
| --- | --- | --- |
| 拉伸状态 | 注塑微型拉伸试样 | 不与热压试样混用 |
| 仪器与速度 | Instron 5500R-1132、Bluehill v3.3、Epsilon 3542 引伸计；1 mm/min | 不从横梁速度推断未报告的局部应变率 |
| 试验标准 | 来源参考文献 [32] 引用 ASTM D1708-18（2018） | 不从标准反推未报告的尺寸、调湿或拟合区间 |
| 制备路径 | 前驱物处理后，拉伸制备包括 140 °C 挤出与混合，再注塑 | 140 °C 是制备条件，不是已知拉伸温度 |
| 未知项 | 拉伸温度、压力、湿度、成型后调湿及模量拟合区间 | 不用其他试验的条件补齐 |

Table 1 的凝胶分数涉及另述的热压材料，不能转移为这些注塑拉伸试样的属性。
来源的许可记录为 CC BY 4.0。原有记录保留生产方留存 PDF 的检查及哈希；
独立来源审阅没有重新核验当前原始 PDF 字节，本页也没有重复该核验。

精确查看 R10，避免把同源的其他配方混入：

```sh
python -m materials_boundaries catalog reference-properties --material-id state_ewurum2025_pbs_lignin_r10_injection_molded --source-id ewurum_mcdonald_2025_pbs_lignin --quantity youngs_modulus --text --lang zh
```

详见[反应型 PBS/木质素的原有条件与证据说明](MATERIAL_GROWTH_EWURUM_REACTIVE_20261025.md#source-and-measurement-scope)。

## Curauá/RPUF：密度均值不能提供力学强度

来源标识：`czlonka_2021_curaua_rpuf`。
Członka 等（2021）的 Table 2 记录 curauá 纤维增强硬质聚氨酯泡沫的表观密度。
这里的基体是 RPUF；天然纤维的出现也不等于整个复合材料是天然材料类别。

| 标称漂白 curauá 载量，占总 RPUF 质量 | 表观密度均值，kg/m³ | 每组密度样本数 | 原文变异指标字面值 |
| --- | ---: | ---: | --- |
| 0.1 wt% | 38.4 | 10 | 0.4 |
| 0.5 wt% | 37.9 | 10 | 0.6 |
| 1 wt% | 37.6 | 10 | 0.4 |

原文将上标指标称为 coefficient of variance，但单位没有明确。
上表仅保留其字面值，不能补上百分号，也不能改写为 SD、置信区间或零不确定性；
目录的类型化不确定度仍为 `null`。统计分组 C/B/A 与不确定度是不同信息。

| 条件项目 | 目录已有内容 | 使用边界 |
| --- | --- | --- |
| 测量 | 第 3.2 节描述质量除以体积，引用 ISO 845；每组 10 个密度样本 | 不补写未确定的标准版本、样本独立性或其他试验样本数 |
| 固化背景 | 报告室内条件下固化 24 h；热学讨论另有至少 7 d 后固化 | 精确密度测量龄期未解决，不能任选一个时间作为密度测试时刻 |
| 未知项 | 密度测量温度、压力、湿度及详细调理 | 不转移力学或热学试验条件 |
| 组成 | 标称纤维载量 | 不表示最终组成分析或验证过的固化网络化学计量 |

密度记录不提供拉伸强度、导热系数或工程许用值。不能仅凭论文标题给出数值化的生物基比例，
也不能用这些密度值直接排名三种配方的综合性能。

来源许可记录为 CC BY 4.0。原有证据记录了生产方对 PDF 的检查，以及独立候选审阅对
官方 XML 与事实关联的复核；独立 PDF 请求曾返回 HTTP 403，未独立确认 PDF 字节和页图。

```sh
python -m materials_boundaries catalog reference-properties --source-id czlonka_2021_curaua_rpuf --text --lang zh
```

详见[curauá 泡沫的原有来源限定](MATERIAL_GROWTH_CURAUA_20261025.md#source-qualifications-retained-in-product-records)。

## 三组材料共同的使用边界

引用时保留完整提交 SHA、状态与属性 ID、来源定位、单位和统计含义。
来源引用标准、软件校验通过和独立科学验证是不同状态。
三组参考属性均保持 `catalog_only`，没有自动成为计算器输入、普适材料界或工程许用值。
需要补充某个未知条件时，应先取得支持该项事实的来源证据，再按现有审阅流程更新，
不能根据常识、相近配方或另一项试验的条件填补。

本页各组数字是各自已有记录的整理，不是本轮接纳增量；材料数量与版本边界见
[交接入口](../HANDOFF.md)。历史集成说明保留当时的阶段状态，不应被当作 main 的实时发布状态。

## 计算来源参考密度：模型条件与适用范围

JARVIS 与 PolyOmics 的这类记录存放于 `reference-properties`，其证据类别为
`published_computational_reference`，判定基础为 `source_reports_calculation`。
`catalog predictions` 则查询另一个预测对象目录。先依据记录类型选入口，再阅读方法和来源。
命令需要包含相应来源记录及方法契约的工作目录或安装；检索得到记录并不等于完成接纳或发布。
源码提交号、包版本号、工作数据快照及验收决定应分别记录。

| 来源与固定版本 | 属性及方法字段 | 密度基础的含义 | 阅读时保留的未知项 |
| --- | --- | --- | --- |
| JARVIS-DFT，Figshare `10.6084/m9.figshare.6815699.v11` | `mass_density`；`source_reported_computational_structure_density` | `crystallographic` 描述基于结构胞的质量/体积约定；证据仍为计算来源 | 每条模型的实际生成程序版本、收敛、稳定性、实验存在性及温压条件 |
| PolyOmics，Hugging Face 固定提交 `cbab9483395a32dd968fbeb047808031fb0f3a13` | `mass_density`；`source_reported_molecular_simulation_density` | `simulation_cell` 指分子模拟周期盒 | 实际 CSV 聚合口径、采样/导出窗口、真实生成程序与引擎版本、逐条轨迹条件及误差 |

JARVIS 的 `crystallographic` 基础字段本身不证明衍射实测或实验晶相。
目录保留来源报告的 OptB88vdW 优化结构密度，没有据结构重新计算数值。
所选模型和组成范围按固定规则限定；代表模型的选择不建立最低能量相或稳定相结论。
`metal` 作为组成分类时也不能单独证明金属电子行为。

PolyOmics 的身份遵从所选有限连接图范围。UUID 定位模型状态，链/分子输入数保持为模型输入，
不能改作独立试样数、牌号或生产批号。记录中的输入字面值与论文处方只能支持各自陈述，
不补齐逐条实际轨迹条件；空白引擎版本也不能用软件默认值代替。
未指定的立构、跨来源化学等价、商业产品或实验存在性仍受原有范围限制。

两类记录的 `reported_value` 保留来源标量；`summary_statistic=reported_value` 不等于已核实均值。
`sample_count.value=null` 和缺失不确定度都不表示零误差或某个默认样本数。
引用 g/cm³ 单位时应保留相应固定方法/文档的证据定位，不把方法证据写成每个 CSV 单元格自带的单位声明。
同一单位也不提供不同模型、密度基础、温压、统计口径之间的可比性保证。

PolyOmics 的固定论文写出质量除以时间平均体积 `m / mean(V)`，所检查代码使用瞬时密度的时间平均
`mean(m/V)`；两者一般不能直接视为相同估计量。本项目保留源标量，不据此改算密度、误差或平均窗口。
论文目标条件、代码处方和源记录输入不替代实际轨迹；输入处方版本与所检查发布代码不同的情况也继续保留。
数据集年份未知时，不从版权年份、修订日期或论文年份补写。

先精确查看一个 JARVIS 状态：

```sh
python -m materials_boundaries catalog reference-properties --source-id jarvis_dft_figshare_v11_2025_3d --material-id state_jarvis_v11_jvasp_10073 --evidence-kind published_computational_reference --quantity mass_density --text --lang zh
```

再查看一个 PolyOmics 模型状态：

```sh
python -m materials_boundaries catalog reference-properties --source-id polyomics_hf_7475_pfas_cbab9483395a --material-id state_polyomics_005f1275_8238_4e0b_a43c_e55fc933d46e --evidence-kind published_computational_reference --quantity mass_density --text --lang zh
```

保留输出中的来源定位、固定版本、原始字符串、密度基础、方法、差异说明和未知条件。
这些数值仍为 `catalog_only`，不会自动成为复合材料计算器输入、工程许用值或普适材料界。
来源转录核对、软件检查和独立科学同行评审分别记载，不能相互升级。

来源归属：JARVIS-DFT 为 Kamal Choudhary 的固定
[Figshare v11 数据](https://doi.org/10.6084/m9.figshare.6815699.v11)；PolyOmics 为 RadonPy Consortium 的固定
[数据记录](https://doi.org/10.57967/hf/7475)。两者的数据许可按各自固定记录保留
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 归属和修改说明；数据许可不自动覆盖软件及上游资产。
上述说明整理已检查的字段与限定，不重新获取原文、不重分析轨迹，也不替代各自的最终接纳决定。


## SCC 鲜态配方的流动扩展度

固定来源为 SAFHI, Amine el Mahdi 的 Zenodo 10569517 version1 数据（DOI 10.5281/zenodo.10569517），数据元数据标记 CC BY 4.0。2024-01-27 是数据集公开日期，不是逐条实验日期；原论文完整引文保留，但本项目没有重新核验每篇原实验。数据许可与汇编方法论文 DOI 10.1016/j.dib.2024.110256 的许可分别处理。

参考属性 `slump_flow_spread` 的量纲为长度，本批单位为 mm，表示来源明确报告的鲜态 slump-flow spread。它不是坍落高度、J-Ring 扩展度、压缩强度、黏度或密度，也不证明配方符合某项 SCC 标准。记录采用文献汇编证据 `published_handbook_reference`、`source_reports_compiled_measurements`、`source_reported_compilation`；不表示汇编者进行了新实验。

测试标准、具体几何/直径聚合口径、温度、加载条件、独立试样 n、均值与误差仍按记录保留未知。不能由配料用量推算硬化后密度或最终化学组成，也不能把来源行数当重复试验数。

CSV 配料字面量和原工作簿存值分别保留，差异列入 `source_discrepancies`，完整双视图列在 `original_ingredient_dual_views`。不自行决定哪份正确，不平均、归一化或把储存位数当测量精度。可选成分空白为未知，不能当零。

材料身份是明确限定的来源名义配方代表。保守双视图风险分组、156 条来源行暂缓选择和代表选择属于本项目策展；完整信息在 `scope_note` 的 Project curation selection metadata 段，不是原作者报告的测试条件。被暂缓行仍参与重复风险连通；分组可能合并不同配方，不证明组内化学等价。配方代码、流动值或来源行本身不增加材料身份。候选、隔离目录、最终接纳与发布仍须区分。

只读取一个具备真实差异的示例状态：

```sh
python -m materials_boundaries catalog reference-properties --source-id scc_zenodo_10569517_v1 --material-id state_scc10569517_04cd95308a290a9191e0e255_reported_fresh --quantity slump_flow_spread --text --lang zh
```

该例的流动值 CSV 字面量为 `720 mm`，原工作簿存值为 `719.86699999999996`；两者并列保留，不作为两次试验或误差范围。使用时同时读取原引文、配料差异、未知条件及适用范围。

## Sylgard 184 固化条件与拉伸模量

Johnston等（2014，DOI 10.1088/0960-1317/24/3/035017）的Sylgard 184结果属于同一商业材料的不同固化状态。来源按10:1份混合，未据此推断质量比。新增的25、125、150、200°C固化状态与已有100°C状态共用材料身份；固化温度不是力学测试温度。

拉伸试样的固化时长分别为25°C/48h、100°C/48min、125°C/33min、150°C/23min、200°C/18min；高温组包含原文热传播修正。不能套用压缩试样的另一组时长。原文报告拉伸测试平均环境约21°C、39%RH，并未给出这些条件为设定点或调湿程序；冷却和固化后测试时间按各状态条件保留。

Table 2的Young’s modulus分别为1.32±0.07、2.05±0.12、2.46±0.16、2.59±0.08、2.97±0.04 MPa，每组6个拉伸试样。原文称误差为95%置信区间，但区间估计对象、构造方法及拟合/平均顺序未说明；保留报告值，不将其改写为逐试样模量的算术均值或标准差。

原文已作几何修正，使用时不能重复乘以0.40。线性区描述为应变小于40%，精确下端与拟合算法未知；这些结果不是任意温度、老化状态或大变形条件下的通用常数。强度、压缩模量及由假定泊松比推导的模量未随本批接纳。

```sh
python -m materials_boundaries.database query --source johnston_2014_bulk_sylgard184 --quantity youngs_modulus
```

本批保留来源的CC BY3.0署名要求，仅整理事实与条件，不打包原文资产。审核与本地应用入口见[聚合物探索记录](../experimental/polymer-exploration/20261103/README.zh.md)。来源转录独审及软件契约通过，不等于独立科学同行评审或工程许用值认证。

## 2026-11-03：丝材方法文本补查（更正已独审并本地应用）

Aniskevich／Bulderberga（2023，固定数据DOI 10.5281/zenodo.8089569）工作簿的`Samples`绘图文本框还包含参考丝材方法，早期单元格提取没有覆盖。文本写明ZWICK 2.5、初始夹头间距100mm、以夹头间距变化计算应变，以及0.05–0.25%的模量拟合区间；具体拟合算法与端点处理未知。

参考丝材方法段写1mm/min，实测列E5/G5表头写10mm/min，两者冲突。原生22条记录现将实际逐行速率标为not_verified、text=null，保留两处定位和原值。不能据此开展已确认同速率的材料排名、速率换算或跨研究比较。

参考丝材与细挤出纤维、狗骨试样分别读取；不能引入狗骨的夹式引伸计、预载或标准几何。温湿度、调湿／干燥、确切逐行n和avedev统计定义仍未知。详见[原冻结候选](../experimental/polymer-exploration/20261103/filament-drawing-method-audit/README.zh.md)及[本地接纳记录](../experimental/polymer-exploration/20261103/local-acceptance-r4/README.zh.md)。原候选中的待审文字保留历史阶段，最终状态由后续具名审阅和应用收据证明。

## PA12老化研究：原染色参考组及本轮补充

Zakręcki／Cieślik（2025，DOI 10.3390/ma18194478）原已收录的PA2200强度记录属于SLS染色未加速老化参考组。43.72MPa均值、1.03MPa标准差和n=6与同指纹原文XML一致，本轮不更改该对象。“Reference”不等于未后处理、无染色或已调湿；具体含水率、调湿／干燥、保存与恢复时间仍未知。

正文报告的38°C空气温度、55°C黑标温度和50%RH照射阶段属于加速暴露程序，不是该参考组的拉伸测试环境。23°C仅为老化换算输入，不能补作未知的拉伸测试温度。作者以375／750小时腔体暴露对应约6／12个月，不构成本项目验证的自然服役寿命或临床耐久性。

本轮另接纳同一身份下5状态、8项性质；原文不同位置的后处理顺序／名称差异与CV矛盾保留，不统一为已确认的精确执行顺序，不据CV重新计算SD。未选择的其他条目仍暂缓，不以本次有限接纳认证整来源。详细复查见[PA12老化来源审计](../experimental/polymer-exploration/20261103/pa12-ageing-source-audit/README.zh.md)。

## 2026-11-03：PBS、打印聚合物与PUR的有限补充

PBS已有9个状态补充9项拉伸强度，保留作者均值±SD、每组10个拉伸试样及未知生产批次数。新R系列强度仅写ASTM D1708和参考文献年份2018，确切版本未知；不把DCP/PBS预处理干燥填作成型后调湿。R0身份仍暂缓，凝胶分数“—”不填为零。

Şahin的5个既有打印状态补充s_M拉伸强度，不混用s_B断裂应力。拉伸测试23°C、横梁5.0mm/min、n=5、SD明确；打印前丝材干燥与打印后未知调湿分开，100%切片填充不等于零孔隙率。

PUR仅更新来源说明以涵盖已收录LPO-1、LPO-2、SPO-2、SPO-3；4条表观密度不变。24h室温固化不填作密度测试温度，压缩试样数、目标密度和标准化密度不移给密度结果。

以上为本地已独审数据，接纳和软件核验见[r4收据](../experimental/polymer-exploration/20261103/local-acceptance-r4/README.zh.md)。PA12风化仅审计来源，NR有限应变模量仍未接纳；NBR等未确认的温湿度、调湿或±定义继续未知。
