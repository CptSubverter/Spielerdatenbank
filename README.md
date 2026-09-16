# Bahnengolf.net – GitHub-Datenbank

Abgeglichene statische Datenbank für Bahnengolf.net. Die Daten wurden mit den verfügbaren Ergebnis-, Spieler-, Vereins-, Verbands- und DRL-Daten abgeglichen und relational verknüpft.

## Stand
- vollständiger Spielerbestand mit geprüften Relationen
- 13 Landesverbände/Verbandsbereiche in der Verbandsansicht
- Spieler, Ergebnisse und Turniere relational verknüpft
- unsichere Spielerzuordnungen werden nicht stillschweigend übernommen

## Funktionen
- Spielersuche nach Name, Spielernummer, Verein und Verband
- Vereins-Suche und Vereins-Spielerliste
- Verbands-Suche mit Spielerlisten
- Turnier-Suche und Teilnehmerlisten
- Spielerprofile mit tatsächlich verknüpften Turnierteilnahmen
- responsive Darstellung für Smartphone und PC

Die Oberfläche lädt die Daten direkt aus demselben GitHub-Pages-Verzeichnis.

Technischer Hinweis: Die Relationsdaten werden automatisch per GitHub Actions neu aufgebaut, wenn sich die Quelldaten oder der Relationsgenerator ändern.
