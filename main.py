from fastapi import FastAPI, File, UploadFile
from PIL import Image
import io
import asyncio
import os
#import OpenAI 
import openai 


from utils.ObjectModel import detect
from utils.faceDetect import face_detection
from utils.metadata import read_data
from utils.qr_code import qr_checker
from utils.nsfw import nsfw_detect
from utils.genai_llm import llm_response
from config import config
from fastapi.middleware.cors import CORSMiddleware

#import Key 
open.api_key = os.getenv("OPENAI_API_KEY")
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

	#Determine if content is NSFW based on LLM response.

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
        'harm',
        'deceased',
        'blood',
        'death',
        'killed',
        'gunshot',
        
    ]

    # Check if any NSFW keywords are present and threat level is HIGH
    has_nsfw_keywords = any(keyword in reasons for keyword in nsfw_keywords)
    return has_nsfw_keywords and threat_level == 'HIGH' 


#Add the LLM API Route

# Load your OpenAI API key securely (store in an env variable or config)
openai.api_key = "your_openai_api_key_here"

@app.post("/llm")
async def llm_endpoint(prompt: str):

#Sends user input to OpenAI's LLM (GPT-4) and returns the response.

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI assistant."},
                      {"role": "user", "content": prompt}]
        )
        return {"llm_response": response["choices"][0]["message"]["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
		
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
        # Read image from uploaded file
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Run object and QR detection concurrently
        detection_result, qr_details = await asyncio.gather(
            detect.run_detection(image),
            qr_checker.process_qr_scan(image),
        )

        detected_objects = [val["object"] for val in detection_result]
        vul = "Low"

        moderate_items = ["Car Plate Number", "Knife"]
        high_risk_items = ["Id Card", "Credit Card", "House Number Plate"]

        if any(item in detected_objects for item in moderate_items):
            vul = "Moderate"
        if any(item in detected_objects for item in high_risk_items):
            vul = "High"
        if qr_details.get("is_malicious", False):
            vul = "High"

        return {"Vulnerable": vul}

    try:
        # Read image from uploaded file
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Run object and QR detection concurrently
        detection_result, qr_details = await asyncio.gather(
            detect.run_detection(image),
            qr_checker.process_qr_scan(image),
        )

        detected_objects = [val["object"] for val in detection_result]
        vul = "Low"

        moderate_items = ["Car Plate Number", "Knife"]
        high_risk_items = ["Id Card", "Credit Card", "House Number Plate"]

        if any(item in detected_objects for item in moderate_items):
            vul = "Moderate"
        if any(item in detected_objects for item in high_risk_items):
            vul = "High"
        if qr_details.get("is_malicious", False):
            vul = "High"

        return {"Vulnerable": vul}

    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}
    
	
@app.post("/process_qr_with_gpt")	
async def process_qr_with_gpt(file: UploadFile = File(...)):

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Run QR detection
        qr_details = await qr_checker.process_qr_scan(image)

        # Check if QR code contains data
        if qr_details.get("qr_data"):
            qr_data = qr_details["qr_data"]
            
            # Now analyze the QR code data with GPT-4
            prompt = f"Analyze the following QR code content and determine if it is potentially malicious or a phishing attempt: {qr_data}"
            gpt_response = await llm_response.llm_process(prompt)  # Pass the QR code content to GPT-4
            
            # You could look for certain red flags in the GPT-4 response, such as suspicious terms, phishing indicators, etc.
            if 'phishing' in gpt_response.lower() or 'malicious' in gpt_response.lower():
                qr_details["is_malicious"] = True
            else:
                qr_details["is_malicious"] = False

            return {"qr_details": qr_details, "gpt_analysis": gpt_response}

        return {"message": "No QR code detected."}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    # Increase worker count for concurrency
    uvicorn.run("main:app", host="0.0.0.0", port=8000)







