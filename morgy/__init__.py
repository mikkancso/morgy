import click
import configparser

from morgy.database import Database
from morgy.database.updater import DatabaseUpdater
from morgy.song_cleankeeper.path_sanitizer import PathSanitizer
from morgy.song_cleankeeper.renamer import Renamer
from morgy.integrator import Integrator
from morgy.smart_picker import SmartPicker

CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
db = Database(config["DEFAULT"]["database_path"])


@click.group()
def morgy():
    pass


@morgy.command()
@click.option(
    "--priority",
    default=10,
    help="The priority to add to new music.",
    type=click.IntRange(1, 10),
)
@click.argument("directory")
def update(directory, priority):
    """Update the database of songs."""
    db_updater = DatabaseUpdater(db)
    db_updater.update_db(directory, priority)


@morgy.command()
@click.argument("directory")
@click.argument("output_path")
def sanitize(directory, output_path):
    """Sanitizing mp3 and wma filenames. It does not do the actual
     renaming, just writes the recommendations to the file at output_path"""
    ps = PathSanitizer()
    ps.write_recommendations(directory, output_path)


@morgy.command()
@click.argument("apply_file")
def rename(apply_file):
    """Apply the filename renamings from a file with a format, that
    path_sanitizer output."""
    renamer = Renamer()
    renamer.apply_recommendations(apply_file)


@morgy.command()
@click.argument("path")
def mark_with_guitar(path):
    """Mark songs as able to play on guitar."""
    db.add_guitar_row(path, True)
    db.commit_and_close()


@morgy.command()
@click.argument("directory")
def integrate(directory):
    """Integrate new songs into your music folder and database."""
    integrator = Integrator(directory, db)
    integrator.run()


@morgy.command()
@click.argument("file")
@click.argument("selection")
def write_playlist(file, selection):
    """Create a playlist by selecting filepaths and write it to a file."""
    with open(file, "w") as playlist:
        for song_path in db.get_path_where(selection):
            playlist.write(song_path[0] + "\n")


@morgy.command()
@click.argument("destination")
@click.argument("quantity", type=int)
def pick_and_copy(destination, quantity):
    """Copy some smartly picked songs.
    Destination is the destination directory to copy music to.
    Quantity is the amount of music to be copied in MBs."""
    smart_picker = SmartPicker(db)
    to_copy = smart_picker.pick(quantity * 1024 * 1024)
    smart_picker.decrease_prio(to_copy)
    # should it be a different class?
    smart_picker.copy_list_to_destination(to_copy, destination)


@morgy.command()
@click.argument("destination")
def write_guitar_files(destination):
    """Write files marked with guitar to a destination folder."""
    smart_picker = SmartPicker(db)
    to_copy = smart_picker.pick_all_from_guitar()
    smart_picker.copy_list_to_destination(to_copy, destination)

if __name__ == "__main__":
    morgy()
