from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import os
import uuid
import tempfile
import zipfile
import shutil
import subprocess
import numpy as np
import cv2
from PIL import Image

app = FastAPI()

# CORS設定（フロントとAPI接続できるように）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/merge")
async def merge(
    videos: List[UploadFile] = File(...),
    images: List[UploadFile] = File(...)
    print("動画ファイル数:", len(videos))
    print("画像ファイル数:", len(images))
    print("保存完了:", video_paths, image_paths)
):
    temp_dir = tempfile.mkdtemp()
    output_files = []

    def detect_transparent_area(image_path):
        with Image.open(image_path) as img:
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img_np = np.array(img)
            alpha = img_np[:, :, 3]
            mask = (alpha == 0).astype(np.uint8) * 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None
            x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
            return x, y, w, h

    def overlay_ffmpeg(video_path, image_path, x, y, w, h, output_path):
        scaled_video = os.path.join(temp_dir, f"scaled_{uuid.uuid4()}.mp4")
        scale_cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"scale={w}:{h}", "-an", scaled_video
        ]
        subprocess.run(scale_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        overlay_cmd = [
            "ffmpeg", "-y", "-i", image_path, "-i", scaled_video,
            "-filter_complex", f"[0][1]overlay={x}:{y}",
            "-c:a", "copy", output_path
        ]
        subprocess.run(overlay_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for video in videos:
        video_path = os.path.join(temp_dir, f"video_{uuid.uuid4()}.mp4")
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        for image in images:
            image_path = os.path.join(temp_dir, f"image_{uuid.uuid4()}.png")
            with open(image_path, "wb") as f:
                shutil.copyfileobj(image.file, f)

            coords = detect_transparent_area(image_path)
            if not coords:
                continue

            x, y, w, h = coords
            out_path = os.path.join(temp_dir, f"merged_{uuid.uuid4()}.mp4")
            overlay_ffmpeg(video_path, image_path, x, y, w, h, out_path)
            output_files.append(out_path)

    zip_path = os.path.join(temp_dir, "merged.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_path in output_files:
            zipf.write(file_path, arcname=os.path.basename(file_path))

    def stream():
        with open(zip_path, "rb") as f:
            yield from f

    return StreamingResponse(stream(), media_type="application/zip")
