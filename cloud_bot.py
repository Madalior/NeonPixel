import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
import os
import json
import random
import time

# --- CONFIGURATION ---
# 20 GB Limit (in Bytes)
MAX_STORAGE_LIMIT = 20 * 1024 * 1024 * 1024 

# Wallhaven is now the PRIMARY source for almost everything
CATS_WALLHAVEN = ["Anime", "Cars", "Gaming", "Cyberpunk", "Abstract", "Technology"]
CATS_UNSPLASH = ["Nature"] # Unsplash is still king for Nature
CATEGORIES = CATS_WALLHAVEN + CATS_UNSPLASH

# Cloudinary Setup
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- SAFETY CHECK: STORAGE LIMIT ---
def check_storage_space():
    try:
        # Check Cloudinary usage
        usage_data = cloudinary.api.usage()
        current_usage = usage_data.get('storage', {}).get('usage', 0)
        
        # Convert to GB for display
        gb_used = round(current_usage / (1024 * 1024 * 1024), 2)
        print(f"💾 Current Storage Used: {gb_used} GB / 20.0 GB Limit")
        
        if current_usage >= MAX_STORAGE_LIMIT:
            print("🛑 STORAGE LIMIT REACHED! Stopping downloads to save space.")
            return False # Stop
        return True # Continue
    except Exception as e:
        print(f"⚠️ Could not check storage usage: {e}")
        return True # Assume safe if check fails

# --- HELPER: SAVE JSON ---
def save_json(filepath, new_data, limit=300):
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
        # Remove duplicates based on Image URL
        unique_data = {v['src']:v for v in final_data}.values()
        final_list = list(unique_data)[:limit]
        
        with open(filepath, "w") as f:
            json.dump(final_list, f, indent=4)
        print(f"✅ Updated {filepath} with {len(new_data)} new items.")

# --- 1. WALLHAVEN (Major Source) ---
def get_wallhaven(device_type):
    ratio = "9x16" if device_type == "mobile" else "16x9"
    print(f"🐉 Searching Wallhaven for {device_type} ({ratio})...")
    
    api_key = os.environ.get('WALLHAVEN_API_KEY')
    items = []
    
    for cat in CATS_WALLHAVEN:
        try:
            # Purity 100 = SFW. Sorting = Toplist gives high quality "Major" downloads
            url = "https://wallhaven.cc/api/v1/search"
            params = {
                "q": cat,
                "purity": "100", 
                "sorting": "toplist", # Changed to 'toplist' for MAJOR downloads
                "ratios": ratio,
                "apikey": api_key 
            }
            
            resp = requests.get(url, params=params).json()
            
            # Wallhaven returns a list. We take a random one from the top 5 to keep it fresh
            if "data" in resp and len(resp["data"]) > 0:
                # Pick a random image from the top 5 results
                limit_index = min(len(resp["data"]), 5)
                img_data = resp["data"][random.randint(0, limit_index-1)]
                
                print(f"   🚀 Uploading {device_type.upper()} {cat}...")
                
                res = cloudinary.uploader.upload(
                    img_data["path"], 
                    folder=f"neonpixel/{device_type}/{cat}", 
                    tags=[cat, device_type]
                )
                
                items.append({
                    "title": f"{cat} {device_type.capitalize()}",
                    "category": cat,
                    "device": device_type,
                    "src": res['secure_url'],
                    "type": "image",
                    "res": "4K"
                })
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Error {cat}: {e}")
    return items

# --- 2. UNSPLASH (Nature Only) ---
def get_unsplash(device_type):
    print(f"📸 Searching Unsplash for {device_type}...")
    api_key = os.environ.get('UNSPLASH_ACCESS_KEY')
    if not api_key: return []
    
    orientation = "portrait" if device_type == "mobile" else "landscape"
    items = []
    
    for cat in CATS_UNSPLASH:
        try:
            url = "https://api.unsplash.com/photos/random"
            params = {"query": f"{cat} wallpaper", "count": 1, "orientation": orientation, "client_id": api_key}
            data = requests.get(url, params=params).json()
            
            if isinstance(data, list):
                for i in data:
                    print(f"   🚀 Uploading {device_type.upper()} {cat}...")
                    res = cloudinary.uploader.upload(
                        i['urls']['regular'], 
                        folder=f"neonpixel/{device_type}/{cat}", 
                        tags=[cat, device_type]
                    )
                    items.append({
                        "title": f"{cat} Wallpaper", 
                        "category": cat, 
                        "device": device_type,
                        "src": res['secure_url'], 
                        "type": "image", 
                        "res": "4K"
                    })
        except: pass
    return items

# --- 3. PIXABAY (Videos) ---
def get_pixabay_videos():
    print("🎥 Searching Pixabay (Vertical Videos)...")
    api_key = os.environ.get('PIXABAY_API_KEY')
    if not api_key: return []
    items = []
    
    # We download videos for ALL categories
    for cat in CATEGORIES:
        try:
            url = "https://pixabay.com/api/videos/"
            params = {"key": api_key, "q": f"{cat} vertical", "per_page": 5}
            data = requests.get(url, params=params).json()
            if "hits" in data and data["hits"]:
                vid = random.choice(data["hits"])
                print(f"   🚀 Uploading Video: {cat}...")
                
                # Videos are heavy, check size? Cloudinary handles this via streaming
                res = cloudinary.uploader.upload(
                    vid["videos"]["medium"]["url"], 
                    folder=f"neonpixel/videos/{cat}", 
                    resource_type="video", 
                    tags=[cat, "live"]
                )
                items.append({
                    "title": f"{cat} Live", 
                    "category": cat, 
                    "device": "mobile",
                    "src": res['secure_url'], 
                    "type": "video", 
                    "res": "1080p"
                })
        except: pass
    return items

# --- MAIN TASK ---
if __name__ == "__main__":
    # 1. CHECK STORAGE FIRST
    if check_storage_space():
        
        # 2. Download Content
        mob_wh = get_wallhaven("mobile")
        mob_us = get_unsplash("mobile")
        desk_wh = get_wallhaven("desktop")
        desk_us = get_unsplash("desktop")
        videos = get_pixabay_videos()

        # 3. Save
        all_images = mob_wh + mob_us + desk_wh + desk_us
        save_json("data/cloud_wallpapers.json", all_images, 300)
        save_json("data/videos.json", videos, 50)
        
    else:
        print("💤 Bot sleeping due to storage limit.")