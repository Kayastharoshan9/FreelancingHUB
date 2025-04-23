import os
from django.conf import settings

def stripe_key(request):
    """
    Add Stripe publishable key to the context.
    """
    return {
        'STRIPE_PUBLISHABLE_KEY': os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    }