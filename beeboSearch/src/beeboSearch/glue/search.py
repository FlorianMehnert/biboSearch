from bs4 import BeautifulSoup
import requests


def search(search_term):
    BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient/start.do?Login=webopac&BaseURL=this"

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
    response = session.get(search_url, params=params)

    soup = BeautifulSoup(response.content, 'html.parser')

    titles = []
    table = soup.find("table").children
    for a in [a for a in table if "st" in a.text]:
        row_number = a.find("th").get_text(strip=True)

        title_tag = a.find("a", href=True, title=None)
        title = title_tag.get_text(strip=True) if title_tag else None

        text = a.get_text(strip=True)
        year = None
        if '[' in text and ']' in text:
            year = text.split('[')[1].split(']')[0]

        ausleihbar = False
        if a.find("span", class_="textgruen"):
            ausleihbar = True

        dvd_link = title_tag['href'] if title_tag else None
        kind_of_medium = a.find("img")
        kind_of_medium = kind_of_medium.get("title") if kind_of_medium else None
        titles.append(year + f" {kind_of_medium} " + title + f"{' ausleihbar' if ausleihbar else ''}")

    return titles
