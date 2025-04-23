from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from projects.models import Project, Tag, Review, Job, Bid, Milestone, ClientReview, FreelancerReview, Payment
from .serializers import (
    ProjectSerializer, TagSerializer, ReviewSerializer,
    JobSerializer, BidSerializer, MilestoneSerializer,
    ClientReviewSerializer, FreelancerReviewSerializer,
    PaymentSerializer
)
from users.models import Profile


@api_view(['GET'])
def getRoutes(request):
    routes = [
        {'GET': '/api/projects'},
        {'GET': '/api/projects/id'},
        {'POST': '/api/projects/id/vote'},

        {'GET': '/api/jobs'},
        {'GET': '/api/jobs/id'},
        {'POST': '/api/jobs/create'},
        {'PUT': '/api/jobs/id/update'},
        {'DELETE': '/api/jobs/id/delete'},

        {'GET': '/api/bids'},
        {'POST': '/api/jobs/id/bid'},
        {'PUT': '/api/bids/id/update'},
        {'DELETE': '/api/bids/id/delete'},

        {'GET': '/api/milestones/job/id'},
        {'POST': '/api/jobs/id/milestones/create'},
        {'PUT': '/api/milestones/id/update'},
        {'PUT': '/api/milestones/id/complete'},

        {'POST': '/api/milestones/id/payment'},
        {'GET': '/api/payments/user'},

        {'POST': '/api/jobs/id/review-client'},
        {'POST': '/api/jobs/id/review-freelancer'},
    ]
    return Response(routes)


# Project views
@api_view(['GET'])
def getProjects(request):
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getProject(request, pk):
    project = Project.objects.get(id=pk)
    serializer = ProjectSerializer(project, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def projectVote(request, pk):
    project = Project.objects.get(id=pk)
    user = request.user.profile
    data = request.data

    review, created = Review.objects.get_or_create(
        owner=user,
        project=project,
    )

    review.value = data['value']
    review.save()
    project.getVoteCount

    serializer = ProjectSerializer(project, many=False)
    return Response(serializer.data)


# Job views
@api_view(['GET'])
def getJobs(request):
    query = request.GET.get('search', '')
    
    if query:
        jobs = Job.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(required_skills__name__icontains=query)
        ).distinct()
    else:
        jobs = Job.objects.filter(status='open')
        
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getJob(request, pk):
    job = Job.objects.get(id=pk)
    serializer = JobSerializer(job, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createJob(request):
    profile = request.user.profile
    data = request.data
    
    job = Job.objects.create(
        owner=profile,
        title=data['title'],
        description=data['description'],
        budget_min=data['budget_min'],
        budget_max=data['budget_max'],
        deadline=data['deadline'],
        job_type=data.get('job_type', 'remote'),
        location=data.get('location', ''),
    )
    
    # Add required skills
    if 'required_skills' in data:
        for skill_id in data['required_skills']:
            skill = Tag.objects.get(id=skill_id)
            job.required_skills.add(skill)
    
    serializer = JobSerializer(job, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateJob(request, pk):
    profile = request.user.profile
    data = request.data
    
    try:
        job = Job.objects.get(id=pk, owner=profile)
    except Job.DoesNotExist:
        return Response({'detail': 'Job not found or you are not the owner'}, status=status.HTTP_404_NOT_FOUND)
    
    job.title = data.get('title', job.title)
    job.description = data.get('description', job.description)
    job.budget_min = data.get('budget_min', job.budget_min)
    job.budget_max = data.get('budget_max', job.budget_max)
    job.deadline = data.get('deadline', job.deadline)
    job.job_type = data.get('job_type', job.job_type)
    job.location = data.get('location', job.location)
    job.save()
    
    # Update required skills if provided
    if 'required_skills' in data:
        job.required_skills.clear()
        for skill_id in data['required_skills']:
            skill = Tag.objects.get(id=skill_id)
            job.required_skills.add(skill)
    
    serializer = JobSerializer(job, many=False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteJob(request, pk):
    profile = request.user.profile
    
    try:
        job = Job.objects.get(id=pk, owner=profile)
    except Job.DoesNotExist:
        return Response({'detail': 'Job not found or you are not the owner'}, status=status.HTTP_404_NOT_FOUND)
    
    job.delete()
    return Response({'detail': 'Job deleted successfully'})


# Bid views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createBid(request, pk):
    profile = request.user.profile
    job = Job.objects.get(id=pk)
    data = request.data
    
    # Check if user already has a bid on this job
    if Bid.objects.filter(job=job, freelancer=profile).exists():
        return Response({'detail': 'You have already placed a bid on this job'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create a new bid
    bid = Bid.objects.create(
        freelancer=profile,
        job=job,
        amount=data['amount'],
        delivery_time=data['delivery_time'],
        proposal=data['proposal']
    )
    
    serializer = BidSerializer(bid, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateBid(request, pk):
    profile = request.user.profile
    data = request.data
    
    try:
        bid = Bid.objects.get(id=pk, freelancer=profile)
    except Bid.DoesNotExist:
        return Response({'detail': 'Bid not found or you are not the owner'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the bid can be updated
    if bid.status != 'pending':
        return Response({'detail': 'Cannot update a bid that has been accepted or rejected'}, status=status.HTTP_400_BAD_REQUEST)
    
    bid.amount = data.get('amount', bid.amount)
    bid.delivery_time = data.get('delivery_time', bid.delivery_time)
    bid.proposal = data.get('proposal', bid.proposal)
    bid.save()
    
    serializer = BidSerializer(bid, many=False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteBid(request, pk):
    profile = request.user.profile
    
    try:
        bid = Bid.objects.get(id=pk, freelancer=profile)
    except Bid.DoesNotExist:
        return Response({'detail': 'Bid not found or you are not the owner'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the bid can be deleted
    if bid.status != 'pending':
        return Response({'detail': 'Cannot delete a bid that has been accepted or rejected'}, status=status.HTTP_400_BAD_REQUEST)
    
    bid.delete()
    return Response({'detail': 'Bid deleted successfully'})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def acceptBid(request, pk):
    profile = request.user.profile
    
    try:
        bid = Bid.objects.get(id=pk)
        job = bid.job
    except Bid.DoesNotExist:
        return Response({'detail': 'Bid not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Ensure only the job owner can accept bids
    if job.owner != profile:
        return Response({'detail': 'Only the job owner can accept bids'}, status=status.HTTP_403_FORBIDDEN)
    
    # Ensure job is still open
    if job.status != 'open':
        return Response({'detail': 'This job is no longer open for bidding'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Mark the bid as accepted
    bid.status = 'accepted'
    bid.save()
    
    # Mark the job as in progress
    job.status = 'in_progress'
    job.save()
    
    # Reject all other bids
    Bid.objects.filter(job=job).exclude(id=bid.id).update(status='rejected')
    
    serializer = BidSerializer(bid, many=False)
    return Response(serializer.data)


# Milestone views
@api_view(['GET'])
def getJobMilestones(request, pk):
    job = Job.objects.get(id=pk)
    milestones = job.milestones.all()
    serializer = MilestoneSerializer(milestones, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createMilestone(request, pk):
    profile = request.user.profile
    data = request.data
    
    try:
        job = Job.objects.get(id=pk)
    except Job.DoesNotExist:
        return Response({'detail': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Ensure only the job owner can create milestones
    if job.owner != profile:
        return Response({'detail': 'Only the job owner can create milestones'}, status=status.HTTP_403_FORBIDDEN)
    
    milestone = Milestone.objects.create(
        job=job,
        title=data['title'],
        description=data['description'],
        amount=data['amount'],
        due_date=data['due_date']
    )
    
    serializer = MilestoneSerializer(milestone, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateMilestone(request, pk):
    profile = request.user.profile
    data = request.data
    
    try:
        milestone = Milestone.objects.get(id=pk)
        job = milestone.job
    except Milestone.DoesNotExist:
        return Response({'detail': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Ensure only the job owner can update milestones
    if job.owner != profile:
        return Response({'detail': 'Only the job owner can update milestones'}, status=status.HTTP_403_FORBIDDEN)
    
    milestone.title = data.get('title', milestone.title)
    milestone.description = data.get('description', milestone.description)
    milestone.amount = data.get('amount', milestone.amount)
    milestone.due_date = data.get('due_date', milestone.due_date)
    milestone.save()
    
    serializer = MilestoneSerializer(milestone, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def completeMilestone(request, pk):
    profile = request.user.profile
    
    try:
        milestone = Milestone.objects.get(id=pk)
        job = milestone.job
    except Milestone.DoesNotExist:
        return Response({'detail': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Ensure only the job owner can mark milestones as complete
    if job.owner != profile:
        return Response({'detail': 'Only the job owner can mark milestones as complete'}, status=status.HTTP_403_FORBIDDEN)
    
    milestone.status = 'completed'
    milestone.save()
    
    # Check if all milestones are completed
    if job.milestones.exclude(status='completed').count() == 0 and job.milestones.count() > 0:
        job.status = 'completed'
        job.save()
    
    serializer = MilestoneSerializer(milestone, many=False)
    return Response(serializer.data)


# Payment views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createPayment(request, pk):
    profile = request.user.profile
    
    try:
        milestone = Milestone.objects.get(id=pk)
        job = milestone.job
    except Milestone.DoesNotExist:
        return Response({'detail': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Ensure only the job owner can make payments
    if job.owner != profile:
        return Response({'detail': 'Only the job owner can make payments'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get the freelancer (the one with the accepted bid)
    accepted_bid = job.bids.filter(status='accepted').first()
    if not accepted_bid:
        return Response({'detail': 'No accepted bid found for this job'}, status=status.HTTP_400_BAD_REQUEST)
    
    freelancer = accepted_bid.freelancer
    
    # Create the payment record
    payment = Payment.objects.create(
        job=job,
        milestone=milestone,
        client=profile,
        freelancer=freelancer,
        amount=milestone.amount
    )
    
    serializer = PaymentSerializer(payment, many=False)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserPayments(request):
    profile = request.user.profile
    
    # Get payments where user is either client or freelancer
    payments = Payment.objects.filter(Q(client=profile) | Q(freelancer=profile))
    
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)


# Review views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createClientReview(request, pk):
    profile = request.user.profile
    data = request.data
    
    try:
        job = Job.objects.get(id=pk, status='completed')
    except Job.DoesNotExist:
        return Response({'detail': 'Completed job not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Ensure only the job owner can review the freelancer
    if job.owner != profile:
        return Response({'detail': 'Only the job owner can leave a review for the freelancer'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get the freelancer (the one with the accepted bid)
    accepted_bid = job.bids.filter(status='accepted').first()
    if not accepted_bid:
        return Response({'detail': 'No accepted bid found for this job'}, status=status.HTTP_400_BAD_REQUEST)
    
    freelancer = accepted_bid.freelancer
    
    # Check if a review already exists
    if ClientReview.objects.filter(job=job, reviewer=profile).exists():
        return Response({'detail': 'You have already left a review for this job'}, status=status.HTTP_400_BAD_REQUEST)
    
    review = ClientReview.objects.create(
        job=job,
        reviewer=profile,
        freelancer=freelancer,
        rating=data['rating'],
        comment=data['comment']
    )
    
    serializer = ClientReviewSerializer(review, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createFreelancerReview(request, pk):
    profile = request.user.profile
    data = request.data
    
    try:
        job = Job.objects.get(id=pk, status='completed')
    except Job.DoesNotExist:
        return Response({'detail': 'Completed job not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get the freelancer (the one with the accepted bid)
    accepted_bid = job.bids.filter(status='accepted', freelancer=profile).first()
    if not accepted_bid:
        return Response({'detail': 'You are not the freelancer for this job'}, status=status.HTTP_403_FORBIDDEN)
    
    # Check if a review already exists
    if FreelancerReview.objects.filter(job=job, reviewer=profile).exists():
        return Response({'detail': 'You have already left a review for this job'}, status=status.HTTP_400_BAD_REQUEST)
    
    review = FreelancerReview.objects.create(
        job=job,
        reviewer=profile,
        client=job.owner,
        rating=data['rating'],
        comment=data['comment']
    )
    
    serializer = FreelancerReviewSerializer(review, many=False)
    return Response(serializer.data)
