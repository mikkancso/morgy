import os
import shutil
import sys
import random

from morgy.database import Database


class SmartPicker:
    def __init__(self, database=None):
        self.db = database if database else Database()

    def build_dict_from_database(self):
        titles = dict()
        generator = self.db.get_title_path_and_prio()
        for (title, path, prio) in generator:
            # remove ' (live)', because it is the same song
            title = "".join(title.split(" (live)"))
            if title not in titles:
                titles[title] = list()
            titles[title].append((path, prio))
        return titles

    def get_weighted_selected_paths(self, titles):
        selected_paths = list()
        for title, paths_n_prios in titles.items():
            r = random.randint(0, len(paths_n_prios) - 1)
            selected_path, selected_prio = paths_n_prios[r]
            for i in range(0, int(selected_prio)):
                selected_paths.append(selected_path)
        return selected_paths

    def pick(self, quantity):
        # db -> dict: 'title': [(path1, prio1), (path2, prio2), ...]
        titles = self.build_dict_from_database()
        # pick one (path, prio) for each title
        # put paths prio times in a list (path1, path1, path1, path2, ...)
        selected_paths = self.get_weighted_selected_paths(titles)
        random.shuffle(selected_paths)

        # copy to a new list if: not copied yet, quantity is not reached yet
        list_to_copy = list()
        for path in selected_paths:
            if path not in list_to_copy:
                list_to_copy.append(path)
                quantity = quantity - os.stat(path).st_size
                if quantity < 0:
                    break

        return list_to_copy

    def decrease_prio(self, list_to_copy):
        for path in list_to_copy:
            self.db.decrease_prio(path)
        self.db.commit_and_close()

    def prepend_number(self, path, number):
        number_to_prepend = str(number).zfill(3)
        return number_to_prepend + path

    def print_progress(self, progress):
        sys.stdout.write("\r{}".format(progress))
        sys.stdout.flush()

    def copy_list_to_destination(self, list_to_copy, destination):
        numbering = 0
        for path in list_to_copy:
            dest = destination + self.prepend_number(os.path.basename(path), numbering)
            numbering = numbering + 1
            shutil.copyfile(path, dest)
            self.print_progress(str(numbering) + "/" + str(len(list_to_copy)))
