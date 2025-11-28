import os, json

def generate(folder, output):
    items = []
    for f in os.listdir(folder):
        items.append({
            "title": f,
            "path": f"{folder}/{f}"
        })
    json.dump(items, open(f"data/{output}", "w"), indent=4)

os.makedirs("data", exist_ok=True)

generate("wallpapers", "wallpapers.json")
generate("videos", "videos.json")

print("JSON updated.")
