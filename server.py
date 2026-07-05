from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import traceback

from src.analyzer.dl_scorer import analyze_dl_quality

app = FastAPI(title="AI Image Analyzer DL API")

@app.post("/analyze/dl")
async def analyze_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            return JSONResponse(status_code=400, content={"error": "Invalid image file or format not supported."})
            
        result = analyze_dl_quality(img_bgr)
        # return dict, FastAPI will automatically serialize to JSON
        return result
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        return JSONResponse(status_code=500, content={"error": error_msg})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
