import argparse
import os
import shutil
import tempfile

from morgy.database.updater import DatabaseUpdater
from morgy.song_cleankeeper.path_sanitizer import PathSanitizer
from morgy.song_cleankeeper.renamer import Renamer


class Integrator:
    def __init__(self, to_integrate):
        self.to_integrate = os.path.realpath(to_integrate)
        self.info = dict()
        self.db_updater = DatabaseUpdater()
        self.path_sanitizer = PathSanitizer()
        self.renamer = Renamer()

    def ask_for_path(self, folder):
        self.info[folder] = dict()
        print("Please provide info about {}".format(folder))
        path = ""
        while not os.path.isdir(path):
            path = input("Destination folder: ")
        self.info[folder]["path"] = os.path.realpath(path)

    def move(self, folder):
        real_folder = os.path.realpath(folder)
        self.info[folder]["destination"] = real_folder.replace(
            self.to_integrate, self.info[folder]["path"]
        )

        shutil.move(real_folder, self.info[folder]["destination"])

    def run(self):
        for dirpath, dirnames, filenames in os.walk(self.to_integrate):
            if len(filenames) > 0 and len(dirnames) == 0:
                dirpath = os.path.realpath(dirpath)
                self.ask_for_path(dirpath)

        recommendations = tempfile.NamedTemporaryFile()
        self.path_sanitizer.write_recommendations(
            self.to_integrate, recommendations.name
        )
        input(
            "The recommendations for renaming the files will be presented to you. Press enter to continue."
        )
        # FIXME: works only on unix with vim :D
        os.system("vim {}".format(recommendations.name))
        self.renamer.apply_recommendations(recommendations.name)
        recommendations.close()

        for folder in self.info.keys():
            self.move(folder)
            self.db_updater.update_db(self.info[folder]["destination"], 10)
        self.db_updater.remove_not_existing_entries()
        self.db_updater.close()


def main():
    parser = argparse.ArgumentParser(
        description="Integrate new songs into your music folder and database."
    )
    parser.add_argument("-i", "--integrate", help="The directory to integrate.")

    args = parser.parse_args()
    integrator = Integrator(args.integrate)
    integrator.run()


if __name__ == "__main__":
    main()
