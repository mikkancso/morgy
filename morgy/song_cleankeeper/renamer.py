import os


class Renamer:
    def apply_recommendations(self, recommendations):
        current_dir = ""
        with open(recommendations, "r") as recommendations_file:
            for line in recommendations_file:
                if "\t" not in line:
                    current_dir = line.strip()
                else:
                    try:
                        current_filename, new_filename = line.strip().split("\t")
                        os.rename(
                            os.path.join(current_dir, current_filename),
                            os.path.join(current_dir, new_filename),
                        )
                    except FileNotFoundError:
                        if os.path.isfile(os.path.join(current_dir, new_filename)):
                            print("Already renamed: " + new_filename)
                        else:
                            print("File not found: " + current_filename)
