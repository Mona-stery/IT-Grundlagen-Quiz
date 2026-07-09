# 💻 IT-Grundlagen Quiz

Eine interaktive Desktop-Anwendung zum Lernen und Testen von IT-Grundlagen-Wissen. Gebaut mit Python und [customtkinter](https://github.com/TomSchimansky/CustomTkinter) für eine moderne, dunkle Benutzeroberfläche.

---

## ✨ Funktionen

### 🏠 Startseite
- Übersicht über die Anzahl der gespeicherten Fragen und Kategorien
- Schnellzugriff auf alle Bereiche der Anwendung

### ▶ Quiz-Modus
- Zufällige Auswahl von bis zu **15 Fragen** pro Durchlauf
- Fortschrittsanzeige mit Fortschrittsbalken
- Antworten per Klick auswählen und bestätigen
- **Sofortiges Feedback**: Richtige Antworten werden grün, falsche rot markiert
- Punktestand wird während des Quiz angezeigt
- **Ergebnisseite** am Ende mit Punktzahl, Prozentanzeige und Emoji-Bewertung:
  - 🏆 Ab 80 % — *Ausgezeichnet!*
  - 👍 Ab 60 % — *Gut gemacht!*
  - 📚 Ab 40 % — *Weiter üben!*
  - 💪 Unter 40 % — *Nicht aufgeben!*

### ＋ Fragen hinzufügen
- Formular zum Erstellen eigener Fragen mit:
  - **Kategorie** (z. B. Netzwerk, Hardware, Sicherheit)
  - **Fragetext**
  - **Vier Antwortmöglichkeiten** (A – D)
  - **Auswahl der richtigen Antwort** per Radio-Button
- Fragen werden direkt in der JSON-Datei gespeichert
- Nach dem Speichern kann sofort die nächste Frage eingegeben werden

### 📋 Fragen verwalten
- Scrollbare Liste aller gespeicherten Fragen
- Anzeige der Kategorie pro Frage
- **Löschen** einzelner Fragen per Klick auf das 🗑-Symbol

---

## 🚀 Installation & Start

### Voraussetzungen
- Python 3.10 oder höher
- pip (Python-Paketmanager)

### Einrichtung

1. **Repository klonen oder herunterladen**

2. **Abhängigkeiten installieren:**
   ```bash
   pip install customtkinter
   ```

3. **Anwendung starten:**
   ```bash
   python main.py
   ```

> **Hinweis:** Falls du eine virtuelle Umgebung (`.venv`) verwendest, stelle sicher, dass `customtkinter` dort installiert ist.

---

## 📁 Projektstruktur

```
IT-Grundlagen-Quiz/
├── main.py            # Hauptanwendung (GUI + Logik)
├── questions.json     # Fragenkatalog (wird automatisch gelesen/geschrieben)
└── README.md          # Diese Datei
```

### questions.json – Format

Die Fragen werden als JSON-Array gespeichert. Jede Frage hat folgendes Format:

```json
{
  "question": "Wie viele Bits hat ein Byte?",
  "options": ["4", "8", "16", "32"],
  "correct": 1,
  "category": "Grundlagen"
}
```

| Feld       | Beschreibung                                      |
|------------|---------------------------------------------------|
| `question` | Der Fragetext                                     |
| `options`  | Array mit genau vier Antwortmöglichkeiten         |
| `correct`  | Index der richtigen Antwort (0 = A, 1 = B, …)    |
| `category` | Kategorie der Frage (frei wählbar)                |

---

## 🎨 Design

Die Anwendung verwendet ein **dunkles Farbschema** mit folgenden Merkmalen:

- Tiefes Navy als Hintergrundfarbe
- Lila Akzentfarbe (`#6c63ff`) für interaktive Elemente
- Abgerundete Karten mit subtilen Rahmen
- Hover-Effekte für alle Buttons
- Grüne / rote Farbgebung für richtige / falsche Antworten

---

## 🛠 Technologien

| Technologie                                                        | Verwendung              |
|--------------------------------------------------------------------|-------------------------|
| [Python 3](https://www.python.org/)                                | Programmiersprache      |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter)   | Moderne GUI-Bibliothek  |
| JSON                                                               | Datenspeicherung        |

---

## 📄 Lizenz

Dieses Projekt ist frei zur persönlichen und schulischen Nutzung.
