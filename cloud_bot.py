import cloudinary
import cloudinary.uploader
import requests
import os
import json
import random

# --- CONFIGURATION ---
CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract"]

# Cloudinary Setup
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- 1. DOWNLOAD IMAGES (UNSPLASH) ---
def get_unsplash_images():
    print("📸 Starting Image Search (Unsplash)...")
    new_items = []
    
    api_key = os.environ.get('UNSPLASH_ACCESS_KEY')
    if not api_key:
        print("⚠️ No Unsplash Key found.")
        return []

    for cat in CATEGORIES:
        try:
            url = "https://api.unsplash.com/photos/random"
            params = {
                "query": f"{cat} dark wallpaper",
                "count": 1, 
                "orientation": "portrait",
                "client_id": api_key
            }
            
            data = requests.get(url, params=params).json()
            
            # Error check
            if isinstance(data, dict) and "errors" in data:
                print(f"   ⚠️ Unsplash Error: {data['errors']}")
                continue
                
            # If data is a list (success)
            for item in data:
                img_url = item['urls']['regular']
                img_id = item['id']
                
                print(f"   🚀 Uploading Image: {cat} {img_id}")
                
                upload_res = cloudinary.uploader.upload(
                    img_url, 
                    folder=f"neonpixel/{cat}", 
                    public_id=f"{cat}_{img_id}",
                    tags=[cat, "wallpaper"]
                )
                
                new_items.append({
                    "title": f"{cat} Wallpaper",
                    "category": cat,
                    "src": upload_res['secure_url'],
                    "type": "image",
                    "res": "4K"
                })

        except Exception as e:
            print(f"   ❌ Image Error ({cat}): {e}")
            
    return new_items

# --- 2. DOWNLOAD VIDEOS (PIXABAY) ---
def get_pixabay_videos():
    print("🎥 Starting Video Search (Pixabay)...")
    new_items = []
    
    api_key = os.environ.get('PIXABAY_API_KEY')
    if not api_key:
        print("⚠️ No Pixabay Key found.")
        return []

    for cat in CATEGORIES:
        try:
            url = "https://pixabay.com/api/videos/"
            params = {
                "key": api_key,
                "q": f"{cat} vertical loop",
                "per_page": 3,
                "video_type": "all"
            }
            
            data = requests.get(url, params=params).json()
            
            if "hits" in data and len(data["hits"]) > 0:
                vid = random.choice(data["hits"])
                # Pixabay has different sizes. 'medium' or 'small' is best for web.
                vid_url = vid["videos"]["medium"]["url"]
                vid_id = vid["id"]

                print(f"   🚀 Uploading Video: {cat} {vid_id}")
                
                upload_res = cloudinary.uploader.upload(
                    vid_url, 
                    folder=f"neonpixel/videos/{cat}", 
                    public_id=f"live_{cat}_{vid_id}",
                    resource_type="video",
                    tags=[cat, "live"]
                )
                
                new_items.append({
                    "title": f"{cat} Live",
                    "category": cat,
                    "path": upload_res['secure_url'],
                    "type": "video",
                    "res": "1080p"
                })
        except Exception as e:
            print(f"   ❌ Video Error ({cat}): {e}")
            
    return new_items

# --- MAIN TASK ---
def run_bot():
    # 1. Get New Content
    images = get_unsplash_images()
    videos = get_pixabay_videos()

    # 2. Update Wallpapers JSON
    if images:
        f_path = "data/cloud_wallpapers.json"
        existing = []
        if os.path.exists(f_path):
            try: existing = json.load(open(f_path))
            except: pass
        
        final_img = images + existing
        os.makedirs("data", exist_ok=True)
        json.dump(final_img[:100], open(f_path, "w"), indent=4)
        print(f"✅ Saved {len(images)} new images.")

    # 3. Update Videos JSON
    if videos:
        f_path = "data/videos.json"
        existing = []
        if os.path.exists(f_path):
            try: existing = json.load(open(f_path))
            except: pass
            
        final_vid = videos + existing
        os.makedirs("data", exist_ok=True)
        json.dump(final_vid[:50], open(f_path, "w"), indent=4)
        print(f"✅ Saved {len(videos)} new videos.")

if __name__ == "__main__":
    run_bot()