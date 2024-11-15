import os
from dotenv import load_dotenv
load_dotenv(override=True)
class Config:
    def __init__(self):
        self.MONGODB_URI = os.getenv('MONGODB_URI')
  
config = Config()


