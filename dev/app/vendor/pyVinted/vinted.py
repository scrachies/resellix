from .items.items import Items
from .requester import requester


class Vinted:
    def __init__(self, proxy=None):
        if proxy is not None:
            requester.session.proxies.update(proxy)
        self.items = Items()
