from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from .models import Profile, Skill

def paginateProfiles(request, profiles, results):
    """
    Helper function to paginate profiles
    """
    page = request.GET.get('page', 1)
    paginator = Paginator(profiles, results)
    
    try:
        profiles = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        profiles = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        profiles = paginator.page(page)
    
    # For pagination template display
    leftIndex = int(page) - 2
    if leftIndex < 1:
        leftIndex = 1
    
    rightIndex = int(page) + 2
    if rightIndex > paginator.num_pages:
        rightIndex = paginator.num_pages
    
    custom_range = range(leftIndex, rightIndex + 1)
    
    return custom_range, profiles


def searchProfiles(request):
    """
    Helper function to search for profiles
    """
    search_query = ''
    
    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')
        
    # Get skills that match search query
    skills = Skill.objects.filter(name__icontains=search_query)
    
    # Get profiles that match search query
    profiles = Profile.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(short_intro__icontains=search_query) |
        Q(bio__icontains=search_query) |
        Q(skill__in=skills) |
        Q(location__icontains=search_query)
    )
    
    return profiles, search_query