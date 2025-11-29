import requests
import os
import json
import random
import time
from duckduckgo_search import DDGS
import yt_dlp

# --- CONFIGURATION ---
CATEGORIES = ["Anime", "Cars", "Nature", "Gaming", "Cyberpunk", "Abstract", "Technology"]
# This file handles a single run (1 image + 1 video)
# The YAML workflow will call this script 10 times.

# --- HELPER: SAVE JSON LOCALLY ---
def save_json_local(filepath, item, limit=500):
    os.makedirs("data", exist_ok=True)
    existing_data = []
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f: 
                existing_data = json.load(f)
        except: existing_data = []

    if item:
        # Prepend new item, keep latest 
        final_list = [item] + existing_data
        final_list = final_list[:limit]
        
        with open(filepath, "w") as f: 
            json.dump(final_list, f, indent=4)
        print(f"✅ Saved 1 new item to {filepath}")
    elif not os.path.exists(filepath):
        # Ensure file exists even if no data
        with open(filepath, "w") as f: json.dump([], f)

# --- INTELLIGENT TAGGER FUNCTION ---
def detect_subcategory(main_cat, text_to_scan):
    # (Keywords removed for brevity, assuming they are defined here)
    SUB_KEYWORDS = { "Anime": ["Naruto", "One Piece"], "Cars": ["JDM", "BMW"], "Nature": ["Forest"], "Gaming": ["Valorant"], "Cyberpunk": ["Neon"], "Abstract": ["Fluid"], "Technology": ["Code"] }
    text = text_to_scan.lower()
    if main_cat in SUB_KEYWORDS:
        for keyword in SUB_KEYWORDS[main_cat]:
            if keyword.lower() in text: return keyword 
    return "General"

# --- 1. WALLHAVEN (Image Download to Repo) ---
def download_wallhaven_image():
    api_key = os.environ.get('WALLHAVEN_API_KEY')
    new_item = None
    cat = random.choice(CATEGORIES)
    device = random.choice(["mobile", "desktop"])
    ratio = "9x16" if device == "mobile" else "16x9"
    
    print(f"🐉 Fetching Image: {cat} ({device})...")
    
    try:
        url = "https://wallhaven.cc/api/v1/search"
        params = {"q": cat, "purity": "100", "sorting": "random", "ratios": ratio, "apikey": api_key}
        HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        resp = requests.get(url, params=params, headers=HEADERS).json()
        
        if "data" in resp and resp["data"]:
            img_data = resp["data"][0]
            img_url = img_data["path"]
            
            # Subcategory tagging
            tags_list = [t['name'] for t in img_data.get('tags', [])]
            sub_cat = detect_subcategory(cat, " ".join(tags_list))
            
            # --- SAVE LOCALLY TO REPO ---
            os.makedirs(f"wallpapers/{device}/{cat}", exist_ok=True)
            filename = f"wallpapers/{device}/{cat}/{img_data['id']}.jpg"
            
            img_content = requests.get(img_url, headers=HEADERS).content
            with open(filename, "wb") as f: f.write(img_content)
            
            new_item = {
                "title": f"{sub_cat} Wallpaper", 
                "category": cat,
                "subcategory": sub_cat,
                "device": device, 
                "src": filename, # <-- RELATIVE PATH
                "type": "image", 
                "res": "4K"
            }
    except Exception as e: print(f"Error: {e}")
    return new_item

# --- 2. PINTEREST VIDEO (Download to Repo) ---
def download_pinterest_video():
    print("📌 Hunting Video...")
    new_item = None
    ddgs = DDGS()
    
    # We must save to the repo now
    temp_filename = "videos/temp_vid.mp4" 
    os.makedirs("videos", exist_ok=True)

    ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': temp_filename, 'quiet': True}
    cat = random.choice(CATEGORIES)
    
    try:
        query = f"site:pinterest.com/pin/ {cat} aesthetic video vertical"
        results = list(ddgs.text(query, max_results=1))
        
        if results:
            vid_url = results[0]['href']
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.extract_info(vid_url, download=True)
            
            if os.path.exists(temp_filename):
                title = os.path.basename(temp_filename) # Filename is unique enough
                sub_cat = detect_subcategory(cat, title)
                
                # We need a new name to move the file after download
                final_name = f"videos/{cat}_{os.path.basename(title)}.mp4"
                os.rename(temp_filename, final_name)
                
                new_item = {
                    "title": f"{sub_cat} Live", 
                    "category": cat, 
                    "subcategory": sub_cat,
                    "device": "mobile", 
                    "src": final_name, # <-- RELATIVE PATH
                    "type": "video", 
                    "res": "HD"
                }
    except: pass
    return new_item

# --- MAIN TASK (Single Run) ---
if __name__ == "__main__":
    # 1. Download 1 Image
    img_item = download_wallhaven_image()
    if img_item:
        save_json_local("data/cloud_wallpapers.json", img_item, 500)
    
    # 2. Download 1 Video
    video_item = download_pinterest_video()
    if video_item:
        save_json_local("data/videos.json", video_item, 100)