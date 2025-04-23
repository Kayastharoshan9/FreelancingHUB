from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile, Skill, Message, ClientReview, FreelancerReview


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'email', 'username', 'password1', 'password2']
        labels = {
            'first_name': 'Name',
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'email', 'username', 'user_type', 'hourly_rate', 'location', 
                  'bio', 'short_intro', 'profile_image', 'social_github', 'social_twitter',
                  'social_linkedin', 'social_youtube', 'social_website']
        
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'short_intro': forms.Textarea(attrs={'rows': 2}),
        }
        
        labels = {
            'user_type': 'Account Type',
            'hourly_rate': 'Hourly Rate (USD)',
            'social_github': 'GitHub',
            'social_twitter': 'Twitter',
            'social_linkedin': 'LinkedIn',
            'social_youtube': 'YouTube',
            'social_website': 'Website',
            'short_intro': 'Short Introduction',
        }
        
        help_texts = {
            'user_type': 'Select how you want to use FreelanceHub',
            'profile_image': 'Upload a professional profile photo (max 5MB)',
            'hourly_rate': 'Only applies for freelancer accounts',
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name != 'user_type':  # Skip user_type as we're using form-select class
                field.widget.attrs.update({'class': 'form-control'})
            
            # Add placeholder text
            if name == 'name':
                field.widget.attrs.update({'placeholder': 'Your full name'})
            elif name == 'username':
                field.widget.attrs.update({'placeholder': 'Username'})
            elif name == 'email':
                field.widget.attrs.update({'placeholder': 'Email address'})
            elif name == 'location':
                field.widget.attrs.update({'placeholder': 'City, Country'})
            elif name == 'hourly_rate':
                field.widget.attrs.update({'placeholder': 'e.g. 25.00'})
            elif name == 'short_intro':
                field.widget.attrs.update({'placeholder': 'Brief introduction (1-2 sentences)'})
            elif name == 'bio':
                field.widget.attrs.update({'placeholder': 'Tell us about yourself, your experience and skills'})
            elif 'social_' in name:
                field.widget.attrs.update({'placeholder': 'https://'})
                
        # Make certain fields required visually
        self.fields['name'].widget.attrs.update({'required': 'required'})
        self.fields['email'].widget.attrs.update({'required': 'required'})


class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = '__all__'
        exclude = ['owner']

    def __init__(self, *args, **kwargs):
        super(SkillForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'subject', 'body']

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class VerificationForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            'id_document_front', 
            'id_document_back', 
            'passport_document',
            'address_proof', 
            'selfie_with_id'
        ]
        labels = {
            'id_document_front': 'Front side of ID/Driver\'s License',
            'id_document_back': 'Back side of ID/Driver\'s License',
            'passport_document': 'Passport (if available)',
            'address_proof': 'Proof of Address (utility bill, bank statement)',
            'selfie_with_id': 'Selfie holding your ID document'
        }
        help_texts = {
            'id_document_front': 'Upload a clear image of the front of your government-issued ID.',
            'id_document_back': 'Upload a clear image of the back of your government-issued ID.',
            'passport_document': 'Optional: Upload a clear image of your passport bio page if available.',
            'address_proof': 'Document showing your name and address (issued within last 3 months).',
            'selfie_with_id': 'Upload a photo of yourself holding your ID next to your face.'
        }

    def __init__(self, *args, **kwargs):
        super(VerificationForm, self).__init__(*args, **kwargs)
        
        # Mark only ID front, back and selfie as required
        self.fields['passport_document'].required = False
        self.fields['address_proof'].required = False
        
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class PaymentInfoForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bank_account_name',
            'bank_account_number',
            'bank_name',
            'bank_routing_number',
            'bank_swift_code',
            'paypal_email',
            'wallet_address',
            'wallet_qr_code'
        ]
        labels = {
            'bank_account_name': 'Account Holder Name',
            'bank_account_number': 'Bank Account Number',
            'bank_name': 'Bank Name',
            'bank_routing_number': 'Routing Number / Sort Code',
            'bank_swift_code': 'SWIFT/BIC Code (for international transfers)',
            'paypal_email': 'PayPal Email',
            'wallet_address': 'Cryptocurrency Wallet Address',
            'wallet_qr_code': 'Upload QR Code for your Crypto Wallet'
        }

    def __init__(self, *args, **kwargs):
        super(PaymentInfoForm, self).__init__(*args, **kwargs)
        
        # Make all fields optional
        for field in self.fields.values():
            field.required = False
            
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ClientReviewForm(ModelForm):
    """
    Form for clients to review freelancers
    """
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Share your experience working with this freelancer...'}),
        label='Your Review'
    )
    
    class Meta:
        model = ClientReview
        fields = ['rating', 'quality', 'communication', 'deadlines', 'comment']
        labels = {
            'rating': 'Overall Rating',
            'quality': 'Quality of Work',
            'communication': 'Communication',
            'deadlines': 'Meeting Deadlines'
        }
        widgets = {
            'rating': forms.HiddenInput(),
            'quality': forms.HiddenInput(),
            'communication': forms.HiddenInput(),
            'deadlines': forms.HiddenInput(),
        }


class FreelancerReviewForm(ModelForm):
    """
    Form for freelancers to review clients
    """
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Share your experience working with this client...'}),
        label='Your Review'
    )
    
    class Meta:
        model = FreelancerReview
        fields = ['rating', 'requirements', 'communication', 'payment', 'comment']
        labels = {
            'rating': 'Overall Rating',
            'requirements': 'Clear Requirements',
            'communication': 'Communication',
            'payment': 'Payment Promptness'
        }
        widgets = {
            'rating': forms.HiddenInput(),
            'requirements': forms.HiddenInput(),
            'communication': forms.HiddenInput(),
            'payment': forms.HiddenInput(),
        }
