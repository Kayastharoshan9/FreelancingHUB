from django.db import models
import uuid
from django.contrib.auth.models import User
from users.models import Profile


class Project(models.Model):
    owner = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    featured_image = models.ImageField(upload_to='projects', null=True, blank=True, default="projects/default.jpg")
    demo_link = models.CharField(max_length=2000, null=True, blank=True)
    source_link = models.CharField(max_length=2000, null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    vote_total = models.IntegerField(default=0, null=True, blank=True)
    vote_ratio = models.IntegerField(default=0, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-vote_ratio', '-vote_total', 'title']

    @property
    def imageURL(self):
        try:
            url = self.featured_image.url
        except:
            url = '/static/images/default.jpg'
        return url

    @property
    def reviewers(self):
        queryset = self.review_set.all().values_list('owner__id', flat=True)
        return queryset

    @property
    def getVoteCount(self):
        reviews = self.review_set.all()
        upVotes = reviews.filter(value='up').count()
        totalVotes = reviews.count()

        ratio = (upVotes / totalVotes) * 100 if totalVotes > 0 else 0
        
        self.vote_total = totalVotes
        self.vote_ratio = ratio
        self.save()


class Review(models.Model):
    VOTE_TYPE = (
        ('up', 'Up Vote'),
        ('down', 'Down Vote'),
    )
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    body = models.TextField(null=True, blank=True)
    value = models.CharField(max_length=200, choices=VOTE_TYPE)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    class Meta:
        unique_together = [['owner', 'project']]

    def __str__(self):
        return self.value


class Tag(models.Model):
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPES = (
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
    )
    
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='client_jobs')
    freelancer = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='freelancer_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.ManyToManyField(Tag, related_name='job_skills', blank=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)
    job_type = models.CharField(max_length=10, choices=JOB_TYPES, default='fixed')
    location = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created']


class Bid(models.Model):
    freelancer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='bids')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.IntegerField(help_text="Delivery time in days")
    proposal = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return f"{self.freelancer.name}'s bid on {self.job.title}"
    
    class Meta:
        ordering = ['amount']
        unique_together = ['freelancer', 'job']


class Milestone(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    is_funded = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['created']


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('escrow', 'In Escrow'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
    )
    
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='client_payments')
    freelancer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='freelancer_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return f"Payment for {self.milestone.title}"
    
    class Meta:
        ordering = ['-created']


class ClientReview(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='client_review')
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_as_client')
    freelancer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_from_clients')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return f"Client review for {self.job.title}"


class FreelancerReview(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='freelancer_review')
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_from_freelancers')
    freelancer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_as_freelancer')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    def __str__(self):
        return f"Freelancer review for {self.job.title}"


class Contract(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Acceptance'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='contracts')
    freelancer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='contracts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    terms = models.TextField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_signed_by_client = models.BooleanField(default=False)
    is_signed_by_freelancer = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    
    def __str__(self):
        return f"Contract for {self.job.title}"
    
    class Meta:
        ordering = ['-created']