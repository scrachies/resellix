from urllib.parse import parse_qsl, urlparse

from requests.exceptions import HTTPError

from pyVinted.items.item import Item
from pyVinted.requester import requester
from pyVinted.settings import Urls


class Items:
    def search(self, url, nbrItems: int = 20, page: int = 1, time: int = None, json: bool = False):
        locale = urlparse(url).netloc
        requester.setLocale(locale)
        params = self.parseUrl(url, nbrItems, page, time)
        api_url = f"https://{locale}{Urls.VINTED_API_URL}/{Urls.VINTED_PRODUCTS_ENDPOINT}"
        response = requester.get(url=api_url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
        if json:
            return items
        return [Item(_item) for _item in items]

    def parseUrl(self, url, nbrItems=20, page=1, time=None) -> dict:
        querys = parse_qsl(urlparse(url).query)

        def join_vals(key: str) -> str:
            return ",".join(str(tpl[1]) for tpl in querys if tpl[0] == key)

        def join_array(prefix: str) -> str:
            keys = (f"{prefix}[]", f"{prefix}_ids[]", f"{prefix}_id[]")
            vals = []
            for tpl in querys:
                if tpl[0] in keys:
                    vals.append(str(tpl[1]))
            return ",".join(vals)

        return {
            "search_text": "+".join(
                str(tpl[1]).replace(" ", "+")
                for tpl in querys
                if tpl[0] == "search_text"
            ),
            "catalog_ids": join_array("catalog"),
            "color_ids": join_array("color"),
            "brand_ids": join_array("brand"),
            "size_ids": join_array("size"),
            "material_ids": join_array("material"),
            "status_ids": join_array("status"),
            "country_ids": join_array("country"),
            "city_ids": join_array("city"),
            "is_for_swap": ",".join("1" for tpl in querys if tpl[0] == "disposal[]"),
            "currency": join_vals("currency") or "EUR",
            "price_to": join_vals("price_to"),
            "price_from": join_vals("price_from"),
            "page": page,
            "per_page": nbrItems,
            "order": join_vals("order") or "newest_first",
            "time": time,
        }
