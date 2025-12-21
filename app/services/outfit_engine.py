import random
from collections import defaultdict

SLOTS = ["top", "bottom", "shoes", "outerwear"]

CONTEXT_RULES = {
    "office": {"formality_min": 3},
    "brunch": {"formality_min": 2},
    "date": {"formality_min": 3},
    "gym": {"formality_min": 1},
}

def generate_outfit(items: list[dict], context: str) -> dict:
    rules = CONTEXT_RULES.get(context, {})
    min_formality = rules.get("formality_min", 1)

    filtered = [
        it for it in items
        if it["formality"] >= min_formality
    ]

    by_category = defaultdict(list)
    for it in filtered:
        by_category[it["category"]].append(it)

    outfit = {}
    for slot in SLOTS:
        options = by_category.get(slot, [])
        if options:
            outfit[slot] = random.choice(options)

    return outfit
    
def generate_outfits(items: list[dict], context: str, k: int = 3) -> list[dict]:
    # generate k outfits, avoid exact duplicates
    seen = set()
    outfits = []
    tries = 0

    while len(outfits) < k and tries < 50:
        tries += 1
        o = generate_outfit(items, context)
        key = tuple((slot, o.get(slot, {}).get("id")) for slot in SLOTS)
        if key in seen:
            continue
        seen.add(key)
        outfits.append(o)

    return outfits

