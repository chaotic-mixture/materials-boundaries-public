# はじめに：Materials Boundaries

## 現在の v0.23.0：明示的な PA12 CF15 温度観測図

新しい独立経路は、**一つの出典報告手順に属する表3の承認済み6セルすべて**だけを
表示します。公表要約の記述的転記であり、材料予測や独立した科学的検証ではありません。
科学カタログ、**12観測・52出典・36論断・12予測・合成温度モデル5件・7分岐・8計算規則**
は不変で、観測はすべて `catalog_only` のままです。

```sh
python -m materials_boundaries observation plot-temperature --dataset-id ciganas-2026-pa12-cf15-fff-uts-temperature --output /tmp/pa12-temperature-plot-ja --lang ja
python -m materials_boundaries observation plot-temperature --help --lang ja
```

上記の正確なデータセット ID と出力先は**必須**です。全記録の既定描画、部分集合、
任意の圧力型記録や自動グループはありません。`--lang en|zh|ja|de` は最後の指定が優先
されます。図スキーマ **1.0.0** は、不変の観測 **1.3.0**・一般閲覧 **1.1.0** と別です。
`observation inspect` は数値軸のないテキスト表示で、従来の選択とカタログ順序を保ちます。

接続しない同一様式の6点は**報告された中心 UTS 値で、平均値とは断定しません**。
数値軸は報告試験槽温度（°C）と出典 MPa です。端部付き縦ひげは **±報告 SD** であり、
SEM・信頼区間・観測最小最大・厳密な上下界・包含率ではありません。**各条件で引張試験3回**
との報告がありますが、元の反復データと独立性は未検証です。30分間の試験槽安定化は直接の
試料温度を確定しません。横ひげがないのは**温度不確かさが未報告で、ゼロではない**ためです。
固定の 15–125 °C／0–55 MPa 表示域は余白・基線で、材料限界ではありません。接続線、
フィット、補間、外挿、順位付け、重ね描き、設計許容値や安全性の主張は追加しません。

正確な出典表は文字列と末尾ゼロを保ちます。Pa は別の正確な単位メタデータで、
**1 MPa = 1000000 Pa** は精度を追加せず、幾何学から再計算しません。中心統計量・集計、
応力・断面積根拠、含水率・湿度、局所ひずみ速度は不明のままです。水平 ±45° FFF、乾燥、
宣言15 wt.%、100% インフィル、名目寸法、1 mm/min クロスヘッド手順という条件は、
測定済み組成・空隙ゼロ・等方性を保証しません。

`observation-temperature-plot` 接頭辞で JSON、CSV、広幅／狭幅 SVG、スクリプト不要の
応答型 HTML を生成します。簡潔な SVG でも、6項目の重要警告・凡例・正確な出典表と記録 ID・
共通手順／形状／不明条件の要約・正確な出典位置・版と権利帰属を表示します。完全なメタデータ
辞書、各記録で繰り返す来歴、6組の SI 値は JSON／CSV と実行不能の HTML 詳細に欠落なく
保ち、解釈に必須の警告をそこに隠すことはありません。JSON／CSV は決定的かつ言語非依存です。式に似た文字列を
改変しないため、出典・ID・JSON 列はテキストとして読み込みます。新規検証は書込み前に
現行カタログから再構築します。不正入力は出力を変更しませんが、その後のファイル障害の
全ファイル原子的ロールバックは保証しません。図は表3の出典順に戻し、一般閲覧は格納順です。

HTML 版、PDF 未検証、対象外の表4差異、CC BY 4.0 帰属と図への改編表示を保ちます。
出典媒体や生データは追加しません。機械支援翻訳は独立した科学的・母語レビューではなく、
ブラウザー QA は未検証です。[図・API・CSV の全契約](OBSERVATION_TEMPERATURE_PLOT.md)
· [移行](MIGRATION_v0.23.0.md)。

## 以前の v0.22.0：六つの試験槽条件での PA12 CF15 引張要約

Ciganas、Kalinauskis、Cigane（2026）の表3から UTS／SD の6セルを追加します。
報告された試験槽条件は **23、40、60、80、100、120 °C** です。現在は
**4研究の12観測・52出典**で、**論断36件、予測12件、合成温度モデル5件、
7分岐、実行可能な複合材料規則8件**は変わりません。

水平 FFF 印刷の Fiberlogy PA12 CF15、交互の +45°／−45° ラスター、
試験槽で30分間安定化後の 1 mm/min クロスヘッド速度という特定手順です。
直接測定した試料温度、温度安定性公差、局所ひずみ速度や実際の含水率は不明です。
乾燥は含水率測定ではなく、15 wt.% は宣言された配合、100% インフィルは印刷設定で、
測定済み繊維量や空隙ゼロを意味しません。応力定義、断面積の根拠、中心統計量と集計法
も不明です。各条件で試験3回と報告された SD は、SEM、信頼区間、厳密な上下界や
普遍的な設計許容値を与えません。

新しい型は `experiment_derived_tensile_test_summary`、量は
`ultimate_tensile_strength_as_reported_3d` です。**MPa の出典文字列**と SD は、
**正確な Pa 単位換算**から分離します。1 MPa = 1000000 Pa は測定精度を追加せず、
幾何学から応力を再計算しません。従来の2D N/m記録は不変です。補間、連続温度モデル、
順位付け、異なる次元の量との比較は追加しません。

観測スキーマは **1.3.0**、閲覧スキーマは **1.1.0** です。保存済みバンドルは版番号を
書き換えず再生成してください。既定では警告が物性値に先行する12枚のテキストカードを
返します。CSV は報告単位と SI／正規化列を区別します。全カタログは同じ出典セルの
重複別名を拒否しますが、科学的内容を保った部分集合・改名は有効です。他の既存
ファミリーの追加可能性は保持します。

HTML の版、未確認の PDF、選択外の表4のキャッシュ／現行差異を保持します。
一致の確認は選択した表3の6セルの HTML・目視・独立した第二転記に限り、独立実験を
意味しません。論文の CC BY 4.0 と著者・題名・DOI 帰属を保持し、メーカー由来の表1
は除外します。出典媒体や長文は再配布しません。翻訳・ソフトウェア点検は独立した
科学的・母語レビューではありません。

```sh
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang ja
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15-ja --lang ja
python -m materials_boundaries observation inspect --id ciganas2026-pa12cf15-uts-60c --output /tmp/pa12-cf15-60c-ja --lang ja
```

[PA12 CF15](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) · [v0.22.0](MIGRATION_v0.22.0.md) · [Inspection](OBSERVATION_INSPECTION.md)

## 以前の v0.21.0：Ni11X モデル予測6件を追加

追加する公表済み理想せん断予測は **Ni11Cr 4.90、Ni11Mn 5.12、Ni11Fe 5.20、
Ni11Cu 4.51、Ni11Si 4.17、Ni11Ti 4.24 GPa** の6件だけです。
出典は Shimanek らの arXiv:2108.06412v2、表2、PDF／印刷頁27です。
v0.21.0 では **予測12件・科学的方法ファミリー2件・明示的比較グループ3件**です。
論断36件、出典51件、3研究の観測6件、合成温度デモ5件（7分岐）、
実行可能な複合材料規則8件は変わりません。実行時コード、科学的スキーマ、既存出典も不変です。

新グループ名は **Ni11X 周期モデル：Cr、Mn、Fe、Cu、Si、Ti** で、明示的な選択が必要です。
既定の Ni／Ni11Al／Ni11Co は3点のまま、別のシリコン初回不安定性グループも3点のままです。
Ni11Si のせん断予測は純シリコンの引張初回不安定性強度とは異なります。
無選択の予測カタログは12件、Shimanek 出典で絞ると9件を返しますが、新しい図の比較群は作りません。

fcc Ni に基づく12原子・3層の周期セルで、面内の Ni 1サイトを X で置換したモデルです。
(111)[1,1,-2] の正の pure-alias せん断角を規定し、原子位置とその他のセルパラメータを緩和します。
比較可能性は**公表された方法の範囲のみ**で、未監査の入力や不明な条件の一致を意味しません。
純粋な X の強さ、市販合金、実験測定、普遍的な上限ではありません。

表の6ラベルに pv／sv 接尾辞はありませんが、PAW データセットや価電子配置を特定せず、
半内殻状態の不在も証明しません。物理温度、スカラー圧力、磁気状態／スピン分極、
統計的／全不確かさは不明のままです。GGA の参照は **Perdew ら（1992）で、PBE と推定しません**。
**0.08 GPa のピーク収束基準は誤差棒ではありません**。4.90、5.20 の桁数は原文の表示精度です。
出典 PDF・全文・図を再配布しません。転記・翻訳の点検は独立した科学的・母語レビューではありません。

```sh
python -m materials_boundaries catalog predictions --query shimanek_v2_table2_cr_mn_fe_cu_si_ti --text --lang ja
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-ja --lang ja
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_ni_al_co --output /tmp/ni-original-ja --lang ja
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability-ja --lang ja
```

[方法・出典・限界](COMPUTATIONAL_PREDICTIONS.md) · [移行](MIGRATION_v0.21.0.md)

## 以前の v0.20.0：オフライン観測閲覧ビュー

3研究の既存のモデル依存要約6件を、出典順のカード／表として閲覧できます。
科学的記録は不変で、論断36件、出典51件、観測6件、計算予測6件、合成温度デモ
5件（7分岐）を保持します。実行可能な複合材料規則は8件のままです。
新しい閲覧バンドルのスキーマは1.0.0、観測スキーマは1.2.0のままです。

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang ja
python -m materials_boundaries observation inspect --output /tmp/hbn --source-id falin_et_al_2017_hbn_mechanical_properties --group-by quantity --lang ja
python -m materials_boundaries observation inspect --output /tmp/selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d --lang ja
python -m materials_boundaries observation inspect --help --lang ja
```

`--id` は繰り返し指定できます。`--source-id` と `--quantity` は大文字・小文字を
区別する完全一致です。全フィルターを AND で結合し、量は
`in_plane_stiffness_2d` と `breaking_strength_2d` を指定できます。
既定の `study` と任意の `quantity` は閲覧上のグループ分けだけを変更します。
カタログ順を保ち、数値で並べ替えません。不明・重複・不正形式の ID、未対応の
指定値／科学的方法ファミリー、空の結果はファイル作成前に拒否します。

出力は `observation-inspection.json`、`.csv`、`.ja.svg`、`.narrow.ja.svg`、
`.ja.html` です。HTML はローカルで開ける自己完結型で、スクリプトを使いません。
通信は読者が出典リンクを開く場合のみです。JSON／CSV、出典の表現、数値、ID、
ダイジェストは言語に依存しません。正規化したカタログ表示と出典の原文文字列は
別であり、逐語引用や新しい厚さ換算ではありません。

警告を数値の前に表示します。MoS2 の印刷された q の不整合と実際のフィット q
が不明な点を保持し、再フィット・修正はしません。グラフェンの ± の統計的意味は
未確認です。hBN の強さは FEM による圧子下応力の体積平均で、正確な中心統計量と
応力成分は未指定です。hBN の SD／枚数の根拠は査読著者回答 PDF 8頁のままで、
剛性の標本数を強さの破壊事象数へ転用しません。不明な条件同士の同等性は示せません。

観測計算器、条件を一致させた比較、数値軸、誤差棒、集計、順位付け、重ね描きは
追加しません。古い閲覧バンドルは再生成し、版番号だけを変えないでください。
出典 PDF、図、生データは同梱しません。独立した科学的・母語レビューは未実施です。
[閲覧ガイド](OBSERVATION_INSPECTION.md) · [移行](MIGRATION_v0.20.0.md)

## 以前の v0.19.0：カタログ専用の単層 hBN 観測

Falin ら（2017）のレコード2件と出典1件のみを追加し、**力学論断36件、出典51件、
3研究の観測6件**です。観測スキーマは **1.1.0 → 1.2.0** となり、hBN 専用の閉じた
方法ファミリーを設けます。計算予測6件、合成温度デモ5件（7分岐）、実行可能な
複合材料規則8件は不変で、論断スキーマは1.11.0のままです。

出典は **面内剛性289 ± 24 N/m** と **破壊強さ23.6 ± 1.8 N/m** を明記します。
標準偏差という定義の根拠は、出版社がリンクする**公開査読の著者回答 PDF 8頁、
査読者 #1 の質問3**です。本文の ± 記号だけに由来する定義ではありません。
標準誤差、信頼区間、厳密な限界、完全な不確かさ予算ではなく、反復値の重み付けは
不明です。**N=11 は試験シートの枚数で、剛性平均との対応のみ明示**されます。
曲線総数と破壊事象数は不明です。各シートで通常5回の圧入は、厳密に55本の曲線や
11個の確認済み強さ反復値を意味しません。

剛性は円形膜の AFM フィットで推定します。強さは非線形 FEM による**有限半径の
圧子直下の膜要素応力の体積平均**であり、補足図 S5 の**最大 Von Mises 応力**の
診断や直接測定した均一引張強さではありません。有限ひずみの応力・ひずみ尺度は
不明のままです。出典の式 **q=1/(1.049−0.15ν−0.16ν²)** と **ν=0.211** から得る
**0.9898768854482001 はキュレーターによる算術確認のみ**です。別記の数値 q や
実際のフィット定数は未確認のため、hBN の q の不整合や修正は主張しません。

ambient という記述から数値の温度・圧力・気体組成・湿度は確定しません。
**0.5 μm/s** は負荷・除荷時の探針移動速度であり、ひずみ速度ではありません。
二つの N/m 値は出典の明記値で、**0.334 nm** は出典のモデル厚さの規約のみです。
厚さ換算、再フィット、順位付け、比較、図、複合材料への重ね描きは追加しません。
既存のグラフェンと MoS2 の記録および下記の MoS2 の q 不整合は保持します。

論文は [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) ですが、補足資料と
査読ファイルそれぞれのライセンス範囲は未確認です。出典 PDF、全文、図、スクリーン
ショット、査読報告書、実験生データ集は収録しません。転記確認とソフトウェアテストは
独立した科学的・母語レビューではありません。[hBN の根拠と限界](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
および [v0.19.0 移行](MIGRATION_v0.19.0.md)を参照してください。

```sh
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang ja
python -m materials_boundaries catalog observations --query "hBN stiffness" --json
```

## 以前の v0.18.0：カタログ専用のバルク弾性波

本版は関係2件と出典2件のみを追加し、**力学論断36件、出典50件**、論断スキーマ
**1.11.0** となります。2研究の観測4件、計算予測6件、合成温度デモ5件（7分岐）、
実行可能な複合材料規則8件は不変です。波速計算器、材料入力、テンソル固有値ソルバー、
波の図は追加しません。

無応力平衡状態にある均質・無限の三次元古典的局所線形弾性・非散逸媒質で、等方的な
K、G とスカラー密度 ρ が有限正値なら、**c_L²=(K+4G/3)/ρ**、**c_T²=G/ρ**、
**c_L/c_T∈(√(4/3),∞)** です。これは有限の正ひずみエネルギーを持つ材料集合全体の
比の範囲です。下限は到達されず、共通の有限上限はありませんが、無限大という値が実現
するわけではありません。一つの固定材料では c_L、c_T は有限で方向によらず、横波は
二重縮退します。

所定の実弾性テンソル対称性の下で、**Q_ik=C_ijkl n_j n_l** の単位は Pa、
**Γ=Q/ρ** の単位は m² s⁻² で、Q a=ρc²a です。位相法線 n と変位の偏極 a は
別の変数です。厳密な強楕円性は、すべての単位 n で Q(n) が正定値、すなわちすべての
方向で三つの波速の二乗が厳密に正であることです。全対称ひずみに対するエネルギーの
正定値性は強楕円性を含意しますが、逆は成り立ちません。プロジェクト独自の反例
**K=−G/3、G>0** では Q=GI で三つの波速の二乗が等しく正でも、静水圧的なひずみの
エネルギーは負です。安定な実材料の提案ではなく、既存の全エネルギー安定性基準の意味は
弱めません。

一般異方性のモードが厳密な縦波・横波とは限らず、縦波が常に最速という順序は主張
しません。位相速度は波線・群速度についての結論ではありません。静的・等温弾性率の
自動代入、熱力学的変換、予応力や有限ひずみへの拡張はありません。Chevrot–van der
Hilst（2003）印刷頁498の式 (1)–(4)、Xiang–Qi–Wei arXiv v2 の2、4–5頁が基礎式の
出典で、比の区間とエネルギーの証明は独自導出です。出典の図・全文は収録せず、独立した
科学的・母語レビューは未実施です。[仮定・証明・版・適用除外](BULK_ELASTIC_WAVES.md)と
[v0.18.0 移行ガイド](MIGRATION_v0.18.0.md)を参照してください。

```sh
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang ja
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang ja
```

**以前の v0.17.0** は、一つの研究から単層 MoS2 のカタログ専用レコードを2件追加しました。当時の合計は **2研究の観測4件、出典48件**、観測スキーマは **1.1.0** です。既存のグラフェン記録は変更しません。MoS2 の面内剛性 **180 ± 60 N/m** と破壊強さ **15 ± 3 N/m** の ± は、出典が報告する標準偏差です。**印刷された q の式と記載値 q=0.95 は整合せず、実際のフィット定数は未解明です。再フィットは行いません。** [標準偏差の意味・出典・q の注意点](OBSERVATIONS.md#monolayer-mos2-bertolazzi-et-al-2011-new-records)を参照してください。

**初の公開版（0.16.0）当時の構成：**力学論断34件、出典記録47件、観測2件、計算予測6件、合成温度デモ5件（7分岐）。複合材料の計算規則8件は不変です。当時の論断スキーマは1.10.0で、科学的スキーマとソフトウェアの版は独立しています。

独自のコード、文書、キュレーションには [MIT ライセンス](../LICENSE)を適用し、第三者の著作物や科学的事実を再許諾しません。NIST の低温係数と派生例は利用条件の確認待ちとして慎重に除外しています。これは再配布禁止が確定したという意味ではありません。書誌情報とリンクは保持します。[第三者の権利に関する注意](../THIRD_PARTY_NOTICES.md)

温度デモの係数と範囲は意図的に作成したもので、実材料や測定データではありません。線形デモは50 Kで15 GPa、重複デモは50 Kで25と32.5 GPaの両方を返します。分岐選択、平均化、外挿、不確かさ帯の表示は行いません。[温度ガイド](TEMPERATURE_MODELS.md)

```sh
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-50k.json --lang ja
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-overlap-50k.json --lang ja
python -m materials_boundaries temperature plot --output /tmp/temperature-demos --lang ja
```

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Bulk elastic waves](BULK_ELASTIC_WAVES.md) · [Release scope](MIGRATION_v0.23.0.md)

## ローカルで実行する

Python 3.10 以降を使用します。リポジトリのルートで次のコマンドを実行してください。実行時に外部パッケージやネットワーク接続は必要ありません。

```sh
python -m materials_boundaries validate examples/synthetic-two-phase.json --lang ja
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang ja --unit GPa
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang ja --json
```

表示言語は `--lang en`、`--lang zh`、`--lang de` でも指定できます。JSON のキー、列挙値、数式、数値、単位 ID は変わりません。訳文がない場合は英語を使用し、英語にもキーがなければ欠落を明示するマーカーを表示します。

## 合成データの結果を読む

この例は説明用であり、実測した材料データではありません。

- 相 1：`f1 = 0.5`、`K1 = 10 GPa`、`G1 = 5 GPa`
- 相 2：`f2 = 0.5`、`K2 = 30 GPa`、`G2 = 15 GPa`
- 体積弾性率 K：Reuss `15 GPa`、HS `16.25–17.5 GPa`、Voigt `20 GPa`
- せん断弾性率 G：Reuss `7.5 GPa`、HS 約 `8.37837837838–9.04761904762 GPa`、Voigt `10 GPa`
- ヤング率 E の導出した外側包絡：約 `21.4488468362–23.1528046422 GPa`
- ポアソン比 ν の導出した外側包絡：約 `0.265190525232–0.293562708102`、無次元の単位 `1`

HS の区間は理論的な制約であり、モデル予測、測定の不確かさ区間、工学的な受入れ基準ではありません。出力は浮動小数点による近似値で、区間演算による保証はありません。

## 導出した外側包絡の意味

同一の材料系では E = 9KG/(3K+G)、ν = (3K−2G)/(2(3K+G)) です。E の下端・上端には (Klow,Glow)/(Khigh,Ghigh)、ν の下端・上端には (Klow,Ghigh)/(Khigh,Glow) を使います。別々の HS 区間の端点が同時に到達可能とは限りません。これは保守的な外側包絡であり、厳密な同時到達領域の限界ではありません。前提が不明または不充足なら数値を出力しません。相の大小関係が揃わない場合も E/ν を Reuss・Voigt の界で代替しません。

`--unit` は K/G/E の単位のみを変えます。ν は常に単位 `1` で、−1 < ν < 0.5 を満たす必要があり、負値やゼロも有効です。浮動小数点への丸めでいずれかの除外境界に達した場合、物理的な端点に切り詰めず、`numerical_range_error` と null の結果を返します。依存するいずれかの HS 結果で数値エラーが生じた場合、導出した包絡も利用できません。Decimal 計算は外向き丸めの保証ではありません。

評価出力は v0.2.0 から八つのレコードで、v0.8.0 でもその八つの科学的評価を維持します。固定のリスト長を仮定せず、`claim_id` と `quantity` で選択してください。既存の体積弾性率の ID、規則 ID、数値結果の構造は維持し、型情報と評価出力 schema 1.1.0 は v0.2.0 で導入されました。入力 schema と既存の例は引き続き有効です。[v0.2.0 移行ガイド](MIGRATION_v0.2.0.md)と[モデル・数式](MODEL.md)を参照してください。

## 上下界を使う前に適用条件を確認する

- `satisfied`（充足）：実装された確認項目の範囲内で、入力値と申告内容がすべての必要な前提を支持しています
- `violated`（不充足）：少なくとも一つの前提が入力と矛盾しています。該当する上下界を使用してはいけません
- `unknown`（不明）：少なくとも一つの前提について証拠が不足しています。適用可能だと仮定してはいけません

構成相の等方性と有効媒質の等方性は別の前提です。存在するすべての相の K/G は正でなければなりません。HS と導出した E/ν には、各相の K/G と体積分率の対応を保って番号付けし、`K1 <= K2` と `G1 <= G2` が同時に成り立つことも必要です。Reuss・Voigt ではこの順序は不要です。前提の全体は主張のカタログで確認してください。プログラムは試験片の微細構造を独立に検証しません。評価器では強度・破壊・塑性の数値計算を行いません。以下の破壊モデルはカタログ専用です。

```sh
python -m materials_boundaries evaluate examples/unknown-isotropy.json --lang ja
python -m materials_boundaries evaluate examples/anisotropic-constituent.json --lang ja
python -m materials_boundaries catalog claims
python -m materials_boundaries catalog sources
```

独自の入力を使う場合は例をコピーし、スキーマで定められたキーと列挙値を維持してください。不明な任意の観測項目は `null` にするか省略し、値を作り出したり証拠の不足を `satisfied` に置き換えたりしないでください。単位 ID は大文字・小文字を区別し、`Pa`、`kPa`、`MPa`、`GPa` を使用します。JSON の小数には点を使います。`validate` の後に `evaluate` を実行してください。構造が正しいことだけでは、物理的な適用条件の充足は示せません。

科学的な記述の四つの区分は[用語集](TERMINOLOGY.md)、翻訳の規約と品質確認は[言語サポート](I18N.md)を参照してください。

## 読み取り専用カタログを検索する

検索対象は同梱のキュレーション済みレコードのみで、ネットワークに接続せず、データも変更しません。従来の `catalog claims` と `catalog sources` は引き続き正規形式の JSON を返し、`--json` も同じ形式を明示的に選びます。`--text` はラベルと主要な証拠ステータスの説明を翻訳しますが、文献の原題、証拠の原文、正規 ID は保持します。

```sh
python -m materials_boundaries catalog claims --id hs_bulk_3d_two_phase --text --lang ja
python -m materials_boundaries --lang ja catalog claims --direction interval --text
python -m materials_boundaries catalog claims --query "bulk kochmann" --source-id kochmann_milton_2014 --json
python -m materials_boundaries catalog sources --query "Milton moduli" --year 2014 --text --lang ja
python -m materials_boundaries catalog sources --role changed_assumption_comparison --license CC-BY-4.0 --text --lang ja
python -m materials_boundaries --lang ja catalog --help
```

`--lang` はコマンドの前後どちらにも指定でき、繰り返した場合は最後の指定が優先されます。ヘルプのラベルと説明は翻訳されますが、コマンド構文と ID は正規形式のままです。

`--id` は大文字・小文字を区別する完全一致です。`--query` は空白で分割した各語を Unicode の `casefold` で処理し、すべての語が検索対象の保存フィールドに文字どおりの部分文字列として含まれることを要求します。対象は ID と題名／名称、および出典の著者・DOI・役割、または主張の物理量・方向・`claim_type`・規則 ID・証拠の出典 ID です。v0.4.0–v0.6.0 と v0.8.0 の16件の四言語表示名もリテラル検索の別名です。語幹処理、順位付け、あいまい検索、自動翻訳、ネットワーク検索は行いません。

主張用フィルターは `--direction interval|lower|upper|prediction|relation|constraint`、`--claim-type theoretical_bound|derived_outer_envelope|model_estimate|model_relation|stability_criterion` と、証拠の出典参照に完全一致する `--source-id` です。出典用は `--role`、整数の `--year`、ライセンス識別子またはステータスに完全一致する `--license` です。文字列フィルターは大文字・小文字を区別し、すべての条件を AND で組み合わせ、カタログ順を保持します。空の結果は正常終了（終了コード 0）です。不明な `--id`、無効なフィルター、異なるカタログ種別用のフィルターはエラー（終了コード 2）です。

出典の閲読、数式の照合、ソフトウェアテストの合格は、独立した科学的証明でも内容の再利用許可でもありません。検索での一致は物理的な適用可能性を示さず、ライセンスフィルターは記録済みのメタデータに一致するだけです。独自のコードには MIT ライセンスを適用し、第三者の権利は別に保持します。Python API と出典／主張を追加する際の確認項目は [Catalog reference](CATALOG.md) を参照してください。

## カタログ専用の破壊モデル

v0.3.0 は Griffith／線形弾性破壊力学（LEFM）による臨界遠方引張応力のモデルを二つ追加します。`griffith_central_crack_plane_stress` は平面応力、`griffith_central_crack_plane_strain` は平面ひずみに対応します。どちらも `claim_type: model_estimate`、`direction: prediction`、`bound_kind: null`、`evaluation_support: catalog_only` です。モデルと前提の記録であり、新しい数値評価ではありません。

式は σc = sqrt(E_prime Gc/(πa)) で、平面応力では E_prime = E、平面ひずみでは E_prime = E/(1−ν²) です。E はヤング率（Pa）、Gc は臨界エネルギー解放率（J/m²）、a は中央貫通き裂の全長 2a の半分（m）です。平面ひずみでは無次元のポアソン比 ν も必要です。`parameters` 配列には各記号、物理量、次元、SI 単位、意味を保存します。Gc を自動的に 2γ としてはいけません。新しい二つの表面を作ることだけが散逸となる理想的な完全脆性の場合に限り、Gc = 2γ となります。

均質で等方線形弾性の材料、十分に広い／無限大の板の中央貫通き裂、遠方からのモード I 引張り、十分に小さい降伏域／破壊プロセスゾーンを前提とします。異なるき裂形状や大規模降伏には適用できません。臨界応力は普遍的な引張強さの上界でも設計上の許容応力でもありません。原子スケールのき裂や a → 0 へ連続体の式を外挿してはいけません。

カタログの検索は試験片の前提を立証せず、個別の `satisfied`/`violated`/`unknown` 状態や応力の数値を返しません。前提が不明または不充足なら、この式の使用を正当化できません。`evaluate()` は引き続き schema 1.1.0 の八つの複合材料評価を返します。v0.3.0 では十レコードの主張カタログが schema 1.2.0 となり、当時の v0.4.0 は十五レコードで schema 1.3.0 です。各主張に `claim_type`、`quantity_dimension`、`si_unit`、`evaluation_support` を明示します。

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --direction prediction --text --lang ja
python -m materials_boundaries catalog claims --id griffith_central_crack_plane_strain --json
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --text --lang ja
```

これらの正規コードは四言語で共通であり、検索は表示ラベルを翻訳しません。六つの K/G の上下界は `theoretical_bound`、E/ν は `derived_outer_envelope` です。Griffith への歴史的帰属と現代的な式の照合は別の証拠です。[破壊モデルと証拠](FRACTURE_MODELS.md)、[出典](SOURCES.md)、[v0.3.0 移行ガイド](MIGRATION_v0.3.0.md)を参照してください。v0.3.0 の破壊モデル拡張は論文全文、出版社の PDF、測定データ、再利用許可を追加していません。独自コードは MIT ライセンスですが、独立した科学的査読も未完了です。

## 文献モデルの例

別の[エポキシ／ガラスの例](LITERATURE_EXAMPLE.md)では、公表モデルの E/ν と本プロジェクトで換算した K/G を保存しています。ガラスの体積分率20%、巨視的等方性および完全接合は計算上の仮定であり、試験片の測定結果ではありません。温度と材料の詳細は不明です。

```sh
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --lang ja
```

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang ja
```

```sh
python -m materials_boundaries catalog claims --query porous --direction interval --text --lang ja
```

## 観測を検索する

`catalog observations` も既定では正規 JSON を返し、`--text` で表示言語を選びます。観測の検索対象は ID、名称、`quantity`、`observation_type`、`study_id`、`material.name`、証拠の出典 ID と四言語の編集済み表示名で、同じリテラル全検索語一致です。`--source-id` は主張と観測で共用し、`--quantity` と `--observation-type` (`experiment_derived_model_dependent`, `experiment_derived_tensile_test_summary`) は観測専用で、大文字・小文字を区別して完全一致します。全フィルターは AND で結合し、未対応のカタログ／フィルターの組合せはエラーです。同じ研究 ID の二つの物性記録は一つの研究のままです。

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang ja
```

## 公表された理想せん断予測（v0.12.0）

`catalog predictions --query shimanek_v2_table2_ni_al_co --text --lang ja` で出典確認済みの 3 つの周期モデルを検索し、
`prediction plot --output /tmp/ideal-shear --lang ja` で離散点比較を出力します。
Ni / Ni11Al / Ni11Co：5.13 / 4.58 / 5.46 GPa。同一研究の報告手順に限った
比較であり、市販合金の測定値や普遍的上限ではありません。物理温度、圧力、
磁気状態、不確かさは不明です。0.08 GPa の収束基準は誤差棒ではありません。
[方法、出典、限界](COMPUTATIONAL_PREDICTIONS.md)。
