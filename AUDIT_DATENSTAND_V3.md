# Audit – Neustart 2015–2025 v3

Stand: 15.09.2026

## Soll-Datenbestand

| Bereich | Anzahl |
|---|---:|
| Spieler | 7.564 |
| Spieler mit Pass | 6.438 |
| Spieler ohne Pass | 1.126 |
| Teilnahmen/Ergebnisse | 156.744 |
| Ergebnisse mit Runden | 27.501 |
| Ergebnisse ohne Runden | 129.243 |
| Rundensätze | 27.501 |

## Zeitraum

Ergebnisebene: 2015–2019 und 2022–2025.

Nicht Bestandteil dieser Ergebnisebene: 2020, 2021 und 2026.

## Datenmodell

Teilnahme und Einzelrunde sind getrennte Ebenen. Ein Ergebnis ohne verfügbare Einzelrunden wird nicht entfernt. Bei vorhandenen Runden werden R1–R20 sowie Gesamt und Schnitt geführt.

## Identität

Passnummern werden bevorzugt zur Zuordnung verwendet. Wo keine sichere Zuordnung vorliegt, bleibt der Datensatz offen bzw. passlos. Es werden keine unsicheren Namens-Fuzzy-Matches als bestätigte Identität gespeichert.

## Wichtige technische Prüfung

Die acht Spieler-Shards enthalten 7.564 Spieler. Die historische Ergebnisebene enthält 156.744 Datensätze; davon haben 129.243 keine Einzelrunden und bleiben trotzdem erhalten.

`main` wurde nicht verändert. Dieser Branch ist weiterhin der Prüfstand `datenbank-neustart-2015-2025`.
