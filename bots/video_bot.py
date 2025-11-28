import requests, os

PEXELS_KEY = "YOUR_PEXELS_API_KEY"
SAVE_PATH = "videos/"

os.makedirs(SAVE_PATH, exist_ok=True)

def download(url, filename):
    try:
        vid = requests.get(url).content
        with open(SAVE_PATH + filename, "wb") as f:
            f.write(vid)
        print("Downloaded:", filename)
    except:
        pass

def pexels_live_videos():
    headers = {"Authorization": PEXELS_KEY}
    res = requests.get("https://api.pexels.com/videos/search?query=loop&per_page=20", headers=headers).json()

    for x in res.get("videos", []):
        best_quality = x["video_files"][0]["link"]
        download(best_quality, f"live_{x['id']}.mp4")

pexels_live_videos()
print("Video bot finished.")
