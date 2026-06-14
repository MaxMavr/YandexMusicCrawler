from config import REPOSITORY_CONFIG, CRAWLER_CONFIG
from crawler import Crawler
from db import Repository

repository = Repository(REPOSITORY_CONFIG)
crawler = Crawler(repository, CRAWLER_CONFIG)

for (current_id, len_queue) in crawler:
    print(f"{current_id = }, {len_queue = }")

# app.run(debug=True)
