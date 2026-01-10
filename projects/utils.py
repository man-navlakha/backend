import requests
import os
from datetime import datetime
from django.utils import timezone

def fetch_github_stats(repo_url):
    """
    Fetches stars, forks, and last commit date from GitHub API.
    repo_url: https://github.com/user/repo
    """
    if not repo_url or "github.com" not in repo_url:
        return None

    # Extract owner and repo from URL
    # Handle cases like https://github.com/user/repo/ or https://github.com/user/repo
    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 2:
        return None
    
    repo_name = f"{parts[-2]}/{parts[-1]}"
    api_url = f"https://api.github.com/repos/{repo_name}"
    
    headers = {}
    pat = os.getenv("GITHUB_PAT")
    if pat:
        headers["Authorization"] = f"token {pat}"
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return {
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "updated_at": data.get("pushed_at") # Last commit/push
        }
    except Exception as e:
        print(f"Error fetching GitHub stats for {repo_name}: {e}")
        return None

def update_all_project_stats():
    from .models import Project
    projects = Project.objects.exclude(github__isnull=True).exclude(github__exact='')
    
    count = 0
    for project in projects:
        stats = fetch_github_stats(project.github)
        if stats:
            project.github_stars = stats["stars"]
            project.github_forks = stats["forks"]
            if stats["updated_at"]:
                # Convert ISO 8601 string to timezone-aware datetime
                dt = datetime.strptime(stats["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                project.github_updated_at = timezone.make_aware(dt)
            project.save()
            count += 1
            print(f"Updated stats for {project.title}")
    
    return count
