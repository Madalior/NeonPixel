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
MAX_STORAGE_LIMIT = 20 * 1024 * 1024 * 1024  # 20 GB (Cloudinary Limit)
MAX_RUNTIME_SECONDS = 5.5 * 60 * 60          # 5.5 Hours (GitHub Action Limit)
CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract", "Technology"]
RELEASE_TAG = "video-assets"                 # Tag for GitHub Releases

# Cloudinary Setup
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- 1. CHECK STORAGE ---
def check_storage_space():
    try:
        usage_data = cloudinary.api.usage()
        current_usage = usage_data.get('storage', {}).get('usage', 0)
        gb_used = round(current_usage / (1024 * 1024 * 1024), 2)
        print(f"💾 Storage: {gb_used} GB / 20.0 GB")
        
        if current_usage >= MAX_STORAGE_LIMIT:
            print("🛑 STORAGE FULL (20GB Reached). Stopping.")
            return False 
        return True 
    except: return True 

# --- 2. SAVE JSON ---
def save_json(filepath, new_data, limit=500):
    os.makedirs("data", exist_ok=True)
    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                existing_data = json.load(f)
        except: existing_data = []

    if not os.path.exists(filepath) and not new_data:
        with open(filepath, "w") as f: json.dump([], f)
        return

    if new_data:
        final_data = new_data + existing_data
        # Remove duplicates
        unique_data = {v['src']:v for v in final_data}.values()
        final_list = list(unique_data)[:limit]
        with open(filepath, "w") as f:
            json.dump(final_list, f, indent=4)
        print(f"✅ Updated {filepath} (+{len(new_data)} items)")

# --- 3. HELPER: GITHUB RELEASE UPLOAD ---
def upload_to_github_release(filepath, filename):
    try:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPOSITORY")
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        try:
            release = repo.get_release(RELEASE_TAG)
        except:
            print(f"   ✨ Creating Release: {RELEASE_TAG}...")
            release = repo.create_git_release(RELEASE_TAG, "Video Assets", "Storage", prerelease=True)

        print(f"   📤 Uploading {filename} to GitHub...")
        asset = release.upload_asset(filepath, name=filename)
        return asset.browser_download_url
    except Exception as e:
        print(f"   ❌ GitHub Error: {e}")
        return None

# --- 4. WALLHAVEN BATCH (Images -> Cloudinary) ---
def download_wallhaven_batch():
    api_key = os.environ.get('WALLHAVEN_API_KEY')
    new_items = []
    
    # Pick RANDOM category and device to keep mixing content
    cat = random.choice(CATEGORIES)
    device = random.choice(["mobile", "desktop"])
    ratio = "9x16" if device == "mobile" else "16x9"
    
    print(f"🐉 Fetching Wallhaven: {cat} ({device})...")
    
    try:
        url = "https://wallhaven.cc/api/v1/search"
        params = {"q": cat, "purity": "100", "sorting": "random", "ratios": ratio, "apikey": api_key}
        resp = requests.get(url, params=params).json()
        
        if "data" in resp and len(resp["data"]) > 0:
            img = resp["data"][0] # Take the first random result
            print(f"   🚀 Uploading {cat}...")
            
            res = cloudinary.uploader.upload(img["path"], folder=f"neonpixel/{device}/{cat}", tags=[cat, device])
            
            new_items.append({
                "title": f"{cat} {device}", 
                "category": cat, 
                "device": device, 
                "src": res['secure_url'], 
                "type": "image", 
                "res": "4K"
            })
    except Exception as e:
        print(f"   ❌ Wallhaven Error: {e}")
        
    return new_items

# --- 5. PINTEREST BATCH (Videos -> GitHub Releases) ---
def download_pinterest_batch():
    print("📌 Hunting Pinterest Video...")
    new_items = []
    ddgs = DDGS()
    temp_file = "temp_vid.mp4"
    ydl_opts = {'format': 'best', 'outtmpl': temp_file, 'quiet': True}
    
    cat = random.choice(CATEGORIES)
    
    try:
        # Search DuckDuckGo
        query = f"site:pinterest.com/pin/ {cat} aesthetic video vertical {random.randint(1, 1000)}"
        results = list(ddgs.text(query, max_results=1))
        
        if results:
            pin_url = results[0]['href']
            print(f"   🔍 Found Pin: {pin_url}")
            
            # Download locally first
            if os.path.exists(temp_file): os.remove(temp_file)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(pin_url, download=True)
            
            if os.path.exists(temp_file):
                unique_name = f"{cat}_{random.randint(10000,99999)}.mp4"
                
                # Upload to GitHub (Unlimited Storage)
                download_url = upload_to_github_release(temp_file, unique_name)
                
                if download_url:
                    new_items.append({
                        "title": f"{cat} Live", 
                        "category": cat, 
                        "device": "mobile", 
                        "src": download_url, 
                        "type": "video", 
                        "res": "HD"
                    })
                
                # Cleanup
                os.remove(temp_file)
    except Exception as e:
        print(f"   ⚠️ Pinterest Skip: {e}")
        
    return new_items

# --- MAIN LOOP ---
if __name__ == "__main__":
    start_time = time.time()
    batch_count = 0
    
    print("🤖 STARTING ENDLESS DOWNLOAD LOOP...")
    
    while True:
        # 1. Check Time Limit (Stop before GitHub kills us)
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print("⏰ Time Limit Reached (5.5 Hours). Stopping.")
            break
            
        # 2. Check Cloudinary Storage (Stop if 20GB full)
        if not check_storage_space():
            break
            
        # 3. Download Logic
        # Always try images (Wallhaven)
        images = download_wallhaven_batch()
        if images: save_json("data/cloud_wallpapers.json", images, 500)
        
        # Try videos every 3rd loop (to save bandwidth/time)
        if batch_count % 3 == 0:
            videos = download_pinterest_batch()
            if videos: save_json("data/videos.json", videos, 100)
        
        batch_count += 1
        print(f"💤 Sleeping 15s... (Batch {batch_count} done)")
        time.sleep(15) # Safety delay
