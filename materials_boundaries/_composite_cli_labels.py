"""Machine-assisted CLI labels; no scientific or native-language review."""
_LABELS = {
'en': {'command':'Prepare and replay one conditional composite case offline', 'init':'Write an explicit blank case or run terminal intake', 'report':'Export one case with assumptions, evidence and results', 'verify':'Replay a saved bundle with the installed software', 'output':'New file or empty local output directory', 'interactive':'Require terminal prompts and explicit save', 'demo':'Write the original fictitious example (not measured data)', 'bundle':'Saved bundle.json', 'saved':'Saved locally', 'cancelled':'Intake cancelled; no case saved', 'replay':'Software replay matched; does not verify the physical sample or prove a theorem', 'mismatch':'Bundle altered or stale; no migration or overwrite performed'},
'zh': {'command':'离线准备并重放单个有条件复合材料案例', 'init':'写入明确的空白案例或启动终端录入', 'report':'导出单个案例的假设、证据和结果', 'verify':'用已安装软件重放保存的报告包', 'output':'新文件或空的本地输出目录', 'interactive':'要求终端交互并明确确认保存', 'demo':'写入原创虚构示例（非实测数据）', 'bundle':'已保存的 bundle.json', 'saved':'已保存到本地', 'cancelled':'已取消录入；未保存案例', 'replay':'软件重放一致；不核验物理样品，也不证明定理', 'mismatch':'报告包已更改或版本过期；未迁移或覆盖'},
'ja': {'command':'条件付き複合材料の単一ケースをオフラインで準備・再現', 'init':'明示的な空白ケースまたは端末で入力', 'report':'単一ケースの仮定・証拠・結果を出力', 'verify':'インストール済みソフトウェアで保存済みバンドルを再現', 'output':'新しいファイルまたは空のローカル出力ディレクトリ', 'interactive':'端末での入力と明示的な保存を要求', 'demo':'独自の架空例を保存（測定データではない）', 'bundle':'保存済み bundle.json', 'saved':'ローカルに保存しました', 'cancelled':'入力を取り消しました。ケースは未保存です', 'replay':'ソフトウェア再現が一致。物理試料の検証や定理の証明ではありません', 'mismatch':'バンドルが変更または旧版です。移行や上書きは行いません'},
'de': {'command':'Einen bedingten Verbundfall offline vorbereiten und reproduzieren', 'init':'Leeren Fall schreiben oder Terminaleingabe starten', 'report':'Einen Fall mit Annahmen, Belegen und Ergebnissen exportieren', 'verify':'Gespeichertes Paket mit installierter Software reproduzieren', 'output':'Neue Datei oder leeres lokales Ausgabeverzeichnis', 'interactive':'Terminaleingaben und ausdrückliches Speichern verlangen', 'demo':'Eigenes fiktives Beispiel schreiben (keine Messdaten)', 'bundle':'Gespeicherte bundle.json', 'saved':'Lokal gespeichert', 'cancelled':'Eingabe abgebrochen; kein Fall gespeichert', 'replay':'Software-Reproduktion stimmt überein; prüft keine physische Probe und beweist keinen Satz', 'mismatch':'Paket verändert oder veraltet; keine Migration oder Überschreibung'},
}


def labels(lang='en'):
    from .validation import ValidationError
    if lang not in _LABELS:
        raise ValidationError('lang: expected en, zh, ja or de')
    return _LABELS[lang]
