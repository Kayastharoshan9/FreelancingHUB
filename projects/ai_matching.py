import json
import os
from openai import OpenAI
from django.db.models import Q
from django.conf import settings
from users.models import Profile, Skill
from projects.models import Project, Tag

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', '')

# Fall back to environment variable if not in settings
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", '')

# Add a fallback mechanism to handle missing API key gracefully
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not set. AI recommendations will not work correctly.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_project_embedding(project):
    """Get embedding for a project based on its description and tags"""
    project_text = f"Project Title: {project.title}\n"
    project_text += f"Description: {project.description}\n"
    
    # Add tags
    tags = list(project.tags.all())
    if tags:
        project_text += "Tags: " + ", ".join([tag.name for tag in tags]) + "\n"
    
    return project_text

def get_freelancer_embedding(profile):
    """Get embedding for a freelancer based on bio, skills, and completed projects"""
    freelancer_text = f"Freelancer: {profile.name}\n"
    
    if profile.short_intro:
        freelancer_text += f"Short Introduction: {profile.short_intro}\n"
    
    if profile.bio:
        freelancer_text += f"Biography: {profile.bio}\n"
    
    # Add skills
    skills = list(Skill.objects.filter(owner=profile))
    if skills:
        freelancer_text += "Skills: " + ", ".join([skill.name for skill in skills]) + "\n"
        
    # Add skill descriptions for more context
    for skill in skills:
        if skill.description:
            freelancer_text += f"- {skill.name}: {skill.description}\n"
    
    # Add past projects if available
    projects = list(Project.objects.filter(owner=profile))
    if projects:
        freelancer_text += "Past Projects: " + ", ".join([project.title for project in projects]) + "\n"
    
    return freelancer_text

def calculate_match_score(project, freelancer_profile):
    """Calculate a match score between a project and freelancer using OpenAI"""
    try:
        # If OpenAI API key is not set, use a fallback method
        if not OPENAI_API_KEY:
            # Fallback to a simple keyword matching algorithm
            project_text = project.title + " " + project.description
            freelancer_text = freelancer_profile.bio or "" + " " + freelancer_profile.short_intro or ""
            
            # Get freelancer skills
            skills = Skill.objects.filter(owner=freelancer_profile).values_list('name', flat=True)
            skill_names = [skill.lower() for skill in skills]
            
            # Get project tags
            tags = project.tags.all().values_list('name', flat=True)
            tag_names = [tag.lower() for tag in tags]
            
            # Calculate a simple match score based on keyword overlap
            score = 50  # Base score
            
            # Skill-tag match bonus
            matched_skills = set(skill_names).intersection(set(tag_names))
            skill_match_score = len(matched_skills) * 10
            
            # Text similarity (very basic)
            word_match_count = 0
            for word in skill_names:
                if word in project_text.lower():
                    word_match_count += 1
            
            # Final score calculation
            final_score = min(100, score + skill_match_score + word_match_count * 5)
            
            return {
                "score": final_score,
                "reasons": [
                    f"Matched {len(matched_skills)} skills/tags", 
                    f"Found {word_match_count} skill keywords in project description",
                    "Using fallback algorithm (OpenAI API key not set)"
                ]
            }
        
        # Otherwise use OpenAI for scoring
        project_text = get_project_embedding(project)
        freelancer_text = get_freelancer_embedding(freelancer_profile)
        
        prompt = (
            "As an expert freelance matching algorithm, analyze the compatibility between the "
            "following project and freelancer profile. Rate the match on a scale of 0 to 100, "
            "where 0 is no match and 100 is a perfect match. Also provide up to 3 specific reasons "
            "for your rating. Respond in JSON format with 'score' and 'reasons' keys.\n\n"
            f"PROJECT INFORMATION:\n{project_text}\n\n"
            f"FREELANCER INFORMATION:\n{freelancer_text}"
        )
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"Error calculating match score: {e}")
        # Return a basic result without using the API in case of error
        return {
            "score": 50,
            "reasons": ["Error processing match score", str(e)]
        }

def find_matching_projects(freelancer_profile, limit=5):
    """Find projects that match a freelancer's profile"""
    # First get basic keyword matches from skills to project tags
    skill_names = Skill.objects.filter(owner=freelancer_profile).values_list('name', flat=True)
    
    # Start with basic filtering
    matching_projects = Project.objects.filter(
        Q(tags__name__in=skill_names) |
        Q(description__icontains=' '.join(skill_names))
    ).distinct()
    
    # Then enhance with AI matching
    project_matches = []
    
    # Process up to 10 projects with AI to get better matches
    projects_to_process = list(matching_projects[:10])
    
    # If we don't have enough keyword matches, add some other projects
    if len(projects_to_process) < 5:
        other_projects = Project.objects.exclude(id__in=[p.id for p in projects_to_process])[:10-len(projects_to_process)]
        projects_to_process.extend(other_projects)
    
    for project in projects_to_process:
        match_result = calculate_match_score(project, freelancer_profile)
        
        project_matches.append({
            'project': project,
            'score': match_result.get('score', 0),
            'reasons': match_result.get('reasons', [])
        })
    
    # Sort by match score (descending)
    project_matches.sort(key=lambda x: x['score'], reverse=True)
    
    return project_matches[:limit]

def find_matching_freelancers(project, limit=5):
    """Find freelancers that match a project's requirements"""
    # Start with basic filtering based on tags
    tags = project.tags.all().values_list('name', flat=True)
    
    # Get profiles with matching skills
    matching_profiles = Profile.objects.filter(
        Q(skill__name__in=tags) |
        Q(bio__icontains=' '.join(tags)) |
        Q(short_intro__icontains=' '.join(tags))
    ).distinct()
    
    # Only include freelancer profiles (not just clients)
    matching_profiles = matching_profiles.filter(
        Q(user_type='freelancer') | Q(user_type='both')
    ).distinct()
    
    # Enhance with AI matching
    freelancer_matches = []
    
    # Process up to 10 freelancers with AI
    profiles_to_process = list(matching_profiles[:10])
    
    # If we don't have enough keyword matches, add some other freelancers
    if len(profiles_to_process) < 5:
        other_profiles = Profile.objects.filter(
            Q(user_type='freelancer') | Q(user_type='both')
        ).exclude(id__in=[p.id for p in profiles_to_process])[:10-len(profiles_to_process)]
        profiles_to_process.extend(other_profiles)
    
    for profile in profiles_to_process:
        match_result = calculate_match_score(project, profile)
        
        freelancer_matches.append({
            'profile': profile,
            'score': match_result.get('score', 0),
            'reasons': match_result.get('reasons', [])
        })
    
    # Sort by match score (descending)
    freelancer_matches.sort(key=lambda x: x['score'], reverse=True)
    
    return freelancer_matches[:limit]