// Get Stripe publishable key
const stripe = Stripe(document.getElementById('stripe-publishable-key').value);

// Handle form submission
const form = document.getElementById('payment-form');
form.addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Disable the submit button to prevent multiple clicks
    document.getElementById('submit-button').disabled = true;
    
    // Submit the form
    form.submit();
});
