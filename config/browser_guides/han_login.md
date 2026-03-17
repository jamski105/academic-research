# HAN-Server Login — Browser Navigation Guide

## URL-Schema

- **HAN Proxy Base:** `https://han.leibniz-fh.de/han/`
- **Ziel-URL:** `https://han.leibniz-fh.de/han/{SERVICE_PATH}`
- **Beispiel EBSCO:** `https://han.leibniz-fh.de/han/ebscohost`
- **Beispiel ProQuest:** `https://han.leibniz-fh.de/han/proquest`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Username-Feld | `input[name="username"], input[name="loginfmt"]` | `textbox "Email"` |
| Passwort-Feld | `input[name="password"], input[name="passwd"]` | `textbox "Password"` |
| Login-Button | `input[type="submit"], button[type="submit"]` | `button "Sign in"` |
| "Stay signed in?" | `input[id="idBtn_Back"]` | `button "No"` / `button "Yes"` |

## Workflow

### Erstanmeldung (einmalig pro Session)

1. `browser_navigate` → `https://han.leibniz-fh.de/han/{service}`
2. `browser_snapshot` → Login-Formular erkennen
3. **STOPP** → User informieren:
   ```
   HAN-Server Login erforderlich.
   Bitte loggen Sie sich im Browser-Fenster ein.
   Ich warte auf die Weiterleitung zur Zieldatenbank.
   ```
4. `browser_wait_for` → Warte auf Redirect zur Ziel-URL (Timeout: 120s)
5. `browser_snapshot` → Verifiziere, dass Zieldatenbank geladen ist

### Microsoft-Auth-Flow (häufig bei Hochschulen)

Der HAN-Server leitet oft zu `login.microsoftonline.com` weiter:

1. Seite zeigt Microsoft-Login
2. User gibt Email + Passwort ein
3. Mögliche MFA-Abfrage (Authenticator App)
4. "Stay signed in?" Dialog → User wählt
5. Redirect zurück zum HAN-Server → Zieldatenbank

**WICHTIG:** Credentials NIEMALS automatisch eingeben. Immer User manuell einloggen lassen.

## Bekannte Probleme

- **Session-Timeout:** HAN-Sessions laufen nach ~30 Minuten ab → Re-Login nötig
- **MFA:** Multi-Faktor-Authentifizierung kann nicht automatisiert werden
- **Redirect-Ketten:** Manchmal 3-4 Redirects bis zur Zieldatenbank → Geduld
- **Pop-ups:** Manche Datenbanken öffnen Terms-of-Service Pop-ups nach Login
