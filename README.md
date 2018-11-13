# morgy
Music organizer

Usage
=====
python3 smart_picker.py -d <destination> -q <quantity>


Running unit tests
==================
python3 -m unittest


TODOS:
- end-to-end usage guide
- logging instead of print
- crucial fixmes

- flask endpoint
    - for some DB queries
    - for smart picker
    - for integrator
    - for playlist_generator
    - for guitar_marker

- fix renamer bugs
- end-to-end tests for existing features
- new column: guitar
- mp3 tagger
- don't copy those which were copied in the last n songs (n=1000)
- sane way of configuration, kill constants
- album cover pictures?
- refactor: kill integrator

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
