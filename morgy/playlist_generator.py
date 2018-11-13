import argparse

from morgy.database import Database


class PlaylistGenerator:
    def __init__(self):
        self.db = Database()

    def write_playlist(self, path, where):
        with open(path, "w") as playlist:
            for song_path in self.db.get_path_where(where):
                playlist.write(song_path[0] + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Create a playlist by simply enumerating filepaths and write it to a file."
    )
    parser.add_argument("-f", "--file", help="The target playlist filename.")
    parser.add_argument(
        "-s",
        "--selection",
        help="The selection whose results will be written to the file (the WHERE clause in the query).",
    )

    args = parser.parse_args()
    playlist_generator = PlaylistGenerator()
    playlist_generator.write_playlist(args.file, args.selection)


if __name__ == "__main__":
    main()
