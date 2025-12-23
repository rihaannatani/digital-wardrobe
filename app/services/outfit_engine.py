import random
from collections import defaultdict

SLOTS = ["top", "bottom", "shoes", "outerwear"]

CONTEXT_RULES = {
    "office": {"formality_min": 3},
    "brunch": {"formality_min": 2},
    "date": {"formality_min": 3},
    "gym": {"formality_min": 1},
}

def hue_dist(a: int, b: int) -> int:
    d = abs(a - b) % 360
    return min(d, 360 - d)

def harmony_score(h1: int, h2: int) -> float:
    d = hue_dist(h1, h2)
    # Good: same hue (0), analogous (~30), complementary (~180)
    targets = [0, 30, 180]
    best = min(abs(d - t) for t in targets)
    return -float(best)  # higher is better

def generate_outfit(items: list[dict], context: str) -> dict:
    rules = CONTEXT_RULES.get(context, {})
    min_formality = rules.get("formality_min", 1)

    filtered = [it for it in items if int(it.get("formality", 1)) >= min_formality]

    by_category = defaultdict(list)
    for it in filtered:
        by_category[it.get("category")].append(it)

    outfit: dict[str, dict] = {}

    # pick a seed slot
    seed_slot = None
    for s in ["top", "outerwear", "bottom", "shoes"]:
        if by_category.get(s):
            seed_slot = s
            break

    if not seed_slot:
        return outfit

    seed = random.choice(by_category[seed_slot])
    outfit[seed_slot] = seed
    seed_h = seed.get("color_h")

    for slot in SLOTS:
        if slot == seed_slot:
            continue
        options = by_category.get(slot, [])
        if not options:
            continue

        # fallback random if no hue data
        if seed_h is None:
            outfit[slot] = random.choice(options)
            continue

        best_it = None
        best_score = -10_000.0
        for it in options:
            h = it.get("color_h")
            if h is None:
                score = -9999.0
            else:
                score = harmony_score(int(seed_h), int(h))
            if score > best_score:
                best_score = score
                best_it = it

        outfit[slot] = best_it or random.choice(options)

    return outfit

def generate_outfits(items: list[dict], context: str, k: int = 3) -> list[dict]:
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
