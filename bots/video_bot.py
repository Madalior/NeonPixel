import requests, os

PEXELS_API = "YOUR_PEXELS_API_KEY"
url = "https://api.pexels.com/videos/search"

headers = {
    "Authorization": PEXELS_API
}

os.makedirs("videos", exist_ok=True)

params = {
    "query": "loop neon",
    "per_page": 5,
    "orientation": "portrait"
}

data = requests.get(url, headers=headers, params=params).json()

for i, vid in enumerate(data["videos"]):
    video_url = vid["video_files"][0]["link"]
    filename = f"videos/live_{i}.mp4"

    v = requests.get(video_url).content
    open(filename, "wb").write(v)

    print("Saved:", filename)
