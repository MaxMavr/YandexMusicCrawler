from os import getenv

from dotenv import load_dotenv

from api import YandexRequest
from artist import ArtistService

load_dotenv()

api = YandexRequest(getenv("YANDEX_TOKEN"))
artist_service = ArtistService(api)

artist = artist_service.get(100500)

print(artist)