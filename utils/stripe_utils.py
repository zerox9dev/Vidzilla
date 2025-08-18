# Stripe payments functionality disabled in main branch
# Payment functionality is available in 'stripe-payments-feature' branch

from config import (
    STRIPE_CANCEL_URL,
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
    SUBSCRIPTION_PLANS,
)


def create_checkout_session(plan, user_id):
    """Stripe payments disabled in main branch

    Payment functionality is available in 'stripe-payments-feature' branch.
    In main branch, all features are free without payment requirements.

    Returns:
        str: Placeholder URL indicating payments are disabled
    """
    return "https://example.com/payments-disabled"


def verify_payment(session_id):
    """Payment verification disabled in main branch

    Payment functionality is available in 'stripe-payments-feature' branch.
    In main branch, all features are free without payment requirements.

    Returns:
        bool: Always False since payments are disabled
    """
    return False
