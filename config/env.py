import os

# Environment variables
# For local development, you can hard-code your API keys below
# For production, set these as environment variables
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'YOUR_STRIPE_SECRET_KEY_HERE')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'YOUR_STRIPE_PUBLISHABLE_KEY_HERE')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# OpenAI configuration
# Replace this with your actual OpenAI API key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE')

# Deployment environment
DEPLOYMENT_ENVIRONMENT = os.environ.get('DEPLOYMENT_ENVIRONMENT', 'development')

# Domain settings for Stripe redirects
DEVELOPMENT_DOMAIN = os.environ.get('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]
PRODUCTION_DOMAIN = os.environ.get('PRODUCTION_DOMAIN', 'freelancer.example.com')