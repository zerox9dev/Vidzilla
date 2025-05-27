import stripe

from config import (
    STRIPE_CANCEL_URL,
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
    SUBSCRIPTION_PLANS,
)

stripe.api_key = STRIPE_SECRET_KEY


def create_checkout_session(plan, user_id):
    if plan not in SUBSCRIPTION_PLANS:
        raise ValueError("Invalid subscription plan")

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': SUBSCRIPTION_PLANS[plan]['name'],
                },
                'unit_amount': SUBSCRIPTION_PLANS[plan]['price'],
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=STRIPE_SUCCESS_URL,
        cancel_url=STRIPE_CANCEL_URL,
        client_reference_id=str(user_id),
        metadata={'plan': plan}
    )
    return session.url


def verify_payment(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == 'paid'
    except Exception as e:
        print(f"Error verifying payment: {str(e)}")
        return False
