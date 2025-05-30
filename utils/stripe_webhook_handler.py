import logging
from datetime import datetime, timedelta

import stripe
from aiogram import Bot
from aiohttp import web

from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils.user_management import update_subscription

stripe.api_key = STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


async def send_message_to_user(bot: Bot, user_id: int, message: str):
    try:
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        logger.error(f"Failed to send message to user {user_id}: {e}")


async def handle_stripe_webhook(request):
    bot = request.app['bot']
    payload = await request.text()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Error parsing payload: {str(e)}")
        return web.Response(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return web.Response(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        session_with_expand = stripe.checkout.Session.retrieve(
            session.id, expand=['customer']
        )
        user_id = int(session_with_expand.client_reference_id)
        plan = '1month'  # Always 1month plan

        if user_id:
            success = await update_subscription(user_id, plan)
            if success:
                logger.info(f"Subscription activated for user {user_id}")
                end_date = datetime.now() + timedelta(days=30)
                message = (f"Thank you for your subscription! Your access has been activated. "
                           f"Your subscription is valid until {end_date.strftime('%Y-%m-%d')}. "
                           f"You can now send me a link to download a video.")
                await send_message_to_user(bot, user_id, message)
            else:
                logger.error(
                    f"Error activating subscription for user {user_id}")
                message = "There was an error activating your subscription. Please contact support."
                await send_message_to_user(bot, user_id, message)
        else:
            logger.error(f"Missing user_id in session {session.id}")
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        user_id = int(session.client_reference_id)
        message = "Your payment session has expired. Please try again or contact support if you need assistance."
        await send_message_to_user(bot, user_id, message)
    else:
        logger.info(f"Unhandled event type: {event['type']}")

    return web.Response(status=200)


def setup_stripe_webhook(app):
    app.router.add_post('/stripe-webhook', handle_stripe_webhook)
