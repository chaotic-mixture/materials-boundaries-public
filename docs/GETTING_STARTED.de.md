# Erste Schritte: Materials Boundaries

**0.16.0 ist die erste öffentliche Version:** 34 Mechanikaussagen,
47 Quellenrecords, 2 Beobachtungen, 6 rechnerische Vorhersagen und 5 synthetische
Temperaturdemos mit 7 Zweigen. Die acht ausführbaren Verbundregeln sind unverändert.
Das Aussagenschema ist 1.10.0; Schema- und Softwareversion sind unabhängig.

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

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Release scope](MIGRATION_v0.16.0.md)

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

Auch `catalog observations` liefert standardmäßig kanonisches JSON; `--text` wählt die lokalisierte Darstellung. Beobachtungsabfragen durchsuchen ID, Name, `quantity`, `observation_type`, `study_id`, `material.name`, Belegquellen-IDs und kuratierte Anzeigenamen aller vier Sprachen mit derselben wörtlichen Alle-Begriffe-Suche. `--source-id` gilt für Aussagen und Beobachtungen; `--quantity` und `--observation-type experiment_derived_model_dependent` gelten nur für Beobachtungen und vergleichen exakt mit Groß-/Kleinschreibung. Alle Filter werden mit AND verknüpft; unzulässige Katalog-/Filterkombinationen sind Fehler. Zwei Eigenschaftsdatensätze mit derselben Studien-ID bleiben eine Studie.

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang de
```

## Publizierte Vorhersagen idealer Scherung (v0.12.0)

`catalog predictions --text --lang de` durchsucht drei quellengeprüfte periodische
Modelle; `prediction plot --output /tmp/ideal-shear --lang de` exportiert diskrete
Vergleichspunkte. Ni / Ni11Al / Ni11Co: 5.13 / 4.58 / 5.46 GPa. Der Vergleich gilt
nur für das publizierte Verfahren einer Studie, nicht für Messungen kommerzieller
Legierungen oder universelle Grenzen. Temperatur, skalarer Druck, Magnetismus und
Unsicherheit bleiben unbekannt; 0.08 GPa Konvergenz ist kein Fehlerbalken.
[Verfahren, Herkunft und Grenzen](COMPUTATIONAL_PREDICTIONS.md).
