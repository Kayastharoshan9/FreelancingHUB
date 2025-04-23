"""
Advanced Rating Algorithm for FreelanceHub users
This module enhances the basic rating system with:
1. Time-weighted ratings (more recent reviews have greater impact)
2. Project complexity factors 
3. Reliability metrics
4. Analytics for rating trends
"""

import datetime
from django.utils import timezone
from projects.models import ClientReview, FreelancerReview, Job, Milestone
from users.models import Profile

def get_time_weighted_rating(reviews, days_halflife=180):
    """
    Calculate a time-weighted rating where more recent reviews have greater impact.
    The weight of each review decreases by half after days_halflife days.
    """
    if not reviews:
        return 0
    
    now = timezone.now()
    total_weight = 0
    weighted_sum = 0
    
    for review in reviews:
        # Calculate days since the review
        days_since = (now - review.created).days
        # Calculate weight using exponential decay
        weight = 2 ** (-days_since / days_halflife)
        
        weighted_sum += review.rating * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0
        
    return round(weighted_sum / total_weight, 2)

def get_project_complexity_factor(job):
    """
    Calculate a complexity factor for the job based on:
    - Budget
    - Duration
    - Number of milestones
    - Skill requirements
    """
    try:
        # Base complexity starts at 1.0
        complexity = 1.0
        
        # Budget impact (higher budget = higher complexity)
        if job.budget_max:
            if job.budget_max > 5000:
                complexity += 0.3
            elif job.budget_max > 1000:
                complexity += 0.2
            elif job.budget_max > 500:
                complexity += 0.1
        
        # Duration impact (longer jobs are more complex)
        if job.deadline:
            days_duration = (job.deadline - job.created.date()).days
            if days_duration > 90:
                complexity += 0.3
            elif days_duration > 30:
                complexity += 0.2
            elif days_duration > 14:
                complexity += 0.1
        
        # Milestone count impact
        milestone_count = Milestone.objects.filter(job=job).count()
        if milestone_count > 5:
            complexity += 0.3
        elif milestone_count > 3:
            complexity += 0.2
        elif milestone_count > 1:
            complexity += 0.1
        
        # Skill requirements impact
        skill_count = job.required_skills.count()
        if skill_count > 5:
            complexity += 0.3
        elif skill_count > 3:
            complexity += 0.2
        elif skill_count > 1:
            complexity += 0.1
        
        return complexity
    except Exception:
        # If there's any error, return default complexity
        return 1.0

def calculate_freelancer_reliability(profile):
    """
    Calculate a reliability score for freelancers based on:
    - On-time delivery percentage
    - Response rate
    - Milestone completion rate
    - Extended deadlines
    """
    reliability_score = 0
    completed_jobs = Job.objects.filter(
        freelancer=profile, 
        status='completed'
    )
    
    if not completed_jobs.exists():
        return 0
    
    total_jobs = completed_jobs.count()
    
    # On-time delivery percentage (40% weight)
    on_time_jobs = 0
    milestone_completion = 0
    total_milestones = 0
    extended_deadlines = 0
    
    for job in completed_jobs:
        # Check if job was completed on time
        if job.completion_date and job.deadline:
            if job.completion_date.date() <= job.deadline:
                on_time_jobs += 1
        
        # Check milestone completion
        job_milestones = Milestone.objects.filter(job=job)
        total_milestones += job_milestones.count()
        
        for milestone in job_milestones:
            if milestone.is_completed:
                milestone_completion += 1
                
            # Check for deadline extensions
            if milestone.due_date_extended:
                extended_deadlines += 1
    
    # Calculate component scores
    if total_jobs > 0:
        on_time_score = (on_time_jobs / total_jobs) * 40
        reliability_score += on_time_score
    
    if total_milestones > 0:
        milestone_score = (milestone_completion / total_milestones) * 40
        reliability_score += milestone_score
        
        # Penalize for extended deadlines
        extension_penalty = min(20, (extended_deadlines / total_milestones) * 20)
        reliability_score -= extension_penalty
    
    # Response rate (based on message response times - dummy calculation for now)
    reliability_score += 20  # Default response score
    
    return min(100, reliability_score)

def calculate_client_reliability(profile):
    """
    Calculate a reliability score for clients based on:
    - Payment promptness
    - Clear specifications
    - Response rate
    - Milestone approval time
    """
    reliability_score = 0
    client_jobs = Job.objects.filter(
        client=profile
    )
    
    if not client_jobs.exists():
        return 0
        
    total_jobs = client_jobs.count()
    
    # Payment promptness (40% weight)
    prompt_payments = 0
    milestone_approvals = 0
    total_completed_milestones = 0
    specification_changes = 0
    
    for job in client_jobs:
        # Check for payment promptness
        job_milestones = Milestone.objects.filter(job=job, is_completed=True)
        total_completed_milestones += job_milestones.count()
        
        for milestone in job_milestones:
            # If payment was made within 3 days of completion
            if milestone.payment and milestone.completion_date:
                days_to_payment = (milestone.payment.created - milestone.completion_date).days
                if days_to_payment <= 3:
                    prompt_payments += 1
                if milestone.is_approved:
                    milestone_approvals += 1
        
        # Check for specification changes (simplified)
        if job.revision_requested_count:
            specification_changes += job.revision_requested_count
    
    # Calculate component scores
    if total_completed_milestones > 0:
        payment_score = (prompt_payments / total_completed_milestones) * 40
        reliability_score += payment_score
        
        approval_score = (milestone_approvals / total_completed_milestones) * 30
        reliability_score += approval_score
    
    # Specification clarity (penalize for excessive changes)
    if total_jobs > 0:
        average_changes = specification_changes / total_jobs
        spec_penalty = min(20, average_changes * 5)
        reliability_score = max(0, reliability_score - spec_penalty)
    
    # Response rate (based on message response times - dummy calculation for now)
    reliability_score += 20  # Default response score
    
    return min(100, reliability_score)

def get_rating_trend(profile, as_client=False):
    """
    Analyze rating trends over time to identify improvement or decline
    Returns: trend (positive, negative, stable), confidence (0-1)
    """
    # Determine which reviews to use
    if as_client:
        reviews = FreelancerReview.objects.filter(client=profile).order_by('created')
    else:
        reviews = ClientReview.objects.filter(freelancer=profile).order_by('created')
    
    if not reviews or reviews.count() < 3:
        return {'trend': 'stable', 'confidence': 0}
    
    # Group reviews by quarters and calculate average ratings
    quarters = {}
    for review in reviews:
        quarter_key = f"{review.created.year}Q{(review.created.month-1)//3 + 1}"
        if quarter_key not in quarters:
            quarters[quarter_key] = {'sum': 0, 'count': 0}
        quarters[quarter_key]['sum'] += review.rating
        quarters[quarter_key]['count'] += 1
    
    # Calculate average by quarter
    quarter_averages = []
    for quarter, data in sorted(quarters.items()):
        quarter_averages.append(data['sum'] / data['count'])
    
    # Analyze trend
    if len(quarter_averages) < 2:
        return {'trend': 'stable', 'confidence': 0}
    
    # Calculate trend using the last 4 quarters or all if less
    relevant_averages = quarter_averages[-min(4, len(quarter_averages)):]
    
    # Simple trend analysis
    first = relevant_averages[0]
    last = relevant_averages[-1]
    
    if last - first > 0.5:
        trend = 'positive'
        confidence = min(1.0, (last - first) / 2.0)
    elif first - last > 0.5:
        trend = 'negative'
        confidence = min(1.0, (first - last) / 2.0)
    else:
        trend = 'stable'
        confidence = 1.0 - (abs(last - first) / 2.0)
    
    return {
        'trend': trend,
        'confidence': round(confidence, 2),
        'quarters': list(quarters.keys())[-min(4, len(quarters)):],
        'values': relevant_averages
    }

def get_enhanced_rating(profile, as_client=False):
    """
    Get an enhanced rating that takes into account:
    - Time-weighted ratings (more weight to recent reviews)
    - Project complexity factors
    - Reliability metrics
    - Trend analysis
    """
    base_rating = profile.client_rating if as_client else profile.freelancer_rating
    
    # If no ratings yet, return default
    if not base_rating or base_rating == 0:
        return {
            'rating': 0,
            'reliability': 0,
            'trend': 'stable',
            'trend_confidence': 0,
            'time_weighted_rating': 0
        }
    
    # Get appropriate reviews
    if as_client:
        reviews = FreelancerReview.objects.filter(client=profile)
        reliability = calculate_client_reliability(profile)
    else:
        reviews = ClientReview.objects.filter(freelancer=profile)
        reliability = calculate_freelancer_reliability(profile)
    
    # Get time weighted rating
    time_weighted = get_time_weighted_rating(reviews)
    
    # Get trend analysis
    trend_data = get_rating_trend(profile, as_client)
    
    return {
        'rating': base_rating,
        'reliability': reliability,
        'trend': trend_data['trend'],
        'trend_confidence': trend_data['confidence'],
        'time_weighted_rating': time_weighted,
        'trend_quarters': trend_data.get('quarters', []),
        'trend_values': trend_data.get('values', [])
    }

def update_all_ratings():
    """Update enhanced ratings for all profiles"""
    profiles = Profile.objects.all()
    
    for profile in profiles:
        # Update client rating
        profile.calculate_client_rating
        
        # Update freelancer rating
        profile.calculate_freelancer_rating
        
        # Update trust score
        profile.update_trust_score
    
    return len(profiles)