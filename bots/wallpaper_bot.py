import requests, os, json, random

PEXELS_KEY = "YOUR_PEXELS_API_KEY"
PIXABAY_KEY = "YOUR_PIXABAY_API_KEY"
UNSPLASH_KEY = "YOUR_UNSPLASH_API_KEY"

SAVE_PATH = "wallpapers/"

os.makedirs(SAVE_PATH, exist_ok=True)

def download(url, filename):
    try:
        img = requests.get(url).content
        with open(SAVE_PATH + filename, "wb") as f:
            f.write(img)
        print("Downloaded:", filename)
    except:
        pass

def pexels_wallpapers():
    headers = {"Authorization": PEXELS_KEY}
    res = requests.get("https://api.pexels.com/v1/search?query=wallpaper&per_page=30", headers=headers).json()
    for x in res.get("photos", []):
        download(x["src"]["original"], f"pexels_{x['id']}.jpg")

def pixabay_wallpapers():
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q=wallpaper&image_type=photo&per_page=30"
    res = requests.get(url).json()
    for x in res.get("hits", []):
        download(x["largeImageURL"], f"pixabay_{x['id']}.jpg")

def unsplash_wallpapers():
    url = f"https://api.unsplash.com/photos/random?query=wallpaper&count=20&client_id={UNSPLASH_KEY}"
    res = requests.get(url).json()
    for x in res:
        download(x["urls"]["full"], f"unsplash_{x['id']}.jpg")

pexels_wallpapers()
pixabay_wallpapers()
unsplash_wallpapers()

print("Wallpaper bot finished.")
