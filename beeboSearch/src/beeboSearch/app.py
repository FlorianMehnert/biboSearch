import toga
from toga.style.pack import *
from .glue.search import search
import os
import sys

# Add the site-packages directory to the Python path
site_packages_dir = os.path.join(sys.prefix, 'lib', 'python3.12', 'site-packages')
sys.path.append(site_packages_dir)

def build(app):
    main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    # Create a box for search input and button
    search_box = toga.Box(style=Pack(direction=ROW, padding=5))

    search_input = toga.TextInput(placeholder="Search a movie", style=Pack(flex=1))
    search_box.add(search_input)

    def search_movies(widget):
        search_term = search_input.value
        print(search_term)
        titles = search(search_term)
        result_box.clear()
        for title in titles:
            if title[1]:  # ausleihbar
                label = toga.Label(
                    title,
                    style=Pack(padding=5, background_color='#FFFF00')  # Yellow background
                )
            else:
                label = toga.Label(title, style=Pack(padding=5))
            result_box.add(label)

    search_button = toga.Button("Search", on_press=search_movies)
    search_box.add(search_button)

    # Add search box to main box
    main_box.add(search_box)

    # Create a ScrollContainer for the results
    scroll_container = toga.ScrollContainer(horizontal=True, style=Pack(flex=1))

    # Create result box
    result_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    # Add result box to scroll container
    scroll_container.content = result_box

    # Add scroll container to main box
    main_box.add(scroll_container)

    return main_box

def main():
    return toga.App("First App", "org.beeware.beebo.search", startup=build)
