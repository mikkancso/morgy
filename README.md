# morgy
Music organizer

Running unit tests
==================
python3 -m unittest


TODOS:
- code format, pylint
- doksi a használatról, end-to-end a lényeg
- logging print helyett
- crucial fixme-k javítása, pl SQLi
- argparse kiirtása

NOT in scope:
- meglevő unit testek átírása, kiegészítése


Holnaptól:
- flask endpoint
    - egy pár adatbázis lekérdezésnek
    - a smart picker műveletnek
    - az integrate műveletnek
    - playlist_generatornak
    - guitar_markernek


Original README:

Usage:
python3 smart_picker.py -d <destination> -q <quantity>

Run tests:
python3 -m unittest

TODOs:

- fix renamer bugs
- tests for existing features
- new column: guitar
- one common interface, commands call tools
- mp3 tagger
- don't copy those which were copied in the last n songs (n=1000)
- sane way of configuration, kill constants
- refactor: kill integrator
- album cover pictures?
- FIXMEs



- integrator refactor requirement:
1. let the user move directories, songs in their places,
    we should recognize newly added and deleted files
2. we should rename those the same way as before
3. add them to DB with 10 prio

- integrator original requirement:
Use case: there are some music files in a dedicated folder,
e.g. 'toIntegrate'. They are in the format as they have been
downloaded, so not pretty. Integrate them using one tool.
UPDATE: we can expect that the directories are named and
structured well. We can implement 1. later. But, we still
need to ask for final location.
Steps:
1. foreach leaf subdirectory ask for artist, album, cd and
    where do you want to move it (01 Külföldi punk, etc.)
2. rename the files
    ask for confirmation about the renaming
3. move the folder, create parent folder if needed
4. add them to DB with priority 10

