import re
import os
import requests
from django.core.mail import send_mail
from django.conf import settings
import subprocess

def get_latest_github_activity():
    """
    Returns a string describing the latest commit or project activity.
    """
    activity_msg = "My latest activity has been quite busy! \n\n"
    has_activity = False

    try:
        # 1. Try to get the latest local git commit
        commit_info = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%h - %s (%cr)"],
            stderr=subprocess.STDOUT
        ).decode("utf-8")
        activity_msg += f"🚀 **Current Repo**: The last update here was `{commit_info}`. \n"
        has_activity = True
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        # Ignore if git is not available or not a repo
        pass
        
    try:
        # 2. Try to get the latest project update from our database
        from projects.models import Project
        latest_project = Project.objects.filter(github_updated_at__isnull=False).order_by('-github_updated_at').first()
        
        if latest_project:
            updated_time = latest_project.github_updated_at.strftime("%B %d, %Y")
            activity_msg += f"📂 **Project Update**: I recently pushed updates to **{latest_project.title}** on {updated_time}. \n"
            has_activity = True
    except Exception as e:
        print(f"Error fetching DB activity: {e}")

    if not has_activity:
        return "I'm currently working on several updates! You can see my most recent work on [GitHub](https://github.com/man-navlakha).|||SUGGESTIONS|||[\"What are your projects?\", \"What is your tech stack?\", \"Walk me through your resume\"]"

    activity_msg += "\nIs there any specific project you'd like to dive into? |||SUGGESTIONS|||[\"Tell me about Mechanic Setu\", \"What are your skills?\", \"Show me your resume\"]"
    return activity_msg

def shorten_url(url):
    # Place holder for URL shortening if needed, currently just returns original
    return url

def markdown_to_whatsapp(text):
    # Replace bold **text** → *text*
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

    # Replace italic *text* → _text_
    text = re.sub(r"(?<!\*)\*(.*?)\*(?!\*)", r"_\1_", text)

    # Replace strikethrough ~~text~~ → ~text~
    text = re.sub(r"~~(.*?)~~", r"~\1~", text)

    # Replace inline code `code` → ```code``` (monospace)
    text = re.sub(r"`(.*?)`", r"```\1```", text)

    # Replace links [title](url) → title (url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", lambda m: f"{m.group(1)} ({shorten_url(m.group(2))})", text)

    # Replace images ![alt](url) → [alt]
    text = re.sub(r"!\[(.*?)\]\((.*?)\)", lambda m: f"[{m.group(1) or 'Screenshot'}]", text)

    return text

def send_whatsapp_notification(message_text):
    """
    Sends a WhatsApp notification using the WhatsApp Cloud API.
    Required variables in .env:
    - WHATSAPP_ACCESS_TOKEN
    - WHATSAPP_PHONE_NUMBER_ID
    - RECIPIENT_PHONE_NUMBER (your own number)
    """
    url = f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": os.getenv("RECIPIENT_PHONE_NUMBER"),
        "type": "text",
        "text": {"body": message_text},
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"WhatsApp Notification Error: {e}")
        return None

def send_auto_responder(hiring_request):
    """
    Sends a professional thank-you email to the person who filled out the form.
    """
    subject = "Thank you for reaching out - Mann Navlakha"
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #333;">Hello {hiring_request.name},</h2>
        <p>Thank you so much for reaching out through my portfolio website!</p>
        <p>I have received your message regarding: <br>
           <i style="color: #555;">"{hiring_request.message}"</i>
        </p>
        <p>I usually respond within 24 hours. In the meantime, feel free to check out my latest work or connect with me:</p>
        <div style="margin: 20px 0;">
            <a href="https://linkedin.com/in/navlakhaman" style="background: #0077b5; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-right: 10px;">LinkedIn</a>
            <a href="https://github.com/man-navlakha" style="background: #333; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-right: 10px;">GitHub</a>
            <a href="https://man-navlakha.netlify.app/" style="background: #e4405f; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Portfolio</a>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee;">
        <p style="font-size: 0.8em; color: #888;">
            Best regards,<br>
            <strong>Mann Navlakha</strong><br>
            Jr. Frontend Developer
        </p>
    </div>
    """
    
    try:
        send_mail(
            subject,
            "", # Plain text fallback (empty because we use html_message)
            settings.DEFAULT_FROM_EMAIL,
            [hiring_request.email],
            fail_silently=False,
            html_message=html_message
        )
        print(f"Auto-responder sent to {hiring_request.email}")
    except Exception as e:
        print(f"Auto-responder failed: {e}")

def send_hiring_notifications(hiring_request):
    """
    Sends both Email and WhatsApp notifications for a new hiring request.
    """
    # ... existing code ...
    subject = f"🚀 New Hiring Request from {hiring_request.name}"
    message = (
        f"You have a new hiring request!\n\n"
        f"👤 Name: {hiring_request.name}\n"
        f"📧 Email: {hiring_request.email}\n"
        f"💬 Message: {hiring_request.message}\n\n"
        f"Sent from your Portfolio Backend."
    )
    
    # 1. Send Email alert to ADMIN
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [os.getenv("ADMIN_EMAIL", "mannnavlakha1021@gmail.com")],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email notification failed: {e}")

    # 2. Send Auto-Responder to CLIENT
    send_auto_responder(hiring_request)

    # 3. Send WhatsApp alert (Optional)
    whatsapp_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    
    if whatsapp_id and whatsapp_token and "your_" not in whatsapp_id:
        wa_message = f"🚀 *New Hiring Request*\n\n*Name:* {hiring_request.name}\n*Email:* {hiring_request.email}\n*Message:* {hiring_request.message}"
        send_whatsapp_notification(wa_message)
    else:
        print("WhatsApp notification skipped: Credentials not configured.")

def send_contact_notifications(contact_request):
    """
    Sends both Email and WhatsApp notifications for a new contact request.
    """
    subject = f"📬 New Contact Message from {contact_request.name}"
    if contact_request.subject:
        subject = f"📬 {contact_request.subject} (from {contact_request.name})"

    message = (
        f"You have a new contact message!\n\n"
        f"👤 Name: {contact_request.name}\n"
        f"📧 Email: {contact_request.email}\n"
        f"📝 Subject: {contact_request.subject or 'No Subject'}\n"
        f"💬 Message: {contact_request.message}\n\n"
        f"Sent from your Portfolio Backend."
    )
    
    # 1. Send Email alert to ADMIN
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [os.getenv("ADMIN_EMAIL", "mannnavlakha1021@gmail.com")],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email notification failed: {e}")

    # 2. Send Auto-Responder to CLIENT
    send_auto_responder(contact_request)

    # 3. Send WhatsApp alert (Optional)
    whatsapp_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    
    if whatsapp_id and whatsapp_token and "your_" not in whatsapp_id:
        wa_message = f"📬 *New Contact Message*\n\n*Name:* {contact_request.name}\n*Email:* {contact_request.email}\n*Subject:* {contact_request.subject or 'N/A'}\n*Message:* {contact_request.message}"
        send_whatsapp_notification(wa_message)
    else:
        print("WhatsApp notification skipped: Credentials not configured.")
