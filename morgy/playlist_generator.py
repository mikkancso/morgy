import click
from morgy.database import Database


@click.command()
@click.argument("file")
@click.argument("selection")
def write_playlist(file, selection):
    """Create a playlist by selecting filepaths and write it to a file."""
    db = Database()
    with open(file, "w") as playlist:
        for song_path in db.get_path_where(selection):
            playlist.write(song_path[0] + "\n")


if __name__ == "__main__":
    write_playlist()
