import base64
import re

import requests
from bs4 import BeautifulSoup
import streamlit as st
from pygments.lexer import default

BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient/start.do?Login=webopac&BaseURL=this"
BASE_LOGGED_IN_URL = "https://katalog.bibo-dresden.de"

from bs4 import BeautifulSoup
import re


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
        case _:
            return kind_of


@st.cache_resource
def search(search_term):
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
    data = {
        'methodToCall': 'submit',
        'CSId': csid,
        'methodToCallParameter': 'submitSearch'
    }

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
    response = session.get(search_url, params=params)

    # Enable cookie persistence
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting book titles
    titles = []
    table = soup.find("table").children  # [0].find_all('tr')
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
        kind_of_medium = a.find("img")

        kind_of_medium = kind_of_medium.get("title") if kind_of_medium else None
        response = session.get(BASE_LOGGED_IN_URL + dvd_link)
        titles.append(("✅ " if ausleihbar else "❌ ") + year + f" {get_medium(kind_of_medium)} " + title + f"{" ausleihbar" if ausleihbar else " " + find_due_dates(response.content)[0]}")
    return titles


film = st.text_input("search a movie")
titles = search(film)
st.selectbox("results", titles)
