# 材料边界 · Materials Boundaries

Current software release: **v0.37.0**

**查材料数据，读适用条件，运行可追溯的力学计算。**
An open, source-qualified materials database and executable mechanics toolkit.

[下载与版本说明](https://github.com/chaotic-mixture/materials-boundaries-public/releases/tag/v0.37.0) · [数据格式](docs/DATABASE_FORMAT.md) · [计算与知识库](docs/EXECUTABLE_MECHANICS.md) · [贡献数据](docs/DATABASE_CONTRIBUTING.zh.md)

## 单轴拉伸专家系统 · 三个可复现案例

安装下方 wheel 后运行。轴向应变 0.001 即 0.1%。每次输出的 `current` 是当前判断，包含选定记录、材料状态、来源页码、输入、边界条件和实际采用的规则。

| 案例 | 命令 | 当前判断 |
| --- | --- | --- |
| 正常计算 | `materials-tension --strain .001 --assume-model` | 退火 Nickel 200，侧向自由，205 GPa × 0.001 = **0.205 GPa** |
| 缺少模量 | `materials-tension --record refprop_aurubis_c11000_mass_density --strain .001 --assume-model` | 选中的 C11000 记录提供密度，提示补充适用的杨氏模量 |
| 改变约束 | `materials-tension --strain .001 --assume-model --then fixed` | 同一材料改为两个侧向应变均为零，原结果进入历史；当前提示补充同状态泊松比 |

第三例可追加 `--poisson .3`，得到约 **0.276 GPa**。这里的 0.3 是用户提供的教学假设。默认模量来自 [Special Metals Nickel 200 技术公报，表 4](https://www.specialmetals.com/documents/technical-bulletins/nickel-200.pdf) 的 26 °C 退火材料动态弹性数据。将该参考值用于此拉伸估算需要用户明确接受其适用性，并假定无初始应力、无热应变、各向同性和小应变线弹性。输出不提供屈服、失效或工程许用值。

## 材料方向 / Material families

| 方向 | 材料身份数 | 收录示例 |
| --- | ---: | --- |
| 聚合物（`polymer`） | 1,037 | PLA、ABS、PETG、ASA 打印丝材 |
| 金属（`metal`） | 1,037 | C11000 铜、6061 铝合金、Nickel 200 纯镍 |
| 无机材料（`inorganic`） | 1,059 | 硼硅玻璃、熔融石英、氧化铝陶瓷、人造石墨 |
| 复合材料（`composite`） | 1,037 | 混凝土、炭黑填充 EPDM 橡胶、PBS／木质素共混材料 |
| 天然材料（`natural`） | 1,010 | 糖枫木、西加云杉木、亚麻纤维束、大麻纤维束 |

共 5,180 个按来源区分的材料身份。可用 `materials-database summary --category polymer` 查看聚合物概况，将 `polymer` 换成表中其他分类即可切换方向。可计算的性质取决于具体材料状态及其数据。

## 现在有什么 / What's available

| 内容 | v0.36.0 |
| --- | --- |
| 材料身份 | 5,180，按来源限定；别名与多个测量不重复计数 |
| 材料状态 / 性质记录 | 5,262 / 5,412 |
| 数据库操作 | 搜索、分类与证据概览、JSONL 导出、快照校验、版本差异与增量验证 |
| 原有复合材料计算 | 8 条 HS / Reuss / Voigt 及派生外包络规则 |
| **新增可执行模型** | **弹性常数换算；三维各向同性应力—应变、刚度矩阵与应变能** |
| 知识库 | 41 条历史力学条目，加 2 个带公式、来源、条件和限制的可执行模型条目 |

计算来源的性质与实验参考值分开标记。记录数不等于独立实验数，也不等于所有材料都有完整性质。

## 1. 安装 / Install

Python 3.10+，无第三方运行时依赖。安装本仓库发布的 wheel（不是 PyPI 上的同名包）：

```sh
python -m pip install "https://github.com/chaotic-mixture/materials-boundaries-public/releases/download/v0.37.0/materials_boundaries-0.37.0-py3-none-any.whl"
```

或克隆后在仓库根目录运行 `python -m pip install .`。

## 2. 查一个真实材料 / Query a real material

```sh
materials-database query --query C11000 --quantity mass_density
materials-database summary --category polymer
materials-database export --query C11000 --quantity mass_density --output copper-snapshot
materials-database verify --snapshot copper-snapshot
```

例：Aurubis C11000 铜的来源参考密度为 **8.9 g/cm³**；该值的温度、样本数和数值不确定度未报告。输出保留原始单位、来源链接、页码位置和条件，不把未知补成默认值。发布附件 `materials-database-v0.36.0.zip` 提供原生三表、schema 和字段说明，无需安装即可下载数据。

## 3. 直接计算 / Calculate

下面是教学输入，不代表特定钢种的实测值：

```sh
materials-mechanics convert --young 210 --poisson 0.3 --unit GPa --assume-isotropic
materials-mechanics stress --young 210 --poisson 0.3 --unit GPa --assume-isotropic --strain 0.001 -0.0003 -0.0003 0 0 0
materials-mechanics knowledge
```

第一条得到 **K = 175 GPa、G ≈ 80.769 GPa**。第二条在明确假设下得到 **σxx ≈ 0.210 GPa、其余分量约为 0**，同时返回 6×6 刚度矩阵和应变能。可用 `python -m materials_boundaries mechanics ...` 执行同样操作。

新模型要求三维、各向同性、小应变、稳定线弹性，并由用户明确确认；不预测屈服、断裂、塑性或大变形。已有复合材料界限计算仍可通过 `materials-boundaries composite` 使用。详见[计算说明与科学来源](docs/EXECUTABLE_MECHANICS.md)。

## 数据、知识与发布

- [数据库字段与快照](docs/DATABASE_FORMAT.md)：身份、状态、性质、证据、未知条件与来源许可。
- [v0.36.0 更新](docs/RELEASE_v0.36.0.md)：相对公开 v0.35.0 的变化与验证范围。
- [贡献流程](docs/DATABASE_CONTRIBUTING.zh.md)：候选、来源审核、发布；软件测试通过不等于科学审核。
- [开发验证](docs/DATABASE_CI.md)：日常数据检查与历史回放分开。
- [历史开发记录](HISTORY_PRE_V036.md)：旧数量与暂停指令不是当前发布状态。

代码使用 [MIT](LICENSE)。外部来源的许可与收录范围见各来源记录及 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)，不因代码开源而自动重新许可。数据和计算结果不自动构成工程许用值。
