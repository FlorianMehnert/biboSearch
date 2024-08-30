import toga
from toga.style.pack import *
from toga.style import Pack
from .glue.search import search
import os
import sys

# Add the site-packages directory to the Python path
site_packages_dir = os.path.join(sys.prefix, 'lib', 'python3.12', 'site-packages')
sys.path.append(site_packages_dir)


class MovieSearchApp(toga.App):
    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        search_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment='center'))

        self.search_input = toga.TextInput(
            placeholder="Search a movie",
            style=Pack(flex=1, padding=(0, 5), height=48)
        )
        search_box.add(self.search_input)

        self.medium_selection = toga.Selection(
            items=['All', 'DVD', 'Book', 'CD', 'eBook'],
            style=Pack(width=100, padding=(0, 5), height=48)
        )
        search_box.add(self.medium_selection)

        self.search_button = toga.Button(
            "Search",
            on_press=self.search_movies,
            style=Pack(
                padding=(5, 10),
                height=48,
                width=100,
                background_color='#4CAF50',
                color='white',
                font_weight='bold'
            )
        )
        search_box.add(self.search_button)

        main_box.add(search_box)

        self.scroll_container = toga.ScrollContainer(horizontal=True, style=Pack(flex=1))
        self.result_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.scroll_container.content = self.result_box
        main_box.add(self.scroll_container)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def search_movies(self, widget):
        search_term = self.search_input.value
        selected_medium = self.medium_selection.value
        print(f"Searching for: {search_term}, Medium: {selected_medium}")

        titles = search(search_term)
        self.result_box.clear()

        for title, ausleihbar in titles:
            if selected_medium != 'All' and selected_medium.lower() not in title.lower():
                continue

            if ausleihbar:
                label = toga.Label(
                    title,
                    style=Pack(padding=5, background_color='#4CAF50')
                )
            else:
                label = toga.Label(title, style=Pack(padding=5))
            self.result_box.add(label)


def main():
    return MovieSearchApp("Movie Search", "org.beeware.beebo.search")
