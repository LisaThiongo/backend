
import os
from PIL import Image
import json
import logging
from anthropic import Anthropic
from typing import Dict, Optional, Any
import io
import base64

# Logging Configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Claude API Client Configuration
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

THREAT_PROMPT = """
Analyze this image and provide a security assessment. Return a JSON object with this exact structure: if the description is of sexually explicit content, or showing blood or any sort of violence or human injury, set nsfw_content to true
if the image is of a crime scene or shows a deceased individual, set the value of nsfw_content to true and do the same for any other images that you feel are NSFW.
{
    "threat_level": "HIGH/MODERATE/LOW",
    "reasons": [Provide a markdown-formatted paragraph explaining the reasons for the threat level. Use **bold** to emphasize important points and ensure clarity and readability for the assessment. Also tell threats of expose of location and phone model in metadata],
    "detected_elements": {
        "location_indicators": false,
        "weapons": {
            "guns": false,
            "knives": false
        },
        "sensitive_documents": {
            "credit_cards": false,
            "id_cards": false,
            "car_plates": false,
            "house_numbers": false
        },
        "substances": {
            "alcohol": false,
            "drugs": false,
            "cigarettes": false
        },
        "personal_identifiers": {
            "faces": false,
            "names": false
        },
        "nsfw_content": false
    }
}
"""

async def clean_json_text(text: str) -> Optional[str]:
    """Clean and format JSON text."""
    print("################### USING CLAUDE ################")
    try:
        logger.debug(f"Cleaning JSON text")
        
        # Find JSON content between outermost curly braces
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start == -1 or json_end == -1:
            logger.error("No JSON object found in text")
            return None
        
        json_text = text[json_start:json_end + 1]
        json_text = json_text.replace('\n', ' ').strip()
        
        # Validate JSON
        try:
            json.loads(json_text)
            return json_text
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON after cleaning: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error in clean_json_text: {str(e)}")
        return None

async def analyze_image(image: Image.Image) -> Optional[Dict[str, Any]]:
    """Analyze image with Claude model and enhanced error handling."""
    try:
        logger.info("Starting image analysis")

        # Convert image to base64
        with io.BytesIO() as bio:
            image.save(bio, format='PNG')
            image_bytes = bio.getvalue()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Call Claude API with image
        try:
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": THREAT_PROMPT
                            }
                        ]
                    }
                ]
            )

            logger.debug(f"Claude API Response: {response}")

            if not response or not response.content:
                logger.error("Empty response from Claude API")
                return None

            # Extract text from the response
            response_text = response.content[0].text
            logger.debug(f"Response text: {response_text}")

            # Clean and parse JSON
            cleaned_json = await clean_json_text(response_text)
            if not cleaned_json:
                logger.error("Failed to clean JSON response")
                return None

            data = json.loads(cleaned_json)
            
            # Calculate threat score
            if "detected_elements" in data:
                score = await calculate_threat_score(data["detected_elements"])
                data["threat_score"] = score

                # Update threat level based on score
                if score >= 90:
                    data["threat_level"] = "HIGH"
                elif score >= 70:
                    data["threat_level"] = "MODERATE"
                else:
                    data["threat_level"] = "LOW"

            return data

        except Exception as api_error:
            logger.error(f"Claude API error: {str(api_error)}")
            return None

    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        logger.error("Error traceback:", exc_info=True)
        return None

async def calculate_threat_score(detected_elements: Dict) -> int:
    """Calculate threat score based on detected elements."""
    try:
        score = 0
        
        if detected_elements.get("nsfw_content"):
            score = max(score, 95)
        if detected_elements.get("weapons", {}).get("guns"):
            score = max(score, 95)
        if any(detected_elements.get("sensitive_documents", {}).values()):
            score = max(score, 90)
        if any(detected_elements.get("substances", {}).values()):
            score = max(score, 85)
        if detected_elements.get("personal_identifiers", {}).get("faces"):
            score = max(score, 75)
        if detected_elements.get("location_indicators"):
            score = max(score, 70)
        if detected_elements.get("weapons", {}).get("knives"):
            score = max(score, 70)
            
        return score
        
    except Exception as e:
        logger.error(f"Error calculating threat score: {str(e)}")
        return 0

async def llm_process(image: Image.Image) -> Optional[Dict]:
    """Process image with LLM."""
    try:
        logger.info("Starting LLM process")
        
        # Ensure image is in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        llm_response = await analyze_image(image)
        if not llm_response:
            logger.error("No response from analyze_image")
            return None
            
        # Extract required fields
        result = {
            key: llm_response.get(key)
            for key in ["threat_level", "reasons", "threat_score", "detected_elements"]
        }
        
        logger.info("Successfully processed image")
        logger.debug(f"LLM Result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in LLM process: {str(e)}")
        logger.error("Error traceback:", exc_info=True)
        return None

# import os
# from PIL import Image
# import json
# import re
# import google.generativeai as genai
# from config import config
# import aiofiles
# import logging
# import asyncio
# from typing import Dict, Optional, Any
# from concurrent.futures import ThreadPoolExecutor
# import io

# # Logging Configuration
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Constants and Configuration
# TIMEOUT_SECONDS = 60

# # Model Configuration
# genai.configure(api_key=config.GOOGLE_API_KEY)
# model = genai.GenerativeModel(
#     model_name='gemini-1.5-pro',
#     generation_config={
#         'temperature': 0.1,
#         'max_output_tokens': 2048,
#         'top_p': 0.8,
#     }
# )

# THREAT_PROMPT = """
# Analyze this image and provide a security assessment. Return a JSON object with this exact structure: if the description is of sexually explicit content, violence or human injury, set nsfw_content to true
# {
#     "threat_level": "HIGH/MODERATE/LOW",
#     "reasons": [Provide a markdown-formatted paragraph explaining the reasons for the threat level. Use **bold** to emphasize important points and ensure clarity and readability for the assessment.],
#     "detected_elements": {
#         "location_indicators": false,
#         "weapons": {
#             "guns": false,
#             "knives": false
#         },
#         "sensitive_documents": {
#             "credit_cards": false,
#             "id_cards": false,
#             "car_plates": false,
#             "house_numbers": false
#         },
#         "substances": {
#             "alcohol": false,
#             "drugs": false,
#             "cigarettes": false
#         },
#         "personal_identifiers": {
#             "faces": false,
#             "names": false
#         },
#         "nsfw_content": false
#     }
# }
# """

# async def clean_json_text(text: str) -> Optional[str]:
#     """Clean and format JSON text."""
#     try:
#         logger.debug(f"Cleaning JSON text")
        
#         # Find JSON content between outermost curly braces
#         json_start = text.find('{')
#         json_end = text.rfind('}')
        
#         if json_start == -1 or json_end == -1:
#             logger.error("No JSON object found in text")
#             return None
        
#         json_text = text[json_start:json_end + 1]
        
#         # Basic cleanup
#         json_text = json_text.replace('\n', ' ').strip()
        
#         # Validate JSON
#         try:
#             json.loads(json_text)
#             return json_text
#         except json.JSONDecodeError as e:
#             logger.error(f"Invalid JSON after cleaning: {str(e)}")
#             return None
            
#     except Exception as e:
#         logger.error(f"Error in clean_json_text: {str(e)}")
#         return None

# async def analyze_image(image: Image.Image) -> Optional[Dict[str, Any]]:
#     """Analyze image with enhanced error handling."""
#     try:
#         logger.info("Starting image analysis")
        
#         # Convert image to bytes if needed
#         if isinstance(image, Image.Image):
#             with io.BytesIO() as bio:
#                 image.save(bio, format='PNG')
#                 image_bytes = bio.getvalue()
        
#         # Generate content
#         logger.debug("Calling Gemini API")
#         threat_response = await asyncio.to_thread(
#             model.generate_content, [THREAT_PROMPT, image]
#         )
        
#         if not threat_response or not threat_response.candidates:
#             logger.error("No response from Gemini API")
#             return None
            
#         # Extract text
#         threat_text = threat_response.candidates[0].content.parts[0].text
#         logger.debug(f"Received response from API")
        
#         # Clean JSON
#         cleaned_json = await clean_json_text(threat_text)
#         if not cleaned_json:
#             logger.error("Failed to clean JSON response")
#             return None
            
#         # Parse JSON
#         try:
#             data = json.loads(cleaned_json)
#         except json.JSONDecodeError as e:
#             logger.error(f"Failed to parse JSON: {str(e)}")
#             return None
            
#         # Calculate threat score
#         if "detected_elements" in data:
#             score = await calculate_threat_score(data["detected_elements"])
#             data["threat_score"] = score
            
#             # Update threat level
#             if score >= 90:
#                 data["threat_level"] = "HIGH"
#             elif score >= 70:
#                 data["threat_level"] = "MODERATE"
#             else:
#                 data["threat_level"] = "LOW"
        
#         return data
        
#     except Exception as e:
#         logger.error(f"Error in analyze_image: {str(e)}")
#         logger.error(f"Error traceback:", exc_info=True)
#         return None

# async def calculate_threat_score(detected_elements: Dict) -> int:
#     """Calculate threat score."""
#     try:
#         score = 0
        
#         if detected_elements.get("nsfw_content"):
#             score = max(score, 95)
#         if detected_elements.get("weapons", {}).get("guns"):
#             score = max(score, 95)
#         if any(detected_elements.get("sensitive_documents", {}).values()):
#             score = max(score, 90)
#         if any(detected_elements.get("substances", {}).values()):
#             score = max(score, 85)
#         if detected_elements.get("personal_identifiers", {}).get("faces"):
#             score = max(score, 75)
#         if detected_elements.get("location_indicators"):
#             score = max(score, 70)
#         if detected_elements.get("weapons", {}).get("knives"):
#             score = max(score, 70)
            
#         return score
        
#     except Exception as e:
#         logger.error(f"Error calculating threat score: {str(e)}")
#         return 0

# async def llm_process(image: Image.Image) -> Optional[Dict]:
#     """Process image with LLM."""
#     try:
#         logger.info("Starting LLM process")
        
#         llm_response = await analyze_image(image)
#         if not llm_response:
#             logger.error("No response from analyze_image")
#             return None
            
#         # Extract required fields
#         result = {
#             key: llm_response.get(key)
#             for key in ["threat_level", "reasons", "threat_score"]
#         }
        
#         logger.info("Successfully processed image")
#         return result
        
#     except Exception as e:
#         logger.error(f"Error in LLM process: {str(e)}")
#         logger.error(f"Error traceback:", exc_info=True)
#         return None