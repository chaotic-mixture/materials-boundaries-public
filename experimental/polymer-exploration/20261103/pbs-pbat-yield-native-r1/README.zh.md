# 既有 PBAT / PBS-PBAT 屈服强度补充 r1

本包仅为冻结候选，尚未原生接纳或推送。来源及契约提案已独审；本次实现和映射需另行独审。

从 Mtibe 2022 原文 Table 3 的 Tensile Strength at Yield (MPa) 列录入两条既有状态：PBAT 8.38±0.11 MPa，未填充 PBS-PBAT (70/30) 26.99±0.32 MPa。与同一行既有模量逐值交叉核验，不扩充材料身份或状态，不录入三个复合材料行或新 PBS 身份。

§2.6.2 支持每组 5 个拉伸试样、25°C 测试及 25°C/48h 放置。RH、速率、标距尺寸、屈服判据/偏移量、独立生产批次及 ± 的统计定义未知。保留 reported_value / reported_plus_minus_unspecified，不声称均值、SD、SE、置信区间或标准符合性。

新增独立 tensile_yield_strength 压力量契约及四语言标签；未改写既有强度、模量或密度记录。保持 catalog_only、universal_bound=false、engineering_allowable=false，不接入力学计算。

审核入口 REVIEW_INPUTS_R1.json，绑定实现文件、测试结果、候选和完整外部三表。审阅仅可只读检查，不执行本包生产者脚本、不修改文件、不推送、不运行完整历史回归。
