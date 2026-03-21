# Stil-Bewertungskriterien

## Metriken (0-100 pro Dimension)

### 1. Satzlängen-Varianz
- **90+**: Natürliche Variation (CV 0.3-0.5)
- **50-89**: Akzeptabel
- **<50**: Zu gleichmäßig (KI-typisch, CV < 0.2)

### 2. Vokabular-Reichhaltigkeit
- **90+**: Hohe Type-Token-Ratio, viele Hapax
- **50-89**: Durchschnittliches Vokabular
- **<50**: Repetitives Vokabular

### 3. Passiv-Quote
- **90+**: Unter 15% Passiv
- **50-89**: 15-30% Passiv
- **<50**: Über 30% Passiv

### 4. Füllwort-Dichte
- **90+**: Unter 1% Füllwörter
- **50-89**: 1-3% Füllwörter
- **<50**: Über 3% Füllwörter

### 5. Satzanfang-Diversität
- **90+**: Über 85% einzigartige Anfänge
- **50-89**: 50-85% einzigartige Anfänge
- **<50**: Unter 50% — viele Wiederholungen

### 6. Absatzlängen-Konsistenz
- **90+**: Natürliche Variation (CV 0.3-0.6)
- **50-89**: Leicht ungleichmäßig
- **<50**: Zu gleichmäßig oder chaotisch

### 7. Duplikat-Erkennung
- **100**: Keine N-Gram-Überlappung
- **70**: 1-2 ähnliche Absätze
- **<50**: Mehrere duplizierte Passagen

### 8. Lesbarkeit (Flesch/Amstad)
- **90+**: Angemessen für akademischen Text (Flesch 30-60)
- **50-89**: Grenzwertig
- **<50**: Zu einfach oder zu komplex

### 9. KI-Muster-Erkennung (Komposit)
- **90+**: Low Risk — menschlicher Schreibstil
- **50-89**: Medium Risk — einige KI-Signale
- **<50**: High Risk — multiple KI-Muster erkannt

## Gesamt-Scores

- **Gesamt (Ø)**: Durchschnitt aller 9 Metriken
- **Menschlichkeits-Score**: Gewichteter Score mit Fokus auf KI-Erkennung (25%), Satzvariation (15%), Starter-Diversität (15%), Absatz-Konsistenz (15%)
- **KI-Risiko**: low / medium / high (basierend auf Signalanzahl)

## Typische KI-Muster (Deutsch)

- "Es ist wichtig zu beachten, dass..."
- "Darüber hinaus zeigt sich..."
- "Dies verdeutlicht/unterstreicht/belegt..."
- "Zusammenfassend lässt sich sagen..."
- Gleichmäßige Satzlängen (alle 15-20 Wörter)
- Perfekt symmetrische Absätze
- Übermäßiger Gebrauch von Passivkonstruktionen
