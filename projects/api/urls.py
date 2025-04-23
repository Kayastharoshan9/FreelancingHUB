from django.urls import path
from . import views

urlpatterns = [
    path('', views.getRoutes),
    
    # Project routes
    path('projects/', views.getProjects),
    path('projects/<str:pk>/', views.getProject),
    path('projects/<str:pk>/vote/', views.projectVote),
    
    # Job routes
    path('jobs/', views.getJobs),
    path('jobs/<str:pk>/', views.getJob),
    path('jobs/create/', views.createJob),
    path('jobs/<str:pk>/update/', views.updateJob),
    path('jobs/<str:pk>/delete/', views.deleteJob),
    
    # Bid routes
    path('jobs/<str:pk>/bid/', views.createBid),
    path('bids/<str:pk>/update/', views.updateBid),
    path('bids/<str:pk>/delete/', views.deleteBid),
    path('bids/<str:pk>/accept/', views.acceptBid),
    
    # Milestone routes
    path('jobs/<str:pk>/milestones/', views.getJobMilestones),
    path('jobs/<str:pk>/milestones/create/', views.createMilestone),
    path('milestones/<str:pk>/update/', views.updateMilestone),
    path('milestones/<str:pk>/complete/', views.completeMilestone),
    
    # Payment routes
    path('milestones/<str:pk>/payment/', views.createPayment),
    path('payments/user/', views.getUserPayments),
    
    # Review routes
    path('jobs/<str:pk>/review-client/', views.createClientReview),
    path('jobs/<str:pk>/review-freelancer/', views.createFreelancerReview),
]
