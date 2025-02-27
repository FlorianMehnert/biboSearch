import toga
from toga.style.pack import *
from toga.style import Pack
from .glue.search import search
import os
import sys
import time

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

        # Status display area
        self.status_box = toga.Box(style=Pack(direction=COLUMN, padding=5))

        # Progress indicator
        progress_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment='center'))
        self.progress_label = toga.Label("Ready to search", style=Pack(flex=1))
        self.progress_indicator = toga.ProgressBar(max=100, value=0, style=Pack(width=200))
        progress_box.add(self.progress_label)
        progress_box.add(self.progress_indicator)
        self.status_box.add(progress_box)

        # Activity log - shows what's happening during search
        self.activity_label = toga.Label(
            "Enter a search term and press Search",
            style=Pack(padding=5)
        )
        self.status_box.add(self.activity_label)

        # Add a cancel button for long-running searches
        self.cancel_button = toga.Button(
            "Cancel Search",
            on_press=self.cancel_search,
            style=Pack(
                padding=(5, 10),
                height=40,
                width=120,
                background_color='#F44336',
                color='white'
            )
        )
        self.cancel_button.enabled = False
        cancel_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment='center'))
        cancel_box.add(self.cancel_button)
        self.status_box.add(cancel_box)

        main_box.add(self.status_box)

        # Results container
        results_label = toga.Label("Results:", style=Pack(padding=(10, 5, 5, 5), font_weight='bold'))
        main_box.add(results_label)

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
        self.search_active = False
        self.search_cancelled = False
        self.last_status_update = time.time()

    def cancel_search(self, widget):
        """Cancel the current search operation"""
        self.search_cancelled = True
        self.activity_label.text = "Cancelling search..."
        self.cancel_button.enabled = False

    def update_activity_log(self, message):
        """Update the activity log with timestamped message"""
        # Only update if significant time has passed or it's an important message
        current_time = time.time()
        if current_time - self.last_status_update > 0.5 or "error" in message.lower() or "failed" in message.lower():
            self.activity_label.text = message
            self.last_status_update = current_time

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
        self.search_active = True
        self.search_cancelled = False

        # Show progress indicator
        self.progress_label.text = f"Searching for: {search_term}"
        self.progress_indicator.value = 0
        self.status_label.text = "Searching..."
        self.search_button.enabled = False
        self.cancel_button.enabled = True
        self.activity_label.text = f"Starting search for '{search_term}'..."

        # Call the search function with a callback to handle results
        search(search_term, max_pages, callback=self.handle_search_results)

    def handle_search_results(self, results, current_page=None, total_pages=None, is_final=False, status_message=None):
        # If search was cancelled and this isn't the final callback, ignore
        if self.search_cancelled and not is_final:
            return

        selected_medium = self.medium_selection.value

        # Update the UI on the main thread
        def update_ui(_):  # Add the parameter here
            # If this is just a status update
            if status_message and not results:
                self.update_activity_log(status_message)
                return

            # Update progress if page info provided
            if current_page and total_pages:
                self.current_pages = current_page
                self.expected_pages = total_pages
                progress_value = (self.current_pages / self.expected_pages) * 100
                self.progress_indicator.value = progress_value
                self.progress_label.text = f"Loading page {self.current_pages} of {self.expected_pages}..."

            # Process the results
            new_items = 0
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
                    new_items += 1

                self.total_results += 1

            # Update status with new items
            if new_items > 0:
                self.update_activity_log(f"Added {new_items} new items to results")
                self.status_label.text = f"Found {self.filtered_results} items matching '{selected_medium}' filter"

            # If this is the final callback, update the status
            if is_final:
                self.search_active = False
                self.cancel_button.enabled = False
                self.search_button.enabled = True

                # Create final status message
                if self.search_cancelled:
                    final_message = "Search was cancelled."
                elif self.total_results == 0:
                    final_message = "No results found."
                else:
                    final_message = f"Found {self.filtered_results} items matching '{selected_medium}' out of {self.total_results} total results."

                self.status_label.text = final_message
                self.progress_label.text = "Search complete"
                self.activity_label.text = final_message

                # Show completion dialog if necessary
                if self.total_results == 0 and not self.search_cancelled:
                    self.main_window.info_dialog(
                        "No Results",
                        "No matching items found. Try a different search term."
                    )

        # Schedule the UI update on the main thread
        self.add_background_task(update_ui)


def main():
    return MovieSearchApp("Library Search", "org.beeware.beebo.search")
