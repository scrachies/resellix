import requests
from requests.exceptions import HTTPError


class Requester:
    def __init__(self):
        self.HEADER = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
        }
        self.VINTED_AUTH_URL = "https://www.vinted.de/"
        self.MAX_RETRIES = 3
        self.session = requests.Session()
        self.session.headers.update(self.HEADER)

    def setLocale(self, locale: str) -> None:
        self.VINTED_AUTH_URL = f"https://{locale}/"
        self.HEADER["Host"] = locale
        self.session.headers.update(self.HEADER)

    def get(self, url, params=None):
        tried = 0
        while tried < self.MAX_RETRIES:
            tried += 1
            response = self.session.get(url, params=params, timeout=25)
            if response.status_code == 401 and tried < self.MAX_RETRIES:
                self.setCookies()
            elif response.status_code == 200 or tried == self.MAX_RETRIES:
                return response
        return response

    def post(self, url, params=None):
        response = self.session.post(url, params, timeout=25)
        response.raise_for_status()
        return response

    def setCookies(self) -> None:
        self.session.cookies.clear_session_cookies()
        try:
            self.session.head(self.VINTED_AUTH_URL, timeout=25, allow_redirects=True)
        except Exception as exc:
            print(f"pyVinted: cookie fetch error: {exc}")


requester = Requester()
