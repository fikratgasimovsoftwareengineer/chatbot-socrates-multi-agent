from bs4 import BeautifulSoup
import urllib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class GoogleSearch:
    def __init__(self, query: str) -> None:
        self.query = query
        escaped_query = urllib.parse.quote_plus(query)
        self.URL = f"https://www.google.com/search?q={escaped_query}"
        self.ancors_list = []
        self.links = self.get_initial_links()
        self.all_page_data = self.all_pages()

    def clean_urls(self, anchors: list[str]) -> list[str]:

        links: list[str] = []
        for a in anchors:
            links.append(
                list(filter(lambda l: l.startswith("url=https"), a["href"].split("&")))
            )

        links = [
            link.split("url=")[-1]
            for sublist in links
            for link in sublist
            if len(link) > 0
        ]

        return links

    def read_url_page(self, url: str) -> str:

        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(strip=True)

    
    def get_initial_links(self) -> list[str]:
        print("Searching Google...")
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.text, "html.parser")
        anchors = soup.find_all("a")
        filtered_anchors = [
            a for a in anchors if "href" in a.attrs]
        
        return self.clean_urls(filtered_anchors)


    def all_pages(self) -> list[tuple[str, str]]:

        data: list[tuple[str, str]] = []
        with ThreadPoolExecutor(max_workers=4) as executor:

            future_to_url = {
                executor.submit(self.read_url_page, url): url for url in self.links
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    output = future.result()
                    data.append((url, output))

                except requests.exceptions.HTTPError as e:
                    print(e)

        # for url in self.links:
        #     try:
        #         data.append((url, self.read_url_page(url)))
        #     except requests.exceptions.HTTPError as e:
        #         print(e)

        return data
    
if __name__=="__main__":
    search = GoogleSearch("university of uninettuno?")