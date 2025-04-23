from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('logout/', views.LogoutUserView.as_view(), name='logout'),
    path('register/', views.RegisterUserView.as_view(), name='register'),
    
    path('profiles/', views.profiles, name='profiles'),
    path('profile/<str:pk>/', views.ProfileDetailView.as_view(), name='profile'),
    path('account/', views.UserAccountView.as_view(), name='account'),
    path('edit-account/', views.EditAccountView.as_view(), name='edit-account'),
    
    path('create-skill/', views.createSkill, name='create-skill'),
    path('update-skill/<str:pk>/', views.updateSkill, name='update-skill'),
    path('delete-skill/<str:pk>/', views.deleteSkill, name='delete-skill'),
    
    path('inbox/', views.inbox, name='inbox'),
    path('message/<str:pk>/', views.viewMessage, name='message'),
    path('create-message/<str:pk>/', views.createMessage, name='create-message'),
    
    # Verification and payment URLs
    path('verification-status/', views.VerificationStatusView.as_view(), name='verification-status'),
    path('submit-verification/', views.SubmitVerificationView.as_view(), name='submit-verification'),
    path('payment-info/', views.PaymentInfoView.as_view(), name='payment-info'),
]

# Advanced rating views
from .views_rating import rate_freelancer, rate_client

urlpatterns += [
    path('rate-freelancer/<str:profile_id>/', rate_freelancer, name='rate-freelancer'),
    path('rate-client/<str:profile_id>/', rate_client, name='rate-client'),
]
