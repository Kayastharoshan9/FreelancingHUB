from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from .models import Profile, ClientReview, FreelancerReview
from .forms import ClientReviewForm, FreelancerReviewForm
from projects.models import Job, Contract

@login_required
def rate_freelancer(request, profile_id):
    """
    View for a client to rate a freelancer 
    """
    freelancer = get_object_or_404(Profile, id=profile_id)
    client = request.user.profile
    
    # Verify that the current user is a client
    if client.user_type not in ['client', 'both']:
        messages.error(request, "Only clients can rate freelancers.")
        return redirect('profile', pk=profile_id)
    
    # Prevent self-rating
    if client.id == freelancer.id:
        messages.error(request, "You cannot rate yourself.")
        return redirect('profile', pk=profile_id)
    
    if request.method == 'POST':
        # Get rating and review from POST data
        rating = request.POST.get('rating')
        comment = request.POST.get('review')
        
        if not rating:
            messages.error(request, "Please provide a rating.")
            return redirect('profile', pk=profile_id)
        
        # Create or update the review
        review, created = ClientReview.objects.update_or_create(
            reviewer=client,
            freelancer=freelancer,
            defaults={
                'rating': rating,
                'comment': comment,
                'updated': timezone.now()
            }
        )
        
        if created:
            review.created = timezone.now()
            review.save()
        
        # Update freelancer's average rating
        freelancer.calculate_freelancer_rating()
        
        messages.success(request, "Your review has been submitted!")
        return redirect('profile', pk=profile_id)
    
    # Redirect to profile if not a POST request
    return redirect('profile', pk=profile_id)

@login_required
def rate_client(request, profile_id):
    """
    View for a freelancer to rate a client
    """
    client = get_object_or_404(Profile, id=profile_id)
    freelancer = request.user.profile
    
    # Verify that the current user is a freelancer
    if freelancer.user_type not in ['freelancer', 'both']:
        messages.error(request, "Only freelancers can rate clients.")
        return redirect('profile', pk=profile_id)
    
    # Prevent self-rating
    if freelancer.id == client.id:
        messages.error(request, "You cannot rate yourself.")
        return redirect('profile', pk=profile_id)
    
    if request.method == 'POST':
        # Get rating and review from POST data
        rating = request.POST.get('rating')
        comment = request.POST.get('review')
        
        if not rating:
            messages.error(request, "Please provide a rating.")
            return redirect('profile', pk=profile_id)
        
        # Create or update the review
        review, created = FreelancerReview.objects.update_or_create(
            reviewer=freelancer,
            client=client,
            defaults={
                'rating': rating,
                'comment': comment,
                'updated': timezone.now()
            }
        )
        
        if created:
            review.created = timezone.now()
            review.save()
        
        # Update client's average rating
        client.calculate_client_rating()
        
        messages.success(request, "Your review has been submitted!")
        return redirect('profile', pk=profile_id)
    
    # Redirect to profile if not a POST request
    return redirect('profile', pk=profile_id)