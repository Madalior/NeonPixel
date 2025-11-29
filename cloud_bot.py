import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
import os
import json
import random
import time
import subprocess
from duckduckgo_search import DDGS
import yt_dlp
from github import Github

# --- CONFIGURATION ---
MAX_STORAGE_LIMIT = 20 * 1024 * 1024 * 1024  # 20 GB Limit
WORK_CYCLE_SECONDS = 5 * 60                  # 5 Minutes (Work)
BREAK_CYCLE_SECONDS = 60                     # 1 Minute (Break)

CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract", "Technology"]
RELEASE_TAG = "video-assets"

# --- SETUP ---
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- GIT HELPER ---
def git_sync():
    print("💾 SYNCING WITH GITHUB...")
    try:
        # 1. Add files
        subprocess.run(["git", "add", "data/cloud_wallpapers.json", "data/videos.json"], check=True)
        
        # 2. Commit (if changes exist)
        commit_msg = f"🤖 AI Update: +{random.randint(1,99)} assets"
        subprocess.run(["git", "commit", "-m", commit_msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 3. Pull & Rebase (To fix conflicts)
        subprocess.run(["git", "pull", "--rebase"], check=True)
        
        # 4. Push
        subprocess.run(["git", "push"], check=True)
        print("✅ Sync Complete!")
    except Exception as e:
        print(f"⚠️ Git Sync Failed: {e}")

# --- DATA HELPERS ---
def check_storage_space():
    try:
        usage = cloudinary.api.usage().get('storage', {}).get('usage', 0)
        if usage >= MAX_STORAGE_LIMIT: return False 
        return True 
    except: return True 

def save_json(filepath, new_data, limit=500):
    os.makedirs("data", exist_ok=True)
    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f: existing_data = json.load(f)
        except: pass
    
    if new_data:
        final = new_data + existing_data
        unique = {v['src']:v for v in final}.values()
        with open(filepath, "w") as f: json.dump(list(unique)[:limit], f, indent=4)

def upload_to_github(filepath, filename):
    try:
        g = Github(os.environ.get("GITHUB_TOKEN"))
        repo = g.get_repo(os.environ.get("GITHUB_REPOSITORY"))
        try: release = repo.get_release(RELEASE_TAG)
        except: release = repo.create_git_release(RELEASE_TAG, "Assets", "Storage", prerelease=True)
        asset = release.upload_asset(filepath, name=filename)
        return asset.browser_download_url
    except: return None

def detect_subcategory(main_cat, text):
    text = text.lower()
    SUB_KEYWORDS = {
        "Anime": ["Naruto", "One Piece", "Dragon Ball", "Jujutsu Kaisen", "Demon Slayer", "Attack on Titan", "Bleach", "Solo Leveling", "Ghibli", "Pokemon"],
        "Cars": ["JDM", "BMW", "Porsche", "Ferrari", "Lamborghini", "GTR", "Toyota", "Audi", "Drift", "Mustang"],
        "Gaming": ["Valorant", "League of Legends", "Elden Ring", "Genshin Impact", "Minecraft", "Cyberpunk 2077", "GTA", "Call of Duty"],
        "Nature": ["Forest", "Ocean", "Mountain", "Rain", "Space", "Sunset", "Winter", "Desert", "Beach"],
        "Cyberpunk": ["Neon", "City", "Robot", "Future", "Glitch", "Night"],
        "Abstract": ["Fluid", "Geometric", "Dark", "Light", "Minimal", "Colorful"],
        "Technology": ["Code", "Circuit", "AI", "Server", "Hacker"]
    }
    if main_cat in SUB_KEYWORDS:
        for k in SUB_KEYWORDS[main_cat]:
            if k.lower() in text: return k
    return "General"

# --- DOWNLOADERS ---
def download_wallhaven():
    api_key = os.environ.get('WALLHAVEN_API_KEY')
    cat = random.choice(CATEGORIES)
    device = random.choice(["mobile", "desktop"])
    ratio = "9x16" if device == "mobile" else "16x9"
    
    try:
        url = "https://wallhaven.cc/api/v1/search"
        params = {"q": cat, "purity": "100", "sorting": "random", "ratios": ratio, "apikey": api_key}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        data = requests.get(url, params=params, headers=headers).json()
        
        if "data" in data and data["data"]:
            img_data = data["data"][0]
            tags = " ".join([t['name'] for t in img_data.get('tags', [])])
            sub_cat = detect_subcategory(cat, tags)
            
            print(f"   🚀 Uploading Image: {sub_cat} ({cat})...")
            
            img_path = "temp_img.jpg"
            with open(img_path, "wb") as f: 
                f.write(requests.get(img_data["path"], headers=headers).content)
            
            res = cloudinary.uploader.upload(img_path, folder=f"neonpixel/{device}/{cat}", tags=[cat, sub_cat])
            os.remove(img_path)
            
            return [{
                "title": f"{sub_cat} Wallpaper", "category": cat, "subcategory": sub_cat,
                "device": device, "src": res['secure_url'], "type": "image", "res": "4K"
            }]
    except: pass
    return []

def download_pinterest_video():
    cat = random.choice(CATEGORIES)
    try:
        ddgs = DDGS()
        query = f"site:youtube.com/shorts {cat} aesthetic 4k vertical"
        results = list(ddgs.text(query, max_results=1))
        
        if results:
            title = results[0]['title']
            sub_cat = detect_subcategory(cat, title)
            
            print(f"   🎥 Downloading Video: {title}...")
            ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': 'temp.mp4', 'quiet': True}
            
            if os.path.exists("temp.mp4"): os.remove("temp.mp4")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.extract_info(results[0]['href'], download=True)
            
            if os.path.exists("temp.mp4"):
                unique = f"{cat}_{random.randint(1000,9999)}.mp4"
                dl_url = upload_to_github("temp.mp4", unique)
                os.remove("temp.mp4")
                
                if dl_url:
                    return [{
                        "title": f"{sub_cat} Live", "category": cat, "subcategory": sub_cat,
                        "device": "mobile", "src": dl_url, "type": "video", "res": "HD"
                    }]
    except: pass
    return []

# --- MAIN ENGINE ---
if __name__ == "__main__":
    start_time = time.time()
    print("🤖 BOT STARTED: Endless Mode (Until 6h Timeout)")
    
    while True:
        # We removed the MAX_RUNTIME check. It will run until GitHub kills it.
        
        # --- WORK CYCLE (5 Minutes) ---
        cycle_end = time.time() + WORK_CYCLE_SECONDS
        print(f"\n🔨 STARTING 5 MINUTE WORK CYCLE (Until {time.ctime(cycle_end)})")
        
        while time.time() < cycle_end:
            if not check_storage_space(): 
                print("🛑 STORAGE FULL. Exiting.")
                exit() # Full stop if storage is full
            
            # 1. Download Image
            imgs = download_wallhaven()
            if imgs: save_json("data/cloud_wallpapers.json", imgs, 500)
            
            # 2. Download Video (30% chance)
            if random.random() > 0.7: 
                vids = download_pinterest_video()
                if vids: save_json("data/videos.json", vids, 100)
            
            time.sleep(10)
            
        # --- SAVE & BREAK CYCLE ---
        print("\n💾 WORK CYCLE DONE. SAVING & RESTING...")
        git_sync()
        
        print(f"☕ Taking 1 Minute Break...")
        time.sleep(BREAK_CYCLE_SECONDS)