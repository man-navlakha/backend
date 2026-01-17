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


from .utils import markdown_to_whatsapp, send_hiring_notifications, send_contact_notifications, get_latest_github_activity

def chat_response(markdown_text):
    whatsapp_text = markdown_to_whatsapp(markdown_text)
    return whatsapp_text

# --- Models and Serializers ---
from .models import HiringRequest, ContactRequest, ChatSession, ChatMessage
from .serializers import HiringRequestSerializer, ContactRequestSerializer


# --- Function to load portfolio data from the markdown file ---
def load_portfolio_data():
    """Reads the portfolio data exclusively from the database."""
    from projects.models import Project
    from experience.models import Experience, Education
    from .models import Profile
    
    data_parts = []
    
    # 1. Profile / About
    try:
        profile = Profile.objects.first()
        if profile:
            skills_str = ""
            if profile.skills:
                for cat, items in profile.skills.items():
                    skills_str += f"- **{cat}:** {', '.join(items)}\n"
            
            socials_str = "\n".join([f"- [{s['name']}]({s['url']})" for s in profile.social_links]) if profile.social_links else "N/A"
            
            data_parts.append(f"""
### ABOUT {profile.name.upper()}
* **Role:** {profile.role}
* **Summary:** {profile.summary}
* **Email:** {profile.email}
* **Phone:** {profile.phone or 'N/A'}
* **Address:** {profile.address or 'N/A'}
* **Languages:** {", ".join(profile.languages) if profile.languages else 'N/A'}
* **Portfolio Site:** https://man-navlakha.netlify.app/

### SKILLS
{skills_str or 'N/A'}

### SOCIAL LINKS
{socials_str or 'N/A'}
""")
    except Exception as e:
        print(f"Error loading Profile: {e}")

    # 2. Projects
    try:
        db_projects = Project.objects.all().order_by('order')
        project_stats = "\n### PROJECTS\n"
        for p in db_projects:
            updated_str = p.github_updated_at.strftime('%Y-%m-%d') if p.github_updated_at else "N/A"
            project_stats += f"""
* **{p.title}**
  - Category: {p.category or 'N/A'}
  - Built During: {p.get_built_during_display()}
  - Role: {p.role or 'Contributor'}
  - Status: {"Live/In Market" if p.is_live else "In Development"}
  - Overview: {p.overview or p.description or 'N/A'}
  - GitHub: {p.github_stars} Stars, {p.github_forks} Forks (Last push: {updated_str})
  - Quality: Perf: {p.lighthouse_performance}, SEO: {p.lighthouse_seo}, Accessibility: {p.lighthouse_accessibility}
  - Tech: {", ".join(p.tech_stack)}
"""
        data_parts.append(project_stats)
    except Exception as e:
        print(f"Error loading Projects: {e}")

    # 3. Experience
    try:
        db_experiences = Experience.objects.all().order_by('order')
        experience_stats = "\n### PROFESSIONAL EXPERIENCE\n"
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
  - Responsibilities:
    - {resp_str}
  - Achievements:
    - {achieve_str}
"""
        data_parts.append(experience_stats)
    except Exception as e:
        print(f"Error loading Experience: {e}")

    # 4. Education
    try:
        db_education = Education.objects.all().order_by('order')
        edu_stats = "\n### EDUCATION\n"
        for edu in db_education:
            edu_stats += f"""
* **{edu.degree}**
  - Institution: {edu.institution}
  - Period: {edu.period}
  - Score: {edu.score or 'N/A'}
"""
        data_parts.append(edu_stats)
    except Exception as e:
        print(f"Error loading Education: {e}")

    return "\n".join(data_parts)

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
