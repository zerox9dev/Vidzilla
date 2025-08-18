# Stripe webhook handler disabled in main branch
# Payment functionality is available in 'stripe-payments-feature' branch

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiohttp import web

from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils.user_management import update_subscription

logger = logging.getLogger(__name__)


async def send_message_to_user(bot: Bot, user_id: int, message: str):
    try:
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        logger.error(f"Failed to send message to user {user_id}: {e}")


async def handle_stripe_webhook(request):
    """Stripe webhook handler disabled in main branch

    Payment functionality is available in 'stripe-payments-feature' branch.
    In main branch, all features are free without payment requirements.

    Returns:
        web.Response: 200 OK response indicating webhook is disabled
    """
    logger.info("Stripe webhook called but payments are disabled in main branch")
    return web.Response(status=200, text="Payments disabled in main branch")


def setup_stripe_webhook(app):
    app.router.add_post("/stripe-webhook", handle_stripe_webhook)
