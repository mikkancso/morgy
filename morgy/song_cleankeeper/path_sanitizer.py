import argparse
import os


class PathSanitizer:
    def __init__(self):
        self.extensions = ['.mp3',
            '.wma'
        ]

    def handle_dash_and_underscore(self, filename):
        filename = filename.replace('_', ' ')
        filename = filename.replace('-', '')
        return filename

    def split_by_extension(self, filename):
        for extension in self.extensions:
            if filename.endswith(extension):
                this_extension = extension
                filename = filename.replace(extension, '')
                return filename, this_extension
        return filename, ''

    def correct_spaces(self, filename):
        filename, this_extension = self.split_by_extension(filename)

        filename = filename.strip()

        if len(filename) < 3:
            # should log this instead
            print(filename)
        elif filename[0].isdigit() and filename[1].isdigit() and filename[2] is not ' ':
            if filename[2] is '.':
                filename = filename[:2] + ' ' + filename[3:]
            else:
                filename = filename[:2] + ' ' + filename[2:]

        while '  ' in filename:
            filename = filename.replace('  ', ' ')

        return ''.join([filename, this_extension])

    def preprocess(self, filename):
        filename = self.handle_dash_and_underscore(filename)
        filename = filename.lower()
        filename = self.correct_spaces(filename)
        return filename

    def delete_matches(self, filelist):
        i = 0
        while i < min([len(f) for f in filelist]):
            word = filelist[0][i]
            to_be_deleted = True
            for filename in filelist:
                if filename[i] != word:
                    to_be_deleted = False
                    break
            if to_be_deleted:
                for filename in filelist:
                    del(filename[i])
            else:
                i = i + 1

        i = -1
        while i >= -min([len(f) for f in filelist]):
            word = filelist[0][i]
            to_be_deleted = True
            for filename in filelist:
                if filename[i] != word:
                    to_be_deleted = False
                    break
            if to_be_deleted:
                for filename in filelist:
                    del(filename[i])
            else:
                i = i - 1

        return filelist

    def process(self, filelist):
        extensions = []
        for i, filename in enumerate(filelist):
            filelist[i], this_extension = self.split_by_extension(filename)
            extensions.append(this_extension)

        for i, filename in enumerate(filelist):
            filelist[i] = filename.split()

        filelist = self.delete_matches(filelist)

        for i, filename in enumerate(filelist):
            filelist[i] = ' '.join(filename)

        for i, filename in enumerate(filelist):
            filelist[i] = ''.join([filename, extensions[i]])

        return filelist

    def upper_char(self, string, index):
        return string[:index] + string[index].upper() + string[index + 1:]

    def upper_first_and_all_after_dot(self, filename):
        if filename[0].isdigit() and filename[1].isdigit():
            filename = self.upper_char(filename, 3)
        for i in range(len(filename)):
            if filename[i] is '.' and i is not len(filename) - 4:
                filename = self.upper_char(filename, i + 1)

        return filename

    def postprocess(self, filename):
        filename = self.upper_first_and_all_after_dot(filename)
        return filename

    def recommendation_generator(self, directory):
        for dirpath, dirnames, filenames in os.walk(directory):
            yield dirpath + '\n'
            filtered_filenames = [x for x in filenames for extension in self.extensions if x.lower().endswith(extension)]

            processed_filenames = filtered_filenames.copy()

            for i, filename in enumerate(processed_filenames):
                processed_filenames[i] = self.preprocess(filename)

            if len(processed_filenames) > 1:
                processed_filenames = self.process(processed_filenames)

            for i, filename in enumerate(processed_filenames):
                processed_filenames[i] = self.postprocess(filename)

                yield filtered_filenames[i] + '\t' + processed_filenames[i] + '\n'

    def write_recommendations(self, directory, outfile_path):
        recommendations = self.recommendation_generator(directory)
        with open(outfile_path, 'w') as outfile:
            for recommendation in recommendations:
                outfile.write(recommendation)

def main():
    parser = argparse.ArgumentParser(description='Sanitizing mp3 filenames.')
    parser.add_argument('-d', '--directory', help='The directory to look for music in.')
    parser.add_argument('-g', '--generate', help='Generate a file in which recommendations for renaming are.')

    args = parser.parse_args()

    if args.generate and args.directory:
        ps = PathSanitizer()
        ps.write_recommendations(args.directory, args.generate)
    else:
        print('You need to use the -d and -g target!\n')

if __name__ == '__main__':
    main()
