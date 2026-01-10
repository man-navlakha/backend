import os
from dotenv import load_dotenv

load_dotenv()

print(f"GOOGLE_API_KEY: {'Found' if os.getenv('GOOGLE_API_KEY') else 'Not Found'}")
print(f"EMAIL_HOST_USER: {os.getenv('EMAIL_HOST_USER')}")
print(f"WHATSAPP_PHONE_NUMBER_ID: {os.getenv('WHATSAPP_PHONE_NUMBER_ID')}")
