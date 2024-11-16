from fastapi import FastAPI, File, UploadFile
from PIL import Image
import io
import asyncio
from utils.ObjectModel import detect
from utils.faceDetect import face_detection
from utils.metadata import read_data
from utils.qr_code import qr_checker
from utils.genai_llm import llm_response
from config import config
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",      
    "http://localhost:8000",      
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",

] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],          
    allow_headers=["*"],        
)

@app.post("/api")
async def process_image(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Process tasks concurrently
        tasks = [
            detect.run_detection(image),
            qr_checker.process_qr_scan(image),
            read_data.extract_sensitive_metadata(image),
            face_detection.process_image(image),
            llm_response.llm_process(image)
        ]
        detected_objects, qr_details, metadata_details, face_details, llm_result = await asyncio.gather(*tasks)
        
        detected_objects.append(face_details)
       
        return {
            "detected_objects": detected_objects,                               
            "qr_details": qr_details,
            "metadata_details": metadata_details,
            "llm_response": llm_result,
            
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Increase worker count for concurrency
    uvicorn.run("main:app", host="0.0.0.0", port=8000)








# from fastapi import FastAPI, File, UploadFile
# from PIL import Image
# import io
# from utils.ObjectModel import detect
# from utils.faceDetect import face_detection
# # from utils.genai_llm import detect
# from utils.metadata import read_data 
# from utils.qr_code import qr_checker 
# from config import config
# import asyncio

# app = FastAPI()

# @app.post("/api")
# async def process_image(file: UploadFile = File(...)):
#     try:
#         # Read the uploaded image
#         image_bytes = await file.read()
#         image = Image.open(io.BytesIO(image_bytes))

#         # Run object detection concurrently
#         detected_objects, gemini_detected_objects, qr_details,metadata_details, face_details  = await asyncio.gather(
#             detect.run_detection(image),
#              detect.run_detection(image),
#             qr_checker.process_qr_scan(image),
#             read_data.extract_sensitive_metadata(image),
#             face_detection.process_image(image)
           
#         )
        
#         # detected_objects =  await  detect.run_detection(image)
        
#         # # face_details,
#         # # Process additional details concurrently
#         # qr_details, metadata_details = await asyncio.gather(
#         #     # face_detection.process_image(image, gemini_detected_objects),
#         #     qr_checker.process_qr_scan(image),
#         #     read_data.extract_sensitive_metadata(image)
#         # )
        
#         # qr_details = await qr_checker.process_qr_scan(image)
#         # metadata_details  = await read_data.extract_sensitive_metadata(image)
#         # face_details = await face_detection.process_image(image)

#         # # Process LLM
#         # llm_result = await process_by_llm([face_details, qr_details, metadata_details])

#         return {
#     "detection objects": detected_objects,
#     "qr_details": qr_details,
#     "metadata_details": metadata_details,
#     "face_details": face_details
# }

#     # [ qr_details,

#     except Exception as e:
#         return {"error": str(e)}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
    
    

# #    # Process QR code
# #         qr_object = next((obj for obj in gemini_detected_objects if obj["class"] == "QR Scan"), None)
# #         if qr_object:
# #             result = await process_qr(image)
# #             results.append(result)
# #         else:
# #             results.append({"message": "No QR Scan object detected"})



# #         # Process face detection
# #         face_object = next((obj for obj in gemini_detected_objects if obj["class"] == "Face"), None)
# #         if face_object:
# #             result = await process_face(image)
# #             results.append(result)
# #         else:
# #             results.append({"message": "No Face object detected"})
