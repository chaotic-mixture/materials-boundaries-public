# Erste Schritte: Materials Boundaries

## Aktuell v0.23.0: explizites PA12-CF15-Temperaturdiagramm

Der neue separate Weg zeigt **alle sechs zugelassenen Tabelle-3-Zellen eines
quellenberichteten gemeinsamen Protokolls**. Dies ist eine beschreibende
Transkription veröffentlichter Zusammenfassungen, keine Materialvorhersage oder
unabhängige wissenschaftliche Validierung. **12 Beobachtungen, 52 Quellen,
36 Aussagen, 12 Vorhersagen, fünf synthetische Temperaturmodelle, sieben Zweige
und acht ausführbare Regeln** bleiben unverändert; Beobachtungen bleiben `catalog_only`.

```sh
python -m materials_boundaries observation plot-temperature --dataset-id ciganas-2026-pa12-cf15-fff-uts-temperature --output /tmp/pa12-temperature-plot-de --lang de
python -m materials_boundaries observation plot-temperature --help --lang de
```

Die exakte Datensatz-ID und der Ausgabeordner sind **Pflicht**. Kein Standardplot
aller Records, keine Teilmengen, beliebigen druckförmigen Records oder automatischen
Gruppen. Bei `--lang en|zh|ja|de` gewinnt die letzte Angabe. Diagrammschema **1.0.0**
ist von unveränderten Beobachtungen **1.3.0** und allgemeiner Inspektion **1.1.0**
getrennt. `observation inspect` behält Textdarstellung, Auswahl und Katalogreihenfolge.

Sechs unverbundene, gleich gestaltete Punkte zeigen **berichtete UTS-Zentralwerte,
keine behaupteten Mittelwerte**, auf numerischen Kammer-°C-/Quell-MPa-Achsen.
Vertikale Balken mit Endkappen bedeuten **±berichtete SD**, weder SEM noch
Konfidenzintervalle, beobachtete Minima/Maxima, harte Grenzen oder Überdeckung.
**Drei Zugversuche je Bedingung** sind berichtet; Rohreplikate und Unabhängigkeit
sind ungeprüft. 30 Minuten Kammerstabilisierung belegen keine direkte Probentemperatur.
Fehlende x-Balken bedeuten **unberichtete Temperaturunsicherheit, nicht null**.
Die festen Bereiche 15–125 °C / 0–55 MPa sind Anzeigeränder/Basislinie, keine
Materialgrenzen. Keine Verbindungskurve, Anpassung, Interpolation, Extrapolation,
Rangfolge, Überlagerung, Bemessungswerte oder Sicherheitsbehauptung.

Die genaue Quelltabelle bewahrt Zeichenfolgen und Endnullen. Pa bleibt separate
exakte Einheitenmetadaten: **1 MPa = 1000000 Pa** ohne zusätzliche Präzision oder
Geometrieberechnung. Zentralstatistik/Aggregation, Spannungs-/Querschnittsbasis,
Feuchte/RH und lokale Dehnrate bleiben unbekannt. Horizontales ±45°-FFF, Trocknung,
deklarierte 15 wt.%, 100% Infill, Nenndimensionen und 1 mm/min Traverse sind
spezifischer Kontext, kein Nachweis gemessener Zusammensetzung, Porenfreiheit oder Isotropie.

Fünf Ausgaben tragen `observation-temperature-plot`: JSON, CSV, breite/schmale SVG
und skriptfreies responsives HTML. Die kompakte SVG hält alle sechs Warnungen,
Legende, exakte Quelltabelle/Record-IDs, gemeinsame Protokoll-/Geometrie-/Unbekannt-
Zusammenfassung, genaue Quellenstellen und Versions-/Rechtezuordnung sichtbar.
Vollständige Metadatenobjekte, wiederholte Record-Provenienz und alle sechs SI-Paare
bleiben verlustfrei in JSON/CSV und inerten HTML-Details; wesentliche Warnungen
werden dort nicht versteckt. JSON/CSV sind deterministisch und sprachunabhängig.
Quell-, ID- und JSON-Spalten als Text importieren: formelähnliche Strings bleiben
unverändert. Kanonische Prüfung rekonstruiert vor dem Schreiben aus aktuellen
Katalogen; ungültige Eingaben ändern keine Ausgabe. Spätere Dateisystemfehler
haben keine atomare Rückrollgarantie für alle Dateien. Das Diagramm stellt die
Quellreihenfolge wieder her; allgemeine Inspektion behält die Katalogreihenfolge.

HTML-Version, ungeprüftes PDF, Abweichung in ausgeschlossener Tabelle 4, CC-BY-4.0-
Zuordnung und Adaptionshinweis bleiben erhalten. Keine Quellenmedien/Rohdaten kommen
hinzu. Maschinenunterstützte Übersetzung ist keine unabhängige Wissenschafts- oder
Muttersprachprüfung; Browser-QA ist ungeprüft. [Diagramm/API/CSV-Vertrag](OBSERVATION_TEMPERATURE_PLOT.md)
· [Migration](MIGRATION_v0.23.0.md).

## Früher v0.22.0: PA12-CF15-Zugversuche bei sechs Kammerbedingungen

Sechs UTS/SD-Zellen aus Tabelle 3 von Ciganas, Kalinauskis und Cigane (2026)
kommen hinzu, bei berichteten Kammerbedingungen **23, 40, 60, 80, 100 und 120 °C**.
Aktuell: **12 Beobachtungen aus vier Studien und 52 Quellen**. Die **36 Aussagen,
12 Vorhersagen, fünf synthetischen Modelle, sieben Zweige und acht ausführbaren
Verbundregeln** bleiben unverändert.

Die Proben bestehen aus horizontal FFF-gedrucktem Fiberlogy PA12 CF15 mit
wechselndem +45°/−45°-Raster, 30 Minuten Kammerstabilisierung und 1 mm/min
Traversengeschwindigkeit. Direkte Probentemperatur, Stabilitätstoleranz, lokale
Dehnrate und tatsächliche Feuchte sind unbekannt. Trocknung ersetzt keine
Feuchtemessung; 15 wt.% ist deklarierte Rezeptur und 100% Infill eine Druckeinstellung,
kein gemessener Faseranteil oder Nachweis von Porenfreiheit. Spannungsdefinition,
Querschnittsbasis, Zentralstatistik und Aggregation bleiben unbekannt. Drei
Versuche je Bedingung und berichtete SD ergeben weder SEM, Konfidenzintervalle,
harte Grenzen noch universelle Bemessungswerte.

Der neue Typ heißt `experiment_derived_tensile_test_summary`, die Größe
`ultimate_tensile_strength_as_reported_3d`. Exakte **MPa-Quellzeichenfolgen** und SD
bleiben von der **exakten Pa-Einheitenumrechnung** getrennt: 1 MPa = 1000000 Pa.
Dies ergänzt keine Messpräzision und berechnet keine Spannung aus Geometrie.
Die früheren 2D-N/m-Einträge bleiben unverändert. Keine Interpolation, stetige
Temperaturfunktion, Rangfolge oder dimensionsübergreifende Vergleichbarkeit.

Beobachtungsschema **1.3.0**, Inspektionsschema **1.1.0**: gespeicherte Bündel
neu erzeugen, nicht umetikettieren. Standardmäßig erscheinen 12 Textkarten mit
Warnungen vor Eigenschaftswerten. CSV unterscheidet berichtete Einheiten von
SI-/Normalisierungsspalten. Der vollständige Katalog weist doppelte Aliase einer
Quellzelle zurück; Teilmengen und umbenannte Identitäten mit unveränderter
wissenschaftlicher Nutzlast bleiben gültig. Andere bestehende Familien bleiben
unter ihrem vollständigen Vertrag erweiterbar.

HTML-Version, ungeprüftes PDF und die Cache/Live-Abweichung in der ausgeschlossenen
Tabelle 4 bleiben sichtbar. Übereinstimmung gilt nur für sechs ausgewählte
Tabelle-3-Zellen in HTML, visueller Prüfung und zweiter Transkription, nicht für
unabhängige Experimente. Artikel-CC-BY-4.0 mit Autoren/Titel/DOI-Zuordnung bleibt;
Herstellertabelle 1 ist ausgeschlossen. Keine Quellenmedien oder langen Passagen
werden verteilt. Software-/Übersetzungsprüfung ist keine unabhängige Wissenschafts-
oder Muttersprachprüfung.

```sh
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang de
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15-de --lang de
python -m materials_boundaries observation inspect --id ciganas2026-pa12cf15-uts-60c --output /tmp/pa12-cf15-60c-de --lang de
```

[PA12 CF15](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) · [v0.22.0](MIGRATION_v0.22.0.md) · [Inspection](OBSERVATION_INSPECTION.md)

## Früher v0.21.0: sechs zusätzliche Ni11X-Modellvorhersagen

Genau sechs veröffentlichte ideale Scherfestigkeiten kommen hinzu:
**Ni11Cr 4.90, Ni11Mn 5.12, Ni11Fe 5.20, Ni11Cu 4.51, Ni11Si 4.17 und
Ni11Ti 4.24 GPa**. Quelle: Shimanek et al., arXiv:2108.06412v2, Tabelle 2,
PDF-/Druckseite 27. Der Katalog umfasste bei v0.21.0 **12 Vorhersagen, 2 wissenschaftliche
Methodenfamilien und 3 explizite Vergleichsgruppen**. Die 36 Aussagen, 51 Quellen,
6 Beobachtungen aus 3 Studien, 5 synthetischen Temperaturdemos (7 Zweige) und
8 ausführbaren Verbundregeln bleiben unverändert. Laufzeitcode, wissenschaftliche
Schemas und bestehende Quellenrecords werden nicht geändert.

Die neue Gruppe heißt **Ni11X-Periodenmodelle: Cr, Mn, Fe, Cu, Si und Ti** und
muss ausdrücklich gewählt werden. Ni/Ni11Al/Ni11Co bleiben die drei Standardpunkte;
die separate Siliziumgruppe zur ersten Instabilität behält ihre drei Punkte.
Ni11Si-Scherung ist nicht die Zugfestigkeit von reinem Silizium bei der ersten
Instabilität. Der ungefilterte Vorhersagekatalog liefert 12, der Shimanek-Quellenfilter
9 Einträge; ein Quellenfilter definiert keine neue Diagrammgruppe.

Die fcc-Ni-basierten periodischen Modelle haben 12 Atome und 3 Lagen; X ersetzt
einen Ni-Platz in der Scherebene. Positive pure-alias-Scherung auf (111)[1,1,-2]
hält den vorgeschriebenen Scherwinkel fest und relaxiert Atompositionen sowie
nicht vorgeschriebene Zellparameter. Vergleichbarkeit gilt **nur auf Ebene des
veröffentlichten Verfahrens**, nicht als geprüfte Gleichheit der Rohinputs oder
unbekannter Bedingungen. Dies sind keine Festigkeiten von reinem X, Handelsgüten,
Experimente oder universellen oberen Grenzen.

Die sechs Tabellenlabels tragen kein pv/sv-Suffix. Das bestimmt weder die
PAW-Datensätze noch die Valenzkonfigurationen und beweist nicht das Fehlen von
Semicore-Zuständen. Physikalische Temperatur, skalarer Druck, Magnetismus/
Spinpolarisation sowie statistische/Gesamtunsicherheit bleiben unbekannt.
Die GGA verweist auf **Perdew et al. (1992), ohne eine PBE-Zuordnung zu unterstellen**.
**0.08 GPa Spitzenkonvergenz ist kein Fehlerbalken**; 4.90 und 5.20 bewahren die
Druckpräzision, keine Unsicherheitsangabe. Quellen-PDF, Volltext und Abbildungen
werden nicht weitergegeben. Transkriptions- und Übersetzungsprüfungen ersetzen
keine unabhängige wissenschaftliche oder muttersprachliche Prüfung.

```sh
python -m materials_boundaries catalog predictions --query shimanek_v2_table2_cr_mn_fe_cu_si_ti --text --lang de
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-de --lang de
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_ni_al_co --output /tmp/ni-original-de --lang de
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability-de --lang de
```

[Verfahren, Herkunft und Grenzen](COMPUTATIONAL_PREDICTIONS.md) · [Migration](MIGRATION_v0.21.0.md)

## Früher v0.20.0: Offline-Ansicht zur Beobachtungsprüfung

Die sechs vorhandenen modellabhängigen Zusammenfassungen aus drei Studien
erscheinen als Karten/Tabellen in Quellenreihenfolge. Alle wissenschaftlichen
Einträge bleiben erhalten: 36 Aussagen, 51 Quellen, sechs Beobachtungen, sechs
rechnerische Vorhersagen und fünf synthetische Temperaturdemos (sieben Zweige).
Genau acht Verbundregeln sind ausführbar. Das neue Inspektionsschema ist 1.0.0;
das Beobachtungsschema bleibt 1.2.0.

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang de
python -m materials_boundaries observation inspect --output /tmp/hbn --source-id falin_et_al_2017_hbn_mechanical_properties --group-by quantity --lang de
python -m materials_boundaries observation inspect --output /tmp/selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d --lang de
python -m materials_boundaries observation inspect --help --lang de
```

Wiederholtes `--id` wählt exakte IDs. `--source-id` und `--quantity` vergleichen
exakt und beachten Groß-/Kleinschreibung. Alle Filter werden mit AND verknüpft;
zulässige Größen sind `in_plane_stiffness_2d` und `breaking_strength_2d`.
Standard ist `study`; `quantity` ändert nur die Navigation. Die Katalogreihenfolge
bleibt erhalten, ohne numerische Sortierung. Unbekannte, doppelte oder fehlerhafte
IDs, unzulässige Selektoren/Methodenfamilien und leere Ergebnisse werden vor dem
Schreiben zurückgewiesen.

Ausgabe: `observation-inspection.json`, `.csv`, `.de.svg`, `.narrow.de.svg` und
`.de.html`. HTML lässt sich lokal öffnen, ist eigenständig und skriptfrei;
Quellenlinks werden nur auf Wunsch des Lesers geöffnet. JSON/CSV, Quellenwortlaut,
Zahlen, IDs und Prüfsummen sind sprachunabhängig. Die normalisierte Kataloganzeige
ist vom Original-Quellenstring getrennt, kein wörtliches Zitat und keine neue
Dickenumrechnung.

Warnungen stehen vor den Werten: Bei MoS2 bleiben der gedruckte q-Widerspruch und
das unbekannte tatsächliche Fit-q ohne Neufit/Korrektur bestehen. Bei Graphen ist
die statistische Bedeutung von ± ungeprüft. hBN-Festigkeit ist die FEM-
volumengemittelte Spannung unter dem Eindringkörper; genaue zentrale Statistik
und Spannungskomponente bleiben unbestimmt. hBN-SD/Zählbelege stammen weiterhin
aus der Autorenantwort zur Begutachtung, PDF S. 8. Steifigkeitszahlen werden nicht
zu Bruchereigniszahlen. Unbekannte Bedingungen belegen keine Gleichheit.

Kein Beobachtungsrechner, Vergleich bei nachgewiesen gleichen Bedingungen,
numerische Achsen, Fehlerbalken, Aggregation, Rangfolge oder Überlagerung kommt
hinzu. Alte Inspektionsbündel neu erzeugen, nicht nur umetikettieren. Quellen-PDFs,
Abbildungen und Rohdaten werden nicht mitgeliefert. Unabhängige wissenschaftliche
und muttersprachliche Prüfung der Übersetzungen steht aus.
[Inspektionsanleitung](OBSERVATION_INSPECTION.md) · [Migration](MIGRATION_v0.20.0.md)

## Historisch v0.19.0: einlagige hBN-Beobachtungen als Katalogwissen

Genau zwei Einträge aus Falin et al. (2017) und eine Quelle kommen hinzu:
**36 Mechanikaussagen, 51 Quellen, 6 Beobachtungen aus 3 Studien**. Das
Beobachtungsschema steigt von **1.1.0 auf 1.2.0** mit einer eigenen geschlossenen
hBN-Methodenfamilie. Sechs rechnerische Vorhersagen, fünf synthetische
Temperaturdemos (sieben Zweige) und genau acht ausführbare Verbundregeln bleiben
unverändert; das Aussagenschema bleibt 1.11.0.

Die Quelle nennt ausdrücklich **289 ± 24 N/m Steifigkeit in der Ebene** und
**23.6 ± 1.8 N/m Bruchfestigkeit**. Die Definition als Standardabweichung stammt
aus der vom Verlag verlinkten **öffentlichen Autorenantwort zur Begutachtung,
PDF S. 8, Gutachter #1, Frage 3**, nicht allein aus dem ± im Haupttext. Es sind
keine Standardfehler, Konfidenzintervalle, strikten Grenzen oder vollständigen
Unsicherheitsbudgets; die genaue Gewichtung der Wiederholungen bleibt unbekannt.
**N=11 zählt getestete Schichten und ist ausdrücklich dem Steifigkeitsmittel
zugeordnet**. Kurven- und Bruchereigniszahlen sind unbekannt. Typisch fünf
Eindrückungen pro Schicht ergeben nicht exakt 55 Kurven oder elf verifizierte
Festigkeitswiederholungen.

Die Steifigkeit wird durch einen kreisförmigen AFM-Membranfit abgeleitet.
Die Festigkeit verwendet nichtlineare FEM und **volumengemittelte Spannungen
unter dem Eindringkörper mit endlichem Radius**. Sie ist weder die diagnostische
**maximale Von-Mises-Spannung** aus Ergänzungsabbildung S5 noch direkt gemessene
homogene Zugfestigkeit. Spannungs- und Verzerrungsmaße bei endlicher Verformung
bleiben unbekannt. Die gedruckte Formel **q=1/(1.049−0.15ν−0.16ν²)** bei
**ν=0.211** ergibt **0.9898768854482001 ausschließlich als eigene Rechenkontrolle**.
Kein separat gedruckter q-Wert und keine tatsächlich verwendete Fitkonstante sind
verifiziert; ein hBN-q-Widerspruch oder eine Korrektur wird nicht behauptet.

„Ambient“ legt keine numerische Temperatur, Druck, Gaszusammensetzung oder
Feuchte fest. **0.5 μm/s** ist die Sondentranslationsgeschwindigkeit beim Be- und
Entlasten, keine Verzerrungsrate. Beide N/m-Werte stehen ausdrücklich in der
Quelle; **0.334 nm** ist nur deren Modelldickenkonvention. Es gibt keine automatische
Dickenumrechnung, Neuanpassung, Rangliste, Vergleiche, Plots oder Überlagerung mit
Verbundrechnungen. Graphen/MoS2 bleiben erhalten, einschließlich des unten
hervorgehobenen gedruckten MoS2-q-Widerspruchs.

Der Artikel steht unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/);
die eigenständige Lizenzgeltung für Supplement und Begutachtungsdatei ist
ungeklärt. Quellen-PDFs, Volltexte, Abbildungen, Screenshots, Begutachtungsberichte
und Rohdatensammlungen werden nicht mitgeliefert. Transkriptionskontrolle und
Softwaretests ersetzen keine unabhängige wissenschaftliche oder muttersprachliche
Prüfung. Siehe [hBN-Belege und Grenzen](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
und [Migration v0.19.0](MIGRATION_v0.19.0.md).

```sh
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang de
python -m materials_boundaries catalog observations --query "hBN stiffness" --json
```

## Historisch v0.18.0: elastische Volumenwellen als Katalogwissen

Diese Version ergänzt genau zwei Relationen und zwei Quellen: insgesamt
**36 Mechanikaussagen, 50 Quellen**, Aussagenschema **1.11.0**. Vier
Beobachtungen aus zwei Studien, sechs rechnerische Vorhersagen, fünf synthetische
Temperaturdemos (sieben Zweige) und genau acht ausführbare Verbundregeln bleiben
unverändert. Es gibt keinen neuen Wellenrechner, Materialeingang, Tensor-
Eigenwertlöser oder Wellenplot.

Für ein spannungsfreies, homogenes, unbegrenztes dreidimensionales klassisches
lokales linear-elastisches, nichtdissipatives Medium mit endlichen positiven
isotropen K, G und skalarer Dichte ρ gilt **c_L²=(K+4G/3)/ρ**,
**c_T²=G/ρ** und **c_L/c_T∈(√(4/3),∞)**. Das ist der Verhältnisbereich über die
Materialklasse mit positiver Verzerrungsenergie. Das untere Infimum wird nicht
erreicht; es gibt keine gemeinsame endliche obere Schranke, aber Unendlichkeit
ist kein erreichter Materialwert. Ein festes Material hat endliche,
richtungsunabhängige c_L und c_T mit zweifacher transversaler Entartung.

Bei den angegebenen reellen Tensorsymmetrien hat **Q_ik=C_ijkl n_j n_l** die
Einheit Pa, **Γ=Q/ρ** die Einheit m² s⁻²; es gilt Q a=ρc²a. Phasennormale n
und Verschiebungspolarisation a sind verschiedene Variablen. Strikte starke
Elliptizität bedeutet: Q(n) ist für jedes Einheits-n positiv definit,
gleichbedeutend mit drei strikt positiven Geschwindigkeitsquadraten in jeder
Richtung. Positive Energie für alle von null verschiedenen symmetrischen
Verzerrungen impliziert dies, aber nicht umgekehrt. Das eigenständig hergeleitete
Gegenbeispiel **K=−G/3, G>0** ergibt Q=GI und drei gleiche positive
Geschwindigkeitsquadrate, jedoch negative hydrostatische Verzerrungsenergie.
Es ist kein Vorschlag für ein stabiles reales Material; die bisherigen
vollständigen Energie-Stabilitätskriterien behalten ihre stärkere Bedeutung.

Allgemein anisotrope Moden sind nicht notwendigerweise exakt longitudinal oder
transversal; eine universelle Reihenfolge mit schnellster Longitudinalmode wird
nicht behauptet. Phasengeschwindigkeit ist keine Aussage über Strahl- oder
Gruppengeschwindigkeit. Statische/isotherme Moduln dürfen nicht automatisch
eingesetzt werden; thermodynamische Umrechnung, Vorspannung und endliche
Verzerrungen sind nicht abgedeckt. Chevrot–van der Hilst (2003), S. 498,
Gl. (1)–(4), und Xiang–Qi–Wei arXiv v2, S. 2, 4–5, belegen die Grundgleichungen;
Intervall- und Energiebeweise sind eigene Projektableitungen. Keine Quellenbilder
oder Volltexte werden mitgeliefert. Unabhängige wissenschaftliche und
muttersprachliche Prüfung steht aus. Siehe [Annahmen, Beweise, Versionen und
Ausschlüsse](BULK_ELASTIC_WAVES.md) sowie [Migration](MIGRATION_v0.18.0.md).

```sh
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang de
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang de
```

**Die vorherige Version v0.17.0** ergänzte zwei reine Katalogeinträge für
einlagiges MoS2 aus einer Studie: damals insgesamt **4 Beobachtungen aus 2 Studien,
48 Quellen**, Beobachtungsschema **1.1.0**. Die bisherigen Graphen-Einträge
bleiben unverändert. MoS2-Steifigkeit **180 ± 60 N/m** und Bruchfestigkeit
**15 ± 3 N/m** verwenden berichtete Standardabweichungen. **Die gedruckte
q-Formel widerspricht dem angegebenen q=0.95; die tatsächlich verwendete
Fitkonstante bleibt ungeklärt. Es erfolgt keine Neuanpassung.** Siehe
[SD-Bedeutung, Quellenbelege und q-Vorbehalt](OBSERVATIONS.md#monolayer-mos2-bertolazzi-et-al-2011-new-records).

**Historische Basis der ersten öffentlichen Version, 0.16.0:** 34 Mechanikaussagen,
47 Quellenrecords, 2 Beobachtungen, 6 rechnerische Vorhersagen und 5 synthetische
Temperaturdemos mit 7 Zweigen. Die acht ausführbaren Verbundregeln sind unverändert.
Das Aussagenschema war damals 1.10.0; Schema- und Softwareversion sind unabhängig.

Eigener Code, eigene Dokumentation und eigenständige Kuration stehen unter
[MIT](../LICENSE). Werke Dritter und wissenschaftliche Fakten werden nicht neu
lizenziert. NIST-Tieftemperaturkoeffizienten und abgeleitete Beispiele bleiben
vorsorglich bis zur Klärung der Nutzungsbedingungen ausgenommen. Damit ist kein
Weitergabeverbot nachgewiesen. Bibliografische Links bleiben erhalten.
[Hinweise zu Rechten Dritter](../THIRD_PARTY_NOTICES.md)

Die Koeffizienten und Bereiche der Temperaturmodelle sind absichtlich erfunden,
keine realen Material- oder Messdaten. Die lineare Demo ergibt bei 50 K 15 GPa;
die Überlappungsdemo gibt bei 50 K sowohl 25 als auch 32.5 GPa zurück. Keine
Zweigauswahl, Mittelung, Extrapolation oder Unsicherheitsbänder.
[Temperaturleitfaden](TEMPERATURE_MODELS.md)

```sh
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-50k.json --lang de
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-overlap-50k.json --lang de
python -m materials_boundaries temperature plot --output /tmp/temperature-demos --lang de
```

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Bulk elastic waves](BULK_ELASTIC_WAVES.md) · [Release scope](MIGRATION_v0.23.0.md)

## Lokal ausführen

Verwenden Sie Python 3.10 oder neuer. Führen Sie diese Befehle im Stammverzeichnis des Repositorys aus. Zur Laufzeit sind weder externe Pakete noch Netzwerkzugriff erforderlich:

```sh
python -m materials_boundaries validate examples/synthetic-two-phase.json --lang de
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang de --unit GPa
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang de --json
```

Mit `--lang en`, `--lang zh` oder `--lang ja` wählen Sie eine andere Anzeigesprache. JSON-Schlüssel, Aufzählungswerte, Formeln, Zahlen und Einheiten-IDs bleiben unverändert. Fehlende Übersetzungen werden durch Englisch ersetzt; fehlt der Schlüssel auch dort, erscheint eine ausdrückliche Fehlstellenmarkierung.

## Das synthetische Ergebnis verstehen

Das Beispiel dient der Veranschaulichung und enthält keine gemessenen Materialdaten:

- Phase 1: `f1 = 0.5`, `K1 = 10 GPa`, `G1 = 5 GPa`
- Phase 2: `f2 = 0.5`, `K2 = 30 GPa`, `G2 = 15 GPa`
- Kompressionsmodul K: Reuss `15 GPa`; HS `16.25–17.5 GPa`; Voigt `20 GPa`
- Schubmodul G: Reuss `7.5 GPa`; HS ungefähr `8.37837837838–9.04761904762 GPa`; Voigt `10 GPa`
- Abgeleitete äußere Einhüllung des Elastizitätsmoduls E: ungefähr `21.4488468362–23.1528046422 GPa`
- Abgeleitete äußere Einhüllung der Poissonzahl ν: ungefähr `0.265190525232–0.293562708102`, dimensionslose Einheit `1`

Das HS-Intervall ist eine theoretische Einschränkung, keine Modellvorhersage, kein Messunsicherheitsintervall und kein technischer Abnahmegrenzwert. Die Ausgabe besteht aus Gleitkommanäherungen ohne Absicherung durch Intervallrechnung.

## Abgeleitete äußere Einhüllungen verstehen

Für dasselbe Materialsystem gelten E = 9KG/(3K+G) und ν = (3K−2G)/(2(3K+G)). Für den unteren/oberen E-Endpunkt werden (Klow,Glow)/(Khigh,Ghigh) verwendet, für ν dagegen (Klow,Ghigh)/(Khigh,Glow). Endpunkte getrennter HS-Intervalle müssen nicht gleichzeitig erreichbar sein. Dies sind konservative äußere Einhüllungen, keine scharfen gemeinsamen Schranken. Bei unbekannten oder verletzten Voraussetzungen entfallen Zahlenwerte. Bei ungeordneten Phasen gibt es für E/ν keinen Ersatz durch Reuss/Voigt.

`--unit` ändert nur die Einheiten von K/G/E. ν hat stets die Einheit `1` und muss −1 < ν < 0.5 erfüllen; negative Werte und null sind gültig. Rundet ein Gleitkommawert auf einen ausgeschlossenen Randwert, wird `numerical_range_error` mit einem null-Ergebnis ausgegeben, statt einen physikalischen Endpunkt vorzutäuschen. Ein numerischer Fehler in einem benötigten HS-Ergebnis macht auch die abgeleiteten Einhüllungen unverfügbar. Decimal-Rechnung garantiert keine nach außen gerundeten Endpunkte.

Die Auswertung liefert seit v0.2.0 acht Datensätze und behält diese acht wissenschaftlichen Auswertungen in v0.8.0 bei. Wählen Sie nach `claim_id` und `quantity`, statt eine feste Listenlänge vorauszusetzen. Vorhandene Kompressionsmodul-IDs, Regel-IDs und numerische Ergebnisstrukturen bleiben erhalten; Typmetadaten und Ausgabeschema-Version 1.1.0 wurden in v0.2.0 eingeführt. Eingabeschema und Beispiele bleiben gültig. Siehe [Migration auf v0.2.0](MIGRATION_v0.2.0.md) und [Modell/Formeln](MODEL.md).

## Vor der Verwendung die Anwendbarkeit prüfen

- `satisfied` (erfüllt): Die eingegebenen Werte und Angaben stützen innerhalb der implementierten Prüfungen alle erforderlichen Voraussetzungen
- `violated` (verletzt): Mindestens eine Voraussetzung widerspricht den Eingaben; verwenden Sie die betroffene Schranke nicht
- `unknown` (unbekannt): Für mindestens eine Voraussetzung fehlen Belege; setzen Sie ihre Erfüllung nicht voraus

Die Isotropie der Einzelphasen und die des effektiven Mediums sind getrennte Voraussetzungen. Alle vorhandenen Phasen benötigen positive K/G. HS und die abgeleiteten E/ν erfordern zusätzlich eine gleichsinnige Ordnung: `K1 <= K2` und `G1 <= G2` müssen gleichzeitig gelten, wobei die Zuordnung von K/G und Volumenanteil jeder Phase erhalten bleibt. Reuss/Voigt benötigen diese Ordnung nicht. Die vollständigen Annahmen stehen im Aussagenkatalog. Das Programm überprüft die Mikrostruktur einer Probe nicht unabhängig. Numerische Berechnungen von Festigkeit, Versagen und Plastizität bleiben im Auswerter ausgeschlossen. Die folgenden Bruchmodelle sind reine Katalogeinträge.

```sh
python -m materials_boundaries evaluate examples/unknown-isotropy.json --lang de
python -m materials_boundaries evaluate examples/anisotropic-constituent.json --lang de
python -m materials_boundaries catalog claims
python -m materials_boundaries catalog sources
```

Kopieren Sie für eigene Eingaben ein Beispiel und behalten Sie die kanonischen Schlüssel und Aufzählungswerte des Schemas bei. Unbekannte optionale Beobachtungen können `null` sein oder entfallen. Erfinden Sie keine Werte und ersetzen Sie fehlende Belege nicht durch `satisfied`. Einheiten-IDs unterscheiden Groß- und Kleinschreibung: `Pa`, `kPa`, `MPa`, `GPa`. Verwenden Sie in JSON einen Dezimalpunkt. Führen Sie zuerst `validate` und danach `evaluate` aus. Eine gültige Datenstruktur allein belegt noch keine physikalische Anwendbarkeit.

Die vier Arten wissenschaftlicher Aussagen erläutert das [Begriffsverzeichnis](TERMINOLOGY.md). Übersetzungsregeln und Qualitätsprüfungen finden Sie unter [Sprachunterstützung](I18N.md).

## Schreibgeschützte Kataloge durchsuchen

Die Suche prüft ausschließlich mitgelieferte kuratierte Datensätze, ohne Netzwerkzugriff oder Datenänderung. Die bisherigen Befehle `catalog claims` und `catalog sources` liefern weiterhin kanonisches JSON; `--json` wählt dasselbe Format ausdrücklich. Mit `--text` werden Beschriftungen und zentrale Erläuterungen zum Belegstatus übersetzt. Originaltitel, ursprüngliche Belegtexte und kanonische IDs bleiben erhalten.

```sh
python -m materials_boundaries catalog claims --id hs_bulk_3d_two_phase --text --lang de
python -m materials_boundaries --lang de catalog claims --direction interval --text
python -m materials_boundaries catalog claims --query "bulk kochmann" --source-id kochmann_milton_2014 --json
python -m materials_boundaries catalog sources --query "Milton moduli" --year 2014 --text --lang de
python -m materials_boundaries catalog sources --role changed_assumption_comparison --license CC-BY-4.0 --text --lang de
python -m materials_boundaries --lang de catalog --help
```

`--lang` kann vor oder nach dem Befehl stehen; bei Wiederholung gilt die letzte Angabe. Die Hilfe übersetzt Beschriftungen und Beschreibungen, während Befehlssyntax und IDs kanonisch bleiben.

`--id` verlangt eine exakte Übereinstimmung unter Beachtung der Groß- und Kleinschreibung. `--query` trennt Suchbegriffe an Leerraum, wendet Unicode-`casefold` an und verlangt für jeden Begriff einen wörtlichen Teilzeichenketten-Treffer in den durchsuchbaren gespeicherten Feldern. Dazu gehören ID und Titel/Name sowie bei Quellen Autorennamen, DOI und Rolle, bei Aussagen Größe, Richtung, `claim_type`, Regel-ID und Belegquellen-IDs. Die kuratierten Anzeigenamen der sechzehn Einträge aus v0.4.0–v0.6.0 und v0.8.0 sind zusätzlich wörtliche Suchaliase in allen vier Sprachen. Es gibt keine Wortstammbildung, Rangfolge, unscharfe Suche, automatische Übersetzung oder Netzwerksuche.

Aussagen unterstützen `--direction interval|lower|upper|prediction|relation|constraint`, `--claim-type theoretical_bound|derived_outer_envelope|model_estimate|model_relation|stability_criterion` und `--source-id` für eine exakte Belegquellenreferenz. Quellen unterstützen `--role`, ganzzahliges `--year` und `--license` für eine exakte Lizenzkennung oder einen Lizenzstatus. Zeichenkettenfilter beachten Groß- und Kleinschreibung; alle Bedingungen werden mit AND verknüpft, die Katalogreihenfolge bleibt erhalten. Ein leeres Ergebnis ist gültig (Exitcode 0); eine unbekannte `--id`, ein ungültiger Filter oder ein Filter für die falsche Katalogart ist ein Fehler (Exitcode 2).

Das Lesen einer Quelle, ein Formelabgleich oder bestandene Softwaretests sind weder ein unabhängiger wissenschaftlicher Beweis noch eine Erlaubnis zur Wiederverwendung von Inhalten. Ein Suchtreffer belegt keine physikalische Anwendbarkeit; der Lizenzfilter prüft nur gespeicherte Metadaten. Eigener Code steht unter MIT; Rechte Dritter bleiben unberührt. Python-API und Prüfliste für neue Quellen/Aussagen stehen in der [Katalogreferenz](CATALOG.md).

## Bruchmodelle als reine Katalogeinträge

Version 0.3.0 ergänzt zwei Griffith-/linear-elastische bruchmechanische (LEFM) Modelle für die kritische Fernzugspannung: `griffith_central_crack_plane_stress` für ebenen Spannungszustand und `griffith_central_crack_plane_strain` für ebenen Verzerrungszustand. Beide verwenden `claim_type: model_estimate`, `direction: prediction`, `bound_kind: null` und `evaluation_support: catalog_only`. Sie beschreiben Modelle und Voraussetzungen; es entstehen keine neuen numerischen Auswertungen.

Die Formel lautet σc = sqrt(E_prime Gc/(πa)), mit E_prime = E bei ebenem Spannungszustand und E_prime = E/(1−ν²) bei ebenem Verzerrungszustand. E ist der Elastizitätsmodul in Pa, Gc die kritische Energiefreisetzungsrate in J/m² und a die Hälfte der gesamten mittigen Durchrisslänge 2a in m. Der ebene Verzerrungszustand benötigt zusätzlich die dimensionslose Poissonzahl ν. Das Array `parameters` enthält Symbol, Größe, Dimension, SI-Einheit und Bedeutung. Gc darf nicht automatisch durch 2γ ersetzt werden. Diese Gleichheit gilt nur im ideal rein spröden Sonderfall, in dem allein die Bildung zweier neuer Oberflächen Energie dissipiert.

Vorausgesetzt werden ein homogener isotroper linear-elastischer Körper, ein mittiger Durchriss in einer ausreichend breiten/unendlichen Platte, Mode-I-Fernzug und eine ausreichend kleine plastische Zone beziehungsweise Bruchprozesszone. Andere Rissgeometrien und großräumige Plastizität erfordern andere Modelle. Die kritische Spannung ist weder eine universelle obere Schranke der Zugfestigkeit noch eine zulässige Bemessungsspannung. Die Kontinuumsformel darf nicht auf atomare Rissgrößen oder a → 0 extrapoliert werden.

Eine Katalogabfrage belegt keine Voraussetzungen einer konkreten Probe, erzeugt keine instanzbezogenen Zustände `satisfied`/`violated`/`unknown` und berechnet keine Spannung. Unbekannte oder verletzte Voraussetzungen rechtfertigen keine Anwendung. `evaluate()` liefert weiterhin dieselben acht Verbundwerkstoffauswertungen unter Schema 1.1.0. In v0.3.0 wechselte der Aussagenkatalog mit zehn Einträgen zu Schema 1.2.0; v0.4.0 enthält fünfzehn Einträge unter Schema 1.3.0; jeder Eintrag enthält nun `claim_type`, `quantity_dimension`, `si_unit` und `evaluation_support`.

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --direction prediction --text --lang de
python -m materials_boundaries catalog claims --id griffith_central_crack_plane_strain --json
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --text --lang de
```

Diese kanonischen Codes sind in allen vier Sprachen gleich; die Suche übersetzt keine Anzeigetexte. Die sechs K/G-Schranken sind `theoretical_bound`, E/ν sind `derived_outer_envelope`. Die historische Zuschreibung an Griffith ist von der Prüfung der modernen Formel getrennt. Siehe [Bruchmodelle und Belege](FRACTURE_MODELS.md), [Quellen](SOURCES.md) und [Migration auf v0.3.0](MIGRATION_v0.3.0.md). Die Bruchmodellerweiterung v0.3.0 ergänzte keine Volltexte, Verlags-PDFs, Messdaten oder Wiederverwendungsrechte. Die Codelizenz ist weiterhin offen; eine unabhängige wissenschaftliche Prüfung steht aus.

## Ein Literaturmodell

Ein separates [Epoxidharz/Glas-Beispiel](LITERATURE_EXAMPLE.md) enthält veröffentlichte Modellwerte für E/ν und daraus hier berechnete K/G. Der Glasvolumenanteil von 20%, effektive Isotropie und perfekte Haftung sind Rechenannahmen, keine Messungen an einer Probe. Temperatur und Materialdetails bleiben unbekannt.

```sh
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --lang de
```

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang de
```

```sh
python -m materials_boundaries catalog claims --query porous --direction interval --text --lang de
```

## Beobachtungen durchsuchen

Auch `catalog observations` liefert standardmäßig kanonisches JSON; `--text` wählt die lokalisierte Darstellung. Beobachtungsabfragen durchsuchen ID, Name, `quantity`, `observation_type`, `study_id`, `material.name`, Belegquellen-IDs und kuratierte Anzeigenamen aller vier Sprachen mit derselben wörtlichen Alle-Begriffe-Suche. `--source-id` gilt für Aussagen und Beobachtungen; `--quantity` und `--observation-type` (`experiment_derived_model_dependent`, `experiment_derived_tensile_test_summary`) gelten nur für Beobachtungen und vergleichen exakt mit Groß-/Kleinschreibung. Alle Filter werden mit AND verknüpft; unzulässige Katalog-/Filterkombinationen sind Fehler. Zwei Eigenschaftsdatensätze mit derselben Studien-ID bleiben eine Studie.

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang de
```

## Publizierte Vorhersagen idealer Scherung (v0.12.0)

`catalog predictions --query shimanek_v2_table2_ni_al_co --text --lang de` durchsucht drei quellengeprüfte periodische
Modelle; `prediction plot --output /tmp/ideal-shear --lang de` exportiert diskrete
Vergleichspunkte. Ni / Ni11Al / Ni11Co: 5.13 / 4.58 / 5.46 GPa. Der Vergleich gilt
nur für das publizierte Verfahren einer Studie, nicht für Messungen kommerzieller
Legierungen oder universelle Grenzen. Temperatur, skalarer Druck, Magnetismus und
Unsicherheit bleiben unbekannt; 0.08 GPa Konvergenz ist kein Fehlerbalken.
[Verfahren, Herkunft und Grenzen](COMPUTATIONAL_PREDICTIONS.md).
