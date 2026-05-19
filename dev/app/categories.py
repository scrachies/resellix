"""Clothing category filters for snipe targets."""
from __future__ import annotations

# (id, display label)
SNIPE_CATEGORIES: list[tuple[str, str]] = [
    ("all", "Everything"),
    ("polo", "Polos"),
    ("tshirt", "T-shirts / tops"),
    ("hoodie", "Hoodies"),
    ("jumper", "Jumpers / knitwear"),
    ("jacket", "Jackets / coats"),
    ("jeans", "Jeans"),
    ("joggers", "Joggers / sweatpants"),
    ("shorts", "Shorts"),
    ("tracksuit", "Tracksuits"),
    ("shoes", "Shoes / trainers"),
    ("bag", "Bags / backpacks"),
]

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "polo": ["polo"],
    "tshirt": ["t-shirt", "tshirt", "tee shirt", "tee ", " tee", "top ", "hemd", "shirt"],
    "hoodie": ["hoodie", "hoody", "kapuzen", "sweat à capuche", "sudadera"],
    "jumper": ["jumper", "pullover", "sweater", "sweatshirt", "pull ", "pullover", "strick", "knit", "trui", "maglione"],
    "jacket": ["jacket", "jacke", "veste", "coat", "parka", "blouson", "windbreaker", "puffer", "daunen", "nuptse"],
    "jeans": ["jeans", " jean", "denim"],
    "joggers": ["jogger", "jogging", "sweatpant", "track pant", "trainingshose", "jogginghose"],
    "shorts": ["short", "bermuda"],
    "tracksuit": ["tracksuit", "track suit", "trainingsanzug", "survêtement"],
    "shoes": ["shoe", "sneaker", "trainer", "boot", "dunk", "jordan", "air max", "samba", "yeezy slide"],
    "bag": ["backpack", "rucksack", "bag", "sac ", "tasche"],
}


def listing_matches_categories(title: str, category_ids: list[str]) -> bool:
    if not category_ids or "all" in category_ids:
        return True
    hay = (title or "").lower()
    for cid in category_ids:
        keywords = _CATEGORY_KEYWORDS.get(cid, [])
        if any(kw in hay for kw in keywords):
            return True
    return False
