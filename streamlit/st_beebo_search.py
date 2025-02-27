import requests
import streamlit as st

BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient/start.do?Login=webopac&BaseURL=this"
BASE_LOGGED_IN_URL = "https://katalog.bibo-dresden.de"

from bs4 import BeautifulSoup
import re


class Media:
    def __init__(self, url, ausleihbar, year, title, due_dates):
        self.url: str = url if url else ""
        self.ausleihbar: bool = ausleihbar if ausleihbar else False
        self.year = year if year else "No year found"
        self.title: str = title if title else "No title found"
        self.due_dates = due_dates if due_dates else []
        self.kind_of_medium = ""

    def __str__(self):
        ausleihbar = "✅ " if self.ausleihbar else "❌ "
        return ausleihbar + self.year + " " + get_medium(self.kind_of_medium) + " " + self.title + " " + f"{" ausleihbar" if self.ausleihbar else " nicht ausleihbar "}" + (self.due_dates[0] if self.due_dates and not self.ausleihbar else "")


def find_due_dates(html_content):
    """
    return the due date of the media if it is not available
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
        return f"https://katalog.bibo-dresden.de{next_page_url}"  # Ensure full URL


def request_page(session, url, params=None):
    if params is None:
        response = session.get(url)
    else:
        response = session.get(url, params=params)
    if response.status_code == 200:
        return response
    else:
        st.warning(f"page returned with {response.status_code}")


def extract_metadata(session: requests.Session, soup: BeautifulSoup):
    titles: list[str] = []
    table = soup.find("table")
    if table:
        table = table.children  # [0].find_all('tr')
    else:
        return []
    for a in [a for a in table if "st" in a.text]:
        row_number = a.find("th").get_text(strip=True)

        # title
        title_tag = a.find("a", href=True, title=None)  # Exclude links with title="vormerken/bestellen"
        title = title_tag.get_text(strip=True) if title_tag else None

        # Extract the year of the DVD
        text = a.get_text(strip=True)
        year = None
        if '[' in text and ']' in text:
            year = text.split('[')[1].split(']')[0]

        ausleihbar = False
        if a.find("span", class_="textgruen"):
            ausleihbar = True

        # Extract the link to the DVD
        dvd_link = title_tag['href'] if title_tag else None
        kind_of_medium_raw = a.find("img")

        kind_of_medium = kind_of_medium_raw.get("title") if kind_of_medium_raw else None
        response = session.get(BASE_LOGGED_IN_URL + dvd_link)
        due_dates = find_due_dates(response.content)
        current_media = Media(url="", ausleihbar=ausleihbar, year=year, title=title, due_dates=due_dates)
        titles.append(str(current_media))
    return titles


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


@st.cache_resource
def search(search_term, max_pages):
    if search_term:
        session = requests.Session()
    else:
        return []
    url = BASE_URL
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    csid_input = soup.find('input', {'name': 'CSId'})
    if csid_input:
        csid = csid_input['value']

    search_url = f'https://katalog.bibo-dresden.de/webOPACClient/search.do?methodToCall=submit&CSId={csid}&methodToCallParameter=submitSearch'
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
    # response = session.post(search_url, data=data, allow_redirects=False)
    response = request_page(session=session, url=search_url, params=params)  # session.get(search_url, params=params)

    # Enable cookie persistence
    soup = BeautifulSoup(response.content, 'html.parser')

    next_url = get_next_page_link(soup)
    st.write("next url is: " + next_url)
    if next_url:
        st.write(get_max_pages(soup))
        #response = request_page(session=session, url=next_url)

    return extract_metadata(session=session, soup=soup)


film = st.text_input("search a movie")
max_pages = st.number_input("max_pages", min_value=1, step=1)
titles = search(film, max_pages)
st.selectbox("results", titles)

# check with the following for one page
# "everything everywhere all at once"

# check with the following for multipage but no movie in the first page
# "fight club"

# check with the following for alot of pages to test max pages
# "harry"
