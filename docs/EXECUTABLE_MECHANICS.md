# 可执行力学知识库 / Executable mechanics

v0.36.0 新增两个可执行模型，独立于原有 41 条历史知识记录及 8 条复合材料界限规则。
运行 `materials-mechanics knowledge` 可取得机器可读公式、来源与适用条件；条目位于
`materials_boundaries/data/mechanics_models.json`，随安装包分发。

## 弹性常数换算

输入 E、ν 或 K、G 一组，输出 E、ν、K、G、λ。所有模量共用单位 Pa、MPa 或 GPa。

K = E / [3(1−2ν)]；G = E / [2(1+ν)]；
E = 9KG / (3K+G)；ν = (3K−2G) / [2(3K+G)]；λ = K−2G/3。

适用三维稳定各向同性线弹性：E>0 且 −1<ν<0.5，等价于 K>0、G>0。
允许负泊松比；不能将单晶方向模量、不同温度或不同试样的性质任意配对。
来源：[Itasca isotropic elastic model，式 (2)、(4)、(5)](https://docs.itascasoftware.com/itasca900/common/models/elastic/doc/modelelastic.html)。

## 三维应力、刚度与能量

σij = 2G εij + λ tr(ε) δij。应变从无应力参考态计，W = ½ σ:ε。
输入顺序为 xx, yy, zz, yz, xz, xy；后三项是工程剪应变 γij=2εij，
相应剪应力 τij=Gγij。输出矩阵使用同一顺序。应变无量纲，应力单位与模量一致。
能量密度：1 Pa=1 J/m³，1 MPa=10⁶ J/m³，1 GPa=10⁹ J/m³。

来源：[Itasca 式 (1)–(3)](https://docs.itascasoftware.com/itasca900/common/models/elastic/doc/modelelastic.html)，
对照 [INL MOOSE 各向同性刚度张量](https://mooseframework.inl.gov/source/materials/ComputeIsotropicElasticityTensor.html)。
能量表达式由线弹性应力沿加载路径积分得到。

`--assume-isotropic` 是用户对稳定、小应变、各向同性线弹性的断言，不是试样认证。
不会扣除热应变或残余应力。大应变输入可能给出数学结果，但超出物理适用范围。
拒绝 NaN、无穷大、奇异泊松比及无法用有限浮点数表示的输入/结果。
中间运算使用 50 位 Decimal，输出为浮点近似；不是区间包络或不确定度传播。

```sh
python -m materials_boundaries.mechanics convert --young 210 --poisson .3 --assume-isotropic
python -m materials_boundaries.mechanics stress --bulk 100 --shear 40 --assume-isotropic --strain .001 .001 .001 0 0 0
```

第二例为教学用静水应变，各向正应力均为 0.3 GPa。纯工程剪应变 γxy=0.01 时，
G=40 GPa 给出 τxy=0.4 GPa、W=0.002 GPa。
验证涵盖双向换算、负泊松比、静水/纯剪/单轴状态、单位缩放与非法输入拦截。
这是公式核对和软件验证，尚未获得独立科学同行评审。
