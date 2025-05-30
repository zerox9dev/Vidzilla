from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS, SUBSCRIPTION_PLANS
from handlers import facebook, instagram, pinterest, tiktok, twitter, youtube
from utils.stripe_utils import create_checkout_session
from utils.user_management import (
    activate_coupon,
    check_user_subscription,
    create_coupon,
    get_subscription_required_message,
    get_usage_stats,
    is_admin,
    get_users_with_usernames,
    users_collection,
    broadcast_message_to_all_users,
)


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


class AdminActions(StatesGroup):
    waiting_for_coupon_duration = State()
    waiting_for_coupon = State()
    waiting_for_broadcast_message = State()


async def send_welcome(message: Message, state: FSMContext):
    await message.answer(
        f"""<b>👋 Hi, Welcome!</b>

I can download videos from Instagram Reels, TikTok, YouTube, Facebook, Twitter, and Pinterest.

<b>🔒 Subscription Required:</b> To use this bot, a monthly subscription of $1 is required. This small fee helps us maintain our servers.

To use the bot, simply send me a video link from any supported platform after subscribing.

<b>Available commands:</b>
/start - Start working with the bot
/help - Get detailed help
/subscribe - Subscribe to use the bot

""",
        parse_mode="HTML"
    )
    await state.set_state(DownloadVideo.waiting_for_link)


async def send_help(message: Message):
    help_text = """This bot helps download videos from Instagram Reels, TikTok, YouTube, Facebook, Twitter, and Pinterest.

How to use:
1. Subscribe to the bot for $1/month using the /subscribe command
2. Send the bot a link to a video
3. The bot will process the link and return the video in two formats:
 - As a video message
 - As a document file

Commands:
/start - Start working with the bot
/help - Show this help message
/subscribe - Subscribe to use the bot"""

    await message.answer(help_text)


async def process_link(message: Message, state: FSMContext, bot: Bot):
    url = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not check_user_subscription(user_id, username):
        await message.answer(get_subscription_required_message())
        return

    await message.answer("Processing your link...")
    try:
        if 'instagram.com' in url:
            await instagram.process_instagram(message, bot, url)
        elif 'tiktok.com' in url:
            await tiktok.process_tiktok(message, bot, url)
        elif 'x.com' in url or 'twitter.com' in url:
            await twitter.process_twitter(message, bot, url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            await youtube.process_youtube(message, bot, url)
        elif 'facebook.com' in url:
            await facebook.process_facebook(message, bot, url)
        elif 'pin.it' in url or 'pinterest.com' in url:
            await pinterest.process_pinterest(message, bot, url)
        else:
            await message.answer("Unsupported platform. Please provide a link from Instagram, TikTok, YouTube, Facebook, Twitter, or Pinterest.")
    except Exception as e:
        await message.answer(f"Error processing video: {str(e)}")

    await state.set_state(DownloadVideo.waiting_for_link)


async def subscribe_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = []

    plan = '1month'
    details = SUBSCRIPTION_PLANS[plan]
    price_in_dollars = details['price'] / 100  # Convert cents to dollars
    button_text = f"{details['name']} - ${price_in_dollars:.2f}"
    checkout_url = create_checkout_session(plan, user_id)
    keyboard.append([types.InlineKeyboardButton(text=button_text, url=checkout_url)])

    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("To use this bot, a subscription is required. This helps us maintain our servers and provide high-quality service:", reply_markup=reply_markup)


async def generate_coupon_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    # Only 1-month coupons are available now
    coupon_code = create_coupon('1month')
    await message.answer("Coupon generated successfully!")
    await message.answer(f"`{coupon_code}`", parse_mode="Markdown")


async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    stats = get_usage_stats()
    stats_message = (
        f"Usage Statistics:\n\n"
        f"Total Users: {stats['total_users']}\n"
        f"Users With Username: {stats['users_with_username']}\n"
        f"Active Subscriptions: {stats['active_subscriptions']}\n"
        f"Total Downloads: {stats['total_downloads']}\n"
        f"Unused Coupons: {stats['unused_coupons']}"
    )
    await message.answer(stats_message)


async def activate_coupon_command(message: Message, state: FSMContext):
    await message.answer("Please enter your coupon code:")
    await state.set_state(AdminActions.waiting_for_coupon)


async def handle_coupon_activation(message: Message, state: FSMContext):
    coupon_code = message.text.strip()
    activation_result = activate_coupon(message.from_user.id, coupon_code)

    if activation_result:
        await message.answer("Coupon successfully activated! You now have access to the bot for one month.")
    else:
        await message.answer("Invalid or already used coupon code. Please try again or contact the admin.")

    await state.set_state(DownloadVideo.waiting_for_link)


async def list_users_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    users = get_users_with_usernames()
    if not users:
        await message.answer("No users with usernames found.")
        return

    # Limit to first 20 users to avoid message too long errors
    users = users[:20]
    user_list = "\n".join([f"ID: {user['user_id']}, Username: @{user['username']}, Downloads: {user['downloads_count']}" for user in users])
    
    await message.answer(f"Users with usernames (showing first {len(users)}):\n\n{user_list}")


async def broadcast_command(message: Message, state: FSMContext):
    """Command to send a notification to all users that the bot is working again."""
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return
    
    await message.answer("Please enter the message you want to broadcast to all users:")
    await state.set_state(AdminActions.waiting_for_broadcast_message)


async def handle_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    """Handle the broadcast message entered by the admin."""
    broadcast_message = message.text
    
    await message.answer("Broadcasting message to all users. This may take some time...")
    
    success_count, failed_count = await broadcast_message_to_all_users(bot, broadcast_message)
    
    await message.answer(f"Broadcast completed.\nSuccess: {success_count}\nFailed: {failed_count}")
    await state.set_state(DownloadVideo.waiting_for_link)


def register_handlers(dp):
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(send_help, Command(commands=['help']))
    dp.message.register(subscribe_command, Command(commands=['subscribe']))
    dp.message.register(generate_coupon_command, Command(commands=['generate_coupon']))
    dp.message.register(stats_command, Command(commands=['stats']))
    dp.message.register(activate_coupon_command, Command(commands=['activate_coupon']))
    dp.message.register(broadcast_command, Command(commands=['broadcast']))
    dp.message.register(process_link, DownloadVideo.waiting_for_link)
    dp.message.register(handle_coupon_activation, AdminActions.waiting_for_coupon)
    dp.message.register(handle_broadcast_message, AdminActions.waiting_for_broadcast_message)
    dp.message.register(list_users_command, Command(commands=['list_users']))
