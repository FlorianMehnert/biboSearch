import toga
from toga.style.pack import *
from .glue.search import search

import os
import sys

# Add the site-packages directory to the Python path
site_packages_dir = os.path.join(sys.prefix, 'lib', 'python3.12', 'site-packages')
sys.path.append(site_packages_dir)


def build(app):
    main_box = toga.Box(style=Pack(direction=ROW, padding=10))

    search_input = toga.TextInput(placeholder="Search a movie")
    main_box.add(search_input)

    def search_movies(widget):
        search_term = search_input.value
        print(search_term)
        titles = search(search_term)
        result_box.clear()
        for title in titles:
            result_box.add(toga.Label(title))

    search_button = toga.Button("Search", on_press=search_movies)
    main_box.add(search_button)

    result_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
    main_box.add(result_box)

    return main_box


def main():
    #icon_path = os.path.abspath('icons/searching.png')
    return toga.App("First App", "org.beeware.beebo.search", startup=build)
