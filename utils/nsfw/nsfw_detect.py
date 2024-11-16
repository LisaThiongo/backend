import io
from PIL import Image
import requests
from config import config

async def read_nsfw(image: Image):
    try:
        headers = {"Authorization": f"Bearer {config.EDENAI_API_KEY}"}
        url = "https://api.edenai.run/v2/image/explicit_content"

        if image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            # Composite the image on the background using alpha channel
            background.paste(image, mask=image.split()[3])
            image = background
    
        # Save to buffer
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)

        files = {"file": buffer}
        data = {"providers": "google"}

        # Send the POST request
        response = requests.post(url, data=data, files=files, headers=headers)

        if response.status_code == 200:
            result = response.json()
            # Extract NSFW information
            nsfw_result = result.get("google", {}).get("nsfw_likelihood", "UNKNOWN")
            if nsfw_result and nsfw_result.lower() in ["very_likely", "likely"]:
                return True  # NSFW detected
            return False  # Not NSFW
        else:
            print(f"Error: Received status code {response.status_code}")
            print("Response text: ", response.text)
            return False  # Assume not NSFW if there's an error
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False  # Assume not NSFW if there's an exception
