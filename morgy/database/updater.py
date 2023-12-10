import os
from morgy.database import Database
from morgy.database.detail_fetcher import DetailFetcher


class DatabaseUpdater:
    def __init__(self, db):
        self.db = db
        self.detail_fetcher = DetailFetcher()
        self.extensions = [".mp3", ".wma", ".flac"]

    def remove_not_existing_entries(self):
        not_existing_paths = list()
        for path in self.db.get_path_where("1"):
            # FIXME: get_path_where should not return tuuple?
            if not os.path.exists(path[0]):
                not_existing_paths.append(path[0])

        for path in not_existing_paths:
            self.db.delete_entry_with_path(path)

        for guitar_path in self.db.get_rows_from_table("guitar"):
            if guitar_path[0] in not_existing_paths:
                print("Deleting {} from guitar table.".format(guitar_path[0]))
                self.db.delete_entry_with_path_from_guitar(guitar_path[0])

        self.db.commit_and_close()
        self.db.open()

    def update_db(self, directory, priority):
        for dirpath, dirnames, filenames in os.walk(directory):
            filtered_filenames = [
                x
                for x in filenames
                for extension in self.extensions
                if x.lower().endswith(extension)
            ]
            for name in filtered_filenames:
                (
                    artist,
                    year,
                    album,
                    cd_number,
                    number,
                    title,
                ) = self.detail_fetcher.fetch_detail(dirpath, name[:-4])
                path = os.path.join(dirpath, name)
                self.db.add_detail_row(
                    path, artist, year, album, cd_number, number, title, priority
                )

    def close(self):
        self.db.commit_and_close()
