import toga
from toga.style.pack import *
from .glue.search import search
import os
import sys

# Add the site-packages directory to the Python path
site_packages_dir = os.path.join(sys.prefix, 'lib', 'python3.12', 'site-packages')
sys.path.append(site_packages_dir)


def build(app):
    def search_movies(widget):
        search_term = search_input.value
        print(search_term)
        titles = search(search_term)
        result_box.clear()
        for title in titles:
            result_box.add(toga.Label(title, style=Pack(padding=(0, 0, 5, 0))))
    main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    # Top section with search input and button
    top_box = toga.Box(style=Pack(direction=ROW, padding=(0, 0, 5, 0)))
    search_input = toga.TextInput(placeholder="Search a movie", style=Pack(flex=1))
    search_button = toga.Button("Search", on_press=search_movies)

    top_box.add(search_input)
    top_box.add(search_button)

    main_box.add(top_box)

    # Scrollable result area
    result_scroll = toga.ScrollContainer(style=Pack(flex=1))
    result_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
    result_scroll.content = result_box

    main_box.add(result_scroll)



    return main_box


def main():
    return toga.App("Movie Search", "org.beeware.beebo.search", startup=build)
