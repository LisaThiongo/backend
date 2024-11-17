import os
from dotenv import load_dotenv
load_dotenv(override=True)
class Config:
    def __init__(self):
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        self.EDENAI_API_KEY = os.getenv('EDENAI_API_KEY')
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        
  
config = Config()

