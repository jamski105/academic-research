# KVK — Karlsruher Virtueller Katalog — Browser-Guide

**URL:** https://kvk.bibliothek.kit.edu
**Auth:** keine für Metadaten-Abfrage; Fernleihe/Bestellung verlangen Bibliothekskonto
**Anti-Scraping:** niedrig — KVK ist öffentlicher Dienst.

## Login-Flow

Für reine Standort-/Verfügbarkeitsabfragen kein Login erforderlich.

Für Fernleihe / Direktbestellung (nicht automatisiert):
1. Bibliotheks-OPAC der gewählten Bibliothek aufrufen.
2. Dort mit Bibliothekskonto anmelden.
3. Fernleihe-Formular ausfüllen — **nicht automatisch auslösen**,
   nur Standort-Info für Pickup-Liste zurückgeben.

## Discovery-Pfad

1. `browser-use open https://kvk.bibliothek.kit.edu`
2. Suchformular ausfüllen: ISBN (bevorzugt), Titel oder Autor.
3. Datenbanken auswählen (Standard: HEIDI, BVB, GBV, SWB — alle aktivieren).
4. "Suchen"-Button klicken.
5. `browser-use state` → Ergebnisliste mit Bibliotheksbeständen prüfen.
6. Für jeden Treffer: Bibliotheks-Name, Standort, Signatur notieren.

## Volltext-Lokation

KVK liefert **keinen Volltext** — gibt ausschließlich Standort-Informationen zurück.

Output-Format für Pickup-Liste:

```json
{
  "status": "pickup_required",
  "kvk_hits": [
    {
      "library": "Bayerische Staatsbibliothek",
      "location": "München",
      "call_number": "4 Ph.pr. 123",
      "loan_type": "vor_ort"
    }
  ]
}
```

Master-Agent entscheidet, welche Bibliotheken in die Pickup-Liste aufgenommen werden.

## Pickup-Triggers

- KVK-Subagent liefert **immer** `status: pickup_required` — KVK ist
  Standort-Finder, kein Downloader.
- Pickup-Daten enthalten: Bibliotheksname, Ort, Signatur, Ausleihbarkeit
  (Lesesaal, Ausleihe, Fernleihe).
- `status: no_match` wenn KVK 0 Treffer in allen Datenbanken liefert.

## Bekannte Fallstricke

- KVK zeigt physische UND digitale Bestände gemischt — "Online-Ressource"-Treffer
  verweisen auf Volltext-URLs (können als sekundäre Discovery genutzt werden).
- Nicht jede Bibliothek hat Online-Bestellung aktiviert — Fernleihe manuell.
- Signatur-Format variiert stark je Bibliothek — nur als Referenz zurückgeben,
  nicht parsen.
- Einige Datenbanken haben Ladezeiten >5 Sekunden — KVK wartet auf alle
  Teilbibliotheken, bevor Ergebnisse angezeigt werden.
- Timeout bei sehr breiten Suchen (viele Datenbanken aktiv) — ggf. Suche
  auf GBV + BVB einschränken.
