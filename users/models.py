from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('both', 'Client & Freelancer'),
        ('client', 'Client Only'),
        ('freelancer', 'Freelancer Only'),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=500, blank=True, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    short_intro = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(null=True, blank=True, upload_to='profiles/', default="profiles/user-default.png")
    social_github = models.CharField(max_length=200, blank=True, null=True)
    social_twitter = models.CharField(max_length=200, blank=True, null=True)
    social_linkedin = models.CharField(max_length=200, blank=True, null=True)
    social_youtube = models.CharField(max_length=200, blank=True, null=True)
    social_website = models.CharField(max_length=200, blank=True, null=True)
    
    # Rating system
    client_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    freelancer_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    client_reviews_count = models.IntegerField(default=0)
    freelancer_reviews_count = models.IntegerField(default=0)
    
    # Verification and trust score
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='unverified')
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_rejection_reason = models.TextField(blank=True, null=True)
    verification_submission_date = models.DateTimeField(null=True, blank=True)
    trust_score = models.IntegerField(default=0)
    
    # Identity Verification Documents
    id_document_front = models.ImageField(upload_to='verification/id_documents/', null=True, blank=True)
    id_document_back = models.ImageField(upload_to='verification/id_documents/', null=True, blank=True)
    passport_document = models.ImageField(upload_to='verification/passport/', null=True, blank=True)
    address_proof = models.ImageField(upload_to='verification/address_proof/', null=True, blank=True)
    selfie_with_id = models.ImageField(upload_to='verification/selfies/', null=True, blank=True)
    
    # Payment information
    bank_account_name = models.CharField(max_length=200, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    bank_routing_number = models.CharField(max_length=50, blank=True, null=True)
    bank_swift_code = models.CharField(max_length=50, blank=True, null=True)
    
    # Digital wallet information
    paypal_email = models.EmailField(max_length=200, blank=True, null=True)
    wallet_address = models.CharField(max_length=200, blank=True, null=True)
    wallet_qr_code = models.ImageField(upload_to='payment/qr_codes/', null=True, blank=True)
    
    # User type
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='both')
    
    # Additional fields
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return str(self.username)
    
    @property
    def imageURL(self):
        try:
            url = self.profile_image.url
        except:
            url = '/static/images/profiles/user-default.png'
        return url
        
    def calculate_client_rating(self):
        from projects.models import FreelancerReview
        reviews = FreelancerReview.objects.filter(client=self)
        total = reviews.count()
        
        if total > 0:
            sum_rating = sum(review.rating for review in reviews)
            self.client_rating = round(sum_rating / total, 2)
            self.client_reviews_count = total
            self.save(update_fields=['client_rating', 'client_reviews_count'])
        return self.client_rating
    
    def update_client_rating(self):
        """Wrapper for calculate_client_rating to match views_rating.py"""
        return self.calculate_client_rating()
            
    def calculate_freelancer_rating(self):
        from projects.models import ClientReview
        reviews = ClientReview.objects.filter(freelancer=self)
        total = reviews.count()
        
        if total > 0:
            sum_rating = sum(review.rating for review in reviews)
            self.freelancer_rating = round(sum_rating / total, 2)
            self.freelancer_reviews_count = total
            self.save(update_fields=['freelancer_rating', 'freelancer_reviews_count'])
        return self.freelancer_rating
    
    def update_freelancer_rating(self):
        """Wrapper for calculate_freelancer_rating to match views_rating.py"""
        return self.calculate_freelancer_rating()
    
    def update_trust_score(self):
        """Calculate trust score based on verification, ratings, completed jobs, etc."""
        base_score = 0
        
        # Add points for verification status
        if self.verification_status == 'verified':
            base_score += 25
            if not self.is_verified:
                self.is_verified = True
                self.save(update_fields=['is_verified'])
        elif self.verification_status == 'pending':
            base_score += 5
        
        # Add points for identity documents
        id_document_fields = ['id_document_front', 'id_document_back', 'passport_document', 
                             'address_proof', 'selfie_with_id']
        id_document_count = sum(1 for field in id_document_fields if getattr(self, field, None))
        base_score += min(id_document_count * 3, 15)
        
        # Add points for payment methods
        payment_fields = ['bank_account_number', 'paypal_email', 'wallet_address']
        payment_count = sum(1 for field in payment_fields if getattr(self, field, None))
        base_score += min(payment_count * 2, 10)
            
        # Add points for ratings
        base_score += min(int(self.client_rating * 5), 20) if self.client_reviews_count > 0 else 0
        base_score += min(int(self.freelancer_rating * 5), 20) if self.freelancer_reviews_count > 0 else 0
        
        # Add points for profile completeness
        profile_completeness = 0
        required_fields = ['name', 'email', 'location', 'short_intro', 'bio', 'profile_image']
        for field in required_fields:
            if getattr(self, field, None):
                profile_completeness += 1
        
        base_score += int((profile_completeness / len(required_fields)) * 15)
        
        # Add points for connected social accounts
        social_fields = ['social_github', 'social_twitter', 'social_linkedin', 'social_youtube', 'social_website']
        social_count = sum(1 for field in social_fields if getattr(self, field, None))
        base_score += min(social_count * 3, 15)
        
        self.trust_score = min(base_score, 100)  # Cap at 100%
        self.save(update_fields=['trust_score'])
        return self.trust_score
    
    @property
    def earned_badges(self):
        """Get all badges earned by this profile"""
        return self.badgeassignment_set.all()


class Skill(models.Model):
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    # Skill level tracking
    endorsements = models.IntegerField(default=0)
    experience_level = models.IntegerField(default=1)  # 1-5 scale
    
    def __str__(self):
        return str(self.name)
    
    @property
    def get_skill_level_display(self):
        levels = {
            1: "Beginner",
            2: "Intermediate",
            3: "Advanced",
            4: "Expert",
            5: "Master"
        }
        return levels.get(self.experience_level, "Unknown")


class Badge(models.Model):
    """Model for skill badges that can be earned"""
    BADGE_TYPES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
        ('master', 'Master'),
        ('special', 'Special Achievement'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    image = models.ImageField(upload_to='badges/', null=True, blank=True)
    requirements = models.JSONField(default=dict, help_text="JSON with badge requirements")
    points = models.IntegerField(default=10, help_text="Points awarded for earning this badge")
    skill_related = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name="badges")
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    def __str__(self):
        return self.name
    
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = '/static/images/badges/default-badge.png'
        return url


class BadgeAssignment(models.Model):
    """Tracks which profiles have earned which badges"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_earned = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    class Meta:
        unique_together = ('profile', 'badge')
    
    def __str__(self):
        return f"{self.profile.name} earned {self.badge.name}"


class Message(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_messages")
    recipient = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_messages")
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False, null=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ['is_read', '-created']


class ClientReview(models.Model):
    """
    Model for a review given by a client to a freelancer
    """
    reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_given_as_client')
    freelancer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='client_reviews')
    rating = models.IntegerField(default=5)  # Overall rating out of 5
    comment = models.TextField()
    
    # Specific rating factors
    quality = models.IntegerField(default=5)  # Quality of work
    communication = models.IntegerField(default=5)  # Communication
    deadlines = models.IntegerField(default=5)  # Meeting deadlines
    
    # Contract reference (optional, allows linking to specific job)
    contract = models.ForeignKey('projects.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='client_reviews')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    class Meta:
        unique_together = ('reviewer', 'freelancer', 'contract')
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.reviewer.name}'s review of {self.freelancer.name}"


class FreelancerReview(models.Model):
    """
    Model for a review given by a freelancer to a client
    """
    reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_given_as_freelancer')
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='freelancer_reviews')
    rating = models.IntegerField(default=5)  # Overall rating out of 5
    comment = models.TextField()
    
    # Specific rating factors
    requirements = models.IntegerField(default=5)  # Clear requirements
    communication = models.IntegerField(default=5)  # Communication
    payment = models.IntegerField(default=5)  # Payment promptness
    
    # Contract reference (optional, allows linking to specific job)
    contract = models.ForeignKey('projects.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='freelancer_reviews')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    class Meta:
        unique_together = ('reviewer', 'client', 'contract')
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.reviewer.name}'s review of {self.client.name}"