# your_app/views.py
import os
import json
import google.generativeai as genai
import traceback
import uuid  # For generating unique filenames
import base64  # To handle image data
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables at the top
load_dotenv()

import requests 
from imagekitio import ImageKit

try:
    imagekit = ImageKit(
        private_key=os.getenv('IMAGEKIT_PRIVATE_KEY'),
        public_key=os.getenv('IMAGEKIT_PUBLIC_KEY'),
        url_endpoint=os.getenv('IMAGEKIT_URL_ENDPOINT')
    )
except Exception as e:
    print(f"ImageKit initialization failed: {e}")
    imagekit = None

from .utils import markdown_to_whatsapp, send_hiring_notifications, send_contact_notifications, get_latest_github_activity

def chat_response(markdown_text):
    whatsapp_text = markdown_to_whatsapp(markdown_text)
    return whatsapp_text

# --- Models and Serializers ---
from .models import HiringRequest, ContactRequest, ChatSession, ChatMessage
from .serializers import HiringRequestSerializer, ContactRequestSerializer


# --- Function to load portfolio data from the markdown file ---
def load_portfolio_data():
    """Reads the portfolio data from the markdown file and database."""
    file_path = os.path.join(settings.BASE_DIR, 'chatbot', 'portfolio_data.md')
    markdown_content = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        markdown_content = "Markdown portfolio data unavailable."

    # Fetch live project stats from database
    try:
        from projects.models import Project
        from experience.models import Experience
        
        db_projects = Project.objects.all()
        project_stats = "\n### LIVE PROJECT DETAILS & STATS (FROM DATABASE)\n"
        for p in db_projects:
            updated_str = p.github_updated_at.strftime('%Y-%m-%d') if p.github_updated_at else "N/A"
            features_str = ", ".join(p.key_features) if p.key_features else "N/A"
            
            project_stats += f"""
* **{p.title}**
  - Category: {p.category or 'N/A'}
  - Built During: {p.get_built_during_display()}
  - Role: {p.role or 'Contributor'}
  - Status: {"Live/In Market" if p.is_live else "In Development"}
  - Overview: {p.overview or 'N/A'}
  - Views: {p.views}
  - GitHub: {p.github_stars} Stars, {p.github_forks} Forks (Last push: {updated_str})
  - Quality: Performance: {p.lighthouse_performance}, SEO: {p.lighthouse_seo}, Accessibility: {p.lighthouse_accessibility}
  - Test Coverage: {p.test_coverage}%
  - Key Features: {features_str}
  - Tech: {", ".join(p.tech_stack)}
  - Availability: {"Mobile App Available" if p.is_app_available else "Web Only"}
"""

        db_experiences = Experience.objects.all()
        experience_stats = "\n### LIVE PROFESSIONAL EXPERIENCE (FROM DATABASE)\n"
        for exp in db_experiences:
            resp_str = "\n    - ".join(exp.responsibilities) if exp.responsibilities else "N/A"
            tech_str = ", ".join(exp.technologies) if exp.technologies else "N/A"
            achieve_str = "\n    - ".join(exp.achievements) if exp.achievements else "N/A"
            duration = exp.period or f"{exp.start_date} - {exp.end_date or ('Present' if exp.is_current else 'N/A')}"
            
            experience_stats += f"""
* **{exp.role} at {exp.company}**
  - Duration: {duration}
  - Location: {exp.location or 'N/A'}
  - Tech Stack: {tech_str}
  - Key Responsibilities:
    - {resp_str}
  - Key Achievements:
    - {achieve_str}
"""
        
        return f"{markdown_content}\n{project_stats}\n{experience_stats}"
    except Exception as e:
        print(f"Error loading DB stats: {e}")
        return markdown_content

# We'll call this inside the view to get fresh data


from .prompts import PROFILE_PROMPT



# Configure the Gemini API client
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    # Using gemini-flash-latest which points to stable 1.5 with high quotas
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
    )
except Exception as e:
    print(f"API Key not configured or model initialization failed: {e}")
    model = None
    tts_model = None

from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InvalidArgument, PermissionDenied

def stream_gemini_response(history, system_instruction, retry_count=0):
    try:
        # Initialize a fresh model with gemini-flash-latest
        dynamic_model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            system_instruction=system_instruction
        )
        response_stream = dynamic_model.generate_content(history, stream=True)
        full_response = ""
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                # If we detect the tool call, interrupt and return activity
                if "[TOOL_CALL:GET_LATEST_COMMIT]" in full_response:
                    yield get_latest_github_activity()
                    return
                yield chunk.text
        yield "" 
    except ResourceExhausted:
        if retry_count < 1:
            import time
            time.sleep(2)  # Wait 2 seconds and try one last time
            yield from stream_gemini_response(history, system_instruction, retry_count + 1)
        else:
            yield "I'm currently receiving too many requests (API Rate Limit). Please wait a few seconds and try again.|||SUGGESTIONS|||[\"Tell me about your tech stack\", \"What projects have you built?\", \"Show me your resume\"]"
    except PermissionDenied:
        yield "The API Key is valid, but the Generative Language API is disabled. Please enable it in Google Cloud Console.|||SUGGESTIONS|||[]"
    except ServiceUnavailable:
        yield "The AI service is currently overloaded. Please try again in a moment.|||SUGGESTIONS|||[]"
    except InvalidArgument:
        yield "Invalid input received. Please try rephrasing your question.|||SUGGESTIONS|||[]"
    except Exception as e:
        print(f"Error during streaming: {traceback.format_exc()}")
        yield f"I'm sorry, an unexpected error occurred. (Error: {str(e)})|||SUGGESTIONS|||[]"

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

        # 1. Handle Session for Memory
        session_id = request.data.get("session_id")
        session = None
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create()
        else:
            session = ChatSession.objects.create()

        # Regenerate prompt with fresh data
        current_data = load_portfolio_data()
        dynamic_prompt = PROFILE_PROMPT.replace("{PORTFOLIO_DATA}", current_data)
        
        chat_history_raw = request.data.get("history", [])
        user_message_text = chat_history_raw[-1].get("text", "") if chat_history_raw else ""
        
        if not user_message_text:
            return Response({"error": "Message cannot be empty."}, status=400)
        
        # --- NEW LOGIC TO HANDLE SIMPLE GREETINGS ---
        last_user_message_lower = user_message_text.lower().strip()
        if last_user_message_lower in SIMPLE_RESPONSES:
            predefined_response = SIMPLE_RESPONSES[last_user_message_lower]
            # Save to DB if session exists
            ChatMessage.objects.create(session=session, role='user', text=user_message_text)
            ChatMessage.objects.create(session=session, role='model', text=predefined_response)
            
            return StreamingHttpResponse(
                iter([f"{predefined_response}|||SESSION_ID|||{str(session.session_id)}"]), 
                content_type='text/plain'
            )
        # --- END OF NEW LOGIC ---

        # 2. Build history for Gemini from DB (LATEST 10 messages)
        # We get the most recent ones and then reverse to keep chronological order
        db_messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:10]
        formatted_history = []
        # Reverse them so they are in chronological order (oldest to newest)
        for msg in reversed(db_messages):
            formatted_history.append({
                "role": "model" if msg.role == "model" else "user",
                "parts": [{"text": msg.text}]
            })

        # Add the current user message to formatted history if not already there
        # (Usually history in request contains previous turns, but we rely on DB now)
        # To be safe, we just use the final message for the generation
        current_user_part = {"role": "user", "parts": [{"text": user_message_text}]}
        
        # Save current user message to DB
        ChatMessage.objects.create(session=session, role='user', text=user_message_text)

        # 3. Stream response and save model's turn to DB at the end
        def wrapped_stream():
            full_reply = ""
            for chunk in stream_gemini_response(formatted_history + [current_user_part], dynamic_prompt):
                full_reply += chunk
                yield chunk
            
            # Save model reply to DB once streaming is done
            if full_reply:
                ChatMessage.objects.create(session=session, role='model', text=full_reply)
            
            # Append session_id info for frontend to store
            yield f"|||SESSION_ID|||{str(session.session_id)}"

        return StreamingHttpResponse(
            wrapped_stream(),
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
        hiring_request = serializer.save()
        # Trigger smart notifications
        send_hiring_notifications(hiring_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
def submit_contact_request(request):
    serializer = ContactRequestSerializer(data=request.data)
    if serializer.is_valid():
        contact_request = serializer.save()
        # Trigger smart notifications
        send_contact_notifications(contact_request)
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
    Generates an image based on a prompt using the Gemini API, 
    uploads it to ImageKit, and returns the public URL.
    """
    if not imagekit:
        return Response({"error": "Image hosting service is not configured."}, status=500)
    
    # Check if the main Gemini model is configured from your existing setup
    if not model:
        return Response({"error": "Gemini API is not configured."}, status=500)

    prompt_text = request.data.get('prompt', 'a friendly robot waving')
    # Add style hints to the prompt for a "sticker" look
    final_prompt = f"a cute sticker of {prompt_text}, vector art, simple illustration, white background, high quality"
    
    print(f"Received request to generate sticker with Gemini, prompt: '{final_prompt}'")

    try:
        # ======================================================================
        # == PART 1: GEMINI IMAGE GENERATION API CALL                         ==
        # ======================================================================
        
        # Initialize the specific Gemini model for image generation
        # NOTE: Using the 2.0 model which supports multimodal tasks.
        # Using gemini-flash-latest for image tasks
        image_model = genai.GenerativeModel('gemini-flash-latest')

        # Generate the image content
        response = image_model.generate_content(final_prompt)
        
        # The image data is returned in the 'parts' of the first candidate.
        # We need to access the raw binary data from the response.
        image_data_bytes = response.candidates[0].content.parts[0].inline_data.data
        
        if not image_data_bytes:
             raise Exception("Image generation failed: No image data returned from Gemini API.")
        
        # ======================================================================
        # == PART 2: UPLOAD THE IMAGE TO IMAGEKIT.IO (This part is unchanged) ==
        # ======================================================================
        unique_filename = f"sticker_{uuid.uuid4().hex}.png"
        print(f"Uploading to ImageKit as '{unique_filename}'...")

        upload_response_obj = imagekit.upload(
            file=image_data_bytes,
            file_name=unique_filename,
            options={
                "folder": "/portfolio-chatbot-stickers/",
                "is_private_file": False,
            }
        )
        
        response_metadata = upload_response_obj.get("response", {})
        image_url = response_metadata.get("url")
        
        if not image_url:
            print(f"ImageKit upload failed. Full response: {response_metadata}")
            raise Exception("ImageKit upload failed: URL not found in response.")

        print(f"Upload successful. URL: {image_url}")
        
        # ======================================================================
        # == PART 3: RETURN THE PUBLIC URL (This part is unchanged)           ==
        # ======================================================================
        return JsonResponse({"imageUrl": image_url})

    except Exception as e:
        print(f"An error occurred in generate_sticker_image: {traceback.format_exc()}")
        return Response({"error": str(e)}, status=500)
