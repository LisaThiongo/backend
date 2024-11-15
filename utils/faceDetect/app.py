from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
import os
from io import BytesIO
from face_detection import process_image  # Import the process_image function from the above script

app = FastAPI()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Call the function to process the uploaded image
        result = process_image(file)

        # Return the response containing the paths of the processed image and faces data
        return JSONResponse(content={
            "faces_detected": result["faces_detected"],
            "faces_data": result["faces_data"]
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
