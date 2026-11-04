# Materials Boundaries development handoff

## 当前聚合物进展：r36–r38

以[最新本地接手入口](experimental/polymer-exploration/20261104/delivery-r36-r38/README.zh.md)的当前数量、来源/条件边界和精确验收回执为准。当前全库5412条性质、5262个状态；本轮累计新增32条性质、8个状态。安装与CI范围以交付入口的精确回执为准，未知项不补默认值。本轮不合并main、不稳定发布、不部署。以下各历史检查点仅代表各自冻结范围。


## r29–r32聚合物累计交付核验（2026-11-04）

当前全库5180身份、31牌号、5245目录状态记录、5371性质、133来源。四轮已独审本地接纳：既有PBS配方补36条性质和27目录状态，PLA/PCL来源补PDF检查范围及链接；原5335性质、5218状态对象完整保持，无新身份／牌号／来源。目录情境不认证独立物理覆盖。

聚合物1037身份、1078状态记录、1180性质（1000计算／180实验参考标签）。113条实验性质温度未报、128条调湿未报，111条确切n未确认；来源未支持的条件继续未知。弯曲两项性质共享来源n=8组，不计16次独立实验；DMA、DSC及弯曲方法不混同。

[统一交付证据](experimental/polymer-exploration/20261104/delivery-r29-r32/README.zh.md)记录当前测试、实际安装、目录读取和后续提交／CI各自范围；缺少精确回执不视为通过。重建安装包及统一验收以本轮精确回执为准，缺少回执不视为完成；不冒用r31旧包作为当前三表等价证据。软件版本仍0.35.0。仅实验分支交付，不合并main、不稳定发布、不部署。以下保留旧检查点原文。


## 当前本地检查点：PLA/PCL来源更新 r32（2026-11-04）

一个既有来源补充已独审PDF核验范围及官方链接，25条性质的未知条件保持；全库仍为5180身份、5245目录状态、5371性质。接纳后19项数据库检查通过。当前来源更新尚未重新打包，r31安装包只代表其原冻结范围。详见[当前本地证据](experimental/polymer-exploration/20261104/local-acceptance-r32/FINAL_LOCAL_STATUS_R32.zh.md)。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署。

以下保留旧检查点，旧计数、安装和CI仅适用于各自冻结范围。


## 当前本地检查点：PBS弯曲性质 r31（2026-11-04）

以[当前本地接纳与核验入口](experimental/polymer-exploration/20261104/local-acceptance-r31/FINAL_LOCAL_STATUS_R31.zh.md)为准：全库5180身份、5245状态记录、5371性质。9个既有配方补18条弯曲均值／SD及9个来源限定试验上下文，物理形态和与既有试样关联未知，不认证新增独立物理覆盖。5353旧性质、5236旧状态完整保持；两项性质共享来源n=8组，其他未报告条件不补造。聚合物1037身份、1078状态记录、1180性质（1000计算／180实验参考标签）。

真实隔离安装、进程内查询及22项新接纳后检查通过；不累计旧运行，完整历史、HTTP及平台全量未运行。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署，继续本地积累后统一交付。

以下保留先前检查点原文，旧计数、快照和CI仅适用于各自冻结范围。


## 当前本地检查点：PBS DMA Tg r30（2026-11-04）

以[当前本地接纳与核验入口](experimental/polymer-exploration/20261104/local-acceptance-r30/FINAL_LOCAL_STATUS_R30.zh.md)为准：全库5180身份、5236状态、5353性质；9个既有配方新增9条DMA tanδ峰Tg及9个物理条形状态（1聚合物、8聚合物基复合配方），无新身份。5344旧性质、5227旧状态完整保持；三次共同重复保留，选定n和统计未知。聚合物1037身份、1077状态、1178性质（1000计算／178实验参考标签），不作方法可比性或科学认证。

实际隔离安装、进程内查询及22项新接纳后检查通过（19数据库＋3方法保真）。不累计旧19／3／180项；完整历史、HTTP及平台全量未运行。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署，继续本地积累后统一交付。

以下保留先前检查点原文，旧计数、快照和CI仅适用于各自冻结范围。


## 当前本地检查点：PBS DSC r29（2026-11-04）

以[当前本地接纳与核验入口](experimental/polymer-exploration/20261104/local-acceptance-r29/FINAL_LOCAL_STATUS_R29.zh.md)为准：全库5180身份、5227状态、5344性质；既有9配方补9条熔融温度和9个独立DSC状态（1聚合物、8聚合物基复合配方），无新身份。5335旧性质、5218旧状态完整保持，来源差异和未知项不补造。聚合物1037身份、1076状态、1177性质（1000计算／177实验参考标签），不作科学认证。

实际隔离安装、进程内辅助查询及本批19项数据库行为检查通过。先前180项不计作本批重跑；完整历史、HTTP及平台全量未运行。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署，继续本地积累后统一交付。

以下保留先前检查点原文，旧计数、快照和CI仅适用于各自冻结范围。


## r26-r28聚合物统一实验交付（2026-11-04）

当前[交付与核验入口](experimental/polymer-exploration/20261104/delivery-r26-r28/README.zh.md)汇总三轮既有材料热性质补充：5条环氧Tg、1条PHBV-39 Tg和2条同DSC状态熔融峰，共8性质、6状态，无新身份／牌号／来源。全部5327前驱性质和5212前驱状态完整保持，2来源仅追加说明。

当前全库5180身份、31牌号、5218状态、5335性质、133来源；聚合物1037身份、1075状态、1176性质，1000计算和176实验参考只是证据标签。双峰各自ID／标签／列证据保留，不合并温区或平均、不认定两个独立实验。环氧174.5／174.7及错表号、PHBV旧结果／重分析单格归属继续未知，duplicate仅共同方法，选定n／分散度未知。

176实验性质中111条温度字段、124条调湿字段未报告；67确切n、105个n为空、4个仅下限，确切n未确认109条。按性质计数，不作独立试验组；扫描程序不等于环境温度，reported不证明湿度平衡完整。未核实内容不补默认值，不作科学／标准认证、工程允许值、使用温度或引擎输入。

各批已独审；统一当前测试、实际安装、目录读取及提交／推送／CI以精确收据为准，不累加历史测试或冒用旧提交CI。完整历史回归、HTTP和平台全量未运行。不合并main、不稳定发布、不部署。以下历史原文保留。


## r28 本地积累（2026-11-04，尚未提交／推送）

同一既有PHBV-39 DSC状态新增Tm1=159.7°C、Tm2=170.1°C两个熔融峰性质，各自标签／ID／列证据保留，不当温区或两个独立实验。旧5333性质及其余5217状态完整保持，原DSC状态仅改版本／追加性质ID／范围。当前5335性质／5218状态；本轮180组合检查、实际安装、双峰2条与来源7条完整导出核验通过；早期虚构夹具3错误及修正记录保留。n、数值分散度、Guho／重分析单格归属仍未知。闭合温度规则仍五分支，不扩大旧量数域。当前证据与最终独审见[本地接纳入口](experimental/polymer-exploration/20261104/local-acceptance-r28/FINAL_LOCAL_STATUS_R28.zh.md)。继续本地积累后统一推送，不合并main、不部署；本批远端CI未运行。下文为历史阶段。


## r27 本地积累（2026-11-04，尚未提交／推送）

既有PHBV-39新增Table4 DSC Tg −5.3°C及1个独立DSC状态，全部5332旧性质／5217旧状态完整保持。第二次升温和拐点判据有来源支持；旧研究／重分析的单格归属未知，共同duplicate不当选定n。当前5333性质／5218状态；新增数据图、真实隔离安装、Tg单来源1条／全库6条与来源5条完整导出核验通过。172组合结果沿用精确未变实现，本批未重跑。五条供应商Tg范围仍排除。当前证据及最终独审见[本地接纳入口](experimental/polymer-exploration/20261104/local-acceptance-r27/FINAL_LOCAL_STATUS_R27.zh.md)。继续本地积累后统一推送，不合并main、不部署；本批远端CI未运行。下文为历史阶段。


## r26 本地积累（2026-11-04，尚未提交／推送）

新增5条既有PNA-BPF的DSC Tg来源限定记录及5个独立状态，旧记录完整保持。摘要／表格差异、错误表号与未知判据、热历史、调湿、样本数随记录保留。当前5332性质／5217状态；172项本轮组合检查、真实隔离安装及40条来源完整导出通过。本批最终审阅状态及精确证据见[本地接纳入口](experimental/polymer-exploration/20261104/local-acceptance-r26/FINAL_LOCAL_STATUS_R26.zh.md)。继续本地积累后统一推送，不合并main、不部署。本批远端CI未运行；下文为历史交付，不代表本批发布。


## r23-r25聚合物统一实验交付（2026-11-04）

当前[交付与核验入口](experimental/polymer-exploration/20261104/delivery-r23-r25/README.zh.md)汇总3轮既有材料补充：1条NBR撕裂、5条环氧弯曲断裂伸长及5条Izod冲击性质，新增11性质、6试样状态，无新身份／牌号／来源。5316前驱性质完整保持；旧REF只修订版本／流变热处理背景／范围，5旧弯曲状态只修订版本／性质链接／范围，2来源追加说明。

当前全库5180身份、31牌号、5212状态、5327性质、133来源；聚合物1037身份、1069状态、1168性质，1000计算和168实验参考只是证据标签。流变381s不证明实际压机保持；Izod表4.1与摘要／图4.01未解决，缺口、冲击速度和面积算法未知；弯曲应变／断裂判据未知。原文差异不修，未知不补默认值，不作工程输入或科学认证。

168实验性质中111条测试温度、116条调湿字段未报告；67条确切n、97条n为空、4条仅下限，确切n未确认101条。按性质对象计数，不作独立试验组；reported不代表湿度平衡完整。硬度及既有NR／PA12／PLA-PCL暂缓项继续保留。

各批已独审；统一当前测试、安装、目录读取、提交／推送和远端CI以精确收据为准，不累加历史测试或冒用旧提交CI。完整历史回归、HTTP和平台全量未运行。不合并main、不稳定发布、不部署。下文历史原文保留。


## r25本地继续积累（2026-11-04，尚未提交／推送）

当前以[本地状态与精确验收入口](experimental/polymer-exploration/20261104/local-acceptance-r25/FINAL_LOCAL_STATUS_R25.zh.md)及对应独审回执为准。新增5条既有PNA-BPF的Table7 Izod来源限定性质和5个独立试样状态，5322旧性质／5207旧状态完整保持。4.1／4.01表图摘要差异及缺口、速度、面积归一化、破坏模式、统计和环境未知随记录保留，不修值或宣称实验值已确认。

修正新增测试夹具后，本轮整组164项重新执行通过；实际隔离安装、35条来源完整导出及原生三表等价通过，最终接纳读取精确独审回执。当前5327性质／5212状态；聚合物1037身份／1069状态／1168性质，1000计算及168实验标签不作科学认证。111条测试温度、116条调湿字段未报告，101条确切n未确认；按性质计数，不当独立试验组。

当前仅在本地累计r23-r25十一条性质，继续积累并准备统一交付核验，尚未提交／推送或跑本批远端CI。不合并main、不稳定发布、不部署；完整历史回归、HTTP和平台全量未运行。下文为历史阶段，不能作本批发布证明。


## r24本地继续积累（2026-11-04，尚未提交／推送）

当前以[本地状态与精确验收入口](experimental/polymer-exploration/20261104/local-acceptance-r24/FINAL_LOCAL_STATUS_R24.zh.md)及对应独审回执为准。补充5条既有PNA-BPF弯曲断裂伸长，复用弯曲状态，5317旧性质完整保持；未知应变／断裂判据、统计和环境条件保留。158项预览前定向测试、真实隔离安装、30条来源完整导出及原生三表等价通过；最终接纳读取精确独审回执。

当前5322性质／5207状态；聚合物1037身份／1064状态／1163性质，1000计算和163实验标签不作科学认证。106条测试温度、111条调湿字段未报告，96条确切n未确认；按性质计数，不当独立试验组。当前未上传内容累计r23/r24六条性质，不是六种新材料。继续本地积累后统一推送，不合并main、不稳定发布、不部署；本批远端CI、历史回归和HTTP未运行。下文保留历史阶段，不能当本批发布证明。


## r23本地继续积累（2026-11-04，尚未提交／推送）

当前本地以[本地状态及验收入口](experimental/polymer-exploration/20261103/local-acceptance-r23/FINAL_LOCAL_STATUS_R23.zh.md)及对应精确独审回执为准。本轮补既有NBR REF撕裂强度12.32kN/m、独立试样状态和流变t90背景；实际压机保持、精确误差、样本数和环境等未知不补造，硬度继续暂缓。全部5316旧性质保持。

当前全库5317性质／5207状态；聚合物1037身份／1064状态／1158性质，1000计算及158实验参考只是标签。152项预览前定向测试通过；原生5317检查全执行、无复用；隔离安装及三表等价通过。158实验参考中101条测试温度、106条调湿字段未报告，确切n未确认91条。最终验收不从本段推定，读取冻结独审回执。

当前实验分支HEAD仍为ba1dc2f0a06d306a92c89a3b32de33573907ace5，新增内容只在本地；本批远端CI未运行。继续本地积累较大进度后统一推送，不合并main、不稳定发布、不部署。下文为已保留的历史交付，不代表本批已上传。


## r19-r22聚合物统一实验交付（2026-11-03）

当前[交付与核验入口](experimental/polymer-exploration/20261103/delivery-r19-r22/README.zh.md)汇总四轮既有材料补充：2条PBS/PBAT断裂伸长、6条NR/Sylgard邵氏A硬度、5条Sylgard压缩模量和5条极限压缩强度。新增18性质、11试样状态，无新身份／牌号／来源；全部5298个前驱性质完整不变，只2既有状态的版本／链接／范围说明及3来源追加备注。

当前全库5180身份、31牌号、5206状态、5316性质、133来源；聚合物1037身份、1063状态、1157性质，1000计算和157实验参考仅为来源标签，不作科学认证。快照`25d66658d21c8aebad75b875b2da82c121a99f893ddde3965a837cc955f12ba6`。

邵氏A是独立经验标尺，绝对SD／CI为标尺点，置信水平typed percent另列。压缩源MPa与95%CI、摘要GPa／40%及正文约55%范围疑点、Ec异常量级／趋势和提取关系未知均保留，不作单位倍率、Young／导数／割线／泊松比修复，不输入计算器。硬度4试样×8测点不能记32独立试样；压缩n不借其他试验数。

157实验性质中100条测试温度、105条调湿字段未报告；67条有确切n，86条n为空、4条仅下限，确切n未确认90条。按性质对象计数，不当独立试验组；reported可能只有冷却／加工时间，不代表RH完整或湿度平衡。NR断裂伸长单位疑点、部分PA12／PLA-PCL断裂及其他未确认项继续暂缓。

各批来源、实现／映射、安装及本地接纳已独审；统一交付的当前测试、安装、消费者、提交／推送和远端CI仅以精确收据为准，不将历史140／146或旧提交CI冒充新执行。完整历史回归、HTTP和平台全量验收未运行。不合并main、不稳定发布、不部署。下文保留历史原文，当前以本入口为准。


## r15-r18聚合物统一实验交付（2026-11-03）

当前[交付与核验入口](experimental/polymer-exploration/20261103/delivery-r15-r18/README.zh.md)汇总31条既有试样性质补充：19条断裂伸长率、12条拉伸强度处伸长率。两类端点分别表达，三条高PCL断裂缺失和两条PA12统计暂缓记录继续保留。全部5267个前驱性质完整对象不变；无新身份、牌号、状态或来源，只22既有状态的版本／链接／范围说明与5来源追加声明。

当前全库5180身份、31牌号、5195状态、5298性质、133来源；聚合物1037身份、1052状态、1139性质，其中1000计算与139实验参考仅为来源证据标签，不认证科学真实性。快照 `596b1f2b5cfd756c696429a243b98d8c059ab3be3fe76aae370fad5cba7f99fa`。

原文百分数不缩放；绝对SD／±是伸长百分点，CV是相对百分比，不混为中央单位或相对误差。percent_elongation是应用上下文码，不是新物理单位。来源、映射、各批安装及接纳均已独审；原文未知温湿度、调湿、标距／应变约定／断裂选点、统计及批次仍未知。来源条件相容筛查不作科学认证，腔体小时不当自然寿命。

当前139条实验性质中，95条温度、104条调湿字段未报告；76条n数值为空，另4条只报告至少5重复，确切n未确认共80条。59条有来源报告的确切n。样本数关系分类按性质记录计数，不当独立试验组；旧R2 sample_count_value_missing 仅为空值计数，不是全部确切n未知。

统一交付安装、暂存／提交和远端CI均以精确收据为准，不把历史135项测试或旧提交CI冒称新执行。完整历史回归未运行，不合并main、不稳定发布、不部署。下文保留历史阶段原文和数量，当前状态以本入口为准。


## r12–r14聚合物统一实验交付（2026-11-03）

当前[交付与核验入口](experimental/polymer-exploration/20261103/delivery-r12-r14/README.zh.md)汇总15条既有状态性质补充：6条拉伸断裂应力、2条NR规定伸长率应力、7条PLA/PCL拉伸强度。无新增身份或状态，全部5252个前驱性质完整对象不变；只13个既有状态的版本／链接／范围说明和3个来源声明更新。

当前全库5180身份、31牌号、5195状态、5267性质、133来源；聚合物1037身份、1052状态、1108性质，其中1000计算参考和108实验参考为来源分类标签，不认证科学真实性。快照 `7566389019ed828d24a5dd2329c01946f6c0640234680b77cc6b1d7b2c3f276e`。

来源、映射、隔离安装和各批本地接纳均已独审；强度±定义、样本数、温湿度／调湿和应力约定等未确认项保持未知，不借用邻近试验或标准默认值。当前108条实验参考的74条温度、77条调湿字段未报告，59条确切n缺失，按性质记录计数，不当作独立试验组或完整率。

统一交付的当前文件安装、具体暂存／提交及远端CI以精确收据为准；不把旧127项或旧提交CI当作本次新执行。完整历史回归未运行，不合并main、不稳定发布或部署。下文均为各历史检查点，原冻结文字和数量不改写。


## r8–r11 统一实验交付（2026-11-03）

当前[统一交付入口](experimental/polymer-exploration/20261103/delivery-r8-r11/README.zh.md)覆盖10条新增聚合物性质、两个独立pressure类型和既有记录的来源/范围补充。数量仍为5180身份、5195状态、5252性质；聚合物1037身份、1052状态、1093性质。6个旧性质仅作版本/局部比较范围措辞更正；无新身份或状态。
124专项为r11实际执行，本轮不与历史119累加。各本地接纳/独审已完成；统一当前文件安装、具体暂存/提交/远端CI另以交付收据核实，不把旧提交CI当新结果。当前仍为实验交付准备，未合并main、未稳定发布或部署。以下为各历史阶段，冻结收据不改写。

## r11 独立弯曲强度类型及六条既有聚合物补充（2026-11-03）

当前[r11本地接纳](experimental/polymer-exploration/20261103/local-acceptance-r11/README.zh.md)：5180身份、31牌号、5195状态、5252性质、133来源；聚合物1037身份、1052状态、1093性质（1000计算、93实验来源标签，不认证真实性）。快照`58defa23d7fa9a5e28f1f1a30d8ba9a47c311ac7a7293b82284d178385a99af8`。
新增独立pressure类型flexural_strength及既有五个PNA-BPF弯曲状态与PHBV-39共6条性质；旧5246性质对象不变，无新身份或状态。弯曲强度不归弯曲模量或拉伸/屈服/断裂强度，不接引擎或specified_elongation描述符。环氧保留统计未知；PHBV保留mean±SD、至少5重复及1% until yield原文限制，不移用拉伸3N/min。具体提取判据、应力口径、环境/调湿及标准合规未知不补造，名义组成矛盾保留。
本批实际124专项通过，失败/错误/跳过0，不与历史119累加。来源/概念、具体实现及隔离安装独审通过；5252增量检查执行、reuse0，三表已审预览schema通过精确字节转移至原生，两来源24条完整安装导出及四语展示核验通过。最终整合结论见接纳记录。完整历史回归及远端CI未运行；未提交/推送、未合并main、未稳定发布或部署。以下为前驱历史阶段，数量与测试不改写。

## r10 PHBV-39 来源标称拉伸强度（2026-11-03）

当前[r10本地接纳](experimental/polymer-exploration/20261103/local-acceptance-r10/README.zh.md)：5180身份、31牌号、5195状态、5246性质、133来源；聚合物1037身份、1052状态、1087性质（1000计算与87实验来源标签，非科学认证）。
快照`59eb6d9e5ae56afbafd9a3413c456f8d060263d280f2664df00b551c0da69650`。新增既有PHBV-39拉伸强度12.7±1.9 MPa，来源mean±SD、至少5重复；旧5245性质对象不变，无新身份或状态。
来源写加载至屈服，但具体强度提取判据未知；作者标签不自动证明最大/屈服/断裂应力。数值温度、RH、热压后调湿/储存、标准、精确n/批次、应力约定继续未知；不挪用弯曲参数或组成统计。catalog_only，不作计算器输入或工程许用值。
来源/映射及安装独审已通过；5246增量检查、已审完整预览三表schema字节一致性、三条完整安装导出与四语展示已核验。r9的119项测试未在本批重跑；本批运行代码/schema未改。完整历史回归和远端CI未运行，最终整合状态见接纳记录。未提交/推送、未合并main、未稳定发布或部署。以下为各前驱阶段，不表示当前数量。

## Local r9 specified-elongation stress supplement (2026-11-03)

The [r9 local acceptance entry](experimental/polymer-exploration/20261103/local-acceptance-r9/README.zh.md)
updates the registry to **5180 identities, 31 grades, 5195 states, 5245 properties,
133 sources**; polymer **1037 identities, 1052 states, 1086 properties**.
Snapshot: `06d8e433c7c28c7b3b10c7a8f9432082a6ccad789f3e0aac7fb50c08d717c7c5`.
Two REF M100/M200 facts use an independent pressure quantity with a required typed
specified_elongation descriptor. Central values stay MPa, targets stay source percent;
no division, slope conversion or Young/strength reclassification occurs. All old
5243 property objects remain exact; no identities/states/sources are added.

Source/concept, concrete schema/runtime/labels/tests/mapping and actual installation
reviews passed. New disjoint schema branches require targets for this quantity and
forbid them elsewhere; runtime rejects invalid targets/evidence/units. Numerical
fact identity includes target values without decimal-context rounding. Four-language
rendering and complete query/export preserve targets and scope notes. Source-used
ISO edition/compliance, strain estimator, target participants, averaging order,
plus-minus type and n remain unverified; no scientific certification is claimed.

This stage actually executed 119 scoped tests, all passing with zero failures/errors/
skips; prior r8 inherited112 receipts retain their historical stage. Incremental
validation executed 5245 checks, reuse0. Full historical replay was not run. Old r8
code bindings resolve through Git8735dfc; preapplication documents are archived.
This r9 checkpoint remains local and uncommitted. No new push/CI, main merge,
release tag or deployment was performed; continue local accumulation before delivery.

## Local r8 NBR REF supplement (2026-11-03)

The [r8 local acceptance entry](experimental/polymer-exploration/20261103/local-acceptance-r8/README.zh.md)
updates the registry to **5180 identities, 31 grades, 5195 states, 5243 properties,
133 sources**; polymer **1037 identities, 1052 states, 1084 properties**.
Snapshot: `8adff2c3c8e51f3fa1a6825349e870465998c680c0f5aa2dbf16c8ace5857471`.
One tensile-strength mean is added to the existing nonfoamed NBR REF state; no new
identity/state. Six old same-source composite properties change only revision and
comparator-disposition wording, so their notes do not deny separately admitted REF
properties. All their numerical/statistical/condition/method/evidence fields are
unchanged. The whole REF density property remains exact.

Fresh primary XML supports the REF Table 4 result and pooled orientations; no new
PDF or visual inspection is claimed. Strength plus-minus kind, n, environmental
conditions and pooling details remain unknown. Density does not inherit tensile
statistics or methods. Abstract/table disagreement remains explicit.
Source/full-preview and actual isolated installation reviews passed; incremental
validation executed all 5243 property checks, reuse 0. The prior published 112-test
receipt is inherited with unchanged code; it was not rerun for r8. Full historical
replay was not run. This r8 checkpoint is local and uncommitted, beyond the earlier
8735dfc delivery. No new push, CI, main merge, release or deployment was performed.

## Consolidated r5–r7 experimental delivery (2026-11-03)

The [delivery entry](experimental/polymer-exploration/20261103/delivery-r5-r7/README.zh.md)
groups 19 independently reviewed polymer property additions and five specimen states
since `e8c614ae286708cf200c7bbca1fc9bc3ec6e419f`. All old 5223 property objects,
5180 identities and 31 grades are unchanged; 14 existing state records and five
source notes are amended within their reviewed scope. The current snapshot remains
`a0068f8c22fc94cdfb893fda69585b1a416811b937ed2b2b558a803feded0456`.

The additive tensile_yield_strength quantity keeps yield distinct from maximum
strength and moduli. Unknown conditions/statistics and the Sylgard method-range
contradiction remain explicit. Consolidated checks executed 112 scoped tests with
zero failures/errors/skips plus the daily database CI command equivalents. This
later execution does not rewrite earlier r6/r7 receipts saying tests were not rerun.
Full historical replay remains unrun. Earlier bound documents are archived with
original hashes before this delivery update.

Delivery targets only experimental/open-database. Exact remote commit and Actions
results require post-push verification; this pre-push text does not claim either.
No main merge, release tag or deployment is included. The final operation receipt
is retained outside the commit to avoid recursive status-only pushes.

## Local r7 Sylgard strength supplement (2026-11-03)

The [r7 local acceptance record](experimental/polymer-exploration/20261103/local-acceptance-r7/README.zh.md)
updates native counts to **5180 identities, 31 grades, 5195 states,
5242 properties, 133 sources**; polymer **1037 identities, 1052 states, 1083 properties**.
Snapshot: `a0068f8c22fc94cdfb893fda69585b1a416811b937ed2b2b558a803feded0456`.
Five source-labelled ultimate tensile strengths were added on existing Sylgard
184 tensile-cure states; no new identities or states. All old 5237 property objects
remain exact. Source/mapping, integration and actual isolated installation reviews passed.

The original strength calculation-range contradiction remains unresolved: each
record keeps a not_verified/null strength window and the source discrepancy.
The below-40% Young-modulus window and source 0.40 strain factor are not assigned
as a verified UTS extraction method or used to multiply stress/CI. The stated 95%
CI and six samples remain reported facts, with unknown estimand/construction and
peak-extraction/averaging order; no mean-of-six-peaks or SD/SE inferred.

Current incremental validation executed all 5242 property checks (reuse 0).
Runtime/test code is unchanged; prior 78-test evidence is inherited, not rerun or
counted as new r7 executions. Full historical replay was not run. The preview wheel
contains the archived preapplication r6 README, not later handoff documentation.
This checkpoint is local and uncommitted; no push, new hosted CI, main merge,
stable release or deployment was performed. Accumulate reviewed local progress
for consolidated GitHub delivery; remote latest state was not reverified.

## Local r6 epoxy supplement (2026-11-03)

The [r6 local acceptance record](experimental/polymer-exploration/20261103/local-acceptance-r6/README.zh.md)
updates the native registry to **5180 identities, 31 grades, 5195 states,
5237 properties, 133 sources**; polymer **1037 identities, 1052 states, 1078 properties**.
Snapshot: `13f837f4a1e02fd397432aab7e47f0d29a48b38211add517c27fd12d6bd0f56c`.
Five existing PNA-BPF epoxy identities gain five tensile and five flexural moduli.
Five new flexural specimen states preserve the 3.6 mm plate preparation separately
from the existing 4 mm tensile states. No identities were added; all old 5227
property objects remain unchanged, including the unresolved source discrepancies.

Source/mapping, integration and actual isolated installation reviews passed.
Current incremental validation executed all 5237 property checks (reuse 0).
No runtime or test code changed; the prior 78-test receipt is inherited with exact
file hashes, and was not rerun or relabelled as a new r6 test execution.
Full historical replay was not run. Test environment, conditioning, statistics
and modulus extraction details remain unknown where unreported.

This is a local uncommitted checkpoint. No push, new hosted CI, main merge,
stable release or deployment was performed. The installed preview contains the
archived preapplication r5 README, not these later handoff documents. Continue
accumulating reviewed local progress before consolidated GitHub delivery.

## Local r5 polymer supplement (2026-11-03)

The [r5 local acceptance record](experimental/polymer-exploration/20261103/local-acceptance-r5/README.zh.md)
supersedes the native counts below: **5180 identities, 31 grades, 5190 states,
5227 properties, 133 sources**; polymer **1037 identities, 1047 states, 1068 properties**.
Snapshot: `044456eb1e9413ec819b7145543dab8dce4c6e7d1ea963d8c3a2e6f717edbaec`.
Four existing-state properties were added (NR finite-strain tensile modulus,
PHBV-39 flexural modulus, two PBAT/PBS-PBAT yield strengths); all old 5223
property objects remain unchanged. New identities/states: zero.

Source, implementation, combination and isolated installation reviews passed.
The first implementation review found a missing required locale key; its rejection,
exact implementation bytes, fix and four-language retest are retained. All 78 scoped
unit tests passed (zero failures/errors/skips). Incremental validation executed all
5227 property checks because source metadata changed; full historical replay was not run.
The installed preview is a preapplication artifact; its original README is archived.
Its 65 payload files match current native package files except the isolated preview
version marker; later handoff documentation is not claimed to be in that wheel.

This checkpoint is local and uncommitted. No new push, hosted CI, main merge,
stable release or deployment was performed. Accumulate further reviewed local work
before consolidated GitHub delivery. Unknown yield criterion, RH, method windows
and statistical definitions remain explicit; none are engineering allowables.

## Consolidated r4 experimental checkpoint (2026-11-03)

The [r4 delivery entry](experimental/polymer-exploration/20261103/delivery-r4/README.zh.md)
groups the reviewed native update, finite source audits, independent reviews,
installation checks and retained failure history for delivery on
`experimental/open-database`. Exact remote acceptance and hosted CI require
the delivered commit; local checks do not establish those outcomes. Earlier
acceptance-stage documentation bytes are archived with their original hashes.

## Local polymer acceptance checkpoint (2026-11-03)

The reviewed r4 data have been applied locally: **5180 identities, 5190 states,
5223 properties**, snapshot
`62502e5fe24d06f883228fe7d9fea3c579d03d97c25c0b3b8d33a87a9c767bd6`.
See the [local acceptance evidence](experimental/polymer-exploration/20261103/local-acceptance-r4/README.zh.md).
This adds 22 properties and five states, corrects 22 existing properties, and adds
no identities. Unknown conditions and source discrepancies remain explicit.
The r4 isolated installation and incremental validation passed; all 50 scoped
unit tests passed, with no failures, errors or skips. Full historical replay
was not run. This acceptance receipt predates consolidated delivery. No main
merge, stable release or deployment is included.
Earlier entries and frozen candidate manifests retain their historical stages.

## Prior polymer experimental delivery (2026-11-03)

The [consolidated delivery entry](experimental/polymer-exploration/20261103/DELIVERY.md)
separates the reviewed Sylgard addition (four states and four moduli, zero new
identities) from the PA12 source audits and the unreviewed filament/ageing
candidates. The actual native fingerprint is
`aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f`.
Source values, unresolved discrepancies and frozen failed checks remain visible.
An isolated Windows wheel installation matches this native fingerprint.
Exact commit delivery and hosted CI must be checked separately; no main merge,
stable release or deployment is authorized by these local results.

## Local existing-record follow-up (2026-11-02, reviewed data)

After delivered commit `e89d079fbdf46937a043b34f7cb73a442a814b20`, local work
rechecks 15 existing density records from NBS and Watanabe. The
[source/condition guide](docs/MATERIAL_SOURCE_CONDITIONS.zh.md) and
[field-level candidate](experimental/data-updates/source-conditions-20261102/source-review.json)
separate 17 scoped absence checks from 14 conditioning fields that remain
unverified. Numerical facts and material identities are unchanged. The candidate
data fingerprint is `84c1dbb84bce4f79172521a831126bc37ae9c079bb12cc8deae6ff11c7a86ba5`.
Compatible `1.0.N` record revisions now permit an explicit correction without
changing IDs or the table schema version. The
[independent review](experimental/data-updates/source-conditions-20261102/INDEPENDENT_REVIEW.json)
approved this exact finite amendment at 2026-11-02 03:40:41 UTC, after rehashing
52 evidence files and reviewing the source scope, implementation and actual
checks. Frozen candidate inputs retain their preparation-time pending status.
Consolidated experimental delivery and its exact hosted CI are separate evidence;
the predecessor's green CI does not certify this successor. No main merge,
stable release or deployment is included.

## Database development continuation (2026-11-02)

Continue from `experimental/open-database`, baseline commit
`a35928deaf3a1b5ad89211a798bcf0eaf5e02929`, using
[database contribution stages](docs/DATABASE_CONTRIBUTING.zh.md) and
[layered database checks](docs/DATABASE_CI.md). The current
[coverage and SCC review account](docs/DATABASE_COVERAGE.zh.md) binds the native
database fingerprint and separates working counts from reviewed data.
The user requested continued work under this database standard and consolidated
GitHub delivery after substantial local progress; main merge, stable release and
deployment remain separate. The older scope and validation narrative below is
retained as historical software-checkpoint evidence. Its complete-history gates
do not replace the current database contribution workflow, and daily database
checks do not certify those historical release gates.

The [SCC independent data review](experimental/material-batches/scc-fresh-flow-recipes-20261029/DATABASE_DATA_REVIEW.json)
approved the exact 1,000 candidate identities/states/properties and one source as
reviewed data on 2026-11-02. It binds database fingerprint
`b931d7f94c8e40a73fcc918f47c9a8e9a0cffd5e5f31224aa97dafd48e045ff4`
and 38 reviewed evidence files. It grants no software acceptance or publication
clearance. This completes the finite local data increment under the new database
workflow; the old SCC software-acceptance record below remains historical.
The new summary
command reports native conditions, evidence and source-rights statuses without
granting admission or publication status. No historical failed or incomplete
regression is reclassified as passing by this transition.

## Current local development scope

The user has resumed material expansion toward at least 1,000 admitted unique
material identities in each of the five primary classes. The local baseline
commit is `f13586759af6a391635fa81da20c73eb6a6c1c6c`; later experimental work is
uncommitted. No push, main merge, release, deployment or DOI action is authorized
by this handoff. Current remote/main/published counts have not been verified here.

The completed local JARVIS checkpoint accepted a 2,000-identity increment after
independent source/identity/implementation review, installed verification and
complete reconciliation of 1,887 original local methods: 1,871 passed, 16 policy
skips and no failed, errored or incomplete methods (Windows Python 3.11).
That frozen checkpoint contains 3,180 identities. It is a completed predecessor
checkpoint, not a claim about the latest successor or any published release.
The earlier five-identity Sanchez acceptance remains part of that history.

The completed finite local PolyOmics checkpoint accepted 1,000 source-qualified
hypothetical linear constitution models, forming 4,180 identities. Actual
validation covered 1,887 original methods plus 40 disjoint dedicated methods:
1,911 passed, 16 exact policy skips, no failures/errors/incomplete methods.
Independent final review rehashed all 213 evidence files and the 1,281-file
snapshot. Original failed attempts and full failed-partition retries are retained;
P0/P2 successes were reused only for identical inputs. This finite registry
acceptance did not certify the frozen status prose or any remote publication.

The SCC working graph contains 5,180 source-qualified identities, including
1,000 nominal cementitious recipe representatives. Its exact 24-file application
(16 replacements, eight additions) was independently cleared after the accepted
4,180 predecessor, backed up and fully read back into a 1,289-file snapshot.
Acceptance of that successor is established only by its own 1,887 original
methods plus 48 disjoint dedicated methods, installed/source/history/current
documentation evidence, independent final review and an explicit local decision.
Neither catalogue counts nor the earlier preview checks establish that decision.

Use the immutable local `LOCAL_ACCEPTANCE.json` records and their pinned evidence
in the supplied handoff evidence package to determine which exact snapshots are
accepted. Those records may be outside the source checkout; a missing record
does not establish acceptance. Later edits require their own applicable input
and test accounting. This document does not turn a predecessor result into a
successor, hosted-CI or publication result.

The [growth record](docs/MATERIAL_GROWTH_1000_PER_CLASS.zh.md) separates the
completed JARVIS checkpoint from SCC working counts and required gates.
The [reference walkthrough](docs/MATERIAL_REFERENCE_WALKTHROUGH.zh.md) and
[source/condition notes](docs/MATERIAL_SOURCE_CONDITIONS.zh.md) explain the
measured, DFT, MD and compiled SCC reading paths and their unknown conditions.
Independent source/transcription checks do not certify independent scientific
peer review, experimental existence, engineering allowables or universal bounds.
Unverified SCM mirror provenance/rights and other held sources remain held.

## Archived growth preparation notes

The following notes retain the preparation-time source and review narrative.
Their stage words such as pending, unapplied and running refer to that archived
preparation snapshot. Use the completed checkpoint and explicit successor gates
above together with actual immutable evidence to interpret later progress.

### Coordinator growth notes prepared during 2026-10-27–28

Material expansion has resumed under the user's goal of at least 1,000 admitted
unique material identities in each of the five primary classes. The
[growth record](docs/MATERIAL_GROWTH_1000_PER_CLASS.zh.md) pins local baseline
coverage, source inventories and remaining review/admission gates. The source
audit admits zero new identities. No push, main merge or deployment is authorized.
The pause snapshot below remains a historical account of the 2026-10-26 closure.

The five revised Sanchez aluminium-alloy identities are accepted in the local
experimental worktree after independent source/implementation review, installed
checks and reconciliation of all 1887 frozen local root IDs: 1871 passed,
16 skipped, zero failures/errors/incomplete IDs (Windows Python 3.11).
The [acceptance record](experimental/material-batches/sanchez-al-mea-revised-20261027/LOCAL_ACCEPTANCE.json)
pins the exact identities and evidence; the
[verification report](experimental/material-batches/sanchez-al-mea-revised-20261027/INTEGRATION_VALIDATION.md)
retains repaired failures, cancelled attempts and unrun hosted/cross-platform
scope. This is local acceptance, not a main merge, release or hosted CI pass.

The JARVIS source audit, frozen 2,000 source-fact selection, corrected native
mapping, finite hypothetical-model identity/compositional classification and
four-file isolated method implementation now have scoped independent approval.
The [current native batch](experimental/material-batches/jarvis-density-native-draft-20261028/README.md)
retains the rejected locator version, repaired review, exact hashes and isolated
compiler replay. These decisions do not establish experimental existence,
metallic electronic behavior or cross-provider phase equivalence. Runtime
registry/helper wiring and local integration are now independently reviewed.
Focused history checks and real isolated installed checks passed; the frozen
1887-ID full-root regression is running. Read the
[current integration report](experimental/material-batches/jarvis-density-native-draft-20261028/INTEGRATION_VALIDATION.md)
for exact scopes, build failure/retry and pending coverage. Final acceptance
remains pending; all 2,000 candidates still contribute zero to the completed quota.
The earlier JARVIS r1/r2 rounds failed and were stopped; their partial results
are retained, with no passing aggregate. The reviewed Emax-only correction is
preparing for r3. Its whole-public-tree freeze, external live receipt and exact
unrun scope are recorded in the integration report; the earlier running status
above is historical and does not certify r3 launch or completion.

The [PolyOmics source/identity review](experimental/material-batches/polyomics-density-candidates-20261028/REVIEW_STATUS.md)
approves 1,000 frozen source facts and finite hypothetical linear constitution-model
identities. The [separate MD implementation review](experimental/material-batches/polyomics-md-native-draft-20261028/independent-implementation-review.json)
approves four isolated files only; they remain unapplied. Native mapping,
historical integration, full regression, installed checks and admission remain
pending. PolyOmics contributes zero to the completed quota. The
[SCM mirror audit](experimental/material-batches/scm-mirror-source-audit-20261028/README.md)
is held because official-file equivalence and rights/provenance remain unverified.

For browsing the existing material records, start with the
[Chinese material-reference walkthrough](docs/MATERIAL_REFERENCE_WALKTHROUGH.zh.md).
It covers exact queries, source locators, reported uncertainty and unknown conditions;
it does not add material records or resume material expansion.
The [Chinese source and condition notes](docs/MATERIAL_SOURCE_CONDITIONS.zh.md)
explain the existing PLA/PCL, reactive PBS/lignin and curauá/RPUF records.

Start with the [bounded development kit](docs/development-handoff/README.md) and its [portable onboarding guide](docs/development-handoff/ONBOARDING.md). They provide ready-manifest checks, small-task contracts, independent reviewer prompts and reproducible evidence accounting. The [Chinese operator guide](docs/development-handoff/OPERATOR.zh.md) gives the short operational version.

## Historical material pause (2026-10-26)

Material expansion is paused. The runtime base for this documentation addition is [`3829ec97e396a73168951b7868b9a03d533948b8`](https://github.com/chaotic-mixture/materials-boundaries-public/commit/3829ec97e396a73168951b7868b9a03d533948b8), on `experimental/delgado2020-pla-pcl-runtime`. It contains **1199 experimental project records = 1175 source-qualified identities + 24 reviewed computed compositions**; 62 unadmitted examples remain excluded. This is not a main release.

The [dedicated PLA/PCL run](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40264855280) and [general test run](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40264855167) both completed successfully for that exact runtime base. General CI finished at **2026-10-26 07:21:32 UTC**; independent log/aggregate reconciliation completed at **07:30:04 UTC**. **The current seven-PLA/PCL material stage is closed; engineering and material expansion remain paused.**

- Ubuntu Python 3.11 and 3.12: each completed 1887 root IDs, comprising 1869 passes and 18 policy skips; the hosted aggregate reconciled all 8 partition receipts, with zero incomplete IDs.
- Windows Python 3.10 and 3.13: each completed the selected 526-method subset (512 passes, 14 platform skips) plus wheel smoke. This is not full-root Windows coverage.
- Dedicated runtime profiles: each recorded 439 source executions / 435 distinct methods and 585 installed tests, with no failures/errors/skips. Replay methods are already included, not additional passes.

These material results do not certify later handoff or documentation commits. Conditional/skipped jobs are not passes; scopes are not added into a fictitious total.

The [timestamped pause state](docs/development-handoff/pause-state.json) records the closure evidence, exact scopes and continued stop boundary. Existing validation evidence is in the [runtime report](experimental/material-batches/delgado-pla-pcl-20261026/INTEGRATION_VALIDATION.md); reported scoped checks must not be relabelled as a full-root pass. This handoff changes no material data, scientific contract, runtime or workflow file.

## Hand off one task

1. Pin separate kit and task checkouts as described in onboarding; old task commits may predate this kit.
2. Obtain a current coordinator instruction. Fill one exact manifest with selected records, consumer-local inputs and hashes, permitted files, literal check argv and a stopping point.
3. Run the read-only preflight. A successful result is an accidental-error guard, not user authorization, a security sandbox or scientific approval. Draft and archival examples are not dispatchable.
4. Give the worker only the selected context. Freeze its output for a different reviewer; a reviewer does not repair and approve their own change.
5. Report exact outcomes and unrun scope, then stop. Do not start the next material batch automatically.

Public access transfers no credentials, private evidence or standing permissions. Main merges, releases, deployments and DOI actions require separate authorization. Reading or publishing this kit does not resume material development or make pending CI successful.

## Platform check scope

The [fixture-portability correction](docs/development-handoff/PORTABILITY.md) is validated at published kit commit `62e6395be066a2c69f33920c0f8567ee8f7965f3`: Linux default/CRLF profiles passed 46/46, and the no-alias profile passed 45 plus 1 N/A. The native Windows executor reported 45 passes, zero failures and one explicitly not-applicable alias case, with all 5 positive controls and 40 negative gates correct. The original failure remains recorded. See the report for platform, source hashes and evidence-access limits.

**The kit is ready within this verified scope for a newly authorized bounded task, not automatic resumption.** This final status snapshot does not embed a self-referential CI pass: verify its actual remote commit and hosted CI after publication. No extra commit is required merely to record that check.
