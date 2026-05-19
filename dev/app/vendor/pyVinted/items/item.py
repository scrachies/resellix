from datetime import datetime, timezone


class Item:
    def __init__(self, data):
        self.raw_data = data
        self.id = data["id"]
        self.title = data["title"]
        self.brand_title = data.get("brand_title", "")
        self.size_title = data.get("size_title", "")
        price = data.get("price") or {}
        self.currency = price.get("currency_code", "EUR")
        self.price = price.get("amount", 0)
        photo = data.get("photo") or {}
        self.photo = photo.get("url", "")
        self.url = data.get("url", "")
        ts = None
        try:
            ts = (photo.get("high_resolution") or {}).get("timestamp")
        except Exception:
            pass
        if ts:
            self.created_at_ts = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            self.created_at_ts = datetime.now(timezone.utc)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(("id", self.id))

    def isNewItem(self, minutes=3):
        delta = datetime.now(timezone.utc) - self.created_at_ts
        return delta.total_seconds() < minutes * 60
