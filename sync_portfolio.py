import os
import django
import re

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projects.models import Project
from experience.models import Experience

def sync_projects(content):
    print("Syncing Projects...")
    projects_section = re.search(r'### PROJECTS(.*?)(### EXPERIENCE|---|$)', content, re.DOTALL)
    if not projects_section:
        print("Projects section not found")
        return

    projects_content = projects_section.group(1)
    project_blocks = re.split(r'\* \*\*\d+\. (.*?):\*\*', projects_content)
    
    for i in range(1, len(project_blocks), 2):
        title = project_blocks[i].strip()
        details = project_blocks[i+1]
        
        description_match = re.search(r'\*\*Description:\*\* (.*?)(?=\s*\*|\Z)', details, re.DOTALL)
        description = description_match.group(1).strip() if description_match else ""
        
        date_match = re.search(r'\*\*Date:\*\* (.*?)(?=\s*\*|\Z)', details)
        date = date_match.group(1).strip() if date_match else ""
        
        website_match = re.search(r'\[Visit Site\]\((.*?)\)|\[Visit UserSide\]\((.*?)\)|\[Visit Frontend\]\((.*?)\)', details)
        website = next((g for g in website_match.groups() if g), None) if website_match else None
        
        github_match = re.search(r'\[View on GitHub\]\((.*?)\)|\[Github UserSide\]\((.*?)\)|\[Github Frontend\]\((.*?)\)', details, re.IGNORECASE)
        github = next((g for g in github_match.groups() if g), None) if github_match else None
        
        figma_match = re.search(r'\[View on Figma\]\((.*?)\)', details)
        figma = figma_match.group(1) if figma_match else None

        status_match = re.search(r'\*\*Status:\*\* (.*?)(?=\s*\*|\Z)', details)
        status = status_match.group(1).strip() if status_match else None

        screenshots = re.findall(r'!\[.*?\]\((.*?)\)', details)
        
        tech_match = re.search(r'\*\*Tech Stack:\*\* (.*?)(?=\s*\*|\Z)', details)
        tech_stack = []
        if tech_match:
            tech_stack = [tech.strip() for tech in tech_match.group(1).split(',')]
        
        project, created = Project.objects.update_or_create(
            title=title,
            defaults={
                'description': description,
                'date': date,
                'tech_stack': tech_stack,
                'screenshots': screenshots,
                'website': website,
                'github': github,
                'figma': figma,
                'status': status,
                'order': i // 2
            }
        )
        print(f"{'Created' if created else 'Updated'} project: {title}")

def sync_experience(content):
    print("\nSyncing Experience...")
    # Find the EXPERIENCE section
    experience_section = re.search(r'### EXPERIENCE(.*?)(### EDUCATION|---|$)', content, re.DOTALL)
    if not experience_section:
        print("Experience section not found")
        return

    exp_content = experience_section.group(1)
    # Split by individual experience items
    # Each experience starts with * **Company Name:** (at the beginning of a line)
    exp_blocks = re.split(r'\n\* \*\*(.*?):\*\*', '\n' + exp_content)
    
    for i in range(1, len(exp_blocks), 2):
        company_name = exp_blocks[i].strip()
        details = exp_blocks[i+1]
        
        # Extract fields using more specific regex
        role_match = re.search(r'\*\*Role:\*\* (.*?)(?:\n|$)', details)
        role = role_match.group(1).strip() if role_match else "Developer"
        
        dates_match = re.search(r'\*\*Dates:\*\* (.*?)(?:\n|$)', details)
        dates_str = dates_match.group(1).strip() if dates_match else ""
        
        # Clean up dates (remove duration like "· 3 mos")
        dates_clean = re.split(r'·', dates_str)[0].strip()
        start_date = dates_clean
        end_date = None
        if ' - ' in dates_clean:
            parts = dates_clean.split(' - ')
            start_date = parts[0].strip()
            end_date = parts[1].strip()

        location_match = re.search(r'\*\*Location:\*\* (.*?)(?:\n|$)', details)
        location = location_match.group(1).strip() if location_match else ""
        
        # Responsibilities are lines starting with -
        responsibilities = re.findall(r'-\s+(.*?)(?:\n|$)', details)
        
        exp, created = Experience.objects.update_or_create(
            company_name=company_name,
            role=role,
            defaults={
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'responsibilities': responsibilities,
                'order': i // 2
            }
        )
        print(f"{'Created' if created else 'Updated'} Experience: {role} at {company_name}")

def main():
    file_path = os.path.join('chatbot', 'portfolio_data.md')
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sync_projects(content)
    sync_experience(content)
    print("\nSync complete!")

if __name__ == "__main__":
    main()
