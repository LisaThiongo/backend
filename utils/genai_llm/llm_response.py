import os
from PIL import Image
import json
import re
import google.generativeai as genai
from config import config
import aiofiles

genai.configure(api_key=config.GOOGLE_API_KEY)

# Initialize the model
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={
        'temperature': 0.1,
    }
)

async def clean_json_text(text):
    try:
        # Find JSON-like content between curly braces
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            return None
        
        json_text = text[start:end + 1]
        
        # Convert paragraph-style text in arrays to proper JSON format
        def fix_array_text(match):
            content = match.group(1)
            # Split by newlines and create proper JSON array
            items = [item.strip() for item in content.split('\\n') if item.strip()]
            # Escape quotes and join with commas
            formatted_items = ['"{}"'.format(item.replace('"', '\\"')) for item in items]
            return '[' + ','.join(formatted_items) + ']'
        
        # Fix arrays containing newline-separated text
        json_text = re.sub(r'\[\s*"([^"]+)"\s*\]', fix_array_text, json_text)
        
        # Clean up any remaining issues
        json_text = json_text.replace('\n', ' ')
        json_text = json_text.strip()
        
        return json_text
        
    except Exception as e:
        print(f"Error cleaning JSON text: {str(e)}")
        print("Problematic JSON text:")
        print(json_text)
        return None

async def calculate_threat_score(detected_elements):
    """Calculate a threat score based on the detected elements."""
    score = 0

    # Scoring based on the specified criteria
    if detected_elements.get("nsfw_content", False) or detected_elements.get("weapons", {}).get("guns", False):
        return 95  # NSFW content or guns detected

    if any(detected_elements.get("sensitive_documents", {}).values()):
        return 90  # Sensitive documents detected

    if any(detected_elements.get("substances", {}).values()):
        return 85  # Substances like alcohol, drugs, or cigarettes detected

    if detected_elements.get("personal_identifiers", {}).get("faces", False):
        return 75  # Faces detected

    if detected_elements.get("location_indicators", False) or detected_elements.get("weapons", {}).get("knives", False):
        return 70  # Location indicators or knives detected

    return score

async def analyze_image(image: Image):
    # Prompt for threat analysis
    threat_prompt = """
    Analyze the image for security threats. Return a JSON object containing only these fields:
    {
        "threat_level": "HIGH/MODERATE/LOW",
        "reasons": ["reasons in paragraph form, in a readable format in bullet points seperated by new line"],
        "detected_elements": {
            "location_indicators": false,
            "weapons": {"guns": false, "knives": false},
            "sensitive_documents": {"credit_cards": false, "id_cards": false, "car_plates": true, "house_numbers": false},
            "substances": {"alcohol": false, "drugs": false, "cigarettes": true},
            "personal_identifiers": {"faces": true, "names": false},
            "nsfw_content": false
        },
        "high_risk_elements": ["element1"],
        "moderate_risk_elements": ["element1"],
        "recommendations": ["rec1", "rec2"]
    }
    """
    
    try:
        # Generate threat analysis
        threat_response = model.generate_content([threat_prompt, image])
        
        # Extract content from the model response
        threat_text = threat_response.candidates[0].content.parts[0].text
        
        cleaned_json = await clean_json_text(threat_text)
        print("after cleaning json ##################")
        print(cleaned_json)
        if not cleaned_json:
            raise ValueError("Failed to clean JSON text")
        
        # Parse the cleaned JSON
        data = json.loads(cleaned_json)
        print("after parsing cleaned")

        # Calculate and add threat score
        detected_elements = data.get("detected_elements", {})
        score = await calculate_threat_score(detected_elements)
        
        # Add the score to the response data
        data["threat_score"] = score
        
        # Update threat level based on score if not already set
        if score >= 90:
            data["threat_level"] = "HIGH"
        elif score >= 70:
            data["threat_level"] = "MODERATE"
        else:
            data["threat_level"] = "LOW"
    
        return data
    
    except Exception as e:
        print(f"Error processing threat analysis: {e}")
        if 'threat_text' in locals():
            print("\nRaw response text:")
            print(threat_text)
        return None

async def llm_process(image: Image):
    llm_response = await analyze_image(image)
    return { 
        key: llm_response.get(key) for key in [
            "threat_level", "reasons", "threat_score"
        ]
    } if llm_response else None