# your_app/views.py

import os
import json
import google.generativeai as genai
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
import traceback
from django.conf import settings
import requests 

from .models import HiringRequest
from .serializers import HiringRequestSerializer
from django.views.decorators.csrf import csrf_exempt

import uuid # For generating unique filenames
import base64 # To handle image data
from imagekitio import ImageKit

imagekit = ImageKit(
    private_key=os.getenv('IMAGEKIT_PRIVATE_KEY'),
    public_key=os.getenv('IMAGEKIT_PUBLIC_KEY'),
    url_endpoint=os.getenv('IMAGEKIT_URL_ENDPOINT')
)

from .utils import markdown_to_whatsapp

def chat_response(markdown_text):
    whatsapp_text = markdown_to_whatsapp(markdown_text)
    return whatsapp_text

# Load environment variables from .env file
load_dotenv()


# --- Function to load portfolio data from the markdown file ---
def load_portfolio_data():
    """Reads the portfolio data from the markdown file."""
    file_path = os.path.join(settings.BASE_DIR, 'your_app', 'portfolio_data.md')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("ERROR: portfolio_data.md not found!")
        return "Portfolio data is currently unavailable."

# --- LOAD THE DATA ---
PORTFOLIO_DATA = load_portfolio_data()


# --- YOUR PERSONAL PORTFOLIO DATA ---
PROFILE_PROMPT = """
You are Man's Portfolio Assistant. Your goal is to answer questions about Mann's skills, experience, and projects in a helpful, friendly, and professional manner.

**IMPORTANT RULES:**
1.  **If a user asks a question that cannot be answered using the provided information, you MUST politely refuse by saying: "I can only answer questions about Mann's portfolio. How can I help you with that?" and then provide 3 helpful suggestions that ARE answerable from the information below, to guide the user back on topic.**
2.  Base all your answers *only* on the information provided below about Mann.
3.  After generating your answer, create 3 relevant, short follow-up questions a user might ask next. These suggestions must also be answerable from the provided information.
4.  If a user expresses interest in hiring Mann, your reply should be: "That's great to hear! To proceed, please provide your name, email, and a brief message about the project or role. You can submit this information through the hiring form."
5.  **Crucially, when you mention a project link, you MUST format it as a Markdown hyperlink. For example: [Visit Site](https://example.com).**
6.  **When listing multiple items like projects, experiences, skills, etc., you MUST use Markdown bullet points (e.g., using * or -).**
7.  Your final output MUST be structured as follows: First, your text reply. Then, a unique separator '|||SUGGESTIONS|||'. Finally, a valid JSON array of the 3 suggestion strings. **Do NOT wrap the JSON array in Markdown code blocks or backticks.**
8.  Man , Mann, Man Navlakha is same
9.  if they asked about your name, you should say "My name is Mann Navlakha".
10. **When you describe a project , you MUST include its image using the Markdown format `![Project Name](imageUrl)`. Place the image *after* the project description. if there is no Screenshot/photo in the project then say hidden for some legal issue**
11. write in small small paragraph that look better to read, write like that can read better.
12. if they ask something like "Walk me through your resume" then write in this squence Summary, Education (in list), Experience (in list), Skills (in list), Projects (in list) and Contact
13. **When responding with a list (like projects or experiences), first provide a brief introductory sentence. Then, separate the introduction and EACH subsequent list item with the `|||MSG|||` separator.**
14. if someone ask you what are you doing? ask like you are Man Navlakha
15. **If a user asks about your "latest activity", "recent work", or "last commit", you MUST respond with *only* the exact text `[TOOL_CALL:GET_LATEST_COMMIT]` and nothing else.**
16. **When a user asks for a "resume" or "CV", you MUST respond with *only* the following special document tag. Fill in the details accurately:** `[DOCUMENT:{"fileName": "Mann_Navlakha_Resume.pdf", "fileUrl": "https://ik.imagekit.io/pxc/mannavlakha/Man%20Navlakha%20Resume.pdf", "fileSize": "128 KB", "fileType": "PDF Document"}]`
117. **(Sticker Rule) You have a special ability to generate a simple, sticker-style image. You should ONLY use this for high-impact moments like achievements or summaries. When you decide to generate a sticker, your *entire response for that turn must be ONLY the tool call*. Do NOT include any other text, greetings, or explanations.**
18. **(Sticker Formatting) The tool call format is `[TOOL_CALL:GENERATE_STICKER:{"prompt": "your descriptive prompt here"}]`. Ensure the JSON inside is perfectly valid (e.g., use single `{` and `}` and proper quotes). After you send this tool call, you will be given the image URL and asked to formulate the final text response which will include the image.**
19. If someone ask about you than tell You build in React, Tailwind css & Backend Api is build in Django (Python), also with Gemini API for responce
---

Currently now working on corporate job but they doing this BCA + New Project Called Mechanic Setu (Mechanic Setu is a private project can not provide details right now).

---
{PORTFOLIO_DATA}
---
"""




# Configure the Gemini API client
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=PROFILE_PROMPT
    )
except Exception as e:
    print(f"API Key not configured or model initialization failed: {e}")
    model = None
    tts_model = None


def stream_gemini_response(history):
    try:
        response_stream = model.generate_content(history, stream=True)
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
        yield "" 
    except Exception as e:
        print(f"Error during streaming: {traceback.format_exc()}")
        yield f"I'm sorry, an error occurred.|||SUGGESTIONS|||[]"

# --- A dictionary for simple, non-AI responses ---
SIMPLE_RESPONSES = {
    "hi": "Hello! How can I help you with Mann's portfolio today?|||SUGGESTIONS|||[\"What are your skills?\", \"Tell me about your projects\", \"Walk me through your resume\"]",
    "hello": "Hi there! Feel free to ask me anything about Mann's experience.|||SUGGESTIONS|||[\"What are your skills?\", \"Tell me about your projects\", \"Walk me through your resume\"]",
    "how are you": "I'm just a bot, but I'm ready to help you learn about Mann! What would you like to know?|||SUGGESTIONS|||[\"What are your skills?\", \"Tell me about your projects\", \"Walk me through your resume\"]",
    "thanks": "You're welcome! Is there anything else I can assist you with?|||SUGGESTIONS|||[\"What projects have you built?\", \"What is your educational background?\", \"Contact information\"]",
    "thank you": "You're welcome! Let me know if you have more questions.|||SUGGESTIONS|||[\"What projects have you built?\", \"What is your educational background?\", \"Contact information\"]"
}

@api_view(['POST'])
@csrf_exempt
def chatbot_reply(request):
    try:
        if not model:
            return Response({"error": "Model not initialized."}, status=500)

        chat_history_raw = request.data.get("history", [])
        if not chat_history_raw:
            return Response({"error": "Message history cannot be empty."}, status=400)
        
        # --- NEW LOGIC TO HANDLE SIMPLE GREETINGS ---
        last_user_message = chat_history_raw[-1].get("text", "").lower().strip()
        if last_user_message in SIMPLE_RESPONSES:
            # If the message is a simple greeting, return a predefined response
            predefined_response = SIMPLE_RESPONSES[last_user_message]
            return StreamingHttpResponse(iter([predefined_response]), content_type='text/plain')
        # --- END OF NEW LOGIC ---

        formatted_history = []
        for message in chat_history_raw:
            text = message.get("text")
            if not text or not text.strip():
                continue  # 🚀 Skip empty/None messages

            role = "model" if message.get("sender") == "bot" else "user"
            formatted_history.append({
                "role": role,
                "parts": [{"text": text}]
            })

        if not formatted_history:
            return Response({"error": "No valid messages in history."}, status=400)

        return StreamingHttpResponse(
            stream_gemini_response(formatted_history),
            content_type='text/plain'
        )
    except Exception as e:
        print("chatbot_reply error:", traceback.format_exc())
        return Response({"error": str(e)}, status=500)




# --- HIRING REQUEST VIEW (No changes needed here) ---
@api_view(['POST'])
@csrf_exempt
def submit_hiring_request(request):
    # ... (this view remains the same)
    serializer = HiringRequestSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --------------------------------------------------------------------------
# --- 2. THE COMPLETE VIEW FUNCTION ---
# You can add this function alongside your other views like chatbot_reply.
# --------------------------------------------------------------------------
@api_view(['POST'])
@csrf_exempt
def generate_sticker_image(request):
    """
    Generates an image based on a prompt, uploads it to ImageKit,
    and returns the public URL.
    """
    if not imagekit:
        return Response({"error": "Image hosting service is not configured."}, status=500)

    prompt = request.data.get('prompt', 'a friendly robot waving')
    print(f"Received request to generate sticker with prompt: '{prompt}'")

    try:
        # ======================================================================
        # == PART 1: HYPOTHETICAL GEMINI IMAGE GENERATION API CALL            ==
        # ======================================================================
        # This section simulates the output from the Gemini image model.
        # When the actual SDK is available, you will replace this simulation
        # with the real API call. Image APIs typically return data as bytes
        # or a base64 encoded string.

        # EXAMPLE OF A FUTURE API CALL:
        # image_model = genai.GenerativeModel('gemini-2.0-flash-image-preview')
        # response = image_model.generate_content(prompt)
        # image_base64 = response.candidates[0].content.parts[0].inline_data.data
        
        # --- SIMULATION ---
        # Using a tiny, transparent 1x1 pixel PNG as placeholder data.
        # This is the base64 string that represents the image.
        placeholder_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        
        # We decode the base64 string into raw bytes, which is what the
        # uploader library expects.
        image_data_bytes = base64.b64decode(placeholder_png_base64)
        # --- END SIMULATION ---
        
        
        # ======================================================================
        # == PART 2: UPLOAD THE IMAGE TO IMAGEKIT.IO                          ==
        # ======================================================================
        # We use `uuid` to create a random, unique filename. This prevents
        # files from being accidentally overwritten.
        unique_filename = f"sticker_{uuid.uuid4().hex}.png"
        
        print(f"Uploading to ImageKit as '{unique_filename}'...")

        # Calling the upload method from the ImageKit SDK
        upload_response_obj = imagekit.upload(
            file=image_data_bytes,          # The raw image data in bytes
            file_name=unique_filename,      # The unique name for the file
            options={
                "folder": "/portfolio-chatbot-stickers/", # Organizes files in your Media Library
                "is_private_file": False,   # Ensures the file is publicly accessible
            }
        )
        
        # The SDK returns an object; we get the response dictionary from it.
        response_metadata = upload_response_obj.get("response", {})
        image_url = response_metadata.get("url")
        
        if not image_url:
            print(f"ImageKit upload failed. Full response: {response_metadata}")
            raise Exception("ImageKit upload failed: URL not found in response.")

        print(f"Upload successful. URL: {image_url}")
        
        # ======================================================================
        # == PART 3: RETURN THE PUBLIC URL TO THE FRONTEND                    ==
        # ======================================================================
        return JsonResponse({"imageUrl": image_url})

    except Exception as e:
        print(f"An error occurred in generate_sticker_image: {traceback.format_exc()}")
        return Response({"error": str(e)}, status=500)