# はじめに：Materials Boundaries

## 現在の v0.20.0：オフライン観測閲覧ビュー

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

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Bulk elastic waves](BULK_ELASTIC_WAVES.md) · [Release scope](MIGRATION_v0.20.0.md)

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

`catalog observations` も既定では正規 JSON を返し、`--text` で表示言語を選びます。観測の検索対象は ID、名称、`quantity`、`observation_type`、`study_id`、`material.name`、証拠の出典 ID と四言語の編集済み表示名で、同じリテラル全検索語一致です。`--source-id` は主張と観測で共用し、`--quantity` と `--observation-type experiment_derived_model_dependent` は観測専用で、大文字・小文字を区別して完全一致します。全フィルターは AND で結合し、未対応のカタログ／フィルターの組合せはエラーです。同じ研究 ID の二つの物性記録は一つの研究のままです。

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang ja
```

## 公表された理想せん断予測（v0.12.0）

`catalog predictions --text --lang ja` で出典確認済みの 3 つの周期モデルを検索し、
`prediction plot --output /tmp/ideal-shear --lang ja` で離散点比較を出力します。
Ni / Ni11Al / Ni11Co：5.13 / 4.58 / 5.46 GPa。同一研究の報告手順に限った
比較であり、市販合金の測定値や普遍的上限ではありません。物理温度、圧力、
磁気状態、不確かさは不明です。0.08 GPa の収束基準は誤差棒ではありません。
[方法、出典、限界](COMPUTATIONAL_PREDICTIONS.md)。
