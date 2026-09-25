from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from PIL import Image
import io
import requests
import json
import torch
from transformers import CLIPModel, CLIPProcessor

app = FastAPI(title="Global Photo Search & JSON Extractor")

# Inserted API Keys
SERPAPI_KEY = "bc7fb45412b91e6f20fbf36b3d1426809de11d693248ab1bbd8b993fe5b84cb9"
IMGBB_API_KEY = "f62b430b8b0142157a28384bb4ed14f2"

print("Loading AI Model (OpenAI CLIP)... Please wait.")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("AI Model Loaded Successfully!")

def upload_image_to_cloud(image_bytes):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": IMGBB_API_KEY}
    files = {"image": image_bytes}
    response = requests.post(url, data=payload, files=files)
    res_json = response.json()
    if response.status_code == 200 and res_json.get("success"):
        return res_json["data"]["url"]
    else:
        raise Exception(f"ImgBB Upload Failed: {res_json.get('error', {}).get('message', 'Unknown Error')}")

def generate_image_vector_json(image):
    inputs = processor(images=image, return_tensors="pt")
    outputs = model.get_image_features(**inputs)
    feature_vector = outputs.detach().numpy().flatten().tolist()
    return {
        "vector_dimensions": len(feature_vector),
        "vector_sample_first_10": feature_vector[:10],
        "image_format": image.format,
        "image_resolution": f"{image.size[0]}x{image.size[1]}",
        "color_mode": image.mode
    }

def search_web_and_social_media(public_url):
    search_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_lens",
        "url": public_url,
        "api_key": SERPAPI_KEY
    }
    response = requests.get(search_url, params=params)
    data = response.json()
    results = []
    if "visual_matches" in data:
        for item in data["visual_matches"]:
            results.append({
                "title": item.get("title", "No Title"),
                "source_domain": item.get("source"),
                "found_url": item.get("link"),
                "thumbnail": item.get("thumbnail")
            })
    return results

@app.get("/", response_class=HTMLResponse)
async def serve_home_page():
    return """