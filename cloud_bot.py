import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
import os
import json
import random
import time
from duckduckgo_search import DDGS
import yt_dlp
from github import Github

# --- CONFIGURATION ---
MAX_STORAGE_LIMIT = 20 * 1024 * 1024 * 1024  # 20 GB
MAX_RUNTIME_SECONDS = 5.5 * 60 * 60          # 5.5 Hours
RELEASE_TAG = "video-assets"

CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract", "Technology"]

# --- SMART SUBCATEGORY KEYWORDS ---
# The bot will scan image tags/video titles for these words
SUB_KEYWORDS = {
    "Anime": ["Naruto", "One Piece", "Dragon Ball", "Jujutsu Kaisen", "Demon Slayer", "Attack on Titan", "Bleach", "Solo Leveling", "Ghibli"],
    "Cars": ["JDM", "BMW", "Porsche", "Ferrari", "Lamborghini", "GTR", "Toyota", "Audi", "Drift", "Mustang"],
    "Gaming": ["Valorant", "League of Legends", "Elden Ring", "Genshin Impact", "Minecraft", "Cyberpunk 2077", "GTA", "Call of Duty"],
    "Nature": ["Forest", "Ocean", "Mountain", "Rain", "Space", "Sunset", "Winter", "Desert", "Beach"],
    "Cyberpunk": ["Neon", "City", "Robot", "Future", "Glitch", "Night"],
    "Abstract": ["Fluid", "Geometric", "Dark", "Light", "Minimal", "Colorful"]
}

# Cloudinary Setup
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

def check_storage_space():
    try:
        usage = cloudinary.api.usage().get('storage', {}).get('usage', 0)
        if usage >= MAX_STORAGE_LIMIT: return False 
        return True 
    except: return True 

def save_json(filepath, new_data, limit=500):
    os.makedirs("data", exist_ok=True)
    existing = []
    if os.path.exists(filepath):
        try: existing = json.load(open(filepath, "r"))
        except: pass
    
    if new_data:
        final = new_data + existing
        # Remove duplicates based on src
        unique = {v['src']:v for v in final}.values()
        with open(filepath, "w") as f: json.dump(list(unique)[:limit], f, indent=4)
        print(f"✅ Saved {filepath}")

def upload_to_github(filepath, filename):
    try:
        g = Github(os.environ.get("GITHUB_TOKEN"))
        repo = g.get_repo(os.environ.get("GITHUB_REPOSITORY"))
        try: release = repo.get_release(RELEASE_TAG)
        except: release = repo.create_git_release(RELEASE_TAG, "Assets", "Storage", prerelease=True)
        print(f"   📤 Uploading {filename} to GitHub...")
        asset = release.upload_asset(filepath, name=filename)
        return asset.browser_download_url
    except: return None

# --- INTELLIGENT TAGGER FUNCTION ---
def detect_subcategory(main_cat, text_to_scan):
    text = text_to_scan.lower()
    if main_cat in SUB_KEYWORDS:
        for keyword in SUB_KEYWORDS[main_cat]:
            if keyword.lower() in text:
                return keyword # Found a match!
    return "General"

# --- 1. WALLHAVEN (Images) ---
def download_wallhaven_batch():
    api_key = os.environ.get('WALLHAVEN_API_KEY')
    new_items = []
    cat = random.choice(CATEGORIES)
    device = random.choice(["mobile", "desktop"])
    ratio = "9x16" if device == "mobile" else "16x9"
    
    # Optional: 50% chance to search specifically for a subcategory
    search_query = cat
    if cat in SUB_KEYWORDS and random.random() > 0.5:
        search_query = random.choice(SUB_KEYWORDS[cat])
    
    print(f"🐉 Wallhaven: Searching '{search_query}' ({device})...")
    
    try:
        url = "https://wallhaven.cc/api/v1/search"
        params = {"q": search_query, "purity": "100", "sorting": "random", "ratios": ratio, "apikey": api_key}
        resp = requests.get(url, params=params).json()
        
        if "data" in resp and resp["data"]:
            img_data = resp["data"][0]
            
            # Smart Tagging: Look at Wallhaven tags
            tags_list = [t['name'] for t in img_data.get('tags', [])]
            tag_text = " ".join(tags_list)
            # If we searched for a specific subcat, use that, otherwise detect from tags
            sub_cat = search_query if search_query != cat else detect_subcategory(cat, tag_text)
            
            print(f"   🚀 Uploading {sub_cat} ({cat})...")
            res = cloudinary.uploader.upload(img_data["path"], folder=f"neonpixel/{device}/{cat}", tags=[cat, sub_cat])
            
            new_items.append({
                "title": f"{sub_cat} Wallpaper", 
                "category": cat,
                "subcategory": sub_cat, # <--- Saved to Database
                "device": device, 
                "src": res['secure_url'], 
                "type": "image", 
                "res": "4K"
            })
    except Exception as e: print(f"Error: {e}")
    return new_items

# --- 2. YOUTUBE SHORTS (Videos) ---
def download_video_batch():
    print("📌 Hunting Video...")
    new_items = []
    ddgs = DDGS()
    ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': 'temp.mp4', 'quiet': True}
    cat = random.choice(CATEGORIES)
    
    try:
        # Search for specific subcategories to ensure variety
        search_term = cat
        if cat in SUB_KEYWORDS:
            search_term = f"{cat} {random.choice(SUB_KEYWORDS[cat])}"

        query = f"site:youtube.com/shorts {search_term} aesthetic 4k vertical"
        results = list(ddgs.text(query, max_results=1))
        
        if results:
            vid_url = results[0]['href']
            title = results[0]['title']
            
            # Detect Subcategory from Title
            sub_cat = detect_subcategory(cat, title)
            if sub_cat == "General" and search_term != cat:
                # If title check failed but we searched for a specific term (e.g. "Naruto"), use that
                sub_cat = search_term.split()[-1] # Approximation

            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.extract_info(vid_url, download=True)
            
            if os.path.exists("temp.mp4"):
                if os.path.getsize("temp.mp4") < 50 * 1024 * 1024: # Limit 50MB
                    unique = f"{cat}_{random.randint(1000,9999)}.mp4"
                    dl_url = upload_to_github("temp.mp4", unique)
                    
                    if dl_url:
                        new_items.append({
                            "title": f"{sub_cat} Live", 
                            "category": cat, 
                            "subcategory": sub_cat, # <--- Saved to Database
                            "device": "mobile", 
                            "src": dl_url, 
                            "type": "video", 
                            "res": "HD"
                        })
                os.remove("temp.mp4")
    except: pass
    return new_items

# --- LOOP ---
if __name__ == "__main__":
    start = time.time()
    count = 0
    print("🤖 STARTING SMART SORTING...")
    while True:
        if time.time() - start > MAX_RUNTIME_SECONDS: break
        if not check_storage_space(): break
        
        imgs = download_wallhaven_batch()
        if imgs: save_json("data/cloud_wallpapers.json", imgs, 500)
        
        if count % 3 == 0:
            vids = download_video_batch()
            if vids: save_json("data/videos.json", vids, 100)
        
        count += 1
        time.sleep(15)