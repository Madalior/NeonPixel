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
MAX_STORAGE_LIMIT = 20 * 1024 * 1024 * 1024  # 20 GB (For Cloudinary)
CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract", "Technology"]
RELEASE_TAG = "video-assets" # The tag name for your video storage release

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

def save_json(filepath, new_data, limit=300):
    os.makedirs("data", exist_ok=True)
    existing = []
    if os.path.exists(filepath):
        try: existing = json.load(open(filepath, "r"))
        except: pass
    
    if new_data:
        final = new_data + existing
        unique = {v['src']:v for v in final}.values()
        with open(filepath, "w") as f: json.dump(list(unique)[:limit], f, indent=4)
        print(f"✅ Updated {filepath}")

# --- HELPER: GITHUB RELEASE UPLOAD ---
def upload_to_github_release(filepath, filename):
    try:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPOSITORY")
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Get or Create Release
        try:
            release = repo.get_release(RELEASE_TAG)
        except:
            print(f"   ✨ Creating new Release: {RELEASE_TAG}...")
            release = repo.create_git_release(RELEASE_TAG, "Video Assets", "Storage for unlimited videos", prerelease=True)

        print(f"   📤 Uploading {filename} to GitHub Releases...")
        asset = release.upload_asset(filepath, name=filename)
        return asset.browser_download_url
    except Exception as e:
        print(f"   ❌ GitHub Upload Error: {e}")
        return None

# --- 1. WALLHAVEN (Images -> Cloudinary) ---
def get_wallhaven(device_type):
    ratio = "9x16" if device_type == "mobile" else "16x9"
    print(f"🐉 Searching Wallhaven Images for {device_type}...")
    api_key = os.environ.get('WALLHAVEN_API_KEY')
    items = []
    
    for cat in CATEGORIES:
        try:
            url = "https://wallhaven.cc/api/v1/search"
            params = {"q": cat, "purity": "100", "sorting": "toplist", "ratios": ratio, "apikey": api_key}
            resp = requests.get(url, params=params).json()
            if "data" in resp and resp["data"]:
                limit = min(len(resp["data"]), 5)
                img = resp["data"][random.randint(0, limit-1)]
                print(f"   🚀 Uploading Image: {cat}...")
                res = cloudinary.uploader.upload(img["path"], folder=f"neonpixel/{device_type}/{cat}", tags=[cat, device_type])
                items.append({"title": f"{cat} {device_type}", "category": cat, "device": device_type, "src": res['secure_url'], "type": "image", "res": "4K"})
            time.sleep(1)
        except: pass
    return items

# --- 2. PINTEREST VIDEO (-> GitHub Releases) ---
def get_pinterest_videos():
    print("📌 Searching Pinterest Videos (Hacker Mode)...")
    items = []
    ddgs = DDGS()
    
    # Configure yt-dlp to download to a temp file
    temp_filename = "temp_video.mp4"
    ydl_opts = {
        'format': 'best',
        'outtmpl': temp_filename,
        'quiet': True,
        'no_warnings': True,
    }

    for cat in CATEGORIES:
        try:
            query = f"site:pinterest.com/pin/ {cat} aesthetic video vertical"
            results = list(ddgs.text(query, max_results=2))
            
            for res in results:
                pin_url = res['href']
                print(f"   🔍 Found Pin: {pin_url}")
                
                try:
                    # Download locally
                    if os.path.exists(temp_filename): os.remove(temp_filename)
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(pin_url, download=True)
                    
                    if os.path.exists(temp_filename):
                        # Create a unique name for the file
                        unique_name = f"{cat}_{random.randint(1000,9999)}.mp4"
                        
                        # Upload to GitHub Releases
                        download_url = upload_to_github_release(temp_filename, unique_name)
                        
                        if download_url:
                            items.append({
                                "title": f"{cat} Pinterest", 
                                "category": cat, 
                                "device": "mobile", 
                                "src": download_url, # Direct GitHub Link
                                "type": "video", 
                                "res": "HD"
                            })
                        
                        # Cleanup
                        os.remove(temp_filename)
                        break 
                except Exception as e:
                    print(f"      ⚠️ Failed: {e}")
                    continue
            time.sleep(2)
        except Exception as e:
            print(f"   ❌ Search Error {cat}: {e}")
    return items

# --- MAIN TASK ---
if __name__ == "__main__":
    if check_storage_space():
        # Images (Wallhaven -> Cloudinary)
        mob_wh = get_wallhaven("mobile")
        desk_wh = get_wallhaven("desktop")
        
        # Videos (Pinterest -> GitHub Releases)
        videos = get_pinterest_videos()

        # Save
        all_images = mob_wh + desk_wh
        save_json("data/cloud_wallpapers.json", all_images, 300)
        save_json("data/videos.json", videos, 50)
    else:
        print("💤 Storage full.")