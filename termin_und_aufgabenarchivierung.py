from icalendar import Calendar
from datetime import datetime, date, timezone
import os

# ================================
# Skriptname
# ================================
SCRIPT_NAME = "termin_und_aufgabenarchivierung.py"

# ================================
# Eingabe: Dateiname und Filterdatum
# ================================
input_file = input("Bitte Pfad zur Kalenderdatei (.ics) eingeben [Standard: Kalender.ics]: ").strip()
if not input_file:
    input_file = "Kalender.ics"

while True:
    date_str = input("Bitte Filterdatum eingeben (yyyy-mm-dd) [Standard: 2025-06-01]: ").strip()
    if not date_str:
        date_str = "2025-06-01"
    try:
        FILTER_DATE = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        break
    except ValueError:
        print("Ungültiges Datum. Bitte im Format yyyy-mm-dd eingeben.")

# Ausgabedateien ableiten
base_name = os.path.splitext(os.path.basename(input_file))[0]
active_file = f"{base_name}_aktiv.ics"
archive_file = f"{base_name}_archiv.ics"
log_file = f"{base_name}.log"

# ================================
# Prüfen auf existierende Dateien
# ================================
for fpath in [active_file, archive_file, log_file]:
    if os.path.exists(fpath):
        resp = input(f"Die Datei '{fpath}' existiert bereits. Überschreiben? (j/N): ").strip().lower()
        if resp != 'j':
            print("Abbruch durch Benutzer.")
            exit()

# ================================
# Hilfsfunktion
# ================================
def normalize_dt(val):
    """Konvertiert date/datetime zu datetime mit UTC-Zeit"""
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime.combine(val, datetime.min.time(), tzinfo=timezone.utc)
    if val.tzinfo is None:
        return val.replace(tzinfo=timezone.utc)
    return val

# ================================
# Quelldatei laden
# ================================
with open(input_file, "rb") as f:
    src = Calendar.from_ical(f.read())

active = Calendar()
archive = Calendar()

# Kalender-Metadaten kopieren
for cal in (active, archive):
    for prop in ("PRODID", "VERSION", "CALSCALE", "METHOD"):
        if prop in src:
            cal.add(prop, src[prop])

# ================================
# Statistik vorbereiten
# ================================
stats = {
    "source_components_total": 0,
    "source_relevant": 0,
    "events": 0,
    "todos": 0,
    "archived_total": 0,
    "archived_completed_todos": 0,
    "archived_series_until": 0,
    "archived_single_events": 0,
    "active_total": 0,
    "active_events": 0,
    "active_todos": 0,
}

# ================================
# Komponenten verarbeiten
# ================================
for comp in src.walk():
    stats["source_components_total"] += 1

    name = comp.name
    if name not in ("VEVENT", "VTODO"):
        continue
    stats["source_relevant"] += 1

    dtstart = normalize_dt(comp.get("DTSTART").dt if comp.get("DTSTART") else None)
    due = normalize_dt(comp.get("DUE").dt if comp.get("DUE") else None)
    completed = normalize_dt(comp.get("COMPLETED").dt if comp.get("COMPLETED") else None)
    rrule = comp.get("RRULE")
    until = None
    if rrule and "UNTIL" in rrule:
        until = normalize_dt(rrule["UNTIL"][0])

    is_todo = name == "VTODO"
    is_event = name == "VEVENT"
    is_completed_todo = is_todo and (completed is not None or comp.get("STATUS") == "COMPLETED")

    # ================================
    # Archivierungsregeln
    # ================================
    if is_completed_todo:
        archive.add_component(comp)
        stats["archived_total"] += 1
        stats["archived_completed_todos"] += 1
        continue

    if is_event and rrule and until and until < FILTER_DATE:
        archive.add_component(comp)
        stats["archived_total"] += 1
        stats["archived_series_until"] += 1
        continue

    if is_event and not rrule and dtstart and dtstart < FILTER_DATE:
        archive.add_component(comp)
        stats["archived_total"] += 1
        stats["archived_single_events"] += 1
        continue

    # ================================
    # Alles andere bleibt aktiv
    # ================================
    active.add_component(comp)
    stats["active_total"] += 1
    if is_event:
        stats["active_events"] += 1
    if is_todo:
        stats["active_todos"] += 1

# ================================
# Dateien speichern
# ================================
with open(active_file, "wb") as f:
    f.write(active.to_ical())

with open(archive_file, "wb") as f:
    f.write(archive.to_ical())

# ================================
# Statistik & Kontrolle
# ================================
stat_text = f"""
{SCRIPT_NAME} Statistik
======================
Quelldatei: {os.path.abspath(input_file)}
Gesamt-Komponenten           : {stats['source_components_total']}
Relevante Einträge (VEVENT/VTODO): {stats['source_relevant']}

Archiviert gesamt            : {stats['archived_total']}
  - Abgeschlossene Aufgaben  : {stats['archived_completed_todos']}
  - Serien mit UNTIL < Filter: {stats['archived_series_until']}
  - Einzeltermine < Filter   : {stats['archived_single_events']}

Aktiv gesamt                 : {stats['active_total']}
  - Aktive Termine           : {stats['active_events']}
  - Aktive Aufgaben          : {stats['active_todos']}

Kontrolle: Quelle_relevant = Aktiv + Archiv ?
  {stats['source_relevant']} = {stats['active_total']} + {stats['archived_total']}
"""

print(stat_text)

# ================================
# Warnung bei Inkonsistenz
# ================================
if stats['source_relevant'] != (stats['active_total'] + stats['archived_total']):
    print("WARNUNG: Die Anzahl der relevanten Einträge stimmt nicht mit Aktiv+Archiv überein!")

# ================================
# Logdatei schreiben
# ================================
with open(log_file, "w", encoding="utf-8") as logf:
    logf.write(stat_text)

print(f"Fertig. Logdatei: {os.path.abspath(log_file)}")
print(f"Aktive Termine: {active_file}")
print(f"Archiv: {archive_file}")
