import json
import os


# =========================
# DATA LOADING UTILITY
# =========================
def load_schemes_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, "schemes.json")
        legacy_path = os.path.join(current_dir, "venv", "schemes.json")

        if not os.path.exists(path):
            if os.path.exists(legacy_path):
                path = legacy_path
            else:
                print(f"FILE NOT FOUND: Looking for schemes.json at {path}")
                print("Tip: Keep schemes.json in project root.")
                return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Successfully loaded {len(data)} categories from schemes.json")
            return data
    except Exception as e:
        print(f"JSON Load Error: {e}")
        return []


# =========================
# SEARCH LOGIC (Kept as is for legacy support)
# =========================
SYNONYM_MAP = {
    "farmer": ["agriculture", "crop", "rural", "kisan"],
    "student": ["education", "college", "school", "scholarship"],
    "women": ["girl", "female", "mother", "mahila"],
    "health": ["medical", "hospital", "cancer", "ayushman"],
    "job": ["employment", "skill", "training", "rozgar"],
}


def expand_keywords(query):
    words = query.lower().split()
    expanded = set(words)
    for word in words:
        if word in SYNONYM_MAP:
            expanded.update(SYNONYM_MAP[word])
    return expanded


def search_schemes(query):
    data = load_schemes_data()
    keywords = expand_keywords(query)
    results = []

    for block in data:
        category_name = str(block.get("category", "")).lower()
        schemes = block.get("schemes", [])

        if not isinstance(schemes, list):
            continue

        for scheme in schemes:
            title = str(scheme.get("title", ""))
            content = scheme.get("content", {})

            full_text = f"{title} {category_name} "
            if isinstance(content, dict):
                for value in content.values():
                    if isinstance(value, list):
                        full_text += " ".join(map(str, value)) + " "
                    else:
                        full_text += str(value) + " "

            full_text = full_text.lower()
            if any(keyword in full_text for keyword in keywords):
                results.append(
                    {
                        "title": title,
                        "scheme_url": scheme.get("scheme_url"),
                        "is_closed": scheme.get("is_closed", False),
                    }
                )
    return results


def get_schemes_by_category(category):
    data = load_schemes_data()

    def normalize(text):
        return str(text).lower().replace(" ", "").replace(",", "").replace("&", "")

    requested = normalize(category)
    results = []

    for block in data:
        block_category = normalize(block.get("category", ""))
        if requested == block_category or requested in block_category:
            schemes = block.get("schemes", [])
            for scheme in schemes:
                results.append(
                    {
                        "title": scheme.get("title"),
                        "scheme_url": scheme.get("scheme_url"),
                        "is_closed": scheme.get("is_closed", False),
                    }
                )
    return results


def get_scheme_by_title(title):
    data = load_schemes_data()
    search_title = str(title).strip().lower()

    for block in data:
        for scheme in block.get("schemes", []):
            if str(scheme.get("title")).strip().lower() == search_title:
                return {
                    "title": scheme.get("title"),
                    "category": block.get("category"),
                    "scheme_url": scheme.get("scheme_url"),
                    "is_closed": scheme.get("is_closed", False),
                    "content": scheme.get("content", {}),
                }
    return None
