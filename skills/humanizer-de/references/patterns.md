<!-- vendored from https://github.com/marmbiz/humanizer-de (MIT License)
     Original author: Martin Moeller (www.martin-moeller.biz)
     Pattern descriptions adapted from German Wikipedia (CC BY-SA 4.0)
     See SKILL.md for full attribution.
-->

# Humanizer-de Muster-Bibliothek

## Kurzreferenz

| # | Muster | Schwere | Schlüssel-Indikatoren |
|---|--------|---------|-----------------------|
| 1 | Übermäßige Betonung von Symbolik | HIGH | "steht als Zeugnis", "spielt eine wichtige Rolle", "symbolisiert" |
| 2 | Werbesprache und Superlative | HIGH | "atemberaubend", "einzigartig", "faszinierend", "spektakulär" |
| 3 | Redaktionelle Kommentare | HIGH | "es ist wichtig zu bemerken", "es sollte hervorgehoben werden" |
| 4 | Mechanische Konjunktionen | HIGH | "darüber hinaus", "außerdem", "ferner", "ebenfalls" |
| 5 | Abschnitts-Zusammenfassungen | HIGH | "zusammenfassend", "insgesamt", "kurz gesagt" |
| 6 | Unpassendes "Fazit" | MEDIUM | "== Fazit ==", "== Zusammenfassung ==" |
| 7 | Zu perfekte Dichotomie | MEDIUM | "Trotz X... steht Y vor Z", "Obwohl... jedoch..." |
| 8 | Negative Parallelismen und abgehackte Verneinungen | MEDIUM | "nicht nur... sondern auch", "kein Raten.", symmetrische Satzstrukturen |
| 9 | Trikolon (Regel der Drei) | MEDIUM | Tripel-Aufzählungen ohne echten Grund |
| 10 | Partizip-I-Konstruktionen | HIGH | "gewährleistend", "hervorhebend", "ermöglichend" |
| 11 | Vage Autoritäten | HIGH | "Branchenberichte zeigen", "Manche argumentieren" |
| 12 | Falsche Erweiterung ("von... bis") | MEDIUM | "von traditionellen bis modernen" |
| 13 | Übermäßige Fettschrift | MEDIUM | **wichtige Wörter** in Absätzen fett |
| 14 | Falsche Listen | LOW | `•` statt `-`, Markdown-Syntax statt Wikitext |
| 15 | Emojis vor Überschriften | LOW | "🎓 Bildung", "📊 Statistiken" |
| 16 | Gedankenstriche Überbenutzung | MEDIUM | Mehrere pro Absatz, gepaarte Einschübe, --/—/– Varianten |
| 17 | Briefartiges Schreiben | HIGH | "Betreff:", "Liebe Wikipedia-Editoren", "Mit freundlichen Grüßen" |
| 18 | Kollaborative Kommunikation | HIGH | "Ich hoffe, das hilft", "Natürlich!", "Lassen Sie mich wissen" |
| 19 | Hinweise auf Wissensgrenzen | HIGH | "Stand [Datum]", "Bis zu meinem letzten Update" |
| 20 | Prompt-Ablehnung | HIGH | "Als KI-Sprachmodell kann ich nicht...", "Es tut mir leid, aber..." |
| 21 | Platzhaltertext | HIGH | "[Name einfügen]", "[Datum hier]", "TODO:" |
| 22 | Links zu Suchanfragen | HIGH | "https://www.google.com/search?q=..." |
| 23 | Markdown statt Wikitext | MEDIUM | `# Überschrift` statt `== Überschrift ==` |
| 24 | Fehlerhafter Wikitext und KI-Tool-Artefakte | MEDIUM | Unvollständige Template-Tags, oaicite, contentReference |
| 25 | Defekte Links | MEDIUM | 404-Fehler, Links zu nicht-existenten Artikeln |
| 26 | Zitatfabrikation und ungültige Referenzen | MEDIUM | Erfundene Quellen, ungültige DOIs/ISBNs, halluzinierte Publikationen |
| 27 | Inkorrekte Referenzen-Format | MEDIUM | Englisches Datumsformat, falsche Reihenfolge |
| 28 | Falsche Kategorien | MEDIUM | `[[Category:...]]` statt `[[Kategorie:...]]` |
| 29 | Abrupte Abbrüche | LOW | Text bricht mitten im Satz ab |
| 30 | Wechsel im Schreibstil | MEDIUM | Absätze klingen wie verschiedene Autoren |
| 31 | Bearbeitungszusammenfassungen in Ich-Form | LOW | "Ich habe einen Absatz über...", "Meine Änderungen..." |
| 32 | Persuasive Autoritäts-Floskeln | MEDIUM | "Die eigentliche Frage ist", "Im Kern", "In Wirklichkeit" |
| 33 | Signposting und Ankündigungen | MEDIUM | "Schauen wir uns an", "Hier ist, was Sie wissen müssen" |
| 34 | Fragmentierte Überschriften | LOW | Generischer Einzeiler nach Überschrift ("Geschwindigkeit zählt.") |
| 35 | Rhetorische Fragen als Fake-Engagement | MEDIUM | "Aber was bedeutet das?", "Haben Sie sich jemals gefragt?" |
| 36 | Universelle Menschheitserfahrungs-Eröffnung | MEDIUM | "Seit jeher", "Seit Anbeginn der Zivilisation", "Schon immer" |
| 37 | "In der heutigen X-Welt" Framing | MEDIUM | "In der heutigen digitalen Welt", "Im Zeitalter der..." |
| 38 | Aspirativer Unternehmensschluss | MEDIUM | "bestens aufgestellt", "die Möglichkeiten sind grenzenlos" |
| 39 | Passivkonstruktionen und subjektlose Fragmente | MEDIUM | "wurde durchgeführt", "es wird empfohlen", "Keine Konfiguration nötig." |
| 40 | Konditional-Stapel | MEDIUM | "Wenn das Argument stimmt, und wenn die Evidenz...", gehäufte "wenn"-Klauseln |
| 41 | Fehlkalibriertes epistemisches Vertrauen | MEDIUM | Über-Behauptung: "grundlegend", "entscheidend"; Über-Absicherung: "scheint möglicherweise" |
| 42 | Beleginkongruenz | HIGH | Quelle existiert, belegt aber die Aussage nicht |
| 43 | Versteckte Unicode-Zeichen | HIGH | Zero-Width-Space (U+200B), Soft-Hyphen, BOM, Bidi-Controls (U+202A–E, U+2066–9) |
| 44 | Standard-Kapitel ohne Substanz | MEDIUM | Standard-Überschrift + unbelegter Fülltext; nicht kürzen, sondern konkretisieren/integrieren |
| 45 | Anglizismus-Strukturen | MEDIUM | Harte Calques & False Friends: "am Ende des Tages", "eventuell" = "schließlich", "aktuell" = "tatsächlich" |

---

## Die 45 Muster

### Sprache und Tonfall (12 Muster)

#### 1. Übermäßige Betonung von Symbolik [HIGH]
**Problem:** Bestimmte Wendungen erzeugen symbolische, zu perfekte Bedeutungen.

Häufige Indikatoren:
- "steht als Zeugnis für"
- "ist ein Beweis für"
- "spielt eine wichtige Rolle bei"
- "steht für"
- "symbolisiert"

**Warum LLMs das tun:** Trainiert auf philosophischen Texten und Wikipedia-Artikeln mit erhöhtem abstraktem Diskurs.

**Beispiel:**

❌ Schlecht: "Die Kathedrale steht als Zeugnis für die künstlerische Brillanz des Mittelalters."

✓ Besser: "Die Kathedrale zeigt die Handwerkskunst des Mittelalters – und beeindruckt noch heute."

#### 2. Werbesprache und Superlative [HIGH]
**Problem:** Übertriebene Begeisterung, die mehr nach Marketing als nach neutraler Beschreibung klingt.

Häufige Indikatoren:
- "reiches kulturelles Erbe"
- "atemberaubend"
- "unbedingt besuchen"
- "spektakulär"
- "faszinierend"
- "einzigartig"

**Warum LLMs das tun:** Marketing-Texte sind im Trainingsmaterial überrepräsentiert.

**Beispiel:**

❌ Schlecht: "Die atemberaubende Altstadt mit ihrem reichen kulturellen Erbe zieht Besucher aus aller Welt an."

✓ Besser: "Die Altstadt zieht Besucher an. Ihre Geschichte reicht Jahrhunderte zurück."

#### 3. Redaktionelle Kommentare und Meta-Sprache [HIGH]
**Problem:** Der Text beschreibt sich selbst, statt direkten Inhalt zu vermitteln.

Häufige Indikatoren:
- "es ist wichtig zu bemerken"
- "es kann nicht ignoriert werden"
- "keine Diskussion wäre vollständig ohne"
- "es sollte hervorgehoben werden"
- "es ist erwähnenswert"

**Warum LLMs das tun:** Versucht, Gewichtung und Relevanz zu signalisieren, wo der Kontext unklar ist.

**Beispiel:**

❌ Schlecht: "Es ist wichtig zu bemerken, dass die Bevölkerung in diesem Zeitraum gewachsen ist."

✓ Besser: "Die Bevölkerung wuchs zwischen 1950 und 2000 um 30 Prozent."

#### 4. Mechanische Konjunktionen [HIGH]
**Problem:** Bestimmte Übergangswörter werden übermäßig mechanisch und klischeehaft eingesetzt.

Häufige Indikatoren:
- "darüber hinaus" (zu häufig)
- "außerdem"
- "ferner"
- "gleichzeitig"
- "ebenfalls"

**Warum LLMs das tun:** Diese Wörter sind strukturelle Marker im Training und werden übernutzt.

**Beispiel:**

❌ Schlecht: "Das Unternehmen wurde 1990 gegründet. Darüber hinaus beschäftigt es heute 500 Mitarbeiter. Darüber hinaus ist es in 15 Ländern tätig."

✓ Besser: "Das Unternehmen wurde 1990 gegründet und beschäftigt heute 500 Mitarbeiter in 15 Ländern."

#### 5. Abschnitts-Zusammenfassungen [HIGH]
**Problem:** Jeder Absatz wird automatisch zusammengefasst, statt natürlich zu fließen.

Häufige Indikatoren:
- "zusammenfassend"
- "abschließend"
- "insgesamt"
- "im Wesentlichen"
- "kurz gesagt"

**Warum LLMs das tun:** Versucht, Struktur zu schaffen, wo sie nicht nötig ist.

**Beispiel:**

❌ Schlecht: "Die Region hat drei Universitäten, ein Krankenhaus und eine Bibliothek. Insgesamt verfügt die Stadt über gute Infrastruktur."

✓ Besser: "Die Region hat drei Universitäten, ein Krankenhaus und eine Bibliothek – eine gute Grundversorgung."

#### 6. Unpassendes "Fazit" [MEDIUM]
**Problem:** Wikipedia-Artikel enden mit explizitem "Fazit", was unpassend ist.

Häufige Indikatoren:
- "== Fazit =="
- "== Zusammenfassung =="
- Explizite Conclusion-Sektion

**Warum LLMs das tun:** Akademische Schreibweise wird als Struktur imitiert.

**Lösung:** Entfernen oder in natürliche Übergänge umwandeln.

#### 7. Schlussfolgerungen mit zu starker Dichotomie [MEDIUM]
**Problem:** "Trotz X... steht Y vor Z" – zu perfekt gedachte Gegensätze.

Häufige Indikatoren:
- "Trotz seiner Erfolge steht das Unternehmen vor Herausforderungen"
- "Obwohl... jedoch..."
- "Während X... bleibt Y..."

**Warum LLMs das tun:** Binäre Argumentationsstruktur im Training.

**Beispiel:**

❌ Schlecht: "Trotz seiner technologischen Fortschritte steht das Land vor wirtschaftlichen Herausforderungen."

✓ Besser: "Das Land macht technologische Fortschritte, kämpft aber mit wirtschaftlichen Problemen."

#### 8. Negative Parallelismen und abgehackte Verneinungen [MEDIUM]
**Problem:** "Nicht nur... sondern auch" – zu argumentativ, zu literarisch. Dazu kommen abgehackte Verneinungsfragmente am Satzende wie "kein Raten", "kein Aufwand", die als Kurzform statt als echter Satz angehängt werden.

Häufige Indikatoren:
- "nicht nur... sondern auch"
- "weder... noch... sondern"
- Symmetrische Satzstrukturen
- Abgehackte Verneinungen am Satzende: "kein Raten.", "keine Kompromisse.", "kein Aufwand."

**Warum LLMs das tun:** Rhetorische Effekte aus literarischen Quellen. Die abgehackten Fragmente imitieren knappen Werbetext.

**Beispiel:**

❌ Schlecht: "Die Stadt ist nicht nur ein Handelszentrum, sondern auch ein Kulturzentrum."

✓ Besser: "Die Stadt ist Handels- und Kulturzentrum."

❌ Schlecht (abgehackte Verneinung): "Die Optionen kommen aus dem gewählten Element, kein Raten."

✓ Besser: "Die Optionen kommen aus dem gewählten Element, ohne dass der Nutzer raten muss."

#### 9. Trikolon und schematische Aufzählungen (Regel der Drei) [MEDIUM]
**Problem:** Übermäßige Nutzung der Regel-der-Drei als rhetorisches Mittel. Zusätzlich: auffällige Rundzahlen bei Listen (5, 7 oder 10 Punkte) als schematisches Muster.

Häufige Indikatoren:
- Drei parallele Sätze/Phrasen hintereinander
- "X, Y und Z waren alle charakteristisch für..."
- Tripel-Aufzählungen ohne echten Grund
- Listen mit verdächtig runder Länge (genau 5, 7 oder 10 Punkte), wenn die Sache selbst keine solche Struktur verlangt

**Warum LLMs das tun:** Trikolon ist ein starkes rhetorisches Muster in der Schreibweise. Runde Listenlängen entstehen durch Trainingsdaten, in denen „Top 5/7/10"-Artikel häufig vorkommen.

**Beispiel:**

❌ Schlecht: "Die Wirtschaft war vielfältig, kreativ und widerstandsfähig."

✓ Besser: "Die Wirtschaft war kreativ und widerstandsfähig."

#### 10. Oberflächliche Analysen mit Partizip I [HIGH]
**Problem:** Zu viele "-end" Partizipien, die Aktion beschreiben ohne echte Tiefe.

Häufige Indikatoren:
- "gewährleistend"
- "hervorhebend"
- "zeigend"
- "darstellend"
- "ermöglichend"

**Warum LLMs das tun:** Diese Konstruktionen sind grammatikalisch korrekt, erzeugen aber einen oberflächlichen, technischen Ton.

**Formal-Modus-Ausnahme:** In wissenschaftlichen Texten sind Partizip-I-Konstruktionen stilistisch akzeptiert. In diesem Modus überspringen.

**Beispiel:**

❌ Schlecht: "Die Technologie ermöglicht, dass Unternehmen ihre Effizienz steigern, ihre Kosten senken und ihre Konkurrenzfähigkeit verbessern."

✓ Besser: "Die Technologie hilft Unternehmen effizienter zu werden, Kosten zu senken und konkurrenzfähig zu bleiben."

#### 11. Vage Autoritäten [HIGH]
**Problem:** Unspezifische Quellen, die keinen echten Beweis liefern.

Häufige Indikatoren:
- "Branchenberichte zeigen"
- "Beobachter haben zitiert"
- "Es wird gesagt"
- "Manche argumentieren"
- "Mehrere Studien deuten darauf hin" (ohne Quelle)

**Warum LLMs das tun:** Kann keine echten Quellen zitieren, also erfindet es Platzhalter.

**Abgrenzung:** Muster 11 = keine konkrete Quelle genannt. Muster 26 = Quelle fabriziert (existiert nicht). Muster 42 = Quelle existiert, belegt aber die Aussage nicht.

Keine Quelle erfinden. Entweder: echte Quelle einfügen wenn bekannt, Zuschreibung entfernen, oder mit [ECHTE QUELLE NÖTIG] markieren.

**Beispiel:**

❌ Schlecht: "Branchenberichte zeigen, dass der Markt wächst."

✓ Besser: "Der Markt wächst (laut Wirtschaftsministerium 2024)." oder "Der Markt wächst – ein Trend, der seit 2020 beobachtet wird."

#### 12. Falsche Erweiterung ("von... bis") [MEDIUM]
**Problem:** "Von X bis Y" figurativ verwendet, wo es nicht passt.

Häufige Indikatoren:
- "von traditionellen bis modernen"
- "von klein bis groß"
- "von arm bis reich"
- Übertragene Verwendung von Bereichsbeschreibungen

**Warum LLMs das tun:** Stylistische Marker aus Fachtext-Training.

**Beispiel:**

❌ Schlecht: "Die Stadt zieht Menschen von verschiedensten bis progressivsten Überzeugungen an."

✓ Besser: "Die Stadt zieht Menschen mit sehr unterschiedlichen Überzeugungen an."

### Stil (4 Muster)

#### 13. Übermäßige Fettschrift [MEDIUM]
**Problem:** Bold wird für Emphasis statt für echte Struktur verwendet.

Häufige Indikatoren:
- **wichtige Wörter** in Absätzen fett
- Mehrere fettgedruckte Wörter pro Absatz
- Bold für Hervorhebung statt für Struktur

**Warum LLMs das tun:** Versucht, Wichtigkeit zu signalisieren, wo Klarheit hilft.

**Lösung:** Entfernen oder in Überschriften umwandeln.

#### 14. Falsche Listen [LOW]
**Problem:** Bullet-Punkte in nicht-Wikitext-Format in Wikipedia-Artikel.

Häufige Indikatoren:
- `•` statt `-` oder `*`
- `–` statt `*` für Aufzählungen
- Markdown-Syntax statt Wikitext

**Warum LLMs das tun:** Trainiert auf Markdown und Office-Formaten.

**Lösung:** In korrektes Wikitext-Format konvertieren.

#### 15. Emojis vor Überschriften [LOW]
**Problem:** Emojis werden verwendet, um visuelle Struktur zu schaffen.

Häufige Indikatoren:
- "🎓 Bildung"
- "📊 Statistiken"
- "🌍 Globaler Kontext"

**Warum LLMs das tun:** Modern wirken, aber nicht für Wikipedia.

**Lösung:** Entfernen.

#### 16. Gedankenstriche Überbenutzung [MEDIUM]
**Problem:** Gedankenstriche (–, —, --) werden von LLMs als Stilmittel übermäßig eingesetzt. Ein einzelner Gedankenstrich pro Absatz kann legitim sein; mehrere pro Absatz sind ein starker KI-Tell.

Häufige Indikatoren:
- "Das Projekt – durchgeführt von..." (statt Komma)
- Mehrere Gedankenstriche pro Absatz
- Als Satzzeichen statt Klammer verwendet
- Gepaarte Einschübe: "Der Bericht – der drei Kontinente abdeckte – kam zum Schluss..."
- Spaced Em-Dashes: "Die Politik — ohne Vorwarnung angekündigt — betrifft..."
- Doppelstriche als Ersatz: "Die Änderungen -- laut Kritikern überfällig -- treten sofort in Kraft."

**Warum LLMs das tun:** Englische Schreibweise wird imitiert. Gepaarte Einschübe sehen eingeschoben aus, nicht geschrieben.

**Ersetzungshierarchie** (in Prioritätsreihenfolge):
1. **Punkt** (80% der Fälle – zwei Sätze statt eines mit Strich)
2. **Komma**
3. **Doppelpunkt**
4. **Semikolon**
5. **Klammer**
6. **Satz umschreiben**

**Beispiel:**

❌ Schlecht: "Die neue Regelung – ohne Vorwarnung angekündigt – betrifft Tausende. Die Änderungen – laut Kritikern überfällig – treten sofort in Kraft."

✓ Besser: "Die neue Regelung wurde ohne Vorwarnung angekündigt und betrifft Tausende. Die Änderungen treten sofort in Kraft, was Kritiker für überfällig halten."

**Kein Problem, wenn:** Ein einzelner Gedankenstrich pro Absatz als bewusstes Stilmittel dient und sich nicht wiederholt.

### Kommunikation (6 Muster)

#### 17. Briefartiges Schreiben [HIGH]
**Problem:** Artikel sind als Briefe strukturiert, nicht als Inhalte.

Häufige Indikatoren:
- "Betreff: ..."
- "Liebe Wikipedia-Editoren"
- "Vielen Dank für..."
- "Mit freundlichen Grüßen"

**Warum LLMs das tun:** ChatBot-Verhalten, nicht Enzyklopädie-Verhalten.

**Lösung:** Vollständig entfernen oder umschreiben.

#### 18. Kollaborative Kommunikation [HIGH]
**Problem:** Der Text spricht den Leser direkt an, statt Fakten bereitzustellen.

Häufige Indikatoren:
- "Ich hoffe, das hilft"
- "Natürlich!"
- "Lassen Sie mich wissen"
- "Bitte fragen Sie, wenn..."
- "Wie Sie sehen können..."
- "Ich helfe Ihnen gerne"
- "Selbstverständlich!"

Vollständig löschen. Beim eigentlichen Inhalt anfangen.

**Warum LLMs das tun:** Trainiert, höflich und engagiert zu sein.

**Beispiel:**

❌ Schlecht: "Wie Sie sehen können, war die Produktivität beeindruckend. Lassen Sie mich wissen, wenn Sie weitere Fragen haben!"

✓ Besser: "Die Produktivität war in dieser Zeit bemerkenswert."

#### 19. Hinweise auf Wissensgrenzen [HIGH]
**Problem:** Der Text offenbart seine KI-Natur durch Datums-Hinweise.

Häufige Indikatoren:
- "Stand [Datum]"
- "Bis zu meinem letzten Update"
- "Nach meinem Wissen"
- "[Aktualisierung erforderlich]"

**Warum LLMs das tun:** Versucht, Ehrlichkeit zu zeigen.

**Lösung:** Entfernen oder in neutrale Quellen umwandeln.

#### 20. Prompt-Ablehnung [HIGH]
**Problem:** Der Text lehnt Anfragen ab wie ein Chatbot.

Häufige Indikatoren:
- "Als KI-Sprachmodell kann ich nicht..."
- "Es tut mir leid, aber..."
- "Ich kann keine aktuelle Information bereitstellen..."
- "Das liegt außerhalb meiner Fähigkeiten"

**Warum LLMs das tun:** Sicherheitsrichtlinien und Höflichkeit.

**Lösung:** Entfernen vollständig.

#### 21. Platzhaltertext [HIGH]
**Problem:** Template-Platzhalter wurden nicht gefüllt.

Häufige Indikatoren:
- "[Name einfügen]"
- "[Datum hier]"
- "[Quelle erforderlich]" (in Artikel statt Meta)
- "TODO:"
- "[Bearbeiter Name]"

**Warum LLMs das tun:** Kann keine echten Werte generieren, hinterlässt Platzhalter.

**Lösung:** Entfernen. Füllen nur, wenn der tatsächliche Wert aus dem übergebenen Kontext sicher ableitbar ist; externe Recherche liegt außerhalb des Skill-Umfangs. Im Zweifel entfernen.

#### 22. Links zu Suchanfragen statt Referenzen [HIGH]
**Problem:** URLs sind Google-Suchanfragen statt echte Referenzen.

Häufige Indikatoren:
- "https://www.google.com/search?q=..."
- "https://duckduckgo.com/?q=..."
- Suchanfragen in Fußnoten

**Warum LLMs das tun:** Kann keine echte URL recherchieren.

**Lösung:** Entfernen. Ersetzen nur, wenn eine echte, im Kontext vorhandene Quelle verfügbar ist; eigene Web-Recherche liegt außerhalb des Skill-Umfangs. Eine Quelle zu erfinden ist verboten (siehe Leitplanken).

### Auszeichnungstext (6 Muster)

#### 23. Markdown statt Wikitext [MEDIUM]
**Problem:** Markdown-Syntax in Wikipedia-Artikel statt Wikitext.

Häufige Indikatoren:
- `*fett*` oder `**fett**` statt `'''fett'''`
- `# Überschrift` statt `== Überschrift ==`
- `[Link](url)` statt `[Link url]`

**Warum LLMs das tun:** Trainiert auf Markdown-Quellen.

**Lösung:** Konvertieren zu Wikitext.

#### 24. Fehlerhafter Wikitext und KI-Tool-Artefakte [MEDIUM]
**Problem:** Wikitext-Syntax ist ungültig oder unvollständig. Zusätzlich hinterlassen KI-Tools technische Artefakte im Text.

Häufige Indikatoren:
- "gehe zu [[Suche Nr. 42]]"
- Unvollständige Template-Tags
- `{{cite book|author=` ohne Schließ-`}}`
- `oaicite:0` oder `oaicite:ref` Tags (ChatGPT-Artefakt)
- `contentReference[oaicite:0]` Spans
- `turn0search0` Referenzen (Copilot-Artefakt)
- Markdown-Formatierung in Word- oder PDF-Dokumenten

**Warum LLMs das tun:** Wikitext-Syntax wurde nicht korrekt generiert. KI-Tools fügen interne Referenz-Tags ein, die im Export nicht bereinigt werden.

**Lösung:** Reparieren oder entfernen. KI-Tool-Artefakte immer vollständig löschen.

#### 25. Defekte Links [MEDIUM]
**Problem:** Zu viele rote Links oder tote Referenzen.

Häufige Indikatoren:
- 404 Fehler in Referenzen
- Links zu nicht-existenten Artikeln
- Tippfehler in Kategorien oder Artikeln

**Warum LLMs das tun:** Halluziniert Artikel-Titel.

**Lösung:** Mit den verfügbaren Mitteln prüfen (Syntax, Plausibilität, interne Konsistenz, offensichtliche Tippfehler im übergebenen Kontext). Bei nachweisbarem Defekt: korrigieren oder entfernen. Externe Online-Verifikation eines Links liegt außerhalb des Skill-Umfangs – in diesem Fall mit [LINK NICHT VERIFIZIERT] markieren statt blind zu entfernen.

#### 26. Zitatfabrikation und ungültige Referenzen [MEDIUM]
**Problem:** LLMs erfinden Quellen, die echt aussehen, aber nicht existieren. Das reicht von ungültigen DOI-Prüfziffern bis zu komplett halluzinierten Publikationen.

Häufige Indikatoren:
- DOI mit ungültiger Prüfziffer
- ISBN mit Tippfehler
- Erfundene akademische Quellen (Journal existiert nicht, Ausgabe existiert nicht)
- Autoren existieren, aber die genannte Publikation nicht
- Defekte externe Links mit `utm_source=`-Parametern – besonders verdächtig: `utm_source=chatgpt.com`, `utm_source=claude.ai`, `utm_source=gemini.google.com`, `utm_source=perplexity.ai` (direkter KI-Fingerabdruck)
- Unbenutzte benannte Referenzen (`<ref name="..."/>` ohne zugehörige Definition)

**Warum LLMs das tun:** Kann keine echten Quellen recherchieren und erzeugt plausibel aussehende Referenzen aus dem Training.

**Lösung:** Formale Plausibilität jeder Quelle mit den verfügbaren Mitteln prüfen (Format, interne Konsistenz, DOI-/ISBN-Prüfziffer, `utm_source`-Fingerabdrücke, existierende Autoren-Publikation-Kombinationen im übergebenen Kontext). Externe Online-Verifikation liegt außerhalb des Skill-Umfangs – in diesem Fall mit [QUELLE NICHT VERIFIZIERT] markieren. Bei nachweisbarer Fabrikation: entfernen. Nie eine Quelle erfinden oder stehen lassen, die als erfunden erkannt wurde.

#### 27. Inkorrekte Referenzen-Format [MEDIUM]
**Problem:** Zitierformat entspricht nicht deutschen Wikipedia-Standards.

Häufige Indikatoren:
- Englisches Datumsformat statt deutsches
- Falsche Reihenfolge (Nachname, Vorname)
- Incompatible Zitierstyle

**Warum LLMs das tun:** Englisches Training dominiert.

**Lösung:** Anpassung an deutsches Format (z.B. `1. Januar 2024` statt `January 1, 2024`).

#### 28. Falsche Kategorien [MEDIUM]
**Problem:** Kategorien sind nicht-existent oder nicht-deutsch.

Häufige Indikatoren:
- `[[Category:American Writers]]` statt `[[Kategorie:Amerikanische Schriftsteller]]`
- Erfundene Kategorien
- Rote Kategorie-Links

**Warum LLMs das tun:** Trainiert auf englischen Wikipedia-Kategorien.

**Lösung:** Zu korrekten deutschen Kategorien korrigieren.

### Verschiedenes (3 Muster)

#### 29. Abrupte Abbrüche [LOW]
**Problem:** Text bricht mitten im Satz ab.

Häufige Indikatoren:
- "Die Gründung der Stadt war..."
- Unvollständige Sätze
- Trailing text ohne Sinn

**Warum LLMs das tun:** Token-Limit erreicht oder Ausgabe wurde unterbrochen.

**Lösung:** Löschen oder vervollständigen mit echten Informationen.

#### 30. Wechsel im Schreibstil [MEDIUM]
**Problem:** Plötzlicher Wechsel von informell zu formell oder umgekehrt.

Häufige Indikatoren:
- Absätze klingen wie verschiedene Autoren
- Abrupt wechselnde Tonalität
- Mix aus akademisch und umgangssprachlich

**Warum LLMs das tun:** Verschiedene Trainingsdaten-Quellen.

**Lösung:** Harmonisieren zum konsistenten Stil.

#### 31. Ausführliche Bearbeitungszusammenfassungen in Ich-Form [LOW]
**Problem:** Edit-Summaries sind verbose und persönlich.

Häufige Indikatoren:
- "Ich habe einen Absatz über..."
- "Meine Änderungen verbessern..."
- "Ich denke, dass..."

**Warum LLMs das tun:** Chatbot-Verhalten auch in Metadaten.

**Lösung:** Entfernen oder in neutrale Form umwandeln ("Absatz über X hinzugefügt").

### Rhetorik und Struktur (7 Muster)

#### 32. Persuasive Autoritäts-Floskeln [MEDIUM]

**Wendungen, auf die Sie achten sollten:** "Die eigentliche Frage ist", "Im Kern", "In Wirklichkeit", "Was wirklich zählt", "Im Grunde genommen", "Das tiefere Problem", "Worauf es wirklich ankommt", "Der Kern der Sache", "Letztlich geht es um"

**Problem:** LLMs verwenden diese Wendungen, um gewöhnliche Aussagen als verborgene Erkenntnisse zu verpacken. Die "Wahrheit", die folgt, ist meist eine Wiederholung des bereits Gesagten.

**Kein Problem, wenn:** Der Autor einen echten rhetorischen Schwenk in einem Meinungsartikel oder Essay macht, wo Neuformulierung der Punkt ist und die folgende Aussage sich inhaltlich vom Vorherigen unterscheidet.

**Beispiel:**

❌ Schlecht: "Die eigentliche Frage ist, ob Teams sich anpassen können. Im Kern geht es um organisatorische Bereitschaft. In Wirklichkeit kommt es auf die Integration in bestehende Arbeitsabläufe an."

✓ Besser: "Ob Teams sich anpassen können, hängt vor allem von der organisatorischen Bereitschaft ab und davon, wie bereitwillig sie bestehende Arbeitsabläufe ändern."

#### 33. Signposting und Ankündigungen [MEDIUM]

**Wendungen, auf die Sie achten sollten:** "Schauen wir uns an", "Lassen Sie uns erkunden", "Hier ist, was Sie wissen müssen", "Die Sache ist die", "Was als Nächstes passiert", "Ohne weitere Umschweife", "Jetzt werfen wir einen Blick auf", "Kommen wir zu", "Tauchen wir ein"

**Problem:** LLMs kündigen an, was sie gleich tun werden, statt es einfach zu tun.

**Kein Problem, wenn:** Der Text ein Live-Präsentationsskript, Vorlesungstranskript oder interaktives Tutorial ist, wo direkte Ansprache des Publikums erwartet wird.

**Beispiel:**

❌ Schlecht: "Schauen wir uns an, wie Caching in Next.js funktioniert. Hier ist, was Sie wissen müssen. Lassen Sie uns das Schritt für Schritt durchgehen."

✓ Besser: "Next.js cached auf vier Ebenen: Request-Memoization, Data-Cache, Full-Route-Cache und Router-Cache auf dem Client."

#### 34. Fragmentierte Überschriften [LOW]

**Anzeichen:** Ein Ein-Satz- oder Ein-Fragment-Absatz direkt nach einer Überschrift, gefolgt vom eigentlichen Inhalt. Die verwaiste Zeile wiederholt typischerweise die Überschrift in anderen Worten oder macht eine generische Aussage ("Geschwindigkeit zählt.", "Sicherheit ist alles.", "Testen ist entscheidend.").

**Problem:** LLMs setzen einen kurzen, generischen Satz nach einer Überschrift als rhetorischen "Aufhänger" vor dem eigentlichen Absatz. Entfernen und die Überschrift ihre Arbeit machen lassen.

**Kein Problem, wenn:** Der kurze Einstieg spezifisch ist und Information enthält, die die Überschrift nicht hat.

**Beispiel:**

❌ Schlecht:
> ## Performance
>
> Geschwindigkeit zählt.
>
> Wenn Nutzer eine langsame Seite sehen, verlassen sie die Website.

✓ Besser:
> ## Performance
>
> Wenn Nutzer eine langsame Seite sehen, verlassen sie die Website.

#### 35. Rhetorische Fragen als Fake-Engagement [MEDIUM]

**Wendungen, auf die Sie achten sollten:** "Aber was bedeutet das für...?", "Haben Sie sich jemals gefragt, warum...?", "Doch was steckt dahinter?", "Was heißt das konkret?", "Wer profitiert davon?", "Warum ist das wichtig?"

**Problem:** LLMs streuen rhetorische Fragen ein, um Engagement vorzutäuschen. Die Frage wird sofort im nächsten Satz beantwortet – der Leser hatte nie eine echte Wahl, mitzudenken.

**Kein Problem, wenn:** Der Text ein FAQ-Format hat, eine tatsächliche Frage-Antwort-Struktur verfolgt oder der Autor eine provokante These aufstellt, die er dann widerlegt.

**Beispiel:**

❌ Schlecht: "Aber was bedeutet das für den Mittelstand? Die Antwort ist einfacher als gedacht: Unternehmen müssen sich anpassen."

✓ Besser: "Der Mittelstand muss sich anpassen."

#### 36. Universelle Menschheitserfahrungs-Eröffnung [MEDIUM]

**Wendungen, auf die Sie achten sollten:** "Seit jeher", "Seit Anbeginn der Zivilisation", "Schon immer hat die Menschheit...", "Im Laufe der Geschichte", "Seit Menschengedenken", "Von Anfang an", "Schon die alten Griechen/Römer..."

**Problem:** LLMs eröffnen Texte mit grandiosen Menschheitsaussagen, um einem Alltagsthema historisches Gewicht zu verleihen.

**Kein Problem, wenn:** Der historische Bezug spezifisch ist (Datum, Name, Ort) und direkt zum Thema führt.

**Beispiel:**

❌ Schlecht: "Seit Anbeginn der Zivilisation suchen Menschen nach Wegen, effizienter zu kommunizieren."

✓ Besser: "E-Mail hat den Geschäftsbrief abgelöst. Slack hat die E-Mail nicht abgelöst – aber den Ton verändert."

#### 37. "In der heutigen X-Welt" Framing [MEDIUM]

**Wendungen, auf die Sie achten sollten:** "In der heutigen digitalen Welt", "In einer zunehmend vernetzten Welt", "In Zeiten von...", "Im Zeitalter der Digitalisierung", "In der heutigen schnelllebigen Gesellschaft", "In einer Welt, in der...", "Angesichts der rasanten Entwicklung"

**Problem:** LLMs rahmen gewöhnliche Themen mit Zeitgeist-Floskeln, die nichts aussagen.

**Kein Problem, wenn:** Der Kontext tatsächlich einen historischen Vergleich erfordert und spezifisch wird.

**Beispiel:**

❌ Schlecht: "In der heutigen digitalen Welt ist eine starke Online-Präsenz für Unternehmen unerlässlich."

✓ Besser: "Ohne Website findet ein Handwerksbetrieb heute kaum noch Kunden unter 40."

#### 38. Aspirativer Unternehmensschluss [MEDIUM]

**Wendungen, auf die Sie achten sollten:** "bestens aufgestellt für die Zukunft", "die Möglichkeiten sind grenzenlos", "bereit für die nächste Stufe", "an der Schwelle zu einer neuen Ära", "die Weichen sind gestellt", "mit Zuversicht in die Zukunft blicken", "das Potenzial ist enorm", "auf Erfolgskurs"

**Problem:** LLMs schließen Texte mit optimistischen Zukunftsaussagen, die nichts Konkretes sagen.

**Kein Problem, wenn:** Der Text tatsächlich ein Geschäftsbericht oder eine Pressemitteilung ist, wo solche Formulierungen Konvention sind.

**Beispiel:**

❌ Schlecht: "Mit dieser Strategie ist das Unternehmen bestens aufgestellt für die Zukunft. Die Möglichkeiten sind grenzenlos."

✓ Besser: "Ob die Strategie aufgeht, zeigt sich im nächsten Quartal."

### Argumentation und Evidenz (3 Muster)

#### 39. Passivkonstruktionen und subjektlose Fragmente [MEDIUM]

**Problem:** LLMs verstecken den Akteur durch Passiv oder lassen das Subjekt ganz weg.

Häufige Indikatoren:
- "wurde durchgeführt" (statt "Team X führte durch")
- "es wird empfohlen" (statt "wir empfehlen")
- "Keine Konfiguration nötig."
- "Wird automatisch gespeichert."
- "Kann ohne Weiteres angepasst werden."

**Formal-Modus-Ausnahme:** In wissenschaftlichen Texten sind Passivkonstruktionen Konvention ("wurde analysiert", "es konnte gezeigt werden"). In diesem Modus nur bei klarer Übernutzung eingreifen.

**Beispiel:**

❌ Schlecht: "Keine Konfigurationsdatei nötig. Die Ergebnisse werden automatisch gespeichert."

✓ Besser: "Sie brauchen keine Konfigurationsdatei. Das System speichert die Ergebnisse automatisch."

#### 40. Konditional-Stapel [MEDIUM]

**Problem:** LLMs häufen "wenn"-Klauseln in Schlussfolgerungen, statt direkt auszusagen, was die Analyse ergeben hat.

Häufige Indikatoren:
- "Wenn das Argument stimmt, und wenn die Evidenz diese Lesart stützt..."
- "Sofern der Kontext wie beschrieben war..."
- Mehrere "wenn/falls/sofern"-Klauseln in einem Absatz
- Hedging-Ketten in Schlussfolgerungen

**Kein Problem, wenn:** Der Text tatsächlich unterschiedliche Szenarien analysiert, bei denen die Bedingungen echte Verzweigungen darstellen.

**Beispiel:**

❌ Schlecht: "Wenn das Argument stimmt, und wenn die Evidenz diese Lesart stützt, dann könnte die Politik einen gewissen Effekt gehabt haben – sofern der Kontext wie beschrieben war."

✓ Besser: "Die Evidenz stützt das Argument, dass die Politik in diesem Kontext einen Effekt hatte."

#### 41. Fehlkalibriertes epistemisches Vertrauen [MEDIUM]

**Problem:** LLMs schwanken zwischen Über-Behauptung ("grundlegend", "entscheidend", "zweifellos") und Über-Absicherung ("scheint möglicherweise", "könnte eventuell").

Häufige Indikatoren:
- Über-Behauptung: "grundlegend verändert", "entscheidend geprägt", "zweifellos", "vollständig revolutioniert"
- Über-Absicherung: "scheint möglicherweise", "könnte eventuell", "dürfte unter Umständen"
- Beides im selben Text

**Kein Problem, wenn:** Der Autor bewusst eine starke These aufstellt oder echte Unsicherheit benennt.

**Beispiele:**

❌ Schlecht (Über-Behauptung): "Die Daten zeigen zweifellos, dass Remote-Arbeit die Produktivität grundlegend verändert hat."

✓ Besser: "In den untersuchten Unternehmen stieg die Produktivität im ersten Jahr der Remote-Arbeit um durchschnittlich 8 Prozent."

❌ Schlecht (Über-Absicherung): "Es scheint, dass die Politik möglicherweise einen gewissen Effekt auf die Ergebnisse gehabt haben könnte."

✓ Besser: "Die Politik führte in zwei von drei untersuchten Fällen zu einer moderaten Verbesserung."

### Ergänzungen (4 Muster)

#### 42. Beleginkongruenz [HIGH]

**Kategorie:** Argumentation und Evidenz

**Problem:** Die angegebene Quelle existiert und ist formal korrekt zitiert, belegt aber die getroffene Aussage nicht. Anders als Muster 26 (fabrizierte Quellen) ist die Referenz real – nur der Inhalt passt nicht zur Behauptung.

Häufige Indikatoren:
- Die Quelle behandelt das Thema nur am Rand, wird aber als zentraler Beleg präsentiert
- Widerspruch zwischen Aussage und Quelle
- Scope-Mismatch: Zeitraum, Region oder Population der Quelle passt nicht
- Jahreszahlen in der Aussage weichen von denen der Quelle ab
- Konkrete Zahlen werden zitiert, die so in der Quelle nicht stehen
- Sekundärquelle (Blog, Zeitungsartikel) als Primärbeleg für Forschungsaussage

**Operative Schranke:** Nur dann als Beleginkongruenz markieren, wenn die Quelle tatsächlich geprüft wurde oder eindeutig prüfbar ist. Ohne Prüfmöglichkeit keine Kongruenz-Vorwürfe erheben.

**Lösung:** Bei nachweisbarer Inkongruenz: Aussage an Quelle anpassen, Quelle ersetzen oder mit `[BELEG PRÜFEN]` markieren.

**Beispiel:**

❌ Schlecht: „Laut einer Studie des Fraunhofer-Instituts aus 2019 stieg die Produktivität deutscher Remote-Teams um 23 Prozent.<ref>Fraunhofer IAO: Arbeiten in der Corona-Pandemie, 2020.</ref>"
(Quelle existiert, stammt aber aus 2020 und nennt keine 23 Prozent.)

✓ Besser: Quelle auf tatsächlichen Inhalt prüfen, Aussage anpassen oder passende Quelle suchen.

#### 43. Versteckte Unicode-Zeichen [HIGH]

**Kategorie:** Auszeichnungstext

**Problem:** KI-Tools hinterlassen unsichtbare Unicode-Zeichen im Text. Diese stören Wiki-Syntax, Volltextsuche, Screenreader und Textvergleich.

Häufige Indikatoren:
- Zero-Width Space (U+200B)
- Zero-Width Non-Joiner (U+200C)
- Zero-Width Joiner (U+200D)
- Word Joiner (U+2060)
- Byte Order Mark (U+FEFF) mitten im Text
- Soft-Hyphen (U+00AD) an ungewöhnlichen Stellen
- Bidi-Steuerzeichen: U+202A–U+202E, U+2066–U+2069

**Lösung:** Regex-Scan auf `[​-‍⁠﻿­‪-‮⁦-⁩]` und ersatzlos entfernen. Nicht verwechseln mit U+00A0 (geschütztes Leerzeichen) in stehenden Wendungen wie „5 km" oder „§ 12".

#### 44. Standard-Kapitel ohne Substanz [MEDIUM]

**Kategorie:** Stil

**Problem:** Standard-Überschrift + substanzloser Allgemeinplätze darunter. Die Überschrift selbst kann legitim sein; Tell ist die Kombination.

Häufige Indikatoren:
- Überschriften: „== Herausforderungen ==", „== Zukunftsperspektiven ==", „== Bedeutung ==", „== Relevanz ==", „== Ausblick ==", „== Chancen und Risiken =="
- Darunter: allgemeine Aussagen ohne konkrete Fakten, Zahlen oder Belege
- Prognose-Sprech ohne Träger
- Bloße Wiederholung von Punkten aus früheren Abschnitten

**Lösung:** Nicht kürzen (Leitplanke „Nie kürzen" gilt). Vorgehen:
1. **Substanz finden:** Konkretisieren, Belege einfügen.
2. **Integrieren:** Inhalt in bestehende Kapitel verschieben, Standard-Überschrift entfernen.
3. **Umwidmen:** Generische Überschrift durch spezifische ersetzen.
4. **Fallback:** Bei echter Substanzlosigkeit mit `[SUBSTANZ PRÜFEN]` markieren und stehen lassen.

#### 45. Anglizismus-Strukturen [MEDIUM]

**Kategorie:** Sprache und Tonfall

**Problem:** Nur **harte Transfers**: Calques, False Friends und syntaktische Muster, die im Deutschen als Übersetzungsdeutsch auffallen. Einzelne Anglizismen in Business- oder Umgangssprache sind **kein** Anzeichen.

Harte Indikatoren:
- **Calques:** „am Ende des Tages", „in Reihenfolge zu", „zu Beginn mit"
- **False Friends:** „eventuell" als „schließlich", „aktuell" als „tatsächlich", „sensibel" als „vernünftig/umsichtig"
- **Syntaktische Transfers:** englische Wortstellung in Relativsätzen

**Kein belastbarer Tell:**
- „basiert auf", „in Bezug auf", „adressieren" – in Geschäfts- und Wissenschaftsdeutsch etabliert
- „Sinn machen" – im heutigen Standarddeutsch etabliert
- Einzelne Lehnwörter („Meeting", „Team", „Feedback")

**Register-Hinweis:** False Friends immer korrigieren, unabhängig vom Register. Calques und syntaktische Transfers nur im formal-Modus oder bei Häufung.

**Beispiel:**

❌ Schlecht: „Am Ende des Tages erkannte das Team eventuell, dass die Strategie aktuell nicht trug."

✓ Besser: „Schließlich erkannte das Team, dass die Strategie tatsächlich nicht trug."
