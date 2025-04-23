from django.urls import path
from . import views
from . import stripe_views

urlpatterns = [
    # Project views
    path('projects/', views.projects, name='projects'),
    path('project/<str:pk>/', views.project, name='project'),
    path('create-project/', views.createProject, name='create-project'),
    path('update-project/<str:pk>/', views.updateProject, name='update-project'),
    path('delete-project/<str:pk>/', views.deleteProject, name='delete-project'),
    
    # Job views
    path('jobs/', views.jobs, name='jobs'),
    path('job/<str:pk>/', views.job, name='job'),
    path('create-job/', views.createJob, name='create-job'),
    path('update-job/<str:pk>/', views.updateJob, name='update-job'),
    path('delete-job/<str:pk>/', views.deleteJob, name='delete-job'),
    
    # Bid views
    path('create-bid/<str:job_id>/', views.createBid, name='create-bid'),
    path('update-bid/<str:pk>/', views.updateBid, name='update-bid'),
    path('delete-bid/<str:pk>/', views.deleteBid, name='delete-bid'),
    path('accept-bid/<str:pk>/', views.acceptBid, name='accept-bid'),
    
    # Milestone views
    path('create-milestone/<str:job_id>/', views.createMilestone, name='create-milestone'),
    path('update-milestone/<str:pk>/', views.updateMilestone, name='update-milestone'),
    path('delete-milestone/<str:pk>/', views.deleteMilestone, name='delete-milestone'),
    path('complete-milestone/<str:pk>/', views.completeMilestone, name='complete-milestone'),
    
    # Review views
    path('create-client-review/<str:job_id>/', views.createClientReview, name='create-client-review'),
    path('create-freelancer-review/<str:job_id>/', views.createFreelancerReview, name='create-freelancer-review'),
    
    # Payment views
    path('escrow-payment/<str:milestone_id>/', stripe_views.create_escrow_payment, name='escrow-payment'),
    path('create-checkout-session/<str:milestone_id>/', stripe_views.create_checkout_session, name='create-checkout-session'),
    path('payment-success/<str:milestone_id>/', stripe_views.payment_success, name='payment-success'),
    path('payment-cancel/<str:milestone_id>/', stripe_views.payment_cancel, name='payment-cancel'),
    path('release-payment/<str:payment_id>/', stripe_views.release_escrow_payment, name='release-payment'),
    path('refund-payment/<str:payment_id>/', stripe_views.refund_escrow_payment, name='refund-payment'),
    path('review-and-release/<str:job_id>/<str:milestone_id>/', views.review_and_release_payment, name='review-and-release'),
    path('transactions/', views.transaction_dashboard, name='transactions'),
    path('webhook/', stripe_views.stripe_webhook, name='stripe-webhook'),
    
    # AI Matching views
    path('ai-matching/', views.ai_matching_dashboard, name='ai-matching'),
    path('job-matching/<str:job_id>/', views.job_matching_results, name='job-matching'),
]