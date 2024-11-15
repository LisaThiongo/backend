import os
import PIL.Image
import google.generativeai as genai
from dotenv import load_dotenv

def genai_config():
    load_dotenv()

    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model
   


    
