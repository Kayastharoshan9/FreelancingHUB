import os
import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from .models import Milestone, Payment, Job

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Determine the domain for success/cancel URLs
def get_domain(request):
    # Check for Replit domains environment variables
    if os.environ.get('REPLIT_DEPLOYMENT'):
        return os.environ.get('REPLIT_DEV_DOMAIN')
    elif os.environ.get('REPLIT_DOMAINS'):
        # Use the first domain in the list
        return os.environ.get('REPLIT_DOMAINS').split(',')[0]
    else:
        # Fallback to the request's host
        return request.get_host()

@login_required
def create_escrow_payment(request, milestone_id):
    """
    Show payment options or create a Stripe payment intent for escrow payment
    """
    milestone = get_object_or_404(Milestone, id=milestone_id)
    job = milestone.job
    
    # Ensure only the client can fund the milestone
    if job.client != request.user.profile:
        messages.error(request, "Only the client can fund this milestone.")
        return redirect('job', pk=job.id)
    
    # Check if milestone is already funded
    if milestone.is_funded:
        messages.error(request, "This milestone is already funded.")
        return redirect('job', pk=job.id)
    
    # First, show payment options
    if request.method == 'GET':
        context = {
            'milestone': milestone,
            'job': job,
        }
        return render(request, 'projects/stripe_payment.html', context)
    
    # If POST, proceed with direct payment (legacy method)
    # Calculate the amount in cents for Stripe
    amount_cents = int(milestone.amount * 100)
    
    try:
        # Create a PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            metadata={
                'milestone_id': str(milestone.id),
                'job_id': str(job.id),
                'client_id': str(job.client.id),
                'freelancer_id': str(job.freelancer.id) if job.freelancer else '',
            },
            description=f"Escrow payment for {milestone.title} - {job.title}"
        )
        
        context = {
            'client_secret': intent.client_secret,
            'milestone': milestone,
            'job': job,
            'stripe_publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY'),
        }
        
        return render(request, 'projects/escrow_payment.html', context)
        
    except stripe.error.StripeError as e:
        messages.error(request, f"Stripe error: {str(e)}")
        return redirect('job', pk=job.id)


@login_required
def payment_success(request, milestone_id):
    """
    Handle successful payment
    """
    milestone = get_object_or_404(Milestone, id=milestone_id)
    job = milestone.job
    
    # Create Payment record if payment was successful
    if not milestone.is_funded:
        # Update milestone status
        milestone.is_funded = True
        milestone.save()
        
        # Create Payment record
        Payment.objects.create(
            milestone=milestone,
            client=job.client,
            freelancer=job.freelancer,
            amount=milestone.amount,
            status='escrow'
        )
        
        messages.success(request, "Payment successful! Funds are now in escrow.")
    
    return redirect('job', pk=job.id)


@login_required
def payment_cancel(request, milestone_id):
    """
    Handle cancelled payment
    """
    milestone = get_object_or_404(Milestone, id=milestone_id)
    job = milestone.job
    
    messages.info(request, "Payment was cancelled.")
    return redirect('job', pk=job.id)


@login_required
def release_escrow_payment(request, payment_id):
    """
    Release escrowed funds to the freelancer
    """
    payment = get_object_or_404(Payment, id=payment_id)
    milestone = payment.milestone
    job = milestone.job
    
    # Ensure only the client can release funds
    if job.client != request.user.profile:
        messages.error(request, "Only the client can release escrowed funds.")
        return redirect('job', pk=job.id)
    
    # Check if payment is in escrow
    if payment.status != 'escrow':
        messages.error(request, "This payment is not in escrow.")
        return redirect('job', pk=job.id)
    
    # Check if milestone is completed
    if not milestone.is_completed:
        messages.error(request, "The milestone must be marked as completed before releasing funds.")
        return redirect('job', pk=job.id)
    
    try:
        # Update payment status
        payment.status = 'released'
        payment.save()
        
        # Here you would typically trigger a transfer to the freelancer's connected account
        # For demonstration, we'll just update the status
        
        messages.success(request, f"Funds released to {job.freelancer.name} successfully!")
        return redirect('job', pk=job.id)
        
    except Exception as e:
        messages.error(request, f"Error releasing funds: {str(e)}")
        return redirect('job', pk=job.id)


@login_required
def refund_escrow_payment(request, payment_id):
    """
    Refund escrowed funds to the client (for dispute resolution)
    """
    payment = get_object_or_404(Payment, id=payment_id)
    milestone = payment.milestone
    job = milestone.job
    
    # For simplicity, let's only allow admins to process refunds
    if not request.user.is_staff:
        messages.error(request, "Only administrators can process refunds.")
        return redirect('job', pk=job.id)
    
    # Check if payment is in escrow
    if payment.status != 'escrow':
        messages.error(request, "This payment is not in escrow.")
        return redirect('job', pk=job.id)
    
    try:
        # Update payment status
        payment.status = 'refunded'
        payment.save()
        
        # Here you would typically process a refund through Stripe
        # For demonstration, we'll just update the status
        
        # Update milestone status
        milestone.is_funded = False
        milestone.save()
        
        messages.success(request, f"Funds refunded to {job.client.name} successfully!")
        return redirect('job', pk=job.id)
        
    except Exception as e:
        messages.error(request, f"Error processing refund: {str(e)}")
        return redirect('job', pk=job.id)


@login_required
def create_checkout_session(request, milestone_id):
    """
    Create a Stripe Checkout Session for a milestone payment
    """
    milestone = get_object_or_404(Milestone, id=milestone_id)
    job = milestone.job
    
    # Ensure only the client can fund the milestone
    if job.client != request.user.profile:
        messages.error(request, "Only the client can fund this milestone.")
        return redirect('job', pk=job.id)
    
    # Check if milestone is already funded
    if milestone.is_funded:
        messages.error(request, "This milestone is already funded.")
        return redirect('job', pk=job.id)
    
    # Calculate the amount in cents for Stripe
    amount_cents = int(milestone.amount * 100)
    
    # Get domain for success and cancel URLs
    domain = get_domain(request)
    protocol = 'https' if (request.is_secure() or 'REPLIT' in os.environ) else 'http'
    
    try:
        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Milestone: {milestone.title}',
                            'description': f'Escrow payment for {job.title}',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f'{protocol}://{domain}{reverse("payment-success", kwargs={"milestone_id": milestone.id})}',
            cancel_url=f'{protocol}://{domain}{reverse("payment-cancel", kwargs={"milestone_id": milestone.id})}',
            metadata={
                'milestone_id': str(milestone.id),
                'job_id': str(job.id),
                'client_id': str(job.client.id),
                'freelancer_id': str(job.freelancer.id) if job.freelancer else '',
            },
        )
        
        # Redirect to Stripe Checkout
        return redirect(checkout_session.url)
    
    except stripe.error.StripeError as e:
        messages.error(request, f"Stripe error: {str(e)}")
        return redirect('job', pk=job.id)


@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Verify the webhook signature
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Get the milestone ID from metadata
        milestone_id = payment_intent.get('metadata', {}).get('milestone_id')
        
        if milestone_id:
            try:
                # Update milestone and create payment record
                milestone = Milestone.objects.get(id=milestone_id)
                
                if not milestone.is_funded:
                    milestone.is_funded = True
                    milestone.save()
                    
                    job = milestone.job
                    
                    # Create Payment record if it doesn't exist
                    if not Payment.objects.filter(milestone=milestone).exists():
                        Payment.objects.create(
                            milestone=milestone,
                            client=job.client,
                            freelancer=job.freelancer,
                            amount=milestone.amount,
                            stripe_payment_id=payment_intent.id,
                            status='escrow'
                        )
            except Milestone.DoesNotExist:
                pass
    # Handle checkout.session.completed event
    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Get the milestone ID from metadata
        milestone_id = session.get('metadata', {}).get('milestone_id')
        
        if milestone_id:
            try:
                # Update milestone and create payment record
                milestone = Milestone.objects.get(id=milestone_id)
                
                if not milestone.is_funded:
                    milestone.is_funded = True
                    milestone.save()
                    
                    job = milestone.job
                    
                    # Create Payment record if it doesn't exist
                    if not Payment.objects.filter(milestone=milestone).exists():
                        Payment.objects.create(
                            milestone=milestone,
                            client=job.client,
                            freelancer=job.freelancer,
                            amount=milestone.amount,
                            stripe_payment_id=session.payment_intent,
                            status='escrow'
                        )
            except Milestone.DoesNotExist:
                pass
    
    return HttpResponse(status=200)