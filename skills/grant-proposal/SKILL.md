---
name: grant-proposal
description: Use this skill when the user needs to write a grant proposal / Förderantrag. Triggers on "Förderantrag / Foerderantrag schreiben", "DFG-Antrag", "BMBF-Antrag", "EU-Antrag / EU-Horizon-Antrag", "Drittmittelantrag", "grant proposal", or when the user asks for funding application support. Erstellt strukturierte Förderanträge mit Vault-Quellen und Bibliographie; für Kapiteltext → `chapter-writer`.
license: MIT
---

# Grant-Proposal

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Erstellt strukturierte Förderanträge für DFG, BMBF und EU-Horizon-Europe
auf Basis von Vault-Quellen. Liefert ein vollständiges Antrags-Skelett mit
korrekter Förderlinie-Struktur und Bibliographie-Block.

## Abgrenzung

Erstellt Förderantragsstrukturen und -entwürfe mit Vault-basierten Quellen.
Für allgemeinen Kapiteltext → `chapter-writer`.
Für LaTeX-Ausgabe → `latex-export`.

## Opt-in Guard

Dieser Skill ist **default off**. Er wird nur aktiv, wenn in `./academic_context.md`
der Eintrag `output_targets` den Wert `grant-proposal` enthält:

```
output_targets:
  - grant-proposal
```

Fehlt dieser Eintrag, frage den User, ob er ihn aktivieren möchte, bevor fortgefahren wird.

## Workflow

### 1. Förderlinie wählen

Frage den User via `AskUserQuestion` nach der gewünschten Förderlinie:

- **DFG** — Deutsche Forschungsgemeinschaft (Sachbeihilfe, Emmy Noether etc.)
- **BMBF** — Bundesministerium für Bildung und Forschung (Förderlinien-spezifisch)
- **EU-Horizon** — Horizon Europe (ERC, MSCA, Kooperationsprojekte)

Lade die entsprechende Referenzdatei:
- DFG → `skills/grant-proposal/references/dfg.md`
- BMBF → `skills/grant-proposal/references/bmbf.md`
- EU-Horizon → `skills/grant-proposal/references/eu-horizon.md`

### 2. Vault-Quellen sammeln

```
vault.search("<Forschungsthema>", k=10)
→ relevante paper_id + snippet

vault.find_quotes(paper_id, query="<Antragstitel>", k=3)
→ Zitat-Kandidaten für Bibliographie
```

Baue eine Bibliographie aus den gefundenen Quellen im Format der Förderlinie.

### 3. Antrags-Skelett erstellen

Erstelle das Skelett nach der Struktur der gewählten Referenzdatei.
Platzhalter `[INHALT ERFORDERLICH]` für Abschnitte ohne Vault-Belege.

### 4. Bibliographie-Block

Füge am Ende des Antrags einen vollständigen Bibliographie-Block ein.
DFG: max. 10 Seiten Haupttext + Bibliographie als Anhang.
Format: DIN ISO 690 / APA7 je nach Förderlinie.

### 5. User-Review

Vorlage abschnittsweise dem User zur Freigabe vorlegen.
Nie ohne Freigabe zum nächsten Abschnitt übergehen.

## Wichtige Regeln

- Kein Antrags-Text ohne Vault-Quellen für Kernannahmen
- Bibliographie-Pflicht — kein Antrag ohne Literaturverzeichnis
- Förderlinie-Struktur strikt einhalten (Seitenlimits beachten)
- Opt-in via `output_targets` prüfen vor jedem Aufruf
- DFG, BMBF und EU-Horizon haben unterschiedliche Seitenformate und Anforderungen
