import os
import django
import re

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projects.models import Project
from experience.models import Experience, Education
from chatbot.models import Profile

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
    experience_section = re.search(r'### EXPERIENCE(.*?)(### EDUCATION|---|$)', content, re.DOTALL)
    if not experience_section:
        print("Experience section not found")
        return

    exp_content = experience_section.group(1)
    exp_blocks = re.split(r'\n\* \*\*(.*?):\*\*', '\n' + exp_content)
    
    for i in range(1, len(exp_blocks), 2):
        company_name = exp_blocks[i].strip()
        details = exp_blocks[i+1]
        
        role_match = re.search(r'\*\*Role:\*\* (.*?)(?:\n|$)', details)
        role = role_match.group(1).strip() if role_match else "Developer"
        
        dates_match = re.search(r'\*\*Dates:\*\* (.*?)(?:\n|$)', details)
        dates_str = dates_match.group(1).strip() if dates_match else ""
        
        dates_clean = re.split(r'·', dates_str)[0].strip()
        start_date = dates_clean
        end_date = None
        if ' - ' in dates_clean:
            parts = dates_clean.split(' - ')
            start_date = parts[0].strip()
            end_date = parts[1].strip()

        location_match = re.search(r'\*\*Location:\*\* (.*?)(?:\n|$)', details)
        location = location_match.group(1).strip() if location_match else ""
        
        responsibilities = re.findall(r'-\s+(.*?)(?:\n|$)', details)
        
        exp, created = Experience.objects.update_or_create(
            company=company_name,
            role=role,
            defaults={
                'location': location,
                'period': dates_str,
                'start_date': start_date,
                'end_date': end_date,
                'responsibilities': responsibilities,
                'order': i // 2
            }
        )
        print(f"{'Created' if created else 'Updated'} Experience: {role} at {company_name}")

def sync_education(content):
    print("\nSyncing Education...")
    edu_section = re.search(r'### EDUCATION(.*?)(---|$)', content, re.DOTALL)
    if not edu_section:
        print("Education section not found")
        return

    edu_content = edu_section.group(1)
    edu_blocks = re.split(r'\n\* \*\*(.*?)\*\*', '\n' + edu_content)
    
    for i in range(1, len(edu_blocks), 2):
        degree = edu_blocks[i].strip()
        details = edu_blocks[i+1]
        
        uni_match = re.search(r'-\s+\*\*University:\*\* (.*?)(?:\n|$)', details)
        uni = uni_match.group(1).strip() if uni_match else ""
        if not uni:
            uni_match = re.search(r'-\s+\*\*School:\*\* (.*?)(?:\n|$)', details)
            uni = uni_match.group(1).strip() if uni_match else ""

        dates_match = re.search(r'-\s+\*\*Dates:\*\* (.*?)(?:\n|$)', details)
        dates = dates_match.group(1).strip() if dates_match else ""
        
        score_match = re.search(r'-\s+\*\*(?:CGPA|Percentage).*?:\*\* (.*?)(?:\n|$)', details)
        score = score_match.group(1).strip() if score_match else ""
        
        edu, created = Education.objects.update_or_create(
            degree=degree,
            institution=uni,
            defaults={
                'period': dates,
                'score': score,
                'order': i // 2
            }
        )
        print(f"{'Created' if created else 'Updated'} Education: {degree}")

def sync_profile(content):
    print("\nSyncing Profile...")
    about_match = re.search(r'### ABOUT (.*?)\n(.*?)(?=---|$)', content, re.DOTALL | re.IGNORECASE)
    if not about_match:
        print("About section not found")
        return
    
    details = about_match.group(2)
    
    name_match = re.search(r'\*\*Name\*\*:\s*(.*?)(?:\n|$)', details)
    name = name_match.group(1).strip() if name_match else "Mann Navlakha"
    
    role_match = re.search(r'\*\*Role:\*\*\s*"(.*?)"', details)
    role = role_match.group(1).strip() if role_match else ""
    
    summary_match = re.search(r'\*\*Summary:\*\*\s*(.*?)(?:\n|$)', details)
    summary = summary_match.group(1).strip() if summary_match else ""
    
    email_match = re.search(r'\*\*Email\*\*:\s*\[.*?\]\(mailto:(.*?)\)', details)
    email = email_match.group(1).strip() if email_match else ""
    
    mobile_match = re.search(r'\*\*Mobile Number\*\*:\s*(.*?)(?:\n|$)', details)
    mobile = mobile_match.group(1).strip() if mobile_match else ""
    
    addr_match = re.search(r'\*\*Address\*\*:\s*(.*?)(?:\n|$)', details)
    address = addr_match.group(1).strip() if addr_match else ""
    
    lang_match = re.search(r'\*\*Languages\*\*:\s*(.*?)(?:\n|$)', details)
    languages = [l.strip() for l in lang_match.group(1).split(',')] if lang_match else []
    
    resume_match = re.search(r'\*\*Resume\*\*:\s*\[.*?\]\((.*?)\)', details)
    resume = resume_match.group(1).strip() if resume_match else ""
    
    photo_match = re.search(r'\*\*Photo\*\*:\s*!\[.*?\]\((.*?)\)', details)
    photo = photo_match.group(1).strip() if photo_match else ""
    
    socials = []
    social_lines = re.findall(r'\*\*([\w\s]+)\*\*:\s*\[.*?\]\((.*?)\)', details)
    for s_name, s_url in social_lines:
        if s_name not in ['Resume', 'Photo', 'email', 'Mobile Number', 'Contact', 'Languages', 'Address']:
            socials.append({"name": s_name.strip(), "url": s_url.strip()})

    # Skills
    skills_match = re.search(r'### SKILLS(.*?)(?=---|$)', content, re.DOTALL)
    skills_dict = {}
    if skills_match:
        skill_lines = re.findall(r'\* \*\*(.*?):\*\*\s*(.*?)(?:\n|$)', skills_match.group(1))
        for category, items in skill_lines:
            skills_dict[category.strip()] = [i.strip() for i in items.split(',')]

    profile, created = Profile.objects.update_or_create(
        name=name,
        defaults={
            'role': role,
            'summary': summary,
            'email': email,
            'phone': mobile,
            'address': address,
            'languages': languages,
            'resume_url': resume,
            'photo_url': photo,
            'social_links': socials,
            'skills': skills_dict
        }
    )
    print(f"{'Created' if created else 'Updated'} Profile for: {name}")

def main():
    file_path = os.path.join('chatbot', 'portfolio_data.md')
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sync_profile(content)
    sync_projects(content)
    sync_experience(content)
    sync_education(content)
    print("\nSync complete!")

if __name__ == "__main__":
    main()
