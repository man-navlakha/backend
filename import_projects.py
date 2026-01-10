import os
import django
import re

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projects.models import Project

def import_projects():
    file_path = os.path.join('chatbot', 'portfolio_data.md')
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the PROJECTS section
    projects_section = re.search(r'### PROJECTS(.*?)(### EXPERIENCE|---|$)', content, re.DOTALL)
    if not projects_section:
        print("Projects section not found")
        return

    projects_content = projects_section.group(1)
    
    # Split by individual projects
    # Each project starts with * **N. Title:**
    project_blocks = re.split(r'\* \*\*\d+\. (.*?):\*\*', projects_content)
    
    # re.split with one capturing group returns [preamble, group1, postgroup1, group2, postgroup2...]
    # preamble is usually empty or whitespace
    for i in range(1, len(project_blocks), 2):
        title = project_blocks[i].strip()
        details = project_blocks[i+1]
        
        description_match = re.search(r'\*\*Description:\*\* (.*?)(?=\s*\*|\Z)', details, re.DOTALL)
        description = description_match.group(1).strip() if description_match else ""
        
        date_match = re.search(r'\*\*Date:\*\* (.*?)(?=\s*\*|\Z)', details)
        date = date_match.group(1).strip() if date_match else ""
        
        website_match = re.search(r'\[Visit Site\]\((.*?)\)|\[Visit UserSide\]\((.*?)\)', details)
        website = (website_match.group(1) or website_match.group(2)) if website_match else None
        
        github_match = re.search(r'\[View on GitHub\]\((.*?)\)|\[Github UserSide\]\((.*?)\)', details, re.IGNORECASE)
        github = (github_match.group(1) or github_match.group(2)) if github_match else None
        
        figma_match = re.search(r'\[View on Figma\]\((.*?)\)', details)
        figma = figma_match.group(1) if figma_match else None

        status_match = re.search(r'\*\*Status:\*\* (.*?)(?=\s*\*|\Z)', details)
        status = status_match.group(1).strip() if status_match else None

        # Extract screenshots
        screenshots = re.findall(r'!\[.*?\]\((.*?)\)', details)
        
        # Tech stack
        tech_match = re.search(r'\*\*Tech Stack:\*\* (.*?)(?=\s*\*|\Z)', details)
        tech_stack = []
        if tech_match:
            tech_stack = [tech.strip() for tech in tech_match.group(1).split(',')]
        
        # Create or update project
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

if __name__ == "__main__":
    import_projects()
