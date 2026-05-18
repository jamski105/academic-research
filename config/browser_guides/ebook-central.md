# Ebook Central (ProQuest) — Browser-Guide (Buch-Download)

**URL:** https://ebookcentral.proquest.com
**Auth:** Shibboleth / HAN / IP-basiert (Institutionszugang)
**Anti-Scraping:** niedrig (lizenzierter Zugriff), aber Session-Timeout nach Inaktivität.

## Login-Flow

1. `browser-use open https://ebookcentral.proquest.com`
2. "Sign in" oben rechts klicken.
3. `browser-use state` → "Sign in through your institution" suchen, klicken.
4. Hochschule im Suchfeld eingeben oder aus Liste wählen.
5. Shibboleth-Login: Hochschul-Credentials eingeben (aus Uni-Profil).
6. Auf Weiterleitung zurück zu Ebook Central warten.

Alternativ via HAN-Proxy: `han_login.md` zuerst ausführen, dann
`https://han.<uni-domain>/ebookcentral` aufrufen.

## Discovery-Pfad

1. Suchfeld im Header: Titel, Autor, ISBN eingeben.
2. `browser-use state` → Suchergebnisse prüfen.
3. Filter im linken Panel: "Subject", "Publication Date", "Language".
4. Trefferdetailseite öffnen → Lizenz- und Download-Optionen prüfen.
5. Alternativ über OPAC-Link: OPAC-Eintrag enthält oft Direktlink zu Ebook Central.

## Volltext-Lokation

- Auf Detailseite: "Full Book Download" suchen (wenn Lizenz vorhanden).
- `browser-use state` → Button-Index identifizieren, klicken.
- Falls "Full Book Download" fehlt: "Download Chapter" für kapitelweisen Download.
- Online-Reader ("Read Online") ist kein Download-Äquivalent — nicht verwenden.
- DRM-Hinweis prüfen: "Adobe DRM" bedeutet verschlüsseltes PDF.

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Nur Online-Reader verfügbar (kein "Full Book Download"-Button).
  - DRM-PDF mit Adobe-Encryption (nicht archivierbar).
  - Download-Limit erreicht (z. B. "You have reached the maximum number of
    checkouts").
  - Session-Timeout während Download.
- `status: captcha` wenn CAPTCHA sichtbar.
- `status: no_match` wenn ISBN nicht im Katalog.

## Bekannte Fallstricke

- DRM-PDFs (Adobe Digital Editions) sind technisch downloadbar, aber nicht
  ohne Adobe-Software lesbar und nicht langfristig archivierbar — als
  `pickup_required` behandeln.
- Download-Limit pro User/Tag variiert je Lizenzvertrag (meist 20–50 Seiten
  oder 1 Kapitel/Tag bei Pay-per-Use).
- Session-Timeout nach ~15 Minuten Inaktivität → neu anmelden.
- "Full Book Download" nur bei Institutional-Ownership-Lizenzen — bei
  Short-Term-Loan-Lizenzen nur kapitelweise.
- Einige Institutionen haben Ebook Central nur über HAN eingerichtet, nicht
  direkt — HAN-Flow dann pflichtmäßig.
