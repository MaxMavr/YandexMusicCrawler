from os import getenv
from time import sleep

from dotenv import load_dotenv

from api.request import Request
from crawler import Crawler
from api.artist import ArtistApiClient

load_dotenv()

api = Request(getenv("YANDEX_TOKEN"))
artist_api_client = ArtistApiClient(api)
crawler = Crawler.from_list([160970], artist_api_client)


for artist in crawler:
    sleep(1)
    print(artist)
