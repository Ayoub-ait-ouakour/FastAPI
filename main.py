from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import sys
import os
import uvicorn
import base64


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import get_video, save_picture, get_picture, get_saved_video, list_saved_videos, list_saved_images, get_video_from_script

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Predefined bearer token (replace with your actual token or fetch from environment variables)
BEARER_TOKEN = """L@9#5q-6ZfC]T"fQ+9qqyG7pqoFmGw;"fPxIZkF]|-mhF:by.VjP)Rtx'zaM[iK"""  # You can also use os.environ.get("BEARER_TOKEN")

# Dependency to validate the bearer token
async def token_required(request: Request):
    """
    Validates the bearer token provided in the Authorization header.
    """
    token = None
    if "Authorization" in request.headers:
        try:
            auth = request.headers["Authorization"]
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            if token != BEARER_TOKEN:
                raise HTTPException(status_code=401, detail="Invalid token")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header")
    else:
        raise HTTPException(status_code=401, detail="Token is missing")
    return token

@app.post("/upload-image/")
async def upload_image(
    file: UploadFile = File(...),
    token: str = Depends(token_required)  # Require token validation
):
    try:
        contents = await file.read()
        save_picture(contents)
        return {"message": "Image uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-image/{picture_id}")
async def get_image(
    picture_id: int,
    token: str = Depends(token_required)  # Require token validation
):
    image_data = get_picture(picture_id)
    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")
    return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")

@app.post("/generate-video/")
async def generate_video(
    picture_id: int = Query(...),
    audio_file: UploadFile = File(...),
    token: str = Depends(token_required)  # Require token validation
):
    try:
        image_data = get_picture(picture_id)
        if not image_data:
            raise HTTPException(status_code=404, detail="Image not found")

        audio_contents = await audio_file.read()
        video_data = get_video(image_data, audio_contents)

        return StreamingResponse(io.BytesIO(video_data), media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-video-from-script/")
async def generate_video_from_script(
    picture_id: int = Query(...),
    script_text: str = Query(...),
    token: str = Depends(token_required)  # Require token validation
):
    try:
        if picture_id is None or script_text is None:
            raise HTTPException(status_code=400, detail="picture_id and script are required")

        image_data = get_picture(picture_id)
        if not image_data:
            raise HTTPException(status_code=404, detail="Image not found")

        video_data = get_video_from_script(image_data, script_text)
        return StreamingResponse(io.BytesIO(video_data), media_type="video/mp4")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-video/{video_id}")
async def get_video_endpoint(
    video_id: int,
    token: str = Depends(token_required)  # Require token validation
):
    try:
        video_data = get_saved_video(video_id)
        if not video_data:
            raise HTTPException(status_code=404, detail="Video not found")
        return StreamingResponse(io.BytesIO(video_data), media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-videos/")
async def list_videos(
    token: str = Depends(token_required)  # Require token validation
):
    """
    List all saved videos.
    """
    try:
        video_list = list_saved_videos()
        # Ensure the data is JSON serializable
        serializable_video_list = [{"id": video[0], "data": base64.b64encode(video[1]).decode("utf-8")} for video in video_list]
        return JSONResponse(content=serializable_video_list)
    except Exception as e:
        print("Error", e)
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/list-images/")
async def list_images(
    token: str = Depends(token_required)  # Require token validation
):
    """
    List all saved images.
    """
    try:
        image_list = list_saved_images()
        # Ensure the data is JSON serializable
        serializable_image_list = [{"id": image[0], "data": image[1]} for image in image_list]
        return JSONResponse(content=serializable_image_list)
    except Exception as e:
        print("Error", e)
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)