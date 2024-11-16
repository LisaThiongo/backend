import os
import requests
import json
from dotenv import load_dotenv

async def read_nsfw():
    try:
        print("Inside Read NSFW")
        load_dotenv()
        edenai_api_key = os.getenv("EDENAI_API_KEY")
        if not edenai_api_key:
            raise ValueError("EDENAI_API_KEY is not set in the environment variables.")
        
        headers = {"Authorization": f"Bearer {edenai_api_key}"}
        url = "https://api.edenai.run/v2/image/explicit_content"
        data = {"providers": "google"}

        # Open the file in a context manager to ensure proper closing
        with open("./lib/lor.jpg", "rb") as file:
            files = {'file': file}
            response = requests.post(url, data=data, files=files, headers=headers)

        # Check the response status
        if response.status_code == 200:
            result = response.json()
            print("Result: ", result)
            return result
        else:
            print(f"Error: Received status code {response.status_code}")
            print("Response text: ", response.text)
            return {"error": response.text}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}
