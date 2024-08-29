from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient/start.do?Login=webopac&BaseURL=this"


class SearchApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10)

        self.search_input = TextInput(hint_text='Enter a movie title')
        layout.add_widget(self.search_input)

        search_button = Button(text='Search', on_press=self.search_movie)
        layout.add_widget(search_button)

        self.result_label = Label(text='')
        layout.add_widget(self.result_label)

        return layout

    def search_movie(self, instance):
        search_term = self.search_input.text
        titles = self.search(search_term)
        self.result_label.text = '\n'.join(titles)

    def search(self, search_term):
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
            ausleihbar_string = ""
            if ausleihbar:
                ausleihbar_string = " ausleihbar"
            titles.append(year + f" {kind_of_medium} " + title + ausleihbar_string)

        return titles


if __name__ == '__main__':
    SearchApp().run()
