from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q

from django.utils import timezone
from .models import Profile, Skill, Message, Badge, BadgeAssignment
from .forms import (
    CustomUserCreationForm, ProfileForm, SkillForm, MessageForm,
    VerificationForm, PaymentInfoForm
)
from .utils import paginateProfiles
from projects.ai_matching import find_matching_freelancers

def profiles(request):
    """
    View for displaying profiles with advanced filtering and search capabilities.
    """
    search_query = request.GET.get('search_query', '')
    min_rate = request.GET.get('min_rate')
    max_rate = request.GET.get('max_rate')
    min_rating = request.GET.get('min_rating')
    location = request.GET.get('location')
    skills = request.GET.getlist('skills')
    sort = request.GET.get('sort', '')
    
    # Get all freelancer profiles
    profiles = Profile.objects.filter(user_type__in=['freelancer', 'both'])
    
    # Search functionality
    if search_query:
        profiles = profiles.filter(
            Q(name__icontains=search_query) |
            Q(short_intro__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(skill__name__icontains=search_query)
        ).distinct()
    
    # Filter by hourly rate
    if min_rate:
        profiles = profiles.filter(hourly_rate__gte=float(min_rate))
    if max_rate:
        profiles = profiles.filter(hourly_rate__lte=float(max_rate))
    
    # Filter by rating
    if min_rating:
        profiles = profiles.filter(freelancer_rating__gte=float(min_rating))
    
    # Filter by location
    if location:
        profiles = profiles.filter(location__icontains=location)
    
    # Filter by skills
    if skills:
        for skill in skills:
            profiles = profiles.filter(skill__name__icontains=skill)
    
    # Sorting
    if sort == 'rating':
        profiles = profiles.order_by('-freelancer_rating')
    elif sort == 'hourly_rate_low':
        profiles = profiles.order_by('hourly_rate')
    elif sort == 'hourly_rate_high':
        profiles = profiles.order_by('-hourly_rate')
    else:
        # Default sorting
        profiles = profiles.order_by('-created')
    
    # Get recommended freelancers for authenticated clients
    recommended_freelancers = []
    if request.user.is_authenticated and request.user.profile.user_type in ['client', 'both']:
        try:
            # Get their latest project as a basis for recommendations
            from projects.models import Job
            latest_job = Job.objects.filter(client=request.user.profile).order_by('-created').first()
            
            if latest_job:
                # Find matches using the AI matching algorithm
                from projects.ai_matching import find_matching_freelancers
                freelancer_matches = find_matching_freelancers(latest_job, limit=6)
                recommended_freelancers = [match['profile'] for match in freelancer_matches]
            else:
                # Fallback to top-rated freelancers
                recommended_freelancers = Profile.objects.filter(
                    user_type__in=['freelancer', 'both']
                ).order_by('-freelancer_rating')[:6]
                
        except Exception as e:
            print(f"Error getting recommended freelancers: {e}")
            # Fallback to some top rated freelancers
            recommended_freelancers = Profile.objects.filter(
                user_type__in=['freelancer', 'both']
            ).order_by('-freelancer_rating')[:6]
    
    # Custom pagination
    custom_range, profiles = paginateProfiles(request, profiles, 9)
    
    # Create URL parameters for skills (to be used in pagination)
    skills_params = ""
    for skill in skills:
        skills_params += f"&skills={skill}"
    
    context = {
        'profiles': profiles,
        'search_query': search_query,
        'custom_range': custom_range,
        'min_rate': min_rate,
        'max_rate': max_rate,
        'min_rating': min_rating,
        'location': location,
        'selected_skills': skills,
        'sort': sort,
        'recommended_freelancers': recommended_freelancers,
        'skills_params': skills_params,
    }
    return render(request, 'users/profiles.html', context)


class ProfileDetailView(View):
    def get(self, request, pk):
        profile = Profile.objects.get(id=pk)
        
        # Get top skills (excludes ones with no description)
        top_skills = profile.skill_set.exclude(description__exact="")
        # Get other skills (includes ones with no description)
        other_skills = profile.skill_set.filter(description="")
        
        context = {
            'profile': profile,
            'top_skills': top_skills,
            'other_skills': other_skills
        }
        return render(request, 'users/profile_detail.html', context)


class LoginUserView(View):
    page = 'login'
    
    def get(self, request):
        # If user is already logged in, redirect to profiles page
        if request.user.is_authenticated:
            return redirect('profiles')
        
        return render(request, 'users/login_register.html', {'page': self.page})
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('profiles')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        username = request.POST['username'].lower()
        password = request.POST['password']
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')
            return redirect('login')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'profiles'))
        else:
            messages.error(request, 'Username OR password is incorrect')
            return redirect('login')


class LogoutUserView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.info(request, 'User was logged out')
        return redirect('login')


class RegisterUserView(View):
    page = 'register'
    form = CustomUserCreationForm
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('profiles')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = self.form()
        context = {'page': self.page, 'form': form}
        return render(request, 'users/login_register.html', context)
    
    def post(self, request):
        form = self.form(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            
            messages.success(request, 'User account was created!')
            
            login(request, user)
            return redirect('edit-account')
        else:
            messages.error(request, 'An error has occurred during registration')
            context = {'page': self.page, 'form': form}
            return render(request, 'users/login_register.html', context)


class UserAccountView(LoginRequiredMixin, View):
    def get(self, request):
        profile = request.user.profile
        
        skills = profile.skill_set.all()
        projects = profile.project_set.all()
        
        context = {
            'profile': profile,
            'skills': skills,
            'projects': projects
        }
        return render(request, 'users/account.html', context)


class EditAccountView(LoginRequiredMixin, View):
    form = ProfileForm
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.profile = request.user.profile
    
    def get(self, request):
        form = self.form(instance=self.profile)
        context = {'form': form}
        return render(request, 'users/profile_form.html', context)
    
    def post(self, request):
        form = self.form(request.POST, request.FILES, instance=self.profile)
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Account updated successfully!')
            return redirect('account')
        
        context = {'form': form}
        return render(request, 'users/profile_form.html', context)


@login_required
def createSkill(request):
    profile = request.user.profile
    form = SkillForm()
    
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.owner = profile
            skill.save()
            messages.success(request, 'Skill was added successfully!')
            return redirect('account')
    
    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required
def updateSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    form = SkillForm(instance=skill)
    
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill was updated successfully!')
            return redirect('account')
    
    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required
def deleteSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill was deleted successfully!')
        return redirect('account')
    
    context = {'object': skill}
    return render(request, 'delete_template.html', context)


@login_required
def inbox(request):
    profile = request.user.profile
    messageRequests = profile.received_messages.all()
    unreadCount = messageRequests.filter(is_read=False).count()
    
    context = {
        'messageRequests': messageRequests,
        'unreadCount': unreadCount
    }
    return render(request, 'users/inbox.html', context)


@login_required
def viewMessage(request, pk):
    profile = request.user.profile
    message = profile.received_messages.get(id=pk)
    
    if message.is_read == False:
        message.is_read = True
        message.save()
    
    context = {'message': message}
    return render(request, 'users/message.html', context)


def createMessage(request, pk):
    recipient = Profile.objects.get(id=pk)
    form = MessageForm()
    
    try:
        sender = request.user.profile
    except:
        sender = None
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient
            
            if sender:
                message.name = sender.name
                message.email = sender.email
            
            message.save()
            
            messages.success(request, 'Your message was successfully sent!')
            return redirect('profile', pk=recipient.id)
    
    context = {
        'recipient': recipient,
        'form': form
    }
    return render(request, 'users/message_form.html', context)


class VerificationStatusView(LoginRequiredMixin, View):
    """
    View for displaying the current verification status of a user's profile
    """
    def get(self, request):
        profile = request.user.profile
        
        # Update trust score whenever the verification status page is viewed
        profile.update_trust_score
        
        context = {
            'profile': profile
        }
        return render(request, 'users/verification_status.html', context)


class SubmitVerificationView(LoginRequiredMixin, View):
    """
    View for submitting verification documents
    """
    form_class = VerificationForm
    
    def get(self, request):
        profile = request.user.profile
        form = self.form_class(instance=profile)
        
        context = {
            'form': form,
            'profile': profile
        }
        return render(request, 'users/verification_form.html', context)
    
    def post(self, request):
        profile = request.user.profile
        form = self.form_class(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            verification_form = form.save(commit=False)
            
            # Set verification status to pending
            verification_form.verification_status = 'pending'
            verification_form.verification_submission_date = timezone.now()
            verification_form.save()
            
            # Update trust score after submission
            profile.update_trust_score
            
            messages.success(request, 'Verification documents submitted successfully! Your documents are now under review.')
            return redirect('verification-status')
        
        context = {
            'form': form,
            'profile': profile
        }
        return render(request, 'users/verification_form.html', context)


class PaymentInfoView(LoginRequiredMixin, View):
    """
    View for adding payment information
    """
    form_class = PaymentInfoForm
    
    def get(self, request):
        profile = request.user.profile
        form = self.form_class(instance=profile)
        
        context = {
            'form': form,
            'profile': profile
        }
        return render(request, 'users/payment_info_form.html', context)
    
    def post(self, request):
        profile = request.user.profile
        form = self.form_class(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            
            # Update trust score after adding payment info
            profile.update_trust_score
            
            messages.success(request, 'Payment information updated successfully!')
            return redirect('account')
        
        context = {
            'form': form,
            'profile': profile
        }
        return render(request, 'users/payment_info_form.html', context)
