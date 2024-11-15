from .config import genai_config
import PIL.Image
import requests
import json
from dotenv import load_dotenv
import os
from fastapi import APIRouter, UploadFile

router = APIRouter()


def summarize():
    print("Inside summarize")
    model = genai_config()

    pumpkin = PIL.Image.open("./lib/gun.jpg")
    response = model.generate_content(["""
                                      Evaluate the uploaded image in detail, identifying and classifying objects, text, and other visible elements. Based on the content detected, assign appropriate safety ratings across various categories as described below. For each detected item, provide a reason for the assigned classification. The specific rules for categorization are as follows:
1. Dangerous Content

    If the image contains weapons (e.g., guns, knives, explosives) or any item capable of causing harm to plants, animals, or humans:
        Assign HARM_CATEGORY_DANGEROUS_CONTENT with a HIGH probability.
        Include all firearms, bladed weapons, and improvised weapons.
    If the image contains alcohol, cigarettes, or drugs:
        Assign HARM_CATEGORY_DANGEROUS_CONTENT with a HIGH probability.
    If the image contains vehicles being operated recklessly or hazardous objects, evaluate appropriately and add them to this category if deemed a threat.

2. Privacy Concerns

    If the image contains credit card details, banking information, or house number plates:
        Assign HARM_CATEGORY_PRIVACY with a HIGH probability.
        Include explicit details on what sensitive information was detected and why it qualifies.
    For car license plates, QR codes, or any identifiable digital codes:
        Assign HARM_CATEGORY_PRIVACY with a MEDIUM-HIGH probability.
    For any face or biometric data (e.g., iris scans, fingerprints):
        Assign HARM_CATEGORY_PRIVACY with a MEDIUM-HIGH probability.

3. Other Relevant Fields

    If the image includes content related to self-harm, violence, or explicit material:
        Create and assign a custom field, such as HARM_CATEGORY_SELF_HARM or HARM_CATEGORY_VIOLENCE, with a probability relevant to the content.
    If the image contains symbols or text promoting hate speech, propaganda, or other harmful ideologies:
        Assign HARM_CATEGORY_HATE_SPEECH with a suitable probability.

4. General Rules

    Analyze the image exhaustively for potential harm, privacy risks, or inappropriate content.
    If new, uncategorized items of concern are detected (e.g., child endangerment or unsafe practices), create relevant fields dynamically and classify accordingly.
    For each detected element, include in the output:
        The item identified.
        The category assigned.
        The probability level (e.g., HIGH, MEDIUM-HIGH, LOW, or NEGLIGIBLE).
        A brief explanation for the decision.

Example Output Format:

For each harmful or sensitive content identified, generate output like the following:

    Item Detected: Pistol
        Category: HARM_CATEGORY_DANGEROUS_CONTENT
        Probability: HIGH
        Reason: The item is a firearm capable of causing harm.

    Item Detected: Credit Card Information
        Category: HARM_CATEGORY_PRIVACY
        Probability: HIGH
        Reason: The image contains sensitive financial details that could lead to fraud.

    Item Detected: QR Code
        Category: HARM_CATEGORY_PRIVACY
        Probability: MEDIUM-HIGH
        Reason: The QR code could contain personally identifiable or sensitive information.

Final Notes:

    Be consistent in assigning probabilities based on the nature of the detected items.
    Consider both explicit and implicit risks when evaluating the image.
    Provide detailed reasoning for every classification to ensure transparency and understanding.
                                      """, pumpkin])
    
    print("\nResponse: ", response)
   
async def read_nsfw():
    print("Inside Read NSFW")
    load_dotenv();
    edenai_api_key = os.getenv("EDENAI_API_KEY")
    headers = {"Authorization" : f"Bearer {edenai_api_key}"}
    url = "https://api.edenai.run/v2/image/explicit_content"
    data = {"providers" : "google"}
    files = {'file' : open("./lib/lor.jpg", 'rb')}

    response = requests.post(url, data=data, files=files, headers=headers)

    result = json.loads(response.text)
    print("Result: ", result)
    return result
    

@router.get("/test_nsfw")
async def test_nsfw():
    nsfw = await read_nsfw();
    return nsfw
    
@router.post("/upload_file")
async def upload_image(file: UploadFile):
    return {"filename" : file.filename}
