from .models import Profile, Message

def user_profile(request):
    """
    Add the user's profile to the context. Handles cases where a user's profile
    might not be set up. Also adds unread message count for the navbar.
    """
    context = {'profile': None, 'unread_count': 0}
    
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            unread_count = Message.objects.filter(recipient=profile, is_read=False).count()
            
            # Get suggested freelancers if the user is a client
            suggested_freelancers = []
            if profile.user_type in ['client', 'both']:
                suggested_freelancers = Profile.objects.filter(
                    user_type__in=['freelancer', 'both']
                ).exclude(id=profile.id).order_by('-freelancer_rating')[:3]
            
            # Get projects for recommendation
            projects = []
            try:
                from projects.models import Project
                projects = Project.objects.all().order_by('-created')[:6]
            except:
                pass
            
            context = {
                'profile': profile, 
                'unread_count': unread_count,
                'suggested_freelancers': suggested_freelancers,
                'projects': projects
            }
        except Profile.DoesNotExist:
            pass
    
    return context