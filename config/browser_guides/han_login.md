# HAN-Server Login — Browser Navigation Guide

## URL-Schema

- **HAN Proxy Base:** `http://lfh.hh-han.com/han/`
- **Ziel-URL:** `http://lfh.hh-han.com/han/{service}/{target-url}`
- **Beispiel Springer E-Books IT:** `http://lfh.hh-han.com/han/springer-e-books-it/doi.org/{DOI}`
- **Beispiel Springer E-Books Technik:** `http://lfh.hh-han.com/han/springer-e-books-2023-technik/doi.org/{DOI}`
- **Beispiel ProQuest:** `http://lfh.hh-han.com/han/proquest/...`
- **OpenID Connect Redirect:** `https://login.lfh.hh-han.com/hanopenidc/`
- **Microsoft OAuth:** `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize?...`

### Bekannte HAN-Service-Namen

| Service | URL-Pfad | Beschreibung |
|---------|----------|--------------|
| Springer E-Books IT | `springer-e-books-it` | Springer IT + Informatik Paket |
| Springer E-Books Technik | `springer-e-books-2023-technik` | Springer Technik Paket (Jahrgang variiert) |
| ProQuest | `proquest` | ProQuest Dissertations & Theses |
| EBSCO | (via `publications.ebsco.com` externe Links) | Redirect ueber HAN zu BSP/CASC |

## Redirect-Kette

Der HAN-Proxy leitet ueber OpenID Connect zu Microsoft OAuth weiter:

```
http://lfh.hh-han.com/han/{service}/{target}
  → https://login.lfh.hh-han.com/hanopenidc/  (HAN OpenID Connect)
  → https://login.microsoftonline.com/...       (Microsoft OAuth)
  → [User loggt sich ein]
  → https://login.lfh.hh-han.com/hanopenidc/   (Callback)
  → {target-datenbank}                          (Ziel)
```

## Selektoren (Microsoft Login)

Der Login erfolgt ueber `login.microsoftonline.com`. Die Sprache ist **Deutsch**.
Der Login ist **mehrstufig**: Schritt 1 (Email) → Schritt 2 (Passwort) → optional MFA → optional "Angemeldet bleiben?"

### Schritt 1: Email-Eingabe

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Email-Feld | `input[name="loginfmt"]` | `textbox "Geben Sie Ihre E-Mail-Adresse, Telefonnummer oder Ihren Skype-Namen ein."` |
| Weiter-Button | `input[type="submit"]#idSIButton9` | `button "Weiter"` |
| Hilfe-Link | — | `link "Sie können nicht auf Ihr Konto zugreifen?"` |

### Schritt 2: Passwort-Eingabe

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Passwort-Feld | `input[name="passwd"]` | `textbox "Kennwort eingeben"` (DE) |
| Anmelden-Button | `input[type="submit"]#idSIButton9` | `button "Anmelden"` |

### Schritt 3 (optional): "Angemeldet bleiben?"

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Ja-Button | `input#idSIButton9` | `button "Ja"` |
| Nein-Button | `input#idBtn_Back` | `button "Nein"` |

## Workflow

### Erstanmeldung (einmalig pro Session)

1. `browser_navigate` → `http://lfh.hh-han.com/han/{service}/{target-url}`
2. `browser_snapshot` → Login-Seite erkennen (Redirect zu `login.microsoftonline.com`)
3. **STOPP** → User informieren:
   ```
   HAN-Server Login erforderlich.
   Der Browser zeigt die Microsoft-Anmeldeseite.
   Bitte loggen Sie sich mit Ihren Hochschul-Credentials ein.
   Ich warte auf die Weiterleitung zur Zieldatenbank.
   ```
4. `browser_wait_for` → Warte auf Redirect zur Ziel-URL (Timeout: 120s)
   - Erkennungszeichen: URL enthaelt NICHT mehr `login.microsoftonline.com` und NICHT mehr `login.lfh.hh-han.com`
5. `browser_snapshot` → Verifiziere, dass Zieldatenbank geladen ist

**WICHTIG:** Credentials NIEMALS automatisch eingeben. Immer User manuell einloggen lassen.

### Session wiederverwenden

Nach erfolgreichem Login bleibt die HAN-Session aktiv (~30 Minuten).
Weitere HAN-Links in derselben Session werden automatisch durchgeleitet — kein erneuter Login noetig.

**Pruefen ob Session aktiv:**
1. `browser_navigate` → HAN-URL
2. `browser_snapshot` → Wenn Zieldatenbank direkt geladen → Session aktiv
3. Wenn erneut Microsoft-Login erscheint → Session abgelaufen → erneut STOPP + User informieren

## Bekannte Probleme

- **Session-Timeout:** HAN-Sessions laufen nach ~30 Minuten Inaktivitaet ab → Re-Login noetig
- **MFA:** Multi-Faktor-Authentifizierung (Authenticator App, SMS) kann nicht automatisiert werden
- **Redirect-Ketten:** 3-4 Redirects bis zur Zieldatenbank (HAN → OpenID → Microsoft → Callback → Ziel) → Geduld, bis zu 10 Sekunden
- **Pop-ups:** Manche Datenbanken zeigen Terms-of-Service Pop-ups nach Login
- **HTTP vs HTTPS:** HAN-Basis-URL ist `http://` (nicht `https://`), Redirect geht dann auf HTTPS
- **Service-Namen variieren:** Springer-Pakete haben Jahrgang im Namen (z.B. `springer-e-books-2023-technik`) — bei Fehler ggf. OPAC-Volltext-Links pruefen fuer korrekten Service-Namen
- **Locale:** Microsoft-Login ist auf Deutsch — Accessibility-Labels sind deutsch ("Weiter", "Anmelden", nicht "Next", "Sign in")
- **Tenant-ID:** Die Leibniz FH nutzt Tenant `4816982b-c06f-4896-8381-a1c39af4612e` — bei Aenderung koennten Redirects brechen
