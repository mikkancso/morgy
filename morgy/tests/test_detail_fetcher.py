import unittest
from morgy.database.detail_fetcher import DetailFetcher

class TestDetailFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DetailFetcher()

    def test_complex_case_with_cd_number(self):
        dirpath = '00 All/03 Külföldi Blues, Rock, Metal/Mark Knopfler/1996 Live in Copenhagen/CD1'
        name = '12 Sultans of swing'
        (artist, year, album, cd_number, number, title) = self.fetcher.fetch_detail(dirpath, name)
        self.assertEqual(artist, 'Mark Knopfler')
        self.assertEqual(year, '1996')
        self.assertEqual(album, 'Live in Copenhagen')
        self.assertEqual(cd_number, '1')
        self.assertEqual(number, '12')
        self.assertEqual(title, 'Sultans of swing')

    def test_simple_majority_case(self):
        dirpath = '00 All/01 Külföldi Punk/Millencolin/1994 Same old tunes'
        name = '06 Leona'
        (artist, year, album, cd_number, number, title) = self.fetcher.fetch_detail(dirpath, name)
        self.assertEqual(artist, 'Millencolin')
        self.assertEqual(year, '1994')
        self.assertEqual(album, 'Same old tunes')
        self.assertIsNone(cd_number)
        self.assertEqual(number, '06')
        self.assertEqual(title, 'Leona')

    def test_songs_from_compilations(self):
        dirpath = '00 All/07 Indie, játékzenék/THPS 2'
        name = 'Papa roach - Blood brothers'
        (artist, year, album, cd_number, number, title) = self.fetcher.fetch_detail(dirpath, name)
        self.assertEqual(artist, 'Papa roach')
        self.assertIsNone(year)
        self.assertIsNone(album)
        self.assertIsNone(cd_number)
        self.assertIsNone(number)
        self.assertEqual(title, 'Blood brothers')

    def test_songs_from_compilations_with_numbers(self):
        dirpath = '00 All/03 Külföldi Blues, Rock, Metal/Metallica'
        name = '13 Enter sandman'
        (artist, year, album, cd_number, number, title) = self.fetcher.fetch_detail(dirpath, name)
        self.assertEqual(artist, 'Metallica')
        self.assertIsNone(year)
        self.assertIsNone(album)
        self.assertIsNone(cd_number)
        self.assertIsNone(number)
        self.assertEqual(title, 'Enter sandman')

    def test_songs_with_simple_artist_title_structure(self):
        dirpath = '00 All/01 Külföldi Punk/Alkaline Trio'
        name = 'Private eye'
        (artist, year, album, cd_number, number, title) = self.fetcher.fetch_detail(dirpath, name)
        self.assertEqual(artist, 'Alkaline Trio')
        self.assertIsNone(year)
        self.assertIsNone(album)
        self.assertIsNone(cd_number)
        self.assertIsNone(number)
        self.assertEqual(title, 'Private eye')

    # Also see: 99 red balloons
    def test_leading_numbers_are_in_the_title(self):
        dirpath = '00 All/01 Külföldi Punk/CKY'
        name = '96 quite bitter beings'
        (artist, year, album, cd_number, number, title) = self.fetcher.fetch_detail(dirpath, name)
        self.assertEqual(artist, 'CKY')
        self.assertIsNone(year)
        self.assertIsNone(album)
        self.assertIsNone(cd_number)
        self.assertIsNone(number)
        self.assertEqual(title, '96 quite bitter beings')


if __name__ == '__main__':
    unittest.main()
