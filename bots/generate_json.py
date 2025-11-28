# bots/generate_json.py
import os
import json

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def load_meta(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def write_pretty(name, data):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[WRITE] {name} ({len(data)} items)")

def main():
    walls = load_meta("wallpapers_meta.json")
    vids  = load_meta("videos_meta.json")

    # You could transform / sort here
    walls_sorted = sorted(walls, key=lambda x: x.get("title",""))
    vids_sorted  = sorted(vids, key=lambda x: x.get("title",""))

    write_pretty("wallpapers.json", walls_sorted)
    write_pretty("videos.json", vids_sorted)

if __name__ == "__main__":
    main()
