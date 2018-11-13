import os

class DetailFetcher:
    def split_to_dirs(self, path):
        dirs = list()
        while not path.endswith("00 All"):
            path, directory = os.path.split(path)
            dirs.append(directory)
        return dirs

    def fetch_detail(self, dirpath, name):
        dirs = self.split_to_dirs(dirpath)
        artist = None
        year = None
        album = None
        cd_number = None
        number = None

        # 00 All/03 Külföldi Blues, Rock, Metal/Mark Knopfler/1996 Live in Copenhagen/CD1/12 Sultans of swing.mp3
        if len(dirs) == 4:
            cd_number = dirs[0][-1]
            dirs = dirs[1:]

        # 00 All/01 Külföldi Punk/Millencolin/1994 Same old tunes/06 Leona.mp3
        if len(dirs) == 3:
            if name[:2].isdigit():
                number = name[:2]
                title = name[3:]
            else:
                title = name

            if dirs[0][:4].isdigit():
                year = dirs[0][:4]
                album = dirs[0][5:]
            else:
                album = dirs[0]
            artist = dirs[1]

        # 00 All/07 Indie, játékzenék/THPS 2/Papa roach - Blood brothers.mp3
        elif len(dirs) == 2 and ' - ' in name:
            artist, title = name.split(' - ')

        elif len(dirs) == 2:
            # 00 All/03 Külföldi Blues, Rock, Metal/Metallica/13 Enter sandman.mp3
            # 00 All/01 Külföldi Punk/Alkaline Trio/Private eye.mp3
            # special: 00 All/01 Külföldi Punk/CKY/96 quite bitter beings.mp3
            title = name[3:] if name[:2].isdigit() and int(name[:2]) < 90 else name
            artist = dirs[0]

        else:
            title = name

        return (artist, year, album, cd_number, number, title)
