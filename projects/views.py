from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Avg, Count, Sum
from django.conf import settings

from .models import Project, Tag, Review, Job, Bid, Milestone, Payment, ClientReview, FreelancerReview
from .forms import ProjectForm, ReviewForm, JobForm, BidForm, MilestoneForm, ClientReviewForm, FreelancerReviewForm
from users.models import Profile
from .ai_matching import find_matching_projects, find_matching_freelancers, calculate_match_score

import uuid
from itertools import chain


def home(request):
    """
    View for home page, showing featured projects and jobs.
    """
    featured_projects = Project.objects.all().order_by('-vote_total')[:6]
    latest_jobs = Job.objects.all().order_by('-created')[:4]
    
    context = {
        'featured_projects': featured_projects,
        'latest_jobs': latest_jobs,
    }
    return render(request, 'home.html', context)

def projects(request):
    """
    View for displaying projects and recommended projects if user is logged in.
    """
    search_query = request.GET.get('search', '')
    if search_query:
        projects = Project.objects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(owner__name__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    else:
        projects = Project.objects.all()

    # Get recommended projects for logged-in users
    recommended_projects = []
    if request.user.is_authenticated:
        try:
            # Get recommended projects based on user's profile
            user_profile = request.user.profile
            if user_profile.user_type == 'freelancer':
                # For freelancers, find matching projects
                project_matches = find_matching_projects(user_profile, limit=6)
                # Extract just the project objects from the matches
                recommended_projects = [match['project'] for match in project_matches]
            else:
                # For clients, show popular projects
                recommended_projects = Project.objects.all().order_by('-vote_ratio', '-vote_total')[:6]
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            # Fallback to popular projects
            recommended_projects = Project.objects.all().order_by('-created')[:6]

    context = {
        'projects': projects,
        'recommended_projects': recommended_projects
    }
    return render(request, 'projects/projects.html', context)


def project(request, pk):
    """
    View for displaying a single project.
    """
    project = get_object_or_404(Project, id=pk)
    form = ReviewForm()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        review = form.save(commit=False)
        review.project = project
        review.owner = request.user.profile
        review.save()

        project.getVoteCount

        messages.success(request, 'Your review was successfully submitted!')
        return redirect('project', pk=project.id)
        
    similar_projects = Project.objects.filter(
        Q(tags__in=project.tags.all()) & 
        ~Q(id=project.id)
    ).distinct()[:3]

    return render(request, 'projects/single-project.html', 
                 {'project': project, 'form': form, 'similar_projects': similar_projects})


@login_required(login_url="login")
def createProject(request):
    profile = request.user.profile
    form = ProjectForm()

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = profile
            
            # Save the project first to be able to add many-to-many relationships
            project.save()
            
            # Handle tags from the form
            form.save_m2m()
            
            # Process any price information
            price = form.cleaned_data.get('price')
            if price:
                # Here you could add logic to handle the price 
                # e.g., create a ProjectPrice model instance or similar
                pass
                
            messages.success(request, 'Project created successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'projects/project_form.html', context)


@login_required(login_url="login")
def updateProject(request, pk):
    profile = request.user.profile
    project = get_object_or_404(profile.project_set, id=pk)
    form = ProjectForm(instance=project)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('account')

    context = {'form': form, 'project': project}
    return render(request, 'projects/project_form.html', context)


@login_required(login_url="login")
def deleteProject(request, pk):
    profile = request.user.profile
    project = get_object_or_404(profile.project_set, id=pk)
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('account')
        
    context = {'object': project}
    return render(request, 'projects/delete_template.html', context)


# Job views
@login_required(login_url="login")
def jobs(request):
    """View for displaying jobs"""
    # Filter jobs based on search query
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = Job.objects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(required_skills__name__icontains=search_query)  # Search by tag name
        ).distinct()
    else:
        jobs = Job.objects.all().order_by('-created')
        
    # Get matching jobs for freelancers
    matching_jobs = []
    if request.user.is_authenticated and request.user.profile.user_type in ['freelancer', 'both']:
        try:
            # Find jobs that match the freelancer's skills
            freelancer_skills = [skill.name.lower() for skill in request.user.profile.skill_set.all()]
            if freelancer_skills:
                matching_jobs = Job.objects.filter(
                    Q(status='open') & 
                    (Q(required_skills__name__in=freelancer_skills) |
                     Q(title__icontains=' '.join(freelancer_skills)))
                ).distinct().order_by('-created')[:4]
        except Exception as e:
            print(f"Error getting matching jobs: {e}")
    
    context = {
        'jobs': jobs,
        'matching_jobs': matching_jobs,
        'search_query': search_query
    }
    return render(request, 'projects/jobs.html', context)


@login_required(login_url="login")
def job(request, pk):
    """View for a single job with bidding functionality"""
    job = get_object_or_404(Job, id=pk)
    
    # Handle bid form submission
    if request.method == 'POST' and request.user.profile.user_type in ['freelancer', 'both']:
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.job = job
            bid.freelancer = request.user.profile
            bid.save()
            messages.success(request, 'Your bid has been submitted successfully!')
            return redirect('job', pk=job.id)
    else:
        form = BidForm()
    
    # Check if the current user has already placed a bid
    user_has_bid = False
    user_bid = None
    if request.user.is_authenticated and request.user.profile.user_type in ['freelancer', 'both']:
        user_bid = Bid.objects.filter(job=job, freelancer=request.user.profile).first()
        user_has_bid = user_bid is not None
    
    # Get similar jobs based on required skills
    similar_jobs = []
    if job.required_skills.exists():
        similar_jobs = Job.objects.filter(
            required_skills__in=job.required_skills.all()
        ).exclude(id=job.id).distinct()[:3]
    
    context = {
        'job': job,
        'form': form,
        'user_has_bid': user_has_bid,
        'user_bid': user_bid,
        'similar_jobs': similar_jobs
    }
    return render(request, 'projects/job.html', context)

@login_required(login_url="login")
def createJob(request):
    """View for clients to create a new job posting"""
    profile = request.user.profile
    
    # Only clients or 'both' profiles can create jobs
    if profile.user_type not in ['client', 'both']:
        messages.error(request, 'Only clients can post jobs!')
        return redirect('jobs')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = profile
            job.save()
            messages.success(request, 'Job posting created successfully!')
            return redirect('jobs')
    else:
        form = JobForm()
    
    context = {'form': form}
    return render(request, 'projects/job_form.html', context)

@login_required(login_url="login")
def updateJob(request, pk):
    """View for clients to update their job posting"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=pk, client=profile)
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job posting updated successfully!')
            return redirect('jobs')
    else:
        form = JobForm(instance=job)
    
    context = {'form': form, 'job': job}
    return render(request, 'projects/job_form.html', context)

@login_required(login_url="login")
def deleteJob(request, pk):
    """View for clients to delete their job posting"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=pk, client=profile)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job posting deleted successfully!')
        return redirect('jobs')
    
    context = {'object': job}
    return render(request, 'projects/delete_template.html', context)

@login_required(login_url="login")
def createBid(request, job_id):
    """View for freelancers to create a bid for a job"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=job_id)
    
    # Only freelancers or 'both' profiles can create bids
    if profile.user_type not in ['freelancer', 'both']:
        messages.error(request, 'Only freelancers can submit bids!')
        return redirect('job', pk=job.id)
    
    # Check if user already has a bid for this job
    existing_bid = Bid.objects.filter(job=job, freelancer=profile).first()
    if existing_bid:
        messages.error(request, 'You have already submitted a bid for this job!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.job = job
            bid.freelancer = profile
            bid.save()
            messages.success(request, 'Your bid has been submitted successfully!')
            return redirect('job', pk=job.id)
    else:
        form = BidForm(job=job)  # Pass job to the form for customized help_text
    
    context = {'form': form, 'job': job}
    return render(request, 'projects/bid_form.html', context)

@login_required(login_url="login")
def updateBid(request, pk):
    """View for freelancers to update their bid"""
    profile = request.user.profile
    bid = get_object_or_404(Bid, id=pk, freelancer=profile)
    
    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES, instance=bid)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your bid has been updated successfully!')
            return redirect('job', pk=bid.job.id)
    else:
        form = BidForm(instance=bid)
    
    context = {'form': form, 'bid': bid}
    return render(request, 'projects/bid_form.html', context)

@login_required(login_url="login")
def deleteBid(request, pk):
    """View for freelancers to delete their bid"""
    profile = request.user.profile
    bid = get_object_or_404(Bid, id=pk, freelancer=profile)
    job_id = bid.job.id
    
    if request.method == 'POST':
        bid.delete()
        messages.success(request, 'Your bid has been withdrawn successfully!')
        return redirect('job', pk=job_id)
    
    context = {'object': bid}
    return render(request, 'projects/delete_template.html', context)

@login_required(login_url="login")
def acceptBid(request, pk):
    """View for clients to accept a bid for their job"""
    profile = request.user.profile
    bid = get_object_or_404(Bid, id=pk)
    job = bid.job
    
    # Check if user is the job owner
    if job.client != profile:
        messages.error(request, 'You are not authorized to accept this bid!')
        return redirect('job', pk=job.id)
    
    # Check if job already has an accepted bid
    if job.status != 'open':
        messages.error(request, 'This job already has an accepted bid!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        # Accept the bid and change job status
        bid.status = 'accepted'
        bid.save()
        job.status = 'in_progress'
        job.freelancer = bid.freelancer
        job.save()
        
        # Send notification to the freelancer
        messages.success(request, f'Bid from {bid.freelancer.name} has been accepted!')
        return redirect('job', pk=job.id)
    
    context = {'bid': bid, 'job': job}
    return render(request, 'projects/accept_bid.html', context)

@login_required(login_url="login")
def createMilestone(request, job_id):
    """View for creating milestones for a job"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is either the client or the freelancer for this job
    if job.client != profile and job.freelancer != profile:
        messages.error(request, 'You are not authorized to add milestones to this job!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.job = job
            milestone.created_by = profile
            milestone.save()
            messages.success(request, 'Milestone added successfully!')
            return redirect('job', pk=job.id)
    else:
        form = MilestoneForm()
    
    context = {'form': form, 'job': job}
    return render(request, 'projects/milestone_form.html', context)

@login_required(login_url="login")
def updateMilestone(request, pk):
    """View for updating a milestone"""
    profile = request.user.profile
    milestone = get_object_or_404(Milestone, id=pk)
    job = milestone.job
    
    # Check if user is either the client or the freelancer for this job
    if job.client != profile and job.freelancer != profile:
        messages.error(request, 'You are not authorized to update this milestone!')
        return redirect('job', pk=job.id)
    
    # Don't allow updates to completed milestones
    if milestone.status == 'completed':
        messages.error(request, 'Completed milestones cannot be updated!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        form = MilestoneForm(request.POST, instance=milestone)
        if form.is_valid():
            form.save()
            messages.success(request, 'Milestone updated successfully!')
            return redirect('job', pk=job.id)
    else:
        form = MilestoneForm(instance=milestone)
    
    context = {'form': form, 'milestone': milestone, 'job': job}
    return render(request, 'projects/milestone_form.html', context)

@login_required(login_url="login")
def deleteMilestone(request, pk):
    """View for deleting a milestone"""
    profile = request.user.profile
    milestone = get_object_or_404(Milestone, id=pk)
    job = milestone.job
    
    # Check if user is either the client or the created_by for this milestone
    if job.client != profile and milestone.created_by != profile:
        messages.error(request, 'You are not authorized to delete this milestone!')
        return redirect('job', pk=job.id)
    
    # Don't allow deletion of funded or completed milestones
    if milestone.status in ['funded', 'completed']:
        messages.error(request, f'{milestone.status.title()} milestones cannot be deleted!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        milestone.delete()
        messages.success(request, 'Milestone deleted successfully!')
        return redirect('job', pk=job.id)
    
    context = {'object': milestone}
    return render(request, 'projects/delete_template.html', context)

@login_required(login_url="login")
def completeMilestone(request, pk):
    """View for freelancers to mark a milestone as completed"""
    profile = request.user.profile
    milestone = get_object_or_404(Milestone, id=pk)
    job = milestone.job
    
    # Check if user is the freelancer for this job
    if job.freelancer != profile:
        messages.error(request, 'Only the assigned freelancer can mark milestones as completed!')
        return redirect('job', pk=job.id)
    
    # Check if milestone is funded
    if milestone.status != 'funded':
        messages.error(request, 'Only funded milestones can be marked as completed!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        milestone.status = 'completed'
        milestone.completion_date = timezone.now()
        milestone.save()
        
        messages.success(request, 'Milestone marked as completed! The client can now release the payment.')
        return redirect('job', pk=job.id)
    
    context = {'milestone': milestone, 'job': job}
    return render(request, 'projects/complete_milestone.html', context)

@login_required(login_url="login")
def createClientReview(request, job_id):
    """View for clients to review freelancers after job completion"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the client for this job
    if job.client != profile:
        messages.error(request, 'Only the client can review the freelancer!')
        return redirect('job', pk=job.id)
    
    # Check if job is completed
    if job.status != 'completed':
        messages.error(request, 'You can only review after the job is completed!')
        return redirect('job', pk=job.id)
    
    # Check if client has already reviewed this job
    if FreelancerReview.objects.filter(job=job, client=profile).exists():
        messages.error(request, 'You have already reviewed this freelancer!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        form = FreelancerReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.job = job
            review.client = profile
            review.freelancer = job.freelancer
            review.save()
            
            # Update freelancer's ratings
            job.freelancer.update_ratings()
            
            messages.success(request, 'Thank you for your review!')
            return redirect('job', pk=job.id)
    else:
        form = FreelancerReviewForm()
    
    context = {'form': form, 'job': job, 'freelancer': job.freelancer}
    return render(request, 'projects/review_form.html', context)

@login_required(login_url="login")
def createFreelancerReview(request, job_id):
    """View for freelancers to review clients after job completion"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the freelancer for this job
    if job.freelancer != profile:
        messages.error(request, 'Only the freelancer can review the client!')
        return redirect('job', pk=job.id)
    
    # Check if job is completed
    if job.status != 'completed':
        messages.error(request, 'You can only review after the job is completed!')
        return redirect('job', pk=job.id)
    
    # Check if freelancer has already reviewed this job
    if ClientReview.objects.filter(job=job, freelancer=profile).exists():
        messages.error(request, 'You have already reviewed this client!')
        return redirect('job', pk=job.id)
    
    if request.method == 'POST':
        form = ClientReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.job = job
            review.freelancer = profile
            review.client = job.client
            review.save()
            
            # Update client's ratings
            job.client.update_ratings()
            
            messages.success(request, 'Thank you for your review!')
            return redirect('job', pk=job.id)
    else:
        form = ClientReviewForm()
    
    context = {'form': form, 'job': job, 'client': job.client}
    return render(request, 'projects/review_form.html', context)

# AI Matching Dashboard view
@login_required(login_url="login")
def ai_matching_dashboard(request):
    """
    View for displaying AI-powered matching recommendations
    """
    profile = request.user.profile
    
    # For clients: show matching freelancers for their latest job
    if profile.user_type in ['client', 'both']:
        latest_jobs = Job.objects.filter(client=profile).order_by('-created')[:3]
        
        # Get matching freelancers for each job
        job_matches = []
        for job in latest_jobs:
            try:
                # Find top 3 matching freelancers for this job
                freelancer_matches = find_matching_freelancers(job, limit=3)
                # Extract just the freelancer profile objects and scores
                matches = [
                    {
                        'profile': match['profile'],
                        'score': match['score'],
                        'reasons': match['reasons'][:1] if match['reasons'] else []  # Just the top reason
                    } for match in freelancer_matches
                ]
                
                job_matches.append({
                    'job': job,
                    'matches': matches
                })
            except Exception as e:
                print(f"Error finding matches for job {job.title}: {e}")
    else:
        job_matches = []
    
    # For freelancers: show matching projects
    if profile.user_type in ['freelancer', 'both']:
        try:
            # Find matching projects for this freelancer
            project_matches = find_matching_projects(profile, limit=6)
            # Extract just the project objects and scores
            matching_projects = [
                {
                    'project': match['project'],
                    'score': match['score'],
                    'reasons': match['reasons'][:1] if match['reasons'] else []  # Just the top reason
                } for match in project_matches
            ]
        except Exception as e:
            print(f"Error finding matching projects: {e}")
            matching_projects = []
    else:
        matching_projects = []
    
    context = {
        'profile': profile,
        'job_matches': job_matches,
        'matching_projects': matching_projects
    }
    
    return render(request, 'projects/ai_matching.html', context)

@login_required(login_url="login")
def job_matching_results(request, job_id):
    """
    View for displaying freelancers that match a specific job
    """
    job = get_object_or_404(Job, id=job_id)
    
    # Only allow the job owner to view this page
    if job.client != request.user.profile:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('jobs')
    
    # Get matching freelancers
    try:
        freelancer_matches = find_matching_freelancers(job, limit=10)
        # Extract the freelancer profiles and their match scores
        matches = [
            {
                'profile': match['profile'],
                'score': match['score'],
                'reasons': match['reasons']
            } for match in freelancer_matches
        ]
    except Exception as e:
        print(f"Error finding matching freelancers: {e}")
        matches = []
    
    context = {
        'job': job,
        'matches': matches
    }
    return render(request, 'projects/job_matching_results.html', context)

@login_required(login_url="login")
def review_and_release_payment(request, job_id, milestone_id):
    """Combined view for clients to review freelancers and release payments in one step"""
    profile = request.user.profile
    job = get_object_or_404(Job, id=job_id)
    milestone = get_object_or_404(Milestone, id=milestone_id, job=job)
    
    # Check if user is the client for this job
    if job.client != profile:
        messages.error(request, 'Only clients can review freelancers and release payments!')
        return redirect('job', pk=job.id)
    
    # Check if job is completed or milestone is completed
    if not milestone.is_completed:
        messages.error(request, 'The milestone must be marked as completed before releasing payment!')
        return redirect('job', pk=job.id)
    
    # Get the payment associated with this milestone
    payment = get_object_or_404(Payment, milestone=milestone, status='escrow')
    
    if request.method == 'POST':
        form = ClientReviewForm(request.POST)
        if form.is_valid():
            # Create the review
            review = form.save(commit=False)
            review.job = job
            review.client = profile
            review.freelancer = job.freelancer
            review.save()
            
            # Release the payment
            payment.status = 'released'
            payment.save()
            
            # Update freelancer's ratings
            job.freelancer.update_ratings()
            
            # Check if all milestones are complete and paid
            all_milestones_complete = all(m.is_completed for m in job.milestones.all())
            all_payments_released = not Payment.objects.filter(
                milestone__job=job, 
                status='escrow'
            ).exists()
            
            # If all milestones are complete and all payments released, mark job as complete
            if all_milestones_complete and all_payments_released and job.status != 'completed':
                job.status = 'completed'
                job.save()
            
            messages.success(request, 'Thank you for your review! Payment has been released to the freelancer.')
            return redirect('job', pk=job.id)
    else:
        form = ClientReviewForm()
    
    context = {
        'form': form, 
        'job': job, 
        'milestone': milestone,
        'payment': payment,
        'freelancer': job.freelancer
    }
    return render(request, 'projects/review_and_release.html', context)

# Add Django timezone
from django.utils import timezone

@login_required(login_url="login")
def transaction_dashboard(request):
    """View for users to track all their payment transactions"""
    profile = request.user.profile
    
    # Get payments based on user type
    client_payments = Payment.objects.filter(client=profile).select_related('milestone', 'milestone__job', 'freelancer')
    freelancer_payments = Payment.objects.filter(freelancer=profile).select_related('milestone', 'milestone__job', 'client')
    
    # Pre-filter payments by status
    client_escrow_payments = client_payments.filter(status='escrow')
    freelancer_escrow_payments = freelancer_payments.filter(status='escrow')
    
    # Get payment statistics
    stats = {
        'total_paid': client_payments.filter(status='released').aggregate(total=Sum('amount'))['total'] or 0,
        'total_received': freelancer_payments.filter(status='released').aggregate(total=Sum('amount'))['total'] or 0,
        'in_escrow_client': client_payments.filter(status='escrow').aggregate(total=Sum('amount'))['total'] or 0,
        'in_escrow_freelancer': freelancer_payments.filter(status='escrow').aggregate(total=Sum('amount'))['total'] or 0,
        'pending_release': client_payments.filter(status='escrow', milestone__is_completed=True).count(),
        'pending_completion': freelancer_payments.filter(status='escrow', milestone__is_completed=False).count(),
    }
    
    # Prepare transaction history (last 20 transactions)
    all_payments = list(chain(client_payments, freelancer_payments))
    all_payments.sort(key=lambda x: x.created, reverse=True)
    transaction_history = all_payments[:20]
    
    context = {
        'client_payments': client_payments,
        'freelancer_payments': freelancer_payments,
        'client_escrow_payments': client_escrow_payments,
        'freelancer_escrow_payments': freelancer_escrow_payments,
        'stats': stats,
        'transaction_history': transaction_history,
        'profile': profile
    }
    
    return render(request, 'projects/transaction_dashboard.html', context)
