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
        # Main layout container
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Search box with input, medium selection, and max pages
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

        # Add max pages selection
        pages_box = toga.Box(style=Pack(direction=ROW, padding=(5, 0), alignment='center'))
        pages_label = toga.Label("Max pages:", style=Pack(padding=(0, 5)))
        self.max_pages = toga.NumberInput(
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            style=Pack(width=60, padding=(0, 5), height=40)
        )
        pages_box.add(pages_label)
        pages_box.add(self.max_pages)

        # Search button
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
        main_box.add(pages_box)

        # Progress indicator
        self.progress_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment='center'))
        self.progress_label = toga.Label("Ready to search", style=Pack(flex=1))
        self.progress_indicator = toga.ProgressBar(max=100, value=0, style=Pack(width=200))
        self.progress_box.add(self.progress_label)
        self.progress_box.add(self.progress_indicator)
        self.progress_box.style.visibility = 'hidden'
        main_box.add(self.progress_box)

        # Results container
        self.scroll_container = toga.ScrollContainer(horizontal=True, style=Pack(flex=1))
        self.result_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.scroll_container.content = self.result_box
        main_box.add(self.scroll_container)

        # Status bar
        self.status_label = toga.Label("", style=Pack(padding=5))
        main_box.add(self.status_label)

        # Set up main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

        # For results tracking
        self.total_results = 0
        self.filtered_results = 0
        self.current_pages = 0
        self.expected_pages = 0

    def search_movies(self, widget):
        # Get search parameters
        search_term = self.search_input.value
        selected_medium = self.medium_selection.value
        max_pages = self.max_pages.value

        if not search_term:
            self.main_window.info_dialog(
                "Input Required",
                "Please enter a search term"
            )
            return

        # Clear previous results
        self.result_box.clear()
        self.total_results = 0
        self.filtered_results = 0
        self.current_pages = 0

        # Show progress indicator
        self.progress_box.style.visibility = 'visible'
        self.progress_label.text = f"Searching for: {search_term}"
        self.progress_indicator.value = 0
        self.status_label.text = "Searching..."
        self.search_button.enabled = False

        # Call the search function with a callback to handle results
        search(search_term, max_pages, callback=self.handle_search_results)

    def handle_search_results(self, results, is_final=False):
        selected_medium = self.medium_selection.value

        # Update the UI on the main thread
        def update_ui():
            # Update progress if not final
            if not is_final:
                self.current_pages += 1
                self.expected_pages = max(self.expected_pages, self.current_pages)
                progress_value = (self.current_pages / self.expected_pages) * 100
                self.progress_indicator.value = progress_value
                self.progress_label.text = f"Loading page {self.current_pages}..."

            # Process the results
            for title, ausleihbar in results:
                # Only add to UI if it passes the medium filter
                if selected_medium == 'All' or selected_medium.lower() in title.lower():
                    # Create a container box for the item
                    item_box = toga.Box(style=Pack(
                        direction=ROW,
                        padding=5,
                        alignment='center',
                        background_color='#E8F5E9' if ausleihbar else '#F5F5F5'
                    ))

                    # Add availability indicator
                    avail_label = toga.Label(
                        "✅ " if ausleihbar else "❌ ",
                        style=Pack(width=30, padding=(0, 5))
                    )
                    item_box.add(avail_label)

                    # Add title label
                    title_label = toga.Label(
                        title,
                        style=Pack(flex=1, padding=5)
                    )
                    item_box.add(title_label)

                    # Add the item box to the results
                    self.result_box.add(item_box)
                    self.filtered_results += 1

                self.total_results += 1

            # If this is the final callback, update the status
            if is_final:
                self.progress_box.style.visibility = 'hidden'
                self.status_label.text = f"Found {self.filtered_results} items matching '{selected_medium}' out of {self.total_results} total results."
                self.search_button.enabled = True

                # Show completion dialog
                if self.total_results == 0:
                    self.main_window.info_dialog(
                        "No Results",
                        "No matching items found. Try a different search term."
                    )

        # Schedule the UI update on the main thread
        self.add_background_task(update_ui)


def main():
    return MovieSearchApp("Library Search", "org.beeware.beebo.search")
