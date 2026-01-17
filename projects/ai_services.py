import os
import requests
import json
import base64
import google.generativeai as genai
from django.conf import settings

def get_github_content(repo_url):
    """Fetches README and file structure from GitHub repository."""
    if not repo_url or "github.com" not in repo_url:
        return None

    # Handle cases like https://github.com/user/repo/ or https://github.com/user/repo
    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 2:
        return None
    
    owner = parts[-2]
    repo = parts[-1]
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Portfolio-AI-Magic-Fill"
    }
    pat = os.getenv("GITHUB_PAT")
    if pat:
        headers["Authorization"] = f"token {pat}"
    
    # Get README
    readme_content = ""
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    print(f"Fetching GitHub README from: {readme_url}")
    try:
        r = requests.get(readme_url, headers=headers)
        if r.status_code == 401 or r.status_code == 403:
            print("GitHub auth failed, trying without token...")
            r = requests.get(readme_url, headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "Portfolio-AI-Magic-Fill"})
        
        if r.status_code == 200:
            data = r.json()
            readme_content = base64.b64decode(data['content']).decode('utf-8')
            print(f"Succeeded fetching README ({len(readme_content)} chars)")
        else:
            print(f"Failed to fetch README: HTTP {r.status_code}")
    except Exception as e:
        print(f"Error fetching README: {e}")

    # Get File Tree (top level)
    file_list = []
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    print(f"Fetching GitHub file tree from: {tree_url}")
    try:
        r = requests.get(tree_url, headers=headers)
        if r.status_code == 401 or r.status_code == 403:
            print("GitHub auth failed for tree, trying without token...")
            r = requests.get(tree_url, headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "Portfolio-AI-Magic-Fill"})
            
        if r.status_code == 200:
            file_list = [item['name'] for item in r.json()]
            print(f"Succeeded fetching file list ({len(file_list)} items)")
        else:
            print(f"Failed to fetch file tree: HTTP {r.status_code}")
    except Exception as e:
        print(f"Error fetching file tree: {e}")

    return {
        "readme": readme_content,
        "files": file_list,
        "repo_name": repo
    }

def ai_magic_fill(github_url):
    """Uses Gemini to analyze repo and return structured data for Project model."""
    print(f"Starting AI Magic Fill for: {github_url}")
    content = get_github_content(github_url)
    if not content:
        return None, "Unable to fetch content from GitHub. Check your URL and GitHub PAT."
    
    readme = content.get('readme', '')
    files = content.get('files', [])
    
    if not readme and not files:
        return None, "The repository appear to be empty (no README and no files found)."

    # Configure Gemini
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "GOOGLE_API_KEY not found in server environment."
    
    print(f"Using Google API Key: {api_key[:10]}...")
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')

        print("Sending prompt to Gemini...")
        prompt = f"""
        You are an expert technical portfolio optimizer. I will provide you with the README and file list of a GitHub repository.
        Your task is to analyze the project and return a JSON object that fits my "Project" database model.

        REPO NAME: {content['repo_name']}
        README CONTENT:
        {readme[:7000]}

        FILE STRUCTURE (ROOT):
        {files}

        INSTRUCTIONS:
        1. 'overview': Write a professional 2-3 sentence overview of what the project does. Focus on impact and tech.
        2. 'tech_stack': Return an array of technologies used (e.g. ["React", "Django", "TailwindCSS", "PostgreSQL", "JavaScript"]). Be specific.
        3. 'key_features': Return an array of exactly 4 strings, each being a short, impactful feature (e.g. "Real-time chat using WebSockets").
        4. 'category': Choose ONE of: "Web Development", "Mobile App Development", "Machine Learning", "System Utilities", "Tools & Scripts".
        5. 'role': Identify the most likely role (e.g. "Full Stack Developer", "Frontend Developer", "Backend Developer").
        6. 'lighthouse_performance': Set a goal score (integer 0-100), be realistic but high (85-99).
        7. 'lighthouse_seo': Set a goal score (integer 0-100), usually high (90-100).
        8. 'lighthouse_accessibility': Set a goal score (integer 0-100), usually high (90-100).

        CRITICAL: RETURN ONLY VALID JSON. NO MARKDOWN, NO EXPLANATION.
        JSON STRUCTURE:
        {{
            "overview": "...",
            "tech_stack": ["...", "..."],
            "key_features": ["...", "..."],
            "category": "...",
            "role": "...",
            "lighthouse_performance": 95,
            "lighthouse_seo": 90,
            "lighthouse_accessibility": 100
        }}
        """

        response = model.generate_content(prompt)
        if not response or not response.text:
            return None, "Gemini API returned an empty response."
            
        json_text = response.text.strip()
        print(f"Received raw response from Gemini: {json_text[:100]}...")
        
        # Clean up markdown if it sneaks in
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
             json_text = json_text.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(json_text), None
        except json.JSONDecodeError:
            return None, f"Gemini returned invalid JSON: {json_text[:50]}..."
            
    except Exception as e:
        import traceback
        error_info = f"AI Magic Fill Gemini Error: {str(e)}"
        print(error_info)
        print(traceback.format_exc())
        return None, error_info
