import io
from PIL import Image
import requests
from config import config
import os
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def read_nsfw(image: Image.Image) -> bool:
    """
    Analyze image for NSFW content using Eden AI API.
    
    Args:
        image (PIL.Image.Image): The image to analyze
        
    Returns:
        bool: True if NSFW content detected, False otherwise
    """
    try:
        # Load API key
        api_key = config.EDENAI_API_KEY
        print("api key ", api_key)
        if not api_key:
            logger.error("EDENAI_API_KEY not found in configuration")
            return False

        headers = {"Authorization": f"Bearer {api_key}"}
        url = "https://api.edenai.run/v2/image/explicit_content"

        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Convert image to JPEG bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)

        files = {"file": ("image.jpg", buffer, "image/jpeg")}
        data = {"providers": "google"}

        # Make API request
        response = requests.post(url, data=data, files=files, headers=headers)

        result = json.loads(response.text)
        print("result", result)
        
        # if response.status_code == 200:
        #     result = response.json()
            
        #     # Extract and log NSFW likelihood
        #     nsfw_result = result.get("google", {}).get("nsfw_likelihood", "UNKNOWN")
        #     logger.info(f"NSFW likelihood: {nsfw_result}")
            
        #     # Check if content is NSFW
        #     return nsfw_result.lower() in ["very_likely", "likely"]
        # else:
        #     logger.error(f"API Error: Status {response.status_code} - {response.text}")
        #     return False

    except Exception as e:
        logger.error(f"NSFW detection error: {str(e)}")
        return False
    finally:
        if 'buffer' in locals():
            buffer.close()