import toga
from toga.style.pack import *
from toga.style import Pack
from .glue.search import search
import os
import sys

# Add the site-packages directory to the Python path
site_packages_dir = os.path.join(sys.prefix, 'lib', 'python3.12', 'site-packages')
sys.path.append(site_packages_dir)


def build(app):
    main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    # Create a box for search input, medium selection, and button
    search_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment='center'))

    search_input = toga.TextInput(
        placeholder="Search a movie",
        style=Pack(flex=1, padding=(0, 5), height=48)
    )
    search_box.add(search_input)

    # Add medium selection widget
    medium_selection = toga.Selection(
        items=['All', 'DVD', 'Book', 'CD', 'eBook'],
        style=Pack(width=100, padding=(0, 5), height=48)
    )
    search_box.add(medium_selection)

    def search_movies(widget):
        search_term = search_input.value
        selected_medium = medium_selection.value
        print(f"Searching for: {search_term}, Medium: {selected_medium}")

        titles = search(search_term)
        result_box.clear()

        for title, ausleihbar in titles:
            # Filter by medium if a specific medium is selected
            if selected_medium != 'All' and selected_medium.lower() not in title.lower():
                continue

            if ausleihbar:
                label = toga.Label(
                    title,
                    style=Pack(padding=5, background_color='#FFFF00')  # Yellow background
                )
            else:
                label = toga.Label(title, style=Pack(padding=5))
            result_box.add(label)

    search_button = toga.Button(
        "Search",
        on_press=search_movies,
        style=Pack(padding=(0, 5), height=48, width=100, background_color='#4CAF50', color='white')
    )
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
    return toga.App("Movie Search", "org.beeware.beebo.search", startup=build)
