import requests, os

API_URL = "https://api.unsplash.com/photos/random"
ACCESS_KEY = "YOUR_UNSPLASH_API_KEY"   # free key

os.makedirs("wallpapers", exist_ok=True)

for i in range(10):
    try:
        r = requests.get(API_URL, params={
            "count": 1,
            "query": "dark wallpaper",
            "orientation": "portrait",
            "client_id": ACCESS_KEY
        }).json()

        img_url = r[0]["urls"]["full"]
        filename = f"wallpapers/wp_{i}.jpg"

        img = requests.get(img_url).content
        open(filename, "wb").write(img)

        print("Saved:", filename)

    except:
        pass
