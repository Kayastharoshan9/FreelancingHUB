from django import forms
from .models import Project, Review, Job, Bid, Milestone, ClientReview, FreelancerReview, Tag
from django.forms.widgets import CheckboxSelectMultiple


class ProjectForm(forms.ModelForm):
    # Add a price field that's not part of the model for display purposes
    price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Optional: Estimated project price/value"
    )
    
    # Add field for creating new tags
    new_tags = forms.CharField(
        max_length=200, 
        required=False,
        help_text="Add new tags separated by commas"
    )
    
    class Meta:
        model = Project
        fields = ['title', 'featured_image', 'description', 'demo_link', 'source_link', 'tags']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        # Ensure tags are properly populated from database
        self.fields['tags'].queryset = Tag.objects.all()
        
        self.fields['title'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter project title'
        })
        self.fields['featured_image'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter project description', 
            'rows': 4
        })
        self.fields['demo_link'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter demo link'
        })
        self.fields['source_link'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter source code link'
        })
        self.fields['tags'].widget.attrs.update({
            'class': 'list-unstyled'
        })
        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter estimated price'
        })
        self.fields['new_tags'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'E.g., react, webdev, design'
        })
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            self.save_m2m()
            
            # Process new tags if provided
            new_tags = self.cleaned_data.get('new_tags')
            if new_tags:
                tags_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]
                for tag_name in tags_list:
                    tag, created = Tag.objects.get_or_create(name=tag_name.lower())
                    instance.tags.add(tag)
        
        return instance


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['value', 'body']
        labels = {
            'value': 'Place your vote',
            'body': 'Add a comment with your vote'
        }

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)

        self.fields['value'].widget.attrs.update({'class': 'form-select'})
        self.fields['body'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Write your review here...', 'rows': 4})


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'required_skills', 'budget_min', 'budget_max', 'deadline', 'job_type', 'location']
        widgets = {
            'required_skills': forms.CheckboxSelectMultiple(),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)

        # Get all available tags for the required_skills dropdown
        self.fields['required_skills'].queryset = Tag.objects.all()
        
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter job title'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Describe the job requirements, expectations, and deliverables...', 'rows': 5})
        self.fields['required_skills'].widget.attrs.update({'class': 'list-unstyled'})
        self.fields['budget_min'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Minimum budget'})
        self.fields['budget_max'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Maximum budget'})
        self.fields['deadline'].widget.attrs.update({'class': 'form-control'})
        self.fields['job_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['location'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Job location (or remote)'})

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')

        if budget_min and budget_max and budget_min > budget_max:
            raise forms.ValidationError("Minimum budget cannot be greater than maximum budget.")
        
        return cleaned_data


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount', 'delivery_time', 'proposal']

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job', None)
        super(BidForm, self).__init__(*args, **kwargs)

        self.fields['amount'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Your bid amount'})
        self.fields['delivery_time'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Delivery time in days'})
        self.fields['proposal'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Describe why you are the best candidate for this job and how you plan to execute it...', 'rows': 5})

        if job:
            self.fields['amount'].help_text = f"Budget range: ${job.budget_min} - ${job.budget_max}"
            if job.job_type == 'hourly':
                self.fields['amount'].label = "Hourly Rate ($)"
            else:
                self.fields['amount'].label = "Fixed Price ($)"

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Bid amount must be greater than zero.")
        return amount


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'amount', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job', None)
        super(MilestoneForm, self).__init__(*args, **kwargs)

        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Milestone title'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Describe what will be delivered in this milestone...', 'rows': 3})
        self.fields['amount'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Payment amount for this milestone'})
        self.fields['due_date'].widget.attrs.update({'class': 'form-control'})

        if job and job.job_type == 'fixed':
            self.fields['amount'].help_text = f"Total budget: ${job.budget_min} - ${job.budget_max}"

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class ClientReviewForm(forms.ModelForm):
    class Meta:
        model = ClientReview
        fields = ['rating', 'comment']

    def __init__(self, *args, **kwargs):
        super(ClientReviewForm, self).__init__(*args, **kwargs)

        self.fields['rating'].widget.attrs.update({'class': 'form-select'})
        self.fields['comment'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Share your experience working with this freelancer...', 'rows': 4})


class FreelancerReviewForm(forms.ModelForm):
    class Meta:
        model = FreelancerReview
        fields = ['rating', 'comment']

    def __init__(self, *args, **kwargs):
        super(FreelancerReviewForm, self).__init__(*args, **kwargs)

        self.fields['rating'].widget.attrs.update({'class': 'form-select'})
        self.fields['comment'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Share your experience working with this client...', 'rows': 4})