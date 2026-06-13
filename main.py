from time import sleep

from api.artist import ApiClient
from api.request import Request
from config import POSTGRESQL_PASSWORD, YANDEX_TOKEN, API_RATE
from crawler import Crawler
from db import Repository
from utils.rate_limiter import RateLimiter

_api = Request(YANDEX_TOKEN)
repository = Repository(database="music", password=POSTGRESQL_PASSWORD)
_api_client = ApiClient(_api)
rate_limiter = RateLimiter(API_RATE)

crawler = Crawler.from_list([160970], _api_client, repository, rate_limiter)

for (current_id, len_queue) in crawler:
    print(f"{current_id = }, {len_queue = }")
