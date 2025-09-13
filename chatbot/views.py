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
import requests 

from .models import HiringRequest
from .serializers import HiringRequestSerializer


# --- KEY CHANGE: Import csrf_exempt ---
from django.views.decorators.csrf import csrf_exempt


@api_view(['GET'])
@csrf_exempt
def get_github_activity(request):
    # --- IMPORTANT: Replace 'YOUR_GITHUB_USERNAME' with your actual username ---
    github_username = "YOUR_GITHUB_USERNAME" 
    try:
        url = f"https://api.github.com/users/{github_username}/events/public"
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes
        events = response.json()

        # Find the latest push event
        for event in events:
            if event['type'] == 'PushEvent':
                commit = event['payload']['commits'][0]
                repo_name = event['repo']['name']
                commit_message = commit['message']
                commit_url = f"https://github.com/{repo_name}/commit/{commit['sha']}"
                
                # Format the response
                formatted_response = (
                    f"My latest commit was to the **{repo_name}** repository.\n"
                    f"*- Message:* \"{commit_message}\"\n"
                    f"*You can view it here:* [{commit['sha'][:7]}]({commit_url})"
                )
                return Response({"activity": formatted_response})
        
        return Response({"activity": "I couldn't find a recent commit."})

    except requests.exceptions.RequestException as e:
        print(f"GitHub API Error: {e}")
        return Response({"error": "Failed to fetch data from GitHub."}, status=500)

from .utils import markdown_to_whatsapp

def chat_response(markdown_text):
    whatsapp_text = markdown_to_whatsapp(markdown_text)
    return whatsapp_text


# Load environment variables from .env file
load_dotenv()

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
10. **When you describe a project , you MUST include its image using the Markdown format `![Project Name](imageUrl)`. Place the image *after* the project description.**
11. write in small small paragraph that look better to read, write like that can read better.
12. if they ask something like "Walk me through your resume" then write in this squence Summary, Education (in list), Experience (in list), Skills (in list), Projects (in list) and Contact
13. **When responding with a list (like projects or experiences), first provide a brief introductory sentence. Then, separate the introduction and EACH subsequent list item with the `|||MSG|||` separator.**
14. if someone ask you what are you doing? ask like you are Man Navlakha
15. **If a user asks about your "latest activity", "recent work", or "last commit", you MUST respond with *only* the exact text `[TOOL_CALL:GET_LATEST_COMMIT]` and nothing else.**

---

Currently now working on corporate job but they doing this BCA + New Project Called Mechanic Setu (Mechanic Setu is a private project can not provide details right now).

---

### ABOUT MANN , MAN, MAN NAVLAKHA 
* **Photo**: ![Photo](https://ik.imagekit.io/pxc/mannavlakha/t-man-removebg.png?updatedAt=1755338197921)
* **Name**: Mann Navlakha
* **Role:** "Jr.Frontend Developer"
* **Summary:** A frontend developer with a strong focus on creating responsive, user-friendly interfaces and smooth digital experiences. Mann has extensive experience using React.js. He used it to build the entire career page for HarSar Innovations and the AI model for code review in the Solvinger project. His internship further solidified his React skills, demonstrating his proficiency in building complex, interactive web applications.
* **Email**: [mannnavlakha1021@gmail.com](mailto:mannnavlakha1021@gmail.com)
* **Address**: Vasna, Ahmedabad, Gujarat, India
* **Contect**: 
    * **email**: mannavlakha1021@gmail.com
    * **Mobile Number**: +91 9913151805
* **Languages**: Gujarati (Proficient), English (Intermediate), Hindi (Proficient)
* **Resume**: [Download](https://ik.imagekit.io/pxc/mannavlakha/Man%20Navlakha%20Resume.pdf?updatedAt=1755343374880)
* **Website**: [https://man-navlakha.netlify.app/](https://man-navlakha.netlify.app/)
    * **Social Links:**
        * **LinkedIn**: [https://linkedin.com/in/navlakhaman](https://www.linkedin.com/in/navlakhaman/)
        * **Peerlist**: [https://peerlist.io/mannavlakha](https://peerlist.io/mannavlakha)
        * **Figma Profile**: [https://figma.com/@mannavlakha](https://figma.com/@mannavlakha)

---

### SKILLS
* **Frontend:** HTML, CSS, JavaScript, React, JSX, Next.js, Tailwind CSS, DOM
* **UI/UX Design:** Figma, Adobe XD, Adobe Illustrator, Wireframing, Product Design
* **Backend & API:** Node.js, Express.js, REST API
* **Databases:** SQL
* **Version Control:** Git, GitHub
* **Other Tools:** WordPress

---

### PROJECTS

* **1. Pixel Class:**
    *  **Details:**
        * **Description:** A web application designed for college students to share and access educational content efficiently. Developed the frontend using React.js, Tailwind CSS, and JavaScript, ensuring a responsive and visually appealing design. Integrated API routes, managed authentication using cookies, and optimized the user experience.
        *  **Date:** 2024 - present
        *  **Screenshot:**
            ![Pixel_Class_Screenshot](https://ik.imagekit.io/pxc/mannavlakha/image(1).png)
            ![Pixel_Class_Screenshot](https://ik.imagekit.io/pxc/mannavlakha/image(2).png)  
            ![Pixel_Class_Screenshot](https://ik.imagekit.io/pxc/mannavlakha/image(3).png)
            ![Pixel_Class_Screenshot](https://ik.imagekit.io/pxc/mannavlakha/image(4).png)
        * **Website:** [Visit Site](https://pixelclass.netlify.app/)
        * **Github:** [View on GitHUb](https://github.com/man-navlakha/pxc)

* **2. Solvinger AI:**
    *  **Details:**
        *  **Date:** 2024 - present
        * **Tech Stack:** HTML, CSS, JavaScript, React, JSX, Tailwind CSS
        * **Description:** A Figma-designed AI chatbot UI that delivers a user-friendly and engaging experience. Features include a navigation bar, a dynamic chat UI, and an intuitive input box for quick queries.
        * ![Solvinger_AI_Screenshot](https://ik.imagekit.io/pxc/mannavlakha/Screenshot%202025-08-16%20152513.png)
        * **Live Site:** [Visit Site](https://mysolvingerai.vercel.app/)
        * **Figma Design:** [View on Figma](https://www.figma.com/community/file/1506988206106044637/solvinger-the-ai-chat-bot)

* **3. Career System (for HarSar Innovations):**
    *  **Details:**
        *  **Date:** Mar 2025 - Apr 2025 · 1 mos During Internship
        * **Tech Stack:** React.js, Tailwind CSS, Node.js, Express.js, PostgreSQL
        * **Description:** Developed a complete career page from a Figma design.
        * **Link:** 
            [Visit Frontend](https://career-intern.vercel.app/)
            [Visit Backend](https://server-eight-lac.vercel.app/)
            [Github Frontend](https://github.com/man-navlakha/career-intern)
            [Github Backend](https://github.com/man-navlakha/server)

* **4. System App for Windows:**
    *  **Details:**
        * ![Screenshot](https://ik.imagekit.io/pxc/mannavlakha/image.png)
        * **Description:** A Windows app displaying system information.
        * **GitHub:** [View on GitHub](https://github.com/man-navlakha/system-app)

* **5. Portfolio:**
    *  **Details:**
        * ![Portfolio](https://ik.imagekit.io/pxc/mannavlakha/image.png)
        * **Description:** Mann's personal portfolio website, built using React.js and TailwindCSS.
        * **Live Site:** [Visit Site](https://man-navlakha.netlify.app/)
        * **GitHub:** [View on GitHub](https://github.com/man-navlakha/profile)

* **6. Rent PC Security App for Windows:**
    *  **Details:**
        * **Description:** A Windows Tray app displaying shop & company details and messages. Built using Python.
        * **GitHub:** [View on GitHub](https://github.com/man-navlakha/psr)

---

### EXPERIENCE

* **Naren Advertising and Vision World:**
    * **Dates:** Jun 2023 - Aug 2023 · 3 mos
    * **Location:** Ellisbridge, Ahmedabad, Gujarat, India
    * **Role:** Back-office Executive & Graphic Designer
    * **Responsibilities:**  
      - Created advertising posters using Adobe Illustrator and CorelDraw  
      - Handled back-office tasks such as Excel sheets, word processing, accounting, mailing, and research  

* **Parshwanath Solutions:**
    * **Dates:** Feb 2024 - Oct 2024 · 9 mos
    * **Location:** Gurukul, Ahmedabad, Gujarat, India
    * **Role:** Information Technology Help Desk Technician
    * **Responsibilities:**  
      - Maintained 99.9% system uptime  
      - Resolved 60+ hardware/software issues  
      - Provided Windows/Linux OS configuration and Office 365 support  
      - Managed service desk operations with high customer satisfaction  
      - Documented processes and installed/maintained IT hardware  

* **HarSar Innovations:**
    * **Dates:** Mar 2025 - Apr 2025 · 1 mos
    * **Location:** Remote (Hyderabad)
    * **Role:** Website Developer Intern
    * **Responsibilities:**  
      - Built frontend with React.js and Tailwind CSS  
      - Implemented responsive design for mobile/desktop  
      - Integrated RESTful APIs for dynamic content loading  
      - Developed interactive popups and UI elements  
      - Matched Figma mockups with pixel-perfect design  
      - Created APIs using Node.js and Express.js  
      - Connected PostgreSQL database  
      - Focused on security and clean code practices  
      - Used Git for version control  

---

### EDUCATION

* **Bachelor of Computer Application (BCA)**  
    - **University:** Shreyath University  
    - **Dates:** 2023 – Present  
    - **CGPA (Sem 4 - 2025):** 7.21  

* **Higher Secondary Certificate (H.S.E.B)**  
    - **School:** Shri Ganesh Vidhya Mandir  
    - **Dates:** 2022 – 2023  
    - **Percentage:** 52%  
"""




# Configure the Gemini API client
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=PROFILE_PROMPT
    )
    # Configure the TTS model
    tts_model = genai.GenerativeModel(model_name='gemini-2.5-flash-preview-tts')
except Exception as e:
    print(f"API Key not configured or model initialization failed: {e}")
    model = None
    tts_model = None




# --- STREAMING FUNCTION (No changes needed here) ---
def stream_gemini_response(history):
    try:
        response_stream = model.generate_content(history, stream=True)
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
        # --- KEY FIX ---
        # Yield an empty string at the end to ensure the stream is fully flushed to the client.
        yield "" 
    except Exception as e:
        print(f"Error during streaming: {traceback.format_exc()}")
        yield f"I'm sorry, an error occurred.|||SUGGESTIONS|||[]"


@api_view(['POST'])
@csrf_exempt
def chatbot_reply(request):
    try:
        if not model:
            return Response({"error": "Model not initialized."}, status=500)

        chat_history_raw = request.data.get("history", [])
        if not chat_history_raw:
            return Response({"error": "Message history cannot be empty."}, status=400)

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

# --- NEW VIEW FOR TEXT-TO-SPEECH ---
@api_view(['POST'])
@csrf_exempt
def synthesize_speech(request):
    if not tts_model:
        return Response({"error": "TTS Model not initialized."}, status=500)

    text_to_speak = request.data.get('text', '')
    if not text_to_speak:
        return Response({"error": "No text provided"}, status=400)

    try:
        # Generate audio content using Gemini TTS model
        response = tts_model.generate_content(
            f"Say this in a clear, friendly voice: {text_to_speak}",
            generation_config=genai.GenerationConfig(
                response_modalities=["AUDIO"]
            )
        )

        # Extract audio part (base64-encoded)
        audio_part = response.candidates[0].content.parts[0]
        if hasattr(audio_part, "inline_data"):
            audio_data = audio_part.inline_data.data
            mime_type = audio_part.inline_data.mime_type
        else:
            return Response({"error": "No audio data returned"}, status=500)

        return JsonResponse({"audioContent": audio_data, "mimeType": mime_type})

    except Exception as e:
        print(f"Error during TTS synthesis: {traceback.format_exc()}")
        return Response({"error": str(e)}, status=500)
