import cloudinary
import cloudinary.uploader
import requests
import os
import json
import random
import time

# --- CONFIGURATION ---
CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract"]

# Cloudinary Setup (Reads secure keys from GitHub)
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- HELPER: SAVE JSON SAFELY ---
def save_json(filepath, new_data, limit=100):
    os.makedirs("data", exist_ok=True)
    
    # Load existing data to keep old wallpapers
    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                existing_data = json.load(f)
        except:
            existing_data = []

    # If no file exists and no new data, create an empty one (Prevents Git Errors)
    if not os.path.exists(filepath) and not new_data:
        with open(filepath, "w") as f:
            json.dump([], f, indent=4)
        print(f"⚠️ Created empty file: {filepath}")
        return

    # If we have new data, merge and save
    if new_data:
        final_data = new_data + existing_data
        final_data = final_data[:limit] # Keep list size manageable
        with open(filepath, "w") as f:
            json.dump(final_data, f, indent=4)
        print(f"✅ Updated {filepath} with {len(new_data)} new items.")

# --- 1. DOWNLOAD IMAGES (UNSPLASH) ---
def get_unsplash_images():
    print("📸 Starting Image Search (Unsplash)...")
    api_key = os.environ.get('UNSPLASH_ACCESS_KEY')
    if not api_key:
        print("⚠️ No Unsplash Key found. Skipping.")
        return []

    new_items = []
    for cat in CATEGORIES:
        try:
            # We search specifically for the category (e.g., "Anime dark wallpaper")
            url = "https://api.unsplash.com/photos/random"
            params = {"query": f"{cat} dark wallpaper", "count": 1, "orientation": "portrait", "client_id": api_key}
            data = requests.get(url, params=params).json()
            
            if isinstance(data, list):
                for item in data:
                    img_url = item['urls']['regular']
                    print(f"   🚀 Uploading {cat}...")
                    try:
                        # Upload to Cloudinary
                        res = cloudinary.uploader.upload(img_url, folder=f"neonpixel/{cat}", tags=[cat, "wallpaper"])
                        
                        # Add to list with correct format for index.html
                        new_items.append({
                            "title": f"{cat} Wallpaper", 
                            "category": cat,
                            "src": res['secure_url'], 
                            "type": "image", 
                            "res": "4K"
                        })
                    except Exception as e:
                        print(f"      ❌ Cloudinary Upload Failed: {e}")
            time.sleep(1) # Be nice to the API
        except Exception as e:
            print(f"   ❌ Error {cat}: {e}")
    return new_items

# --- 2. DOWNLOAD VIDEOS (PIXABAY) ---
def get_pixabay_videos():
    print("🎥 Starting Video Search (Pixabay)...")
    api_key = os.environ.get('PIXABAY_API_KEY')
    if not api_key:
        print("⚠️ No Pixabay Key found. Skipping.")
        return []

    new_items = []
    for cat in CATEGORIES:
        try:
            url = "https://pixabay.com/api/videos/"
            params = {"key": api_key, "q": f"{cat} vertical loop", "per_page": 3}
            data = requests.get(url, params=params).json()
            
            if "hits" in data and len(data["hits"]) > 0:
                vid = random.choice(data["hits"])
                print(f"   🚀 Uploading Video {cat}...")
                try:
                    # Upload to Cloudinary
                    res = cloudinary.uploader.upload(vid["videos"]["medium"]["url"], folder=f"neonpixel/videos/{cat}", resource_type="video", tags=[cat, "live"])
                    
                    # Add to list with correct format for index.html
                    new_items.append({
                        "title": f"{cat} Live", 
                        "category": cat,
                        "src": res['secure_url'], 
                        "type": "video", 
                        "res": "1080p"
                    })
                except Exception as e:
                     print(f"      ❌ Cloudinary Upload Failed: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Error {cat}: {e}")
    return new_items

# --- MAIN TASK ---
if __name__ == "__main__":
    # 1. Run Downloads
    images = get_unsplash_images()
    videos = get_pixabay_videos()

    # 2. Save JSONs (This replaces generate_json.py)
    save_json("data/cloud_wallpapers.json", images, 200)
    save_json("data/videos.json", videos, 50)