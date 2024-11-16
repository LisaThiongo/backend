import os
from dotenv import load_dotenv
load_dotenv(override=True)
class Config:
    def __init__(self):
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
  
config = Config()

