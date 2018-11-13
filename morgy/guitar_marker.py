import click
from morgy.database import Database


@click.command()
@click.argument("path")
def mark_with_guitar(path):
    """Mark songs as able to play on guitar."""
    db = Database()
    db.add_guitar_row(path, True)
    db.commit_and_close()


if __name__ == "__main__":
    mark_with_guitar()
