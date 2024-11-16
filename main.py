from fastapi import FastAPI, File, UploadFile
from PIL import Image
import io
import asyncio
from utils.ObjectModel import detect
from utils.faceDetect import face_detection
from utils.metadata import read_data
from utils.qr_code import qr_checker
from utils.nsfw import nsfw_detect
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

def check_nsfw_from_llm(llm_result: dict) -> bool:
    """
    Determine if content is NSFW based on LLM response.
    """
    if not llm_result or not isinstance(llm_result, dict):
        return False

    # Get the reasons text and threat level
    reasons = ' '.join(llm_result.get('reasons', [])).lower()
    threat_level = llm_result.get('threat_level', '').upper()
    threat_score = llm_result.get('threat_score', 0)

    # Keywords that indicate NSFW content
    nsfw_keywords = [
        'sexually suggestive',
        'explicit',
        'inappropriate',
        'suggestive content',
        'adult content',
        'nudity',
        'sexual',
        'violence',
        'injury',
        'harm'
    ]

    # Check if any NSFW keywords are present and threat level is HIGH
    has_nsfw_keywords = any(keyword in reasons for keyword in nsfw_keywords)
    return has_nsfw_keywords and threat_level == 'HIGH' and threat_score >= 90

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
            nsfw_detect.read_nsfw(image),
            llm_response.llm_process(image)
        ]
        detected_objects, qr_details, metadata_details, face_details, _, llm_result = await asyncio.gather(*tasks)
        
        # nsfw_info

        if face_details:
            detected_objects = detected_objects or []
            detected_objects.append(face_details)        
       
        nsfw_status = check_nsfw_from_llm(llm_result)

        return {
            "detected_objects": detected_objects,                               
            "qr_details": qr_details,
            "metadata_details": metadata_details,
            "nsfw_detection" : nsfw_status,
            "llm_response": llm_result
        }

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/extension")
async def process_image(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Process tasks concurrently
        tasks = [
            detect.run_detection(image),
            qr_checker.process_qr_scan(image),
        ]
        detection_result, qr_details = await asyncio.gather(*tasks)
        print(detection_result)
        # Extract the detected objects list
        detected_objects = []
        detected_objects = [val["object"] for val in detection_result]
        # detection_result["detected_objects"]
        
        
        
        print(detected_objects)
        
        # Get list of detected object names
        # detected_object_names = [obj["object"] for obj in detected_objects]

        # Initialize vulnerability level
        vul = "Low"

        # Check for moderate vulnerabilities
        moderate_items = ["Car Plate Number", "Knife"]
        if any(item in detected_objects for item in moderate_items):
            vul = "Moderate"

        # Check for high vulnerabilities
        high_risk_items = ["Id Card", "Credit Card", "House Number Plate"]
        if any(item in detected_objects for item in high_risk_items):
            vul = "High"

        # Check for malicious QR
        if qr_details.get("is_malicious", False):
            vul = "High"

        return {"Vulnerable": vul}
    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}

    

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
