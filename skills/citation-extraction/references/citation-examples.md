# Few-Shot-Beispiele — Zitat-Extraktion

Konkrete Gut/Schlecht-Beispiele zur Qualitaetskalibrierung. Vom Skill
`citation-extraction` bei Bedarf geladen (Progressive Disclosure).

## Stil: APA7-Zitation

**Schlecht** (Grund: fehlende Autor-Initialen, keine DOI, unvollständig):

> Müller, T. (2023). Cloud-Migration in KMU.

**Gut** (Grund: vollständige APA7-Notation mit DOI):

> Müller, T., & Schmidt, A. (2023). Cloud-Migration in deutschen
> KMU: Eine empirische Studie. *Zeitschrift für Wirtschaftsinformatik*,
> 65(3), 215–234. https://doi.org/10.1007/s11576-023-00012-x

## Stil: Bibliography-Vollständigkeit

**Schlecht** (Grund: Eintrag im Text ohne Literaturverzeichnis-Eintrag):

> Text: "Müller (2023) argumentiert…"
> Bibliography: (kein Müller-Eintrag)

**Gut** (Grund: jeder In-Text-Zitat hat Bibliographie-Pendant):

> Text: "Müller (2023) argumentiert…"
> Bibliography: Müller, T. (2023). *Titel*. Verlag. DOI.
