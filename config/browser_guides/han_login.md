# HAN-Login — Shared Auth-Guide für Leibniz FH

**URL:** https://han.leibniz-fh.de
**Purpose:** Zentrale Authentifizierung für EBSCOhost, ProQuest, OPAC und weitere lizenzierte Datenbanken der Leibniz FH.
**Credentials-Quelle:** `~/.academic-research/credentials.json` — Keys `han_user`, `han_password`. Falls Datei fehlt oder Keys leer, User informieren und Modul überspringen.

## Login-Flow

1. `browser-use open https://han.leibniz-fh.de`
2. `browser-use state` → Login-Formular finden (Felder meist "Benutzername"/"Username" und "Passwort"/"Password")
3. Benutzername eintippen: `browser-use input <idx_username> "<han_user>"`
4. Passwort eintippen: `browser-use input <idx_password> "<han_password>"`
5. "Login"-Button per Index klicken: `browser-use click <idx_login>`
6. Auf Weiterleitung warten, dann zur Zieldatenbank navigieren (meist Link in der HAN-Portal-Seite).

## Fehlerbehandlung

- Falsche Credentials → klare Fehlermeldung der HAN-Seite erkennbar in `state`-Output ("Anmeldung fehlgeschlagen" o. ä.). Abbrechen, User informieren.
- 2FA-Prompt → `browser-use screenshot`, User muss manuell bestätigen. Skill pausiert.
- Wartung-Ankündigung → Datenbank-Zugriff heute unmöglich. User informieren, API-Suche fortsetzen.

## Hinweise

- Eine Session reicht meist für alle Leibniz-FH-Datenbanken innerhalb eines Tages.
- Credentials niemals in Logs oder Commits schreiben — Dateipfad ist in `.gitignore`.
