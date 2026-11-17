# Luo 等（2023）LPBF Ti-6Al-4V 过程—组织—力学数据筛查

日期：2026-11-17  
状态：官方仓储元数据和论文方法筛查；未下载二进制工作簿或复算逐曲线性质，未接纳到原生目录。

## 来源和范围

Qixiang Luo, Lu Yin, Timothy W. Simpson, Allison M. Beese, “Dataset of process-structure-property feature relationship for laser powder bed fusion additive manufactured Ti-6Al-4V material,” *Data in Brief* 46 (2023), 108911, DOI [10.1016/j.dib.2023.108911](https://doi.org/10.1016/j.dib.2023.108911)。配套 [Zenodo 记录 6587905](https://zenodo.org/records/6587905)，记录页版本标签为 2023-10-16 更新。

论文报告 42 个不同激光功率—扫描速度参数组；使用 3D Systems ProX DMP 320 激光粉末床熔融制备 Ti-6Al-4V，随后在 670°C 应力消除 5 h，并于氩气炉中冷却 12 h。每个参数组制作两种平板与两种圆棒 ASTM E8/E8M 拉伸试样；数据仓储称 `stress-strain curves.zip` 包含 168 条工程应力—应变曲线，按四种试样组分成四个 Excel 工作簿。论文报告拉伸应变率为 3×10⁻⁴ s⁻¹，使用 10 kN 载荷框架和 DIC/24 mm 轴向引伸计。除曲线外，数据集还列出 42 组的处理参数、孔隙/先前 β 晶粒/表面粗糙度特征、屈服/抗拉/延伸和硬度等性质。

## 可复核元数据与现状

官方记录公开了全部文件名、大小和 MD5；`stress-strain curves.zip` 为 4.2 MB、MD5 `5c044051d1954a9273030f0ebcbec433`。其 Zenodo 预览已读取到四个内含工作簿及各自大小：`flat set 1.xlsx` 887.3 kB、`flat set 2.xlsx` 837.2 kB、`round set 1.xlsx` 1.5 MB、`round set 2.xlsx` 969.8 kB。完整仓储文件清单及哈希记录在 [Zenodo 文件清单 CSV](zenodo_file_manifest.csv)。预览确认归档分组结构，但未暴露工作簿内数据格，下载链接返回二进制，当前读取工具无法解析；本地也未下载或校验 MD5。

记录正文称总共含 7 个文件，但 Files 表实际列出 8 个文件（包含后续添加的应力—应变 ZIP 和显微图像 PPTX）；这是说明文本未同步更新的元数据差异。Files 表列出 `Ti64_OM_summary.pptx` 为 4.5 GB，且文件区汇总也显示 4.5 GB。页面后续的 14.8 TB 是累计数据传输量统计，不是文件包体积。

Zenodo 记录 Rights 下的 License 标签没有显示许可值，不能据此断言仓储内所有原始工作簿可再分发。论文全文页面标示 CC BY 4.0；这支持按许可引用论文事实/表格，不自动填补仓储归档自身空白许可。当前仅记录公开的元数据、方法和来源链接，不复制曲线或工作簿内容。

## 科学与建模边界

- 同一处理参数组仍是特定构建批次和试样几何的观测，不是“所有 Ti-6Al-4V”的代表；此数据仅为指定设备、LPBF 参数族和应力消除热处理链。
- 两种平板与两种圆棒几何分别提供曲线。即使论文的汇总表将处理参数组性质概括为均值/标准差，力学统计仍需核对每种几何的重复数、具体汇总方式与属性字段，不能把几何差异隐藏在一个平均值中。
- 摘要性统计与 168 条原始曲线是不同证据层；未逐工作簿核对单位、应变测量、失效终点、重复关系前，不转录屈服、弹性模量或极限强度。
- 密度/孔隙、微观组织与力学性质属于同一研究过程—结构—性质框架，但各项测量样本是否同件、是否严格一一配对，需依相应 workbook/方法核对，不能预先断言配对。

## 下一步

如能在可解析二进制的环境取得 Zenodo 文件，先核对 `stress-strain curves.zip` MD5 并逐工作簿抽查表头、应力/应变单位、处理参数集和重复编号；然后把平板、圆棒数据与属性表分层对齐，再考虑为具体构建状态建立候选。还需查明 Zenodo 原始文件许可证字段，并按工作簿中的几何、参数组核对摘要力学值的汇总规则。来源：[Zenodo 6587905](https://zenodo.org/records/6587905)、[PMC 论文全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9880387/)、[PubMed 书目信息](https://pubmed.ncbi.nlm.nih.gov/36710913/)。

