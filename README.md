
# FreelanceHub

A comprehensive freelancing platform built with Django that connects clients with skilled freelancers.

## Features

- User Authentication (Client/Freelancer)
- Project Creation and Bidding
- AI-based Project Matching
- Secure Payment Integration with Stripe
- Milestone-based Project Management
- Rating and Review System
- Real-time Messaging
- Identity Verification System

## Setup Instructions

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run migrations:
```bash
python manage.py migrate
```
4. Start the development server:
```bash
python manage.py runserver 0.0.0.0:8000
```

## Environment Variables

Make sure to set up the following environment variables:
- `SECRET_KEY`: Django secret key
- `STRIPE_PUBLIC_KEY`: Stripe public key
- `STRIPE_SECRET_KEY`: Stripe secret key
- `OPENAI_API_KEY`: OpenAI API key for AI matching

## Tech Stack

- Backend: Django
- Database: SQLite
- Payment: Stripe
- AI Integration: OpenAI
- Frontend: HTML, CSS, JavaScript
- Authentication: Django Authentication + JWT

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
