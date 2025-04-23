// Helper functions for Stripe payments

// Handle release payment buttons
document.addEventListener("DOMContentLoaded", function() {
    // Find all release payment buttons
    const releaseButtons = document.querySelectorAll(".release-payment-btn");
    
    if (releaseButtons.length > 0) {
        releaseButtons.forEach(button => {
            button.addEventListener("click", function(e) {
                if (!confirm("Are you sure you want to release this payment? This action cannot be undone.")) {
                    e.preventDefault();
                } else {
                    // Disable button to prevent double clicks
                    button.disabled = true;
                    button.textContent = "Processing...";
                }
            });
        });
    }
    
    // Handle payment form submission
    const paymentForm = document.getElementById("payment-form");
    if (paymentForm) {
        paymentForm.addEventListener("submit", function(e) {
            const submitButton = document.getElementById("submit-button");
            submitButton.disabled = true;
            submitButton.textContent = "Processing...";
        });
    }
});
