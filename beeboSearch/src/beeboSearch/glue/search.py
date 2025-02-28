# File: glue/search.py
import requests
from bs4 import BeautifulSoup
import re
import threading
import time

BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient/start.do?Login=webopac&BaseURL=this"
BASE_LOGGED_IN_URL = "https://katalog.bibo-dresden.de"


class Media:
    def __init__(self, url, ausleihbar, year, title, due_dates):
        self.url: str = url if url else ""
        self.ausleihbar: bool = ausleihbar if ausleihbar else False
        self.year = year if year else "No year found"
        self.title: str = title if title else "No title found"
        self.due_dates = due_dates if due_dates else []
        self.kind_of_medium = ""

    def __str__(self):
        return self.year + " " + get_medium(self.kind_of_medium) + " " + self.title + " " + f"{" ausleihbar" if self.ausleihbar else " nicht ausleihbar "}" + (self.due_dates[0] if self.due_dates and not self.ausleihbar else "")


def find_due_dates(html_content):
    """
    Return the due date of the media if it is not available
    :param html_content:
    :return:
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Search within each hit entry
    for row in soup.find_all('tr'):
        text_content = row.get_text(separator=' ', strip=True)
        # Check if "entliehen bis" is in the row
        if "entliehen" in text_content:
            # Extract the due date using regex (assumes the date follows "entliehen bis")
            due_date_match = re.search(r'entliehen.*?(\d{2}\.\d{2}\.\d{4})', text_content)
            if due_date_match:
                due_date = due_date_match.group(1)
                results.append((due_date))
    return results


def get_medium(kind_of):
    match kind_of:
        case "DVD":
            return "📀"
        case "Blu-ray Disc":
            return "🔵"
        case "CD":
            return "💿"
        case _:
            return kind_of


def get_next_page_link(soup: BeautifulSoup):
    next_page_link = soup.find('a', title="Nächste Seite")
    if next_page_link:
        next_page_url = next_page_link.get('href')
        return f"{BASE_LOGGED_IN_URL}{next_page_url}"  # Ensure full URL
    return None


def request_page(session, url, params=None, status_callback=None):
    if status_callback:
        status_callback(f"Requesting page: {url[:50]}...")

    try:
        if params is None:
            response = session.get(url, timeout=30)  # Add timeout
        else:
            response = session.get(url, params=params, timeout=30)  # Add timeout

        if response.status_code == 200:
            if status_callback:
                status_callback(f"Received response: {response.status_code}")
            return response
        else:
            error_msg = f"Page returned with status code {response.status_code}"
            if status_callback:
                status_callback(error_msg)
            print(error_msg)
            return None
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out for {url[:50]}"
        if status_callback:
            status_callback(error_msg)
        print(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error requesting page: {str(e)}"
        if status_callback:
            status_callback(error_msg)
        print(error_msg)
        return None


def extract_metadata(session: requests.Session, soup: BeautifulSoup, status_callback=None):
    if status_callback:
        status_callback("Extracting metadata from page...")

    results = []
    table = soup.find("table")
    if not table:
        if status_callback:
            status_callback("No results table found on page")
        return []

    table = table.children

    item_count = 0
    for a in [a for a in table if hasattr(a, 'text') and "st" in a.text]:
        try:
            item_count += 1
            if status_callback and item_count % 3 == 0:  # Update status every few items
                status_callback(f"Processing item {item_count}...")

            # title
            title_tag = a.find("a", href=True, title=None)
            title = title_tag.get_text(strip=True) if title_tag else None

            # Extract the year
            text = a.get_text(strip=True)
            year = None
            if '[' in text and ']' in text:
                year = text.split('[')[1].split(']')[0]

            ausleihbar = False
            if a.find("span", class_="textgruen"):
                ausleihbar = True

            # Extract the link
            item_link = title_tag['href'] if title_tag else None
            kind_of_medium_raw = a.find("img")

            kind_of_medium = kind_of_medium_raw.get("title") if kind_of_medium_raw else None

            if item_link:
                if status_callback:
                    status_callback(f"Fetching details for: {title[:30]}...")

                # Simplify - don't fetch details for each item to speed up search
                current_media = Media(url=item_link, ausleihbar=ausleihbar, year=year, title=title, due_dates=[])
                current_media.kind_of_medium = kind_of_medium
                results.append((str(current_media), ausleihbar))

                # Optional: Wait a moment to allow UI updates
                time.sleep(0.1)
        except Exception as e:
            error_msg = f"Error processing item: {str(e)}"
            if status_callback:
                status_callback(error_msg)
            print(error_msg)
            continue

    if status_callback:
        status_callback(f"Extracted {len(results)} items from page")
    return results


def get_max_pages(soup: BeautifulSoup):
    last_page_link = soup.find('a', {'title': 'Letzte Seite'})

    if last_page_link:
        last_page_url = last_page_link.get('href')

        # Extract curPos from URL
        match = re.search(r'curPos=(\d+)', last_page_url)
        if match:
            last_position = int(match.group(1))
            results_per_page = 10  # Adjust based on site pagination
            total_pages = (last_position // results_per_page) + 1
            return total_pages
    return 1  # If we can't determine, assume at least 1 page


def search(search_term, max_pages=3, callback=None):
    """
    Search the library catalog for the given term

    Args:
        search_term: The term to search for
        max_pages: Maximum number of pages to search (default: 3)
        callback: Optional callback function to receive results as they come in

    Returns:
        List of tuples containing (item_description, is_available)
    """
    if not search_term:
        return []

    all_results = []

    # Status update helper
    def status_update(message):
        if callback:
            callback([], status_message=message)

    # Run search in a background thread to avoid blocking the UI
    def search_thread():
        nonlocal all_results

        # Create a session for maintaining cookies
        session = requests.Session()

        # Initialize the session and get the CSId
        status_update("Initializing search session...")
        url = BASE_URL
        response = request_page(session, url, status_callback=status_update)
        if not response:
            status_update("Failed to initialize session")
            if callback:
                callback([], is_final=True, status_message="Search failed: Could not connect to library")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        csid_input = soup.find('input', {'name': 'CSId'})
        if not csid_input:
            status_update("Failed to get CSID token")
            if callback:
                callback([], is_final=True, status_message="Search failed: Authentication issue")
            return

        csid = csid_input['value']
        status_update(f"Got CSID: {csid[:5]}...")

        # Prepare search URL
        search_url = f'{BASE_LOGGED_IN_URL}/webOPACClient/search.do?methodToCall=submit&CSId={csid}&methodToCallParameter=submitSearch'
        params = {
            'searchCategories[0]': '-1',
            'searchString[0]': f'{search_term}',
            'callingPage': 'searchParameters',
            'selectedViewBranchlib': '0',
            'selectedSearchBranchlib': '',
            'searchRestrictionID[0]': '8',
            'searchRestrictionValue1[0]': '',
            'searchRestrictionID[1]': '6',
            'searchRestrictionValue1[1]': '',
            'searchRestrictionID[2]': '3',
            'searchRestrictionValue1[2]': '',
            'searchRestrictionValue2[2]': ''
        }

        # Execute the search
        status_update(f"Searching for: '{search_term}'...")
        response = request_page(session, search_url, params=params, status_callback=status_update)
        if not response:
            if callback:
                callback([], is_final=True, status_message="Search failed: Could not submit search")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        # Check if we have results
        if "keine Treffer" in soup.get_text():
            status_update("No results found")
            if callback:
                callback([], is_final=True, status_message=f"No results found for '{search_term}'")
            return

        # Determine total pages
        total_pages = get_max_pages(soup)
        status_update(f"Found {total_pages} pages of results")

        # Limit to specified max pages
        pages_to_fetch = min(total_pages, max_pages)

        # Process first page
        status_update("Processing first page...")
        first_page_results = extract_metadata(session, soup, status_callback=status_update)
        all_results.extend(first_page_results)

        # If callback is provided, send first batch of results
        if callback and first_page_results:
            callback(first_page_results, current_page=1, total_pages=pages_to_fetch)

        # Process remaining pages
        current_page = 1
        next_url = get_next_page_link(soup)

        while next_url and current_page < pages_to_fetch:
            current_page += 1
            status_update(f"Fetching page {current_page} of {pages_to_fetch}...")
            response = request_page(session, next_url, status_callback=status_update)
            if not response:
                status_update(f"Failed to load page {current_page}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            page_results = extract_metadata(session, soup, status_callback=status_update)
            all_results.extend(page_results)

            # If callback is provided, send this batch of results
            if callback and page_results:
                callback(page_results, current_page=current_page, total_pages=pages_to_fetch)

            # Get next page URL
            next_url = get_next_page_link(soup)

        status_update(f"Completed search with {len(all_results)} items across {current_page} pages")

        # Final callback with all results
        if callback:
            callback(all_results, is_final=True, status_message=f"Found {len(all_results)} items")

    # Start the search in a background thread
    status_update("Starting search...")
    thread = threading.Thread(target=search_thread)
    thread.daemon = True  # Make thread exit when main program exits
    thread.start()

    # For synchronous use, wait for the thread to complete
    if not callback:
        thread.join()
        return all_results
    return []  # When using callback, initial return is empty
