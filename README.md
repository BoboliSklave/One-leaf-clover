# One-leaf-clover
Python script for safely archiving Thunderbird/CalDAV calendars. Moves completed tasks, old single events, and expired series without altering entries. Focused on data preservation, transparency, and trust.
# Thunderbird Calendar Archiver (ICS / CalDAV)

A Python script to archive old Thunderbird calendar entries
without breaking recurring events, alarms, or CalDAV compatibility.

## Why?
Thunderbird has no built-in way to archive calendar data.
Large calendars cause performance and sync issues.

## What it does
- Splits one ICS file into:
  - active calendar
  - archive calendar
- Keeps alarms (VALARM) untouched
- Supports:
  - events (VEVENT)
  - tasks (VTODO)
  - recurring events with UNTIL
- No content modification

## Typical use case
- Export calendar from Thunderbird
- Run this script
- Import results into Radicale / CalDAV / Thunderbird

## Requirements
- Python 3.10+
- icalendar

## Status
Tested with real-world Thunderbird calendars (10+ years)

## Usage

1. Copy `termin_und_aufgabenarchivierung.py` into the folder containing your `kalender.ics` file.  
2. Open a command prompt (CMD) or terminal.  
3. Change directory to the folder containing the script and calendar file:  
```bash
cd path\to\folder

4.  Run the script:

python termin_und_aufgabenarchivierung.py
