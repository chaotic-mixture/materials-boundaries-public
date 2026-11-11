# 当前聚合物条件缺口：只读清单

对应已本地接纳r58，基准提交3880c8ad4c83d8a3c4decf71e130e021b91a8c0d（r58原生更改尚未提交推送）、快照57ba9d57750b80f8dfdeda4e67d1f89ba048c04d6992d510d814e37b3f523ee9，原生三表字节与最终本地独审绑定一致。仅描述目录polymer类别的316条非计算性质（311实验来源参考、5来源派生参考），排除1000条计算性质；类别不证明化学纯度，复合材料不改计聚合物。

| 主来源 | 性质 | 温度明确未报 | 调湿明确未报 | n数值为空 | 确切n未确认 |
| --- | ---: | ---: | ---: | ---: | ---: |
| aniskevich_bulderberga_2023_polymer_mechanical_characterisation | 85 | 85 | 85 | 77 | 77 |
| ivdre_2024_lpo_rigid_pur | 44 | 8 | 36 | 44 | 44 |
| tarasov_2022_pna_bpf_epoxy | 40 | 35 | 40 | 40 | 40 |
| delgado_aguilar_2020_pla_pcl | 25 | 25 | 25 | 25 | 25 |
| johnston_2014_bulk_sylgard184 | 30 | 5 | 0 | 10 | 10 |
| abbasi_2022_manure_phbv | 10 | 3 | 6 | 6 | 10 |
| bianchi_2025_nr_nanoclay | 14 | 7 | 14 | 7 | 7 |
| ewurum_mcdonald_2025_pbs_lignin | 10 | 8 | 10 | 6 | 6 |
| tamas_benyei_santha_2025_nbr_rcf | 6 | 6 | 6 | 6 | 6 |
| mtibe_2022_pbs_pbat_lignin_zno | 9 | 3 | 3 | 3 | 3 |
| sahin_2026_polymer_mechanical_dielectric | 30 | 5 | 30 | 0 | 0 |
| zakrecki_cieslik_2025_pa12_ageing | 13 | 13 | 0 | 0 | 0 |

来源报告确切n共88条；n数值为空224条；确切n未确认共228条。下限等非exact关系不改成恰好该值，也不当零样本。按性质计数，多项性质可能共享方法组，不能累加为独立试样/批次。

机器清单逐条保留完整条件、附加条件、样本数关系及范围说明。reported调湿可能只包含时间/加工背景，不证明RH完整或平衡完成；未单列某字段不等于已核实原文没有该条件，不计算完整率或科学评分。

r58新增4条PUR水吸收体积百分数，reported_value、n未知、±含义未知；体积基准、水温/纯度、预干燥、表面水处理、方向与浸没关系未知。四天浸水及名义几何已报告，室温固化24h不证明湿度平衡。旧r9的312条条目完整保持。本清单只描述目录，不改变原生事实，不构成新的来源独审、测试或科学认证。本批未提交推送，无本批远端CI，不合并main、不发布、不部署。
