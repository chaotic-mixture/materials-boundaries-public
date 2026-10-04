"""Presentation-only report wording; source records and user text are never translated.

All four columns are machine-assisted and have not had independent scientific or
native-language review. Missing keys have a visible marker, never a blank label.
This module deliberately does not change the existing catalog locale contract.
"""

LANGUAGES = ("en", "zh", "ja", "de")

# One row per key keeps parity visible without English-only implicit fallbacks.
_ROWS = {
    "title": ("Conditional two-phase composite report", "两相复合材料条件性报告", "二相複合材料の条件付きレポート", "Bedingter Bericht zum Zweiphasenverbund"),
    "question": ("Question and case", "问题与算例", "問いとケース", "Fragestellung und Fall"),
    "question_text": ("Which conditional scalar bounds follow from the supplied two-phase inputs and assumptions?", "在所提供的两相输入与假设下，可计算哪些条件性标量界限？", "入力された二相の値と仮定から、どの条件付きスカラー限界が計算できるか。", "Welche bedingten skalaren Schranken folgen aus den angegebenen Zweiphaseneingaben und Annahmen?"),
    "case_id": ("Case ID", "算例 ID", "ケース ID", "Fall-ID"),
    "output_unit": ("Selected output unit", "所选输出单位", "選択された出力単位", "Gewählte Ausgabeeinheit"),
    "input_origin": ("Claimed phase-input provenance", "所声明的相输入来源", "申告された相入力の由来", "Angegebene Herkunft der Phaseneingaben"),
    "note": ("Original user note", "原始用户备注", "元のユーザーメモ", "Ursprüngliche Benutzernotiz"),
    "input_sources": ("User-supplied input citation IDs", "用户提供的输入引用 ID", "ユーザー指定の入力引用 ID", "Vom Benutzer angegebene Quellen-IDs der Eingaben"),
    "states": ("Four separate states", "四类独立状态", "独立した四つの状態", "Vier getrennte Statusangaben"),
    "structure": ("Input structure", "输入结构", "入力構造", "Eingabestruktur"),
    "valid_structure": ("Valid structure; this says nothing about a physical sample", "结构有效；这不说明物理样品是否符合模型", "構造は有効。物理試料についての検証ではありません", "Gültige Struktur; keine Aussage über eine physische Probe"),
    "applicability": ("Rule applicability", "规则适用性", "規則の適用性", "Anwendbarkeit der Regeln"),
    "availability": ("Numerical availability", "数值可用性", "数値の利用可否", "Numerische Verfügbarkeit"),
    "review": ("Scientific review", "科学审查", "科学的レビュー", "Wissenschaftliche Prüfung"),
    "review_state": ("Not independently scientifically reviewed; independent_scientific_review = false", "未经独立科学审查；independent_scientific_review = false", "独立した科学的レビューなし；independent_scientific_review = false", "Keine unabhängige wissenschaftliche Prüfung; independent_scientific_review = false"),
    "satisfied": ("Satisfied under supplied assertions", "在所提供的断言下满足", "入力された申告の範囲で充足", "Unter den angegebenen Annahmen erfüllt"),
    "unknown": ("Unknown: applicability evidence is missing", "未知：缺少适用性证据", "不明：適用性の根拠が不足", "Unbekannt: Nachweis der Anwendbarkeit fehlt"),
    "violated": ("Violated: outside implemented scope", "不满足：超出实现范围", "不適合：実装範囲外", "Verletzt: außerhalb des implementierten Bereichs"),
    "computed": ("Computed, approximate", "已计算，近似值", "計算済み、近似値", "Berechnet, näherungsweise"),
    "not_computed": ("Not computed", "未计算", "未計算", "Nicht berechnet"),
    "numerical_range_error": ("Numerical representation error", "数值表示错误", "数値表現エラー", "Fehler der numerischen Darstellung"),
    "unavailable": ("Unavailable", "不可用", "利用不可", "Nicht verfügbar"),
    "none": ("None", "无", "なし", "Keine"),
    "scope_notice": ("Conditional calculations only. Conditions are supplied assertions; a citation or a measured-input label does not verify isotropy, a specimen, temperature, grade, cure state or uncertainty. Effective outputs are calculations, not measured effective properties or engineering allowables.", "仅为条件性计算。条件是所提供的断言；引用或测量输入标签并不验证各向同性、样品、温度、等级、固化状态或不确定度。有效性质输出是计算结果，不是实测有效性质或工程许用值。", "条件付き計算のみです。条件は入力された申告であり、引用や測定入力の表示は等方性、試料、温度、グレード、硬化状態、不確かさを検証しません。有効特性の出力は計算値であり、実測値や設計許容値ではありません。", "Nur bedingte Berechnungen. Bedingungen sind angegebene Annahmen; ein Zitat oder die Kennzeichnung als Messeingabe verifiziert weder Isotropie, Probe, Temperatur, Güte, Aushärtungszustand noch Unsicherheit. Effektive Ausgaben sind Berechnungen, keine gemessenen effektiven Eigenschaften oder technischen zulässigen Werte."),
    "numerical_notice": ("Approximate binary-float endpoints from 80-digit decimal arithmetic; not certified outward-rounded bounds. A numerical error is separate from applicability. No clipping, zero substitution or silent unit change is applied.", "端点由 80 位十进制运算转换为近似二进制浮点数；并非经过认证的向外舍入界限。数值错误与适用性不同。不裁剪、不以零替代、不静默更改单位。", "80 桁の十進演算から得た近似二進浮動小数点の端点であり、外向き丸めを保証した限界ではありません。数値エラーと適用性は別です。切り詰め、ゼロへの置換、無断の単位変更は行いません。", "Näherungsweise binäre Gleitkomma-Endpunkte aus Dezimalrechnung mit 80 Stellen; keine zertifiziert nach außen gerundeten Schranken. Numerische Fehler sind von der Anwendbarkeit getrennt. Kein Abschneiden, Ersetzen durch Null oder stiller Einheitenwechsel."),
    "joint_notice": ("E and ν are conservative outer envelopes from this case's same two HS intervals. Different corners need not share a realizable microstructure; joint_attainability = not_asserted. No imported endpoints or Reuss/Voigt fallback.", "E 和 ν 是由同一算例的两个 HS 区间构造的保守外包络。不同角点不一定对应同一种可实现微结构；joint_attainability = not_asserted。不使用导入端点或 Reuss/Voigt 替代方案。", "E と ν は、このケースの同じ二つの HS 区間から得る保守的な外包絡です。異なる角点が同じ実現可能な微構造に対応するとは限りません。joint_attainability = not_asserted。外部端点や Reuss/Voigt への代替はありません。", "E und ν sind konservative äußere Hüllen aus denselben zwei HS-Intervallen dieses Falls. Verschiedene Ecken müssen nicht zu einer realisierbaren Mikrostruktur gehören; joint_attainability = not_asserted. Keine importierten Endpunkte und kein Reuss/Voigt-Ersatz."),
    "unknown_notice": ("Unknown means missing applicability evidence, not quantified measurement uncertainty. A known violation dominates the overall applicability state without erasing unknown checks.", "未知表示缺少适用性证据，不表示已量化的测量不确定度。已知不满足条件决定总体适用性状态，但不会删除未知检查项。", "不明は適用性の根拠不足を示し、定量化された測定不確かさではありません。既知の不適合が全体の適用性に優先しますが、不明な項目は残ります。", "Unbekannt bedeutet fehlende Anwendbarkeitsnachweise, keine quantifizierte Messunsicherheit. Eine bekannte Verletzung bestimmt den Gesamtstatus, ohne unbekannte Prüfungen zu entfernen."),
    "translation_notice": ("Machine-assisted wording, including English; not independently scientifically or native-language reviewed. Source titles, source notes and user text retain their original wording. Missing labels are explicitly marked with their key.", "包括英文在内的措辞经过机器辅助；未经独立科学或母语审查。来源标题、来源备注和用户文本保留原文。缺失标签明确标注其键名。", "英語を含め、表現は機械支援によるもので、独立した科学的・母語レビューは未実施です。出典の題名、注記、ユーザーの文章は原文のままです。欠落したラベルにはキー名を明示します。", "Maschinell unterstützte Formulierungen, auch auf Englisch; keine unabhängige wissenschaftliche oder muttersprachliche Prüfung. Quellentitel, Quellenhinweise und Benutzertext bleiben im Original. Fehlende Beschriftungen werden ausdrücklich mit ihrem Schlüssel markiert."),
    "source_notice": ("Formula evidence is separate from phase-input evidence. HS 1963 original equations and proof were not inspected; Reuss has contextual support rather than an inspected original equation. Meille–Garboczi identities were checked in extracted text with visual verification incomplete. E/ν envelopes are a project derivation, not a theorem attributed to that paper.", "公式证据与相输入证据分别列出。未检查 HS 1963 原始方程和证明；Reuss 仅有背景支持，并非检查过的原始方程。Meille–Garboczi 恒等式已检查提取文本，但未完成目视验证。E/ν 外包络是项目推导，不能归为该论文的定理。", "公式の根拠と相入力の根拠は別です。HS 1963 の原式と証明は未確認で、Reuss は原式の確認ではなく文脈上の支持です。Meille–Garboczi の恒等式は抽出テキストで確認しましたが、視覚的検証は未完了です。E/ν 外包絡は本プロジェクトの導出で、その論文の定理ではありません。", "Formelbelege und Belege der Phaseneingaben sind getrennt. Originalgleichungen und Beweis von HS 1963 wurden nicht geprüft; Reuss ist kontextuell belegt, nicht durch eine geprüfte Originalgleichung. Meille–Garboczi-Identitäten wurden im extrahierten Text geprüft, die visuelle Prüfung ist unvollständig. E/ν-Hüllen sind eine Projektableitung, kein jenem Artikel zugeschriebener Satz."),
    "early_blockers": ("Conditions to understand before using numbers", "使用数值前应理解的条件", "数値を使用する前に確認すべき条件", "Vor Verwendung der Zahlen zu beachtende Bedingungen"),
    "no_blockers": ("The implemented checks are satisfied under the supplied assertions. This is not independent evidence of their physical truth.", "实现的检查在所提供的断言下满足。这不是其物理真实性的独立证据。", "実装された確認項目は入力の申告の範囲で満たされています。物理的な真実性の独立した根拠ではありません。", "Die implementierten Prüfungen sind unter den angegebenen Annahmen erfüllt. Das ist kein unabhängiger Nachweis ihrer physikalischen Richtigkeit."),
    "answer": ("Answer: all eight results", "结果：全部八项", "結果：全八項目", "Ergebnis: alle acht Resultate"),
    "quantity_k": ("K · Effective bulk modulus", "K · 有效体积模量", "K · 有効体積弾性率", "K · Effektiver Kompressionsmodul"),
    "quantity_g": ("G · Effective shear modulus", "G · 有效剪切模量", "G · 有効せん断弾性率", "G · Effektiver Schubmodul"),
    "quantity_e": ("E · Effective Young modulus", "E · 有效杨氏模量", "E · 有効ヤング率", "E · Effektiver Elastizitätsmodul"),
    "quantity_nu": ("ν · Effective Poisson ratio", "ν · 有效泊松比", "ν · 有効ポアソン比", "ν · Effektive Poissonzahl"),
    "hs_bulk_3d_two_phase": ("HS bulk interval", "HS 体积模量区间", "HS 体積弾性率区間", "HS-Kompressionsmodulintervall"),
    "reuss_bulk": ("Reuss bulk lower endpoint", "Reuss 体积模量下界", "Reuss 体積弾性率下限", "Untere Reuss-Kompressionsmodulschranke"),
    "voigt_bulk": ("Voigt bulk upper endpoint", "Voigt 体积模量上界", "Voigt 体積弾性率上限", "Obere Voigt-Kompressionsmodulschranke"),
    "hs_shear_3d_two_phase": ("HS shear interval", "HS 剪切模量区间", "HS せん断弾性率区間", "HS-Schubmodulintervall"),
    "reuss_shear": ("Reuss shear lower endpoint", "Reuss 剪切模量下界", "Reuss せん断弾性率下限", "Untere Reuss-Schubmodulschranke"),
    "voigt_shear": ("Voigt shear upper endpoint", "Voigt 剪切模量上界", "Voigt せん断弾性率上限", "Obere Voigt-Schubmodulschranke"),
    "youngs_modulus_outer": ("Young modulus derived outer envelope", "杨氏模量推导外包络", "ヤング率の導出外包絡", "Abgeleitete äußere Hülle des Elastizitätsmoduls"),
    "poissons_ratio_outer": ("Poisson ratio derived outer envelope", "泊松比推导外包络", "ポアソン比の導出外包絡", "Abgeleitete äußere Hülle der Poissonzahl"),
    "direction": ("Direction", "界限方向", "限界の方向", "Richtung"),
    "interval": ("Interval", "区间", "区間", "Intervall"),
    "lower": ("One-sided lower bound", "单侧下界", "片側下限", "Einseitige untere Schranke"),
    "upper": ("One-sided upper bound", "单侧上界", "片側上限", "Einseitige obere Schranke"),
    "scalar_modulus_bound": ("Conditional theoretical bound", "条件性理论界限", "条件付き理論限界", "Bedingte theoretische Schranke"),
    "derived_outer_envelope": ("Conservative derived outer envelope", "保守推导外包络", "保守的な導出外包絡", "Konservative abgeleitete äußere Hülle"),
    "collapsed": ("Displayed endpoints coincide at output precision; no exact physical response is established", "显示的端点在输出精度下重合；这不确立精确的物理响应", "表示された端点は出力精度の範囲で一致しますが、厳密な物理応答が確立されたわけではありません", "Die angezeigten Endpunkte fallen bei der Ausgabepräzision zusammen; eine exakte physikalische Antwort ist damit nicht nachgewiesen"),
    "primary_reason": ("Primary reason", "主要原因", "主な理由", "Hauptgrund"),
    "all_blockers": ("All unknown and violated checks", "全部未知与不满足检查项", "不明・不適合の全確認項目", "Alle unbekannten und verletzten Prüfbedingungen"),
    "ordering_display": ("Where available: Reuss lower ≤ HS lower ≤ HS upper ≤ Voigt upper. These endpoints are not asserted to be jointly attainable.", "若可用：Reuss 下界 ≤ HS 下界 ≤ HS 上界 ≤ Voigt 上界。不声明这些端点可同时达到。", "利用可能な場合：Reuss 下限 ≤ HS 下限 ≤ HS 上限 ≤ Voigt 上限。各端点の同時達成は主張しません。", "Soweit verfügbar: Reuss unten ≤ HS unten ≤ HS oben ≤ Voigt oben. Die gemeinsame Erreichbarkeit dieser Endpunkte wird nicht behauptet."),
    "ledger": ("Assumption ledger", "假设清单", "仮定一覧", "Annahmenübersicht"),
    "observed": ("Supplied / observed", "提供值／观测值", "入力値・観測値", "Angegeben / beobachtet"),
    "required": ("Required by this implementation", "本实现所需值", "この実装での要件", "Von dieser Implementierung gefordert"),
    "basis": ("Basis", "依据", "根拠", "Grundlage"),
    "supplied_assertion": ("Supplied assertion, not specimen evidence", "所提供的断言，不是样品证据", "入力された申告であり、試料の根拠ではない", "Angegebene Annahme, kein Probennachweis"),
    "source_model": ("Source model, not specimen verification", "来源模型，不是样品验证", "出典モデルであり、試料検証ではない", "Quellenmodell, keine Probenprüfung"),
    "calculator_assumption": ("Calculator assumption", "计算器假设", "計算上の仮定", "Rechnerannahme"),
    "calculator_choice": ("Calculator-chosen fractions", "计算器选择的体积分数", "計算用に選択した分率", "Für die Berechnung gewählte Anteile"),
    "numerical_check": ("Check of supplied values, not physical verification", "检查提供值，不验证物理真实性", "入力値の確認であり、物理的検証ではない", "Prüfung angegebener Werte, keine physikalische Verifikation"),
    "same_case": ("Same-case computed dependency", "同一算例的计算依赖", "同一ケースの計算依存関係", "Berechnungsabhängigkeit desselben Falls"),
    "next": ("What to supply or change next", "下一步应补充或调整什么", "次に補う情報・検討すべき変更", "Als Nächstes zu ergänzen oder zu prüfen"),
    "next_unknown": ("Supply evidence or an explicitly hypothetical assumption for missing conditions, and known values for missing inputs. Preserve unknowns until then; do not infer a missing fraction or convert mass fractions without density.", "对缺失条件补充证据或明确的假想假设，并提供缺失输入值。在此之前保留未知；不要推断缺失分数，也不要在没有密度时换算质量分数。", "不足している条件には根拠または明示的な仮想仮定を、不足している入力には既知の値を補ってください。それまでは不明を保ち、欠けた分率の推定や密度なしの質量分率変換をしないでください。", "Ergänzen Sie Belege oder ausdrücklich hypothetische Annahmen für fehlende Bedingungen und bekannte Werte für fehlende Eingaben. Bis dahin unbekannt lassen; fehlende Anteile nicht ableiten und Massenanteile nicht ohne Dichte umrechnen."),
    "next_violated": ("Known violated conditions describe an unsupported regime. Do not relabel a true physical condition merely to obtain a number; supplying missing values alone will not remove an existing violation.", "已知不满足条件说明处于不支持的范围。不要为了获得数值而更改真实物理条件的标签；仅补充缺失值不会消除已有的不满足条件。", "既知の不適合は非対応の領域を示します。数値を得るためだけに真の物理条件を書き換えないでください。不足値を補うだけでは既存の不適合は解消しません。", "Bekannte Verletzungen beschreiben einen nicht unterstützten Bereich. Echte physikalische Bedingungen nicht nur für ein Ergebnis umbenennen; fehlende Werte allein beseitigen bestehende Verletzungen nicht."),
    "next_numeric": ("A different representable output unit may help after re-evaluation, but recovery of every dependent result is not guaranteed. A boundary-rounded ν is unavailable rather than clipped.", "重新计算时选择可表示的其他输出单位可能有帮助，但不保证每个依赖结果都能恢复。舍入到边界的 ν 不可用，不作裁剪。", "再評価で表現可能な別の単位を選ぶと改善する場合がありますが、全依存結果の回復は保証されません。境界に丸められた ν は切り詰めず、利用不可とします。", "Eine andere darstellbare Ausgabeeinheit kann nach erneuter Auswertung helfen, garantiert aber nicht die Verfügbarkeit aller abhängigen Ergebnisse. Auf eine Grenze gerundetes ν bleibt unverfügbar und wird nicht abgeschnitten."),
    "next_satisfied": ("To interpret this as a material comparison, independently establish the premises, phase inputs and measurement context. This report does not choose a material or a microstructure.", "若要解释为材料比较，需独立建立前提、相输入及测量背景。本报告不选择材料或微结构。", "材料比較として解釈するには、前提、相入力、測定条件を独立に確認してください。このレポートは材料や微構造を選びません。", "Für einen Materialvergleich müssen Voraussetzungen, Phaseneingaben und Messkontext unabhängig belegt werden. Dieser Bericht wählt kein Material und keine Mikrostruktur aus."),
    "trace": ("Derivation trace", "推导轨迹", "導出経路", "Ableitungsweg"),
    "phase_inputs": ("Supplied phase K/G inputs", "提供的相 K/G 输入", "入力された相の K/G", "Angegebene K/G-Phaseneingaben"),
    "converted_inputs": ("Project-converted constituent K/G inputs", "项目换算的组分 K/G 输入", "プロジェクトで換算した構成相 K/G 入力", "Projektseitig umgerechnete K/G-Eingaben der Bestandteile"),
    "raw_parameters": ("Raw constituent model E/ν parameters (not effective outputs)", "原始组分模型 E/ν 参数（不是有效输出）", "構成相モデルの生 E/ν パラメータ（有効特性の出力ではない）", "Ursprüngliche E/ν-Modellparameter der Bestandteile (keine effektiven Ausgaben)"),
    "original_fraction": ("Original supplied volume fraction", "原始提供的体积分数", "元の入力体積分率", "Ursprünglich angegebener Volumenanteil"),
    "normalized_fraction": ("Normalized volume fraction", "归一化体积分数", "正規化体積分率", "Normierter Volumenanteil"),
    "normalization": ("Fraction normalization record", "分数归一化记录", "分率の正規化記録", "Protokoll der Anteilsnormierung"),
    "normalization_notice": ("Original fractions are preserved. The absolute 1e-12 sum tolerance is numerical bookkeeping, not experimental uncertainty. Exactly zero is inactive; every positive fraction remains active, however small.", "保留原始分数。分数和的绝对容差 1e-12 是数值记账规则，不是实验不确定度。只有精确为零才是不活跃相；任何正分数，无论多小，都是活跃相。", "元の分率は保存されます。合計の絶対許容差 1e-12 は数値処理の規則であり、実験の不確かさではありません。厳密なゼロのみが非活性で、正の分率はどれほど小さくても活性です。", "Ursprüngliche Anteile bleiben erhalten. Die absolute Summentoleranz 1e-12 dient der numerischen Verarbeitung, nicht der experimentellen Unsicherheit. Nur exakt Null ist inaktiv; jeder positive Anteil bleibt aktiv, auch wenn er sehr klein ist."),
    "conversion_notice": ("Raw units are preserved; canonical Pa conversion uses exact powers of ten: Pa=1, kPa=1000, MPa=1000000, GPa=1000000000. Phase IDs, K, G and fractions stay paired; K and G are never sorted independently.", "保留原始单位；规范 Pa 换算使用精确的十次幂：Pa=1、kPa=1000、MPa=1000000、GPa=1000000000。相 ID、K、G 和分数保持配对；绝不单独对 K 与 G 排序。", "元の単位は保存され、Pa への換算は正確な十の累乗を使います：Pa=1、kPa=1000、MPa=1000000、GPa=1000000000。相 ID、K、G、分率の対応は保持され、K と G を別々に並べ替えません。", "Originaleinheiten bleiben erhalten; die Umrechnung in Pa nutzt exakte Zehnerpotenzen: Pa=1, kPa=1000, MPa=1000000, GPa=1000000000. Phasen-IDs, K, G und Anteile bleiben gekoppelt; K und G werden nie unabhängig sortiert."),
    "canonical_pa": ("Canonical value in Pa", "Pa 规范值", "Pa での正規値", "Kanonischer Wert in Pa"),
    "dependency": ("Same-case dependency record", "同一算例的依赖记录", "同一ケースの依存記録", "Abhängigkeitsprotokoll desselben Falls"),
    "corner_notice": ("E uses lower K/lower G and upper K/upper G. ν uses lower K/upper G and upper K/lower G. Each dependency names this same instance and the paired HS bulk/shear claim IDs.", "E 使用 K 下界/G 下界和 K 上界/G 上界。ν 使用 K 下界/G 上界和 K 上界/G 下界。每项依赖均注明同一算例及配对 HS 体积/剪切声明 ID。", "E は K 下限/G 下限と K 上限/G 上限を使用します。ν は K 下限/G 上限と K 上限/G 下限を使用します。各依存関係には同じケースと対応する HS 体積・せん断の claim ID が記録されています。", "E verwendet unteres K/unteres G und oberes K/oberes G. ν verwendet unteres K/oberes G und oberes K/unteres G. Jede Abhängigkeit nennt denselben Fall und die gekoppelten HS-Kompressions-/Schub-Claim-IDs."),
    "evidence": ("Evidence and limits", "证据与限制", "根拠と限界", "Belege und Grenzen"),
    "formula_evidence": ("Formula claim records: exact evidence, review gaps and limits", "公式声明记录：精确证据、审查缺口与限制", "公式 claim 記録：根拠、レビューの不足、限界の原文", "Formel-Claim-Datensätze: genaue Belege, Prüflücken und Grenzen"),
    "phase_evidence": ("Phase-input evidence and context", "相输入证据与背景", "相入力の根拠と背景", "Belege und Kontext der Phaseneingaben"),
    "model_distinction": ("Raw constituent E/ν, project-converted constituent K/G, calculator-chosen fractions and calculated effective-composite E/ν are different records. Unknown temperature, grade, cure state and measurement uncertainty remain unknown.", "原始组分 E/ν、项目换算的组分 K/G、计算器选择的分数和计算得到的复合材料有效 E/ν 是不同记录。未知温度、等级、固化状态和测量不确定度仍为未知。", "構成相の生 E/ν、プロジェクト換算の構成相 K/G、計算用分率、計算された複合材の有効 E/ν は別の記録です。不明な温度、グレード、硬化状態、測定不確かさは不明のままです。", "Ursprüngliches E/ν der Bestandteile, projektseitig umgerechnetes K/G, gewählte Anteile und berechnetes effektives E/ν des Verbunds sind unterschiedliche Datensätze. Unbekannte Temperatur, Güte, Aushärtung und Messunsicherheit bleiben unbekannt."),
    "context_unknown": ("Temperature, material grade, cure state and measurement uncertainty are not established by this instance contract.", "本算例契约未确立温度、材料等级、固化状态或测量不确定度。", "この入力形式では温度、材料グレード、硬化状態、測定不確かさは確立されません。", "Temperatur, Materialgüte, Aushärtungszustand und Messunsicherheit werden durch diesen Fallvertrag nicht festgestellt."),
    "sources": ("Referenced source records (original wording)", "引用来源记录（原文）", "参照出典の記録（原文）", "Referenzierte Quelldatensätze (Originalwortlaut)"),
    "unresolved": ("Unresolved source IDs: unverified user citations", "未解析来源 ID：未经验证的用户引用", "未解決の出典 ID：未検証のユーザー引用", "Nicht aufgelöste Quellen-IDs: ungeprüfte Benutzerzitate"),
    "citation_notice": ("Input source IDs are joined only to the bundled catalog. Unknown IDs stay unresolved; no DOI, URL, credibility or measurement status is inferred. Bibliographic URLs are inert text, including unsafe protocols.", "输入来源 ID 仅与内置目录匹配。未知 ID 保持未解析；不推断 DOI、URL、可信度或测量状态。书目 URL 均为不可点击文本，包括不安全协议。", "入力出典 ID は同梱カタログとのみ照合します。不明な ID は未解決のままで、DOI、URL、信頼性、測定状態を推定しません。危険なプロトコルを含め、文献 URL は動作しない文字列です。", "Quellen-IDs werden nur mit dem mitgelieferten Katalog abgeglichen. Unbekannte IDs bleiben ungelöst; DOI, URL, Glaubwürdigkeit oder Messstatus werden nicht abgeleitet. Bibliografische URLs sind inaktiver Text, auch bei unsicheren Protokollen."),
    "comparison_notice": ("These are not confidence intervals or predictive distributions. An experimental value inside an envelope does not validate a model; a value outside does not automatically refute a theorem. Check definitions, units, constituent inputs, fractions, premises, uncertainty and numerical policy. This workflow has no measured-composite comparison API.", "这些不是置信区间或预测分布。实验值落在包络内不验证模型；落在包络外也不自动反驳定理。需检查定义、单位、组分输入、分数、前提、不确定度及数值策略。本流程没有实测复合材料比较 API。", "信頼区間や予測分布ではありません。実験値が包絡内でもモデルの検証にはならず、外でも自動的に定理を反証しません。定義、単位、構成相入力、分率、前提、不確かさ、数値方針を確認してください。実測複合材の比較 API はありません。", "Dies sind keine Konfidenzintervalle oder Vorhersageverteilungen. Ein Versuchswert innerhalb einer Hülle validiert kein Modell; ein Wert außerhalb widerlegt nicht automatisch einen Satz. Definitionen, Einheiten, Bestandteile, Anteile, Voraussetzungen, Unsicherheit und numerische Regeln prüfen. Dieser Ablauf hat keine API für den Vergleich gemessener Verbunde."),
    "rights_notice": ("Only bibliographic metadata and original project curation notes are included. No source PDFs, figures or article prose are bundled. Project software/curation licensing does not relicense publications or certify reuse permission. Saving locally is not sharing or publication.", "仅包含书目元数据与项目原创整理备注。不附带来源 PDF、图像或文章原文。项目软件／整理许可不会为出版物重新授权，也不证明再利用许可。本地保存不等于分享或发表。", "含まれるのは書誌情報と本プロジェクト独自の整理メモのみです。出典 PDF、図、論文本文は同梱しません。ソフトウェア・整理情報のライセンスは出版物の再許諾や再利用許可を証明しません。ローカル保存は共有や公開ではありません。", "Enthalten sind nur bibliografische Metadaten und eigene Projektanmerkungen. Keine Quellen-PDFs, Abbildungen oder Artikeltexte werden mitgeliefert. Die Projektlizenz lizenziert Publikationen nicht neu und bestätigt keine Wiederverwendungsrechte. Lokales Speichern ist weder Teilen noch Veröffentlichen."),
    "policy": ("Machine-readable policy record", "机器可读策略记录", "機械可読の方針記録", "Maschinenlesbarer Richtliniendatensatz"),
    "reproduce": ("Reproduce", "复现", "再現", "Reproduzieren"),
    "replay_notice": ("software replay only; does not verify the physical sample or prove a theorem", "仅为软件重放；不验证物理样品，也不证明定理", "ソフトウェアの再実行のみ。物理試料の検証や定理の証明ではありません", "Nur Software-Reproduktion; verifiziert weder die physische Probe noch beweist sie einen Satz"),
    "hash_notice": ("Content hashes establish identity, not authorship, truth or permissions. A replacement of the entire bundle can be internally consistent. Bundle replay and exact exported-file integrity are separate checks.", "内容哈希证明内容一致性，不证明作者、真实性或许可。整个包被替换后仍可能内部一致。包重放与导出文件精确完整性是不同检查。", "内容ハッシュは同一性を示し、著作者、真実性、権利は証明しません。バンドル全体の置換でも内部整合性は保てます。バンドルの再実行と出力ファイルのバイト整合性は別の確認です。", "Inhaltshashes belegen Identität, nicht Urheberschaft, Wahrheit oder Berechtigungen. Ein vollständig ersetztes Bündel kann intern konsistent sein. Bündelreproduktion und exakte Integrität der exportierten Dateien sind getrennte Prüfungen."),
    "relative_command": ("Run from the exported report directory (relative filenames only)", "从导出报告目录运行（仅使用相对文件名）", "出力レポートのディレクトリから実行（相対ファイル名のみ）", "Im exportierten Berichtsverzeichnis ausführen (nur relative Dateinamen)"),
}

_CONDITIONS = {
    "dimension": ("3D scalar elastic identities are implemented; no 2D/thickness conversion is inferred.", "实现的是三维标量弹性恒等式；不推断二维／厚度换算。", "3D スカラー弾性恒等式を実装し、2D・厚さ換算は推定しません。", "Implementiert sind skalare 3D-Elastizitätsidentitäten; keine abgeleitete 2D-/Dickenumrechnung."),
    "constituent_symmetry": ("Each constituent must be isotropic; effective isotropy alone does not establish this.", "每个组分必须各向同性；仅有有效各向同性不能确立这一点。", "各構成相の等方性が必要で、有効等方性だけでは成立しません。", "Jeder Bestandteil muss isotrop sein; effektive Isotropie allein belegt dies nicht."),
    "effective_symmetry": ("The effective composite must be isotropic; isotropic constituents do not establish effective isotropy.", "有效复合材料必须各向同性；组分各向同性并不能确立有效各向同性。", "複合材の有効等方性が必要です。構成相が等方的でも、有効等方性は成立しません。", "Der effektive Verbund muss isotrop sein; isotrope Bestandteile belegen keine effektive Isotropie."),
    "kinematics": ("Only small-strain kinematics are implemented; finite strain is unsupported.", "仅实现小应变运动学；不支持有限应变。", "微小ひずみのみ実装し、有限ひずみには非対応です。", "Nur kleine Verzerrungen sind implementiert; endliche Verzerrungen werden nicht unterstützt."),
    "constitutive_law": ("Only linear elasticity is implemented; no viscoelastic, plastic or failure model is executed.", "仅实现线性弹性；不执行黏弹性、塑性或失效模型。", "線形弾性のみ実装し、粘弾性、塑性、破壊モデルは実行しません。", "Nur lineare Elastizität ist implementiert; keine viskoelastischen, plastischen oder Versagensmodelle."),
    "loading": ("Only static loading is supported; dynamic loading is a different regime.", "仅支持静态载荷；动态载荷属于不同范围。", "静的荷重のみ対応し、動的荷重は別の領域です。", "Nur statische Belastung wird unterstützt; dynamische Belastung gehört zu einem anderen Bereich."),
    "interface": ("Perfect bonding is required; imperfect interfaces are not modeled.", "需要完美结合；不建模非完美界面。", "完全接合が必要で、不完全な界面はモデル化しません。", "Perfekte Bindung ist erforderlich; unvollkommene Grenzflächen werden nicht modelliert."),
    "two_phase_description": ("Exactly two declared phase records are required, even when one has zero volume; no phase merging is inferred.", "即使其中一相体积为零，也需恰好两条相记录；不推断相合并。", "一方の体積がゼロでも二つの相記録が必要です。相の統合は推定しません。", "Genau zwei deklarierte Phasendatensätze sind erforderlich, auch bei einem Nullanteil; keine Phasenzusammenfassung."),
    "volume_fractions_known": ("Both volume fractions must be supplied. Do not complement a missing fraction or convert mass fractions without density.", "必须提供两个体积分数。不要补足缺失分数，也不要在缺少密度时换算质量分数。", "両方の体積分率を入力してください。欠けた分率の補完や密度なしの質量分率変換はしません。", "Beide Volumenanteile müssen angegeben werden. Fehlende Anteile nicht ergänzen und Massenanteile nicht ohne Dichte umrechnen."),
    "positive_bulk_moduli": ("Every active phase needs known, strictly positive K and G in all six base rules, including bulk-only Reuss/Voigt. This conservative runtime restriction is not a universal theorem limitation; no void/negative-stiffness fallback is implemented.", "全部六条基础规则均要求每个活跃相的 K 和 G 已知且严格为正，包括仅涉及体积模量的 Reuss/Voigt。这是保守的实现限制，不是普遍定理限制；不实现空隙／负刚度替代方案。", "体積のみの Reuss/Voigt を含む全六基本規則で、各活性相に既知で厳密に正の K と G が必要です。この保守的な実装制限は定理の普遍的制限ではなく、空隙・負剛性の代替計算はありません。", "Alle sechs Grundregeln, auch Reuss/Voigt für K allein, benötigen bekanntes, strikt positives K und G jeder aktiven Phase. Diese konservative Implementierungsgrenze ist keine universelle Theoremgrenze; kein Ersatz für Poren oder negative Steifigkeit."),
    "positive_shear_moduli": ("Known positive G is required even for Reuss/Voigt bulk in this runtime. Exactly zero volume is inactive; a tiny positive phase with missing G is still unknown.", "本实现即使对 Reuss/Voigt 体积模量也要求 G 已知且为正。精确零体积才是不活跃；极小正分数相若缺少 G 仍为未知。", "この実装では Reuss/Voigt の体積弾性率にも既知の正の G が必要です。厳密なゼロ体積のみが非活性で、微小な正の相でも G が欠ければ不明です。", "Diese Implementierung fordert bekanntes positives G auch für Reuss/Voigt-K. Nur exakt Nullvolumen ist inaktiv; bei kleinem positivem Anteil bleibt fehlendes G unbekannt."),
    "well_ordered_phases": ("HS needs paired non-strict K/G ordering. Crossed ordering blocks HS and E/ν, while valid Reuss/Voigt rows remain available; never independently sort K and G.", "HS 需要配对的非严格 K/G 排序。交叉排序阻止 HS 和 E/ν，但有效 Reuss/Voigt 行仍可用；绝不单独对 K 与 G 排序。", "HS には対応を保った非厳密 K/G 順序が必要です。交差順序では HS と E/ν が使えませんが、有効な Reuss/Voigt は残ります。K と G を別々に並べ替えません。", "HS erfordert gekoppelte nichtstrenge K/G-Ordnung. Gekreuzte Ordnung blockiert HS und E/ν, während gültige Reuss/Voigt-Zeilen verfügbar bleiben; K und G nie unabhängig sortieren."),
    "compatible_bulk_shear_bounds": ("Both computed HS intervals must belong to this same instance, phases, fractions, units and conditions. Numerical unavailability of either dependency blocks derived output even when applicability is satisfied.", "两个已计算 HS 区间必须来自相同算例、相、分数、单位和条件。即使适用性满足，只要任一依赖数值不可用，就不能给出推导结果。", "計算された両 HS 区間は同じケース、相、分率、単位、条件に属する必要があります。適用性が満たされても、一方の依存数値が利用不可なら導出結果は使えません。", "Beide berechneten HS-Intervalle müssen zum selben Fall, denselben Phasen, Anteilen, Einheiten und Bedingungen gehören. Ist ein Abhängigkeitsergebnis numerisch unverfügbar, bleibt die abgeleitete Ausgabe trotz erfüllter Anwendbarkeit gesperrt."),
}
_ROWS.update({"condition_" + key: values for key, values in _CONDITIONS.items()})
_ROWS.update({
    "full_records": ("Complete original records (JSON; optional audit detail)", "完整原始记录（JSON；可选审计详情）", "完全な元記録（JSON・任意の監査詳細）", "Vollständige Originaldatensätze (JSON; optionale Prüfdetails)"),
    "compact_legend": ("Status key", "状态说明", "状態の凡例", "Statuslegende"),
    "paired_input_check": ("See paired phase K/G above (stored observed=null)", "见上方配对的相 K/G（原始 observed=null）", "上記の対応する相 K/G を参照（保存値 observed=null）", "Siehe gekoppelte Phasenwerte K/G oben (gespeichert observed=null)"),
    "ledger_columns": ("Condition | supplied / observed | required | state | basis", "条件 | 提供值／观测值 | 要求 | 状态 | 依据", "条件 | 入力・観測値 | 要件 | 状態 | 根拠", "Bedingung | angegeben / beobachtet | gefordert | Status | Grundlage"),
    "check_explanations": ("Why these checks matter", "这些条件为何重要", "確認項目の意味", "Bedeutung der Prüfungen"),
    "review_gaps": ("Unresolved scientific review gaps (original wording, listed once)", "未解决的科学审查缺口（原文，各列一次）", "未解決の科学的レビュー不足（原文・重複なし）", "Offene wissenschaftliche Prüflücken (Originalwortlaut, jeweils einmal)"),
    "shared_limits": ("Shared scope limits (original wording, listed once)", "共同范围限制（原文，各列一次）", "共通の適用範囲の限界（原文・重複なし）", "Gemeinsame Geltungsgrenzen (Originalwortlaut, jeweils einmal)"),
    "record_guide": ("Complete input, evaluation, claim, source and policy records are preserved in bundle.json; HTML also includes a closed optional audit section. The visible report consolidates repeated facts without upgrading review status.", "完整输入、评估、声明、来源和策略记录保存在 bundle.json；HTML 另有默认折叠的可选审计区。正文合并重复信息，不提升审查状态。", "入力、評価、claim、出典、方針の完全な記録は bundle.json に保存され、HTML にも初期状態で閉じた監査欄があります。本文では重複をまとめていますが、レビュー状態は引き上げません。", "Vollständige Eingabe-, Auswertungs-, Claim-, Quellen- und Richtliniendatensätze stehen in bundle.json; HTML enthält zusätzlich einen anfangs geschlossenen Prüfbereich. Der sichtbare Bericht bündelt Wiederholungen ohne Aufwertung des Prüfstatus."),
    "fraction_summary": ("Original → normalized volume fractions", "原始 → 归一化体积分数", "元の体積分率 → 正規化体積分率", "Ursprüngliche → normierte Volumenanteile"),
    "numerical_error_detail": ("Numerical error details (original engine wording)", "数值错误详情（引擎原文）", "数値エラーの詳細（元のエンジン文言）", "Numerische Fehlerdetails (Originalwortlaut der Engine)"),
    "basis_legend": ("Basis key", "依据说明", "根拠の凡例", "Grundlagenlegende"),
    "source_metadata": ("Source inspection / rights", "来源检查／权利", "出典の確認・権利", "Quellenprüfung / Rechte"),
})
# Compact ledger terminology. Canonical identifiers are retained next to these
# labels; only known routine enum values are translated, never arbitrary input.
_CONDITION_NAMES = {
    "dimension": ("Dimension", "空间维数", "空間次元", "Raumdimension"),
    "constituent_symmetry": ("Constituent symmetry", "组分对称性", "構成相の対称性", "Symmetrie der Bestandteile"),
    "effective_symmetry": ("Effective material symmetry", "有效材料对称性", "有効材料の対称性", "Effektive Materialsymmetrie"),
    "kinematics": ("Strain regime", "应变范围", "ひずみ領域", "Verzerrungsbereich"),
    "constitutive_law": ("Constitutive law", "本构关系", "構成則", "Stoffgesetz"),
    "loading": ("Loading", "载荷类型", "荷重条件", "Belastung"),
    "interface": ("Interface", "界面条件", "界面条件", "Grenzfläche"),
    "two_phase_description": ("Two phase records", "两相记录", "二相の記録", "Zwei Phasendatensätze"),
    "volume_fractions_known": ("Known volume fractions", "体积分数已知", "既知の体積分率", "Bekannte Volumenanteile"),
    "positive_bulk_moduli": ("Positive active-phase K", "活跃相 K 为正", "活性相の正の K", "Positives K aktiver Phasen"),
    "positive_shear_moduli": ("Positive active-phase G", "活跃相 G 为正", "活性相の正の G", "Positives G aktiver Phasen"),
    "well_ordered_phases": ("Paired K/G ordering", "配对 K/G 排序", "対応を保った K/G 順序", "Gekoppelte K/G-Ordnung"),
    "compatible_bulk_shear_bounds": ("Compatible same-case HS bounds", "同一算例的兼容 HS 界限", "同一ケースの整合する HS 限界", "Kompatible HS-Schranken desselben Falls"),
}
_VALUES = {
    "isotropic": ("Isotropic", "各向同性", "等方性", "Isotrop"),
    "anisotropic": ("Anisotropic", "各向异性", "異方性", "Anisotrop"),
    "small_strain": ("Small strain", "小应变", "微小ひずみ", "Kleine Verzerrungen"),
    "finite_strain": ("Finite strain", "有限应变", "有限ひずみ", "Endliche Verzerrungen"),
    "linear_elastic": ("Linear elastic", "线性弹性", "線形弾性", "Linear elastisch"),
    "viscoelastic": ("Viscoelastic", "黏弹性", "粘弾性", "Viskoelastisch"),
    "static": ("Static", "静态", "静的", "Statisch"),
    "dynamic": ("Dynamic", "动态", "動的", "Dynamisch"),
    "perfectly_bonded": ("Perfectly bonded", "完美结合", "完全接合", "Perfekt gebunden"),
    "imperfect": ("Imperfect", "非完美", "不完全", "Unvollkommen"),
    "null": ("Unknown", "未知", "不明", "Unbekannt"),
}
_STATES = {
    "satisfied": ("Satisfied", "满足", "充足", "Erfüllt"),
    "unknown": ("Unknown", "未知", "不明", "Unbekannt"),
    "violated": ("Violated", "不满足", "不適合", "Verletzt"),
    "computed": ("Approximate", "近似已计算", "近似・計算済み", "Näherungsweise berechnet"),
    "not_computed": ("Not computed", "未计算", "未計算", "Nicht berechnet"),
    "numerical_range_error": ("Representation error", "表示错误", "表現エラー", "Darstellungsfehler"),
}
_BASES = {
    "supplied_assertion": ("Supplied assertion", "提供的断言", "入力された申告", "Angegebene Annahme"),
    "source_model": ("Source model", "来源模型", "出典モデル", "Quellenmodell"),
    "calculator_assumption": ("Calculator assumption", "计算器假设", "計算上の仮定", "Rechnerannahme"),
    "unknown": ("Unknown basis", "依据未知", "根拠不明", "Unbekannte Grundlage"),
    "numerical_check": ("Numerical input check", "输入数值检查", "入力数値の確認", "Numerische Eingabeprüfung"),
    "same_case": ("Same-case dependency", "同一算例依赖", "同一ケースの依存関係", "Abhängigkeit desselben Falls"),
}
_REQUIRED = {
    "volume_fractions_known": ("Both known; sum to 1", "两者已知；总和为 1", "両方既知・合計 1", "Beide bekannt; Summe 1"),
    "positive_bulk_moduli": ("Known K > 0 for every active phase", "每个活跃相的 K 已知且 > 0", "全活性相で既知の K > 0", "Bekanntes K > 0 jeder aktiven Phase"),
    "positive_shear_moduli": ("Known G > 0 for every active phase", "每个活跃相的 G 已知且 > 0", "全活性相で既知の G > 0", "Bekanntes G > 0 jeder aktiven Phase"),
    "well_ordered_phases": ("(K1-K2)*(G1-G2) >= 0; equality/pure-phase limits included", "(K1-K2)*(G1-G2) >= 0；包含相等／纯相极限", "(K1-K2)*(G1-G2) >= 0・等値／純相極限を含む", "(K1-K2)*(G1-G2) >= 0; Gleichheit/Reinphasengrenzen eingeschlossen"),
    "compatible_bulk_shear_bounds": ("Same phases, fractions, units and conditions", "相、分数、单位和条件均相同", "相・分率・単位・条件が同一", "Dieselben Phasen, Anteile, Einheiten und Bedingungen"),
}
_ROWS.update({"condition_name_" + key: values for key, values in _CONDITION_NAMES.items()})
_ROWS.update({"value_" + key: values for key, values in _VALUES.items()})
_ROWS.update({"state_" + key: values for key, values in _STATES.items()})
_ROWS.update({"basis_" + key: values for key, values in _BASES.items()})
_ROWS.update({"required_" + key: values for key, values in _REQUIRED.items()})
LABELS = {lang: {key: values[index] for key, values in _ROWS.items()}
          for index, lang in enumerate(LANGUAGES)}


def label(key: str, lang: str = "en") -> str:
    """Return a local label or an explicit missing marker; reject bad languages."""
    if lang not in LANGUAGES:
        raise ValueError("lang: expected en, zh, ja or de")
    return LABELS[lang].get(key, "[missing:" + key + "]")
