# De Gruyter — Browser-Guide (Buch-Download)

**URL:** https://www.degruyter.com
**Auth:** Shibboleth/IP-basiert (Institutionszugang) ODER kein Login für OA-Titel
**Anti-Scraping:** mittel — CAPTCHA bei schnellen Requests möglich.

## Login-Flow

**Für OA-Titel:** kein Login erforderlich — direkt zu Discovery-Pfad.

**Für lizenzierte Titel (Institutionszugang):**

1. `browser-use open https://www.degruyter.com`
2. "Sign in" / "Anmelden"-Button oben rechts klicken.
3. `browser-use state` → "Sign in via institution" / "Über Institution anmelden"
   suchen, klicken.
4. Shibboleth-Redirect: Hochschule im Dropdown wählen.
5. Hochschul-Login-Formular ausfüllen (Credentials aus Uni-Profil).
6. Auf Weiterleitung zurück zu DeGruyter warten — angemeldeter Status prüfen.

## Discovery-Pfad

1. Suchfeld im Header: Titel, ISBN oder DOI eingeben.
2. `browser-use state` → Filter "Content Type: Books" im linken Panel setzen.
3. OA-Badge ("Open Access") in Ergebniszeile prüfen.
4. Auf Treffer klicken → Buchdetailseite öffnet.
5. Alternativ per DOI-Direktlink: `https://doi.org/10.1515/...` →
   DeGruyter-Detailseite.

## Volltext-Lokation

- Auf der Buchdetailseite: Button "PDF herunterladen" suchen.
  - OA-Titel: Button direkt verfügbar ohne Login.
  - Lizenzierte Titel: Button nur nach erfolgreichem Institutionszugang.
- `browser-use state` → Button-Index identifizieren.
- Achtung: Buchseite (`/book/<isbn>`) vs. Kapitelseite (`/document/<doi>`):
  - Buchseite → "Download all chapters as PDF" oder Einzelkapitel.
  - Kapitelseite → "PDF herunterladen" für einzelnes Kapitel.
- Vollbuch-Download bevorzugen wenn vorhanden.

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Auth-Wall / "Access options" statt Download-Button sichtbar.
  - Institutionszugang nicht konfiguriert oder Shibboleth fehlgeschlagen.
  - Nur Online-Lese-Option vorhanden (kein PDF-Download).
- `status: captcha` wenn CAPTCHA in `browser-use state` erkennbar →
  Screenshot sichern, User informieren.
- `status: no_match` wenn Suche 0 Treffer liefert.

## Bekannte Fallstricke

- Buch-DOI und Kapitel-DOI sind verschieden — `/book/<isbn>` ist der
  Buchkanon-Einstiegspunkt, `/document/<doi>` für einzelne Kapitel.
- Einzelne Kapitel können lizenziert sein, obwohl das Buch selbst OA ist —
  immer Buchseite prüfen, nicht nur Kapitelseite.
- CAPTCHA erscheint bei >5 schnellen Requests in Folge — mind. 3 Sekunden Pause.
- Shibboleth-Redirect ist mehrstufig: DeGruyter → DFN-AAI → Hochschule →
  zurück — vollständigen Redirect abwarten.
- Einige Bücher nur als eBook ohne freien PDF-Export verfügbar (DRM).
