#!/usr/bin/env python3

from setuptools import find_packages, setup


setup(
    name="morgy",
    version="0.1",
    description="Music organizer",
    long_description=open("README.md").read(),
    author="Miklós Tolnai",
    author_email="mikkancso@gmail.com",
    url="https://github.com/mikkancso/morgy",
    packages=find_packages(),
)
