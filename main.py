import asyncio
import threading
import signal
import sys

from config import REPOSITORY_CONFIG, CRAWLER_CONFIG
from crawler import Crawler
from db import Repository
from ui import create_app


if __name__ == "__main__":
    repository = Repository(REPOSITORY_CONFIG)
    crawler = Crawler(repository, CRAWLER_CONFIG)
    app = create_app(repository)

    def shutdown(signum, frame):
        crawler.stop()
        crawler_thread.join(timeout=30)

        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)


    def run_crawler():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(crawler.run())
        finally:
            loop.close()


    crawler_thread = threading.Thread(target=run_crawler)
    crawler_thread.start()

    app.run(debug=True, use_reloader=False)