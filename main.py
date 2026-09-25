from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from PIL import Image
import io
import requests

app = FastAPI(
    title="Global AI Photo Matcher",
    description="Upload an image to extract metadata and search across the web/social media."
)

SERPAPI_KEY = "bc7fb45412b91e6f20fbf36b3d1426809de11d693248ab1bbd8b993fe5b84cb9"
IMGBB_API_KEY = "f62b430b8b0142157a28384bb4ed14f2"

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

def extract_image_metadata(image):
    return {
        "format": image.format,
        "width": image.size[0],
        "height": image.size[1],
        "mode": image.mode
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

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.post("/analyze-and-search")
async def analyze_and_search_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        metadata = extract_image_metadata(image)
        public_url = upload_image_to_cloud(image_bytes)
        matched_locations = search_web_and_social_media(public_url)
        return {
            "status": "success",
            "uploaded_filename": file.filename,
            "public_hosted_url": public_url,
            "image_metadata_json": metadata,
            "total_matches_found": len(matched_locations),
            "found_locations": matched_locations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
