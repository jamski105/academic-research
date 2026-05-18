# Nationallizenzen DFG — Browser-Guide (Buch-Download)

**URL:** https://www.nationallizenzen.de
**Auth:** DFN-AAI / Shibboleth mit Hochschulkonto (mehrstufig)
**Anti-Scraping:** niedrig auf Nationallizenzen-Portal; mittel beim Ziel-Verlag.

## Login-Flow

Nationallizenzen selbst sind kein Download-Portal — sie ermöglichen Zugang zu
Verlags-Plattformen via Shibboleth.

1. Ziel-Verlagsseite öffnen (z. B. Springer, Wiley — aus Discovery-Ergebnis).
2. Auf der Verlagsseite: "Sign in via institution" oder "Institutional login" klicken.
3. DFN-AAI-Seite öffnet: Hochschule im Suchfeld eingeben oder aus Liste wählen.
4. Hochschul-IdP-Login-Seite: Credentials eingeben (Credentials aus Uni-Profil).
5. Auf Weiterleitung zurück zum Verlag warten.
6. Zugang geprüft → Volltext-Lokation.

## Discovery-Pfad

1. `browser-use open https://www.nationallizenzen.de`
2. Suche im Nationallizenzen-Katalog: Titel, ISBN, DOI oder Verlag.
3. `browser-use state` → Treffer prüfen; Verlags-Link in Trefferdetails notieren.
4. Auf Verlags-Link klicken → Verlagsseite öffnet (Springer, Wiley, etc.).
5. Auf der Verlagsseite weiter im verlagsspezifischen Guide verfahren
   (`springer.md`, etc.).

Alternativ: DOI-Direktlink verwenden — falls Nationallizenz gilt, wird Zugang
nach Shibboleth-Auth gewährt.

## Volltext-Lokation

- Volltext liegt beim jeweiligen Verlag, nicht bei Nationallizenzen.
- Nach erfolgreicher Shibboleth-Auth: Download-Button auf Verlagsseite erscheint.
- Verlagsspezifische Guides für die Volltext-Lokation verwenden:
  - Springer → `springer.md` (Buch-Download-Block)
  - De Gruyter → `degruyter.md`
  - Wiley → verlagseigene URL-Muster

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Hochschule nicht in der betreffenden Nationallizenz enthalten.
  - Shibboleth-Flow schlägt fehl (IdP nicht erreichbar, falsche Credentials).
  - Erscheinungsjahr außerhalb des Nationallizenz-Zeitraums (meist vor 2015).
  - Verlag gibt trotz Auth Access-Denied zurück.
- `status: captcha` wenn Verlag CAPTCHA zeigt nach Auth.
- `status: no_match` wenn Titel nicht im Nationallizenzen-Katalog.

## Bekannte Fallstricke

- Nationallizenzen gelten nur für bestimmte Erscheinungsjahre — häufig bis 2007–2015
  je nach Verlagsvertrag. Neuerscheinungen sind nicht enthalten.
- Auth-Redirect ist mehrstufig: Verlag → Nationallizenzen-Redirect → DFN-AAI →
  Hochschul-IdP → zurück — vollständigen Flow abwarten (kann 10–15 Sekunden dauern).
- Nicht jede Hochschule hat alle Nationallizenzen aktiviert — Uni-Profil prüfen.
- Einige Verlage erfordern zusätzlich Cookie-Akzeptanz vor dem Auth-Flow.
