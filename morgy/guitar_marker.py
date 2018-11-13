import argparse
import os
import shutil
import sys
import random

from morgy.database import Database

class GuitarMarker:
    def __init__(self, database=None):
        self.db = database if database else Database()

    def run(self, path, add=True):
        self.db.add_guitar_row(path, add)
        self.db.commit_and_close()

def main():
    parser = argparse.ArgumentParser(description='Mark songs as able to play on guitar.')
    parser.add_argument('-p', '--path', help='The path to the song to be marked.')

    args = parser.parse_args()
    guitar_marker = GuitarMarker()
    guitar_marker.run(args.path)

if __name__ == '__main__':
    main()
