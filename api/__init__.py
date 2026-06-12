import requests

HEADERS = {
    'X-Yandex-Music-Client': 'YandexMusicAndroid/24023621',
}
DEFAULT_TIMEOUT = 5


class YandexRequest:
    def __init__(self, token: str, language: str = 'ru'):
        self.headers = {
            **HEADERS,
            'Authorization': f'OAuth {token}',
            'Accept-Language': language,
        }

    def get(self, url: str) -> dict:
        response = requests.get(
            url,
            headers=self.headers,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()
        return response.json()
