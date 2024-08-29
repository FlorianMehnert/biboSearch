import requests
from bs4 import BeautifulSoup
import streamlit as st

BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient/start.do?Login=webopac&BaseURL=this"

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
        titles.append(year + f" {kind_of_medium} " + title + f"{" ausleihbar" if ausleihbar else ""}")

    return titles


film = st.text_input("search a movie")
titles = search(film)
st.selectbox("results", titles)
