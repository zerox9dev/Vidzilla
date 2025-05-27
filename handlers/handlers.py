from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS, FREE_LIMIT, SUBSCRIPTION_PLANS
from handlers import facebook, instagram, pinterest, tiktok, twitter, youtube
from utils.stripe_utils import create_checkout_session
from utils.user_management import (
    activate_coupon,
    check_user_limit,
    create_coupon,
    get_limit_exceeded_message,
    get_usage_stats,
    is_admin,
    get_users_with_usernames,
)


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


class AdminActions(StatesGroup):
    waiting_for_coupon_duration = State()
    waiting_for_coupon = State()


async def send_welcome(message: Message, state: FSMContext):
    await message.answer(
        f"""<b>👋 Hi! Welcome to the Social Media Video Downloader Bot!</b>

I can download videos from Instagram Reels, TikTok, YouTube, Facebook, Twitter, and Pinterest.

<b>🎁 Free Trial:</b> You have {FREE_LIMIT} free downloads to try out the bot.

<b>Available commands:</b>
/start - Start working with the bot
/help - Get detailed help
/subscribe - View subscription plans

To use the bot, simply send me a video link from any supported platform.

<b>💡 Tip:</b> If you need more than {FREE_LIMIT} downloads, check out our subscription plans with /subscribe command!""",
        parse_mode="HTML"
    )
    await state.set_state(DownloadVideo.waiting_for_link)


async def send_help(message: Message):
    help_text = f"""This bot helps download videos from Instagram Reels, TikTok, YouTube, Facebook, Twitter, and Pinterest.

How to use:
1. Send the bot a link to a video.
2. The bot will process the link and return the video in two formats:
 - As a video message
 - As a document file

You have {FREE_LIMIT} free downloads. After that, you'll need to subscribe.

Commands:
/start - Start working with the bot
/help - Show this help message
/subscribe - View and purchase subscription plans"""

    if is_admin(message.from_user.id):
        help_text += """

Admin commands:
/generate_coupon - Generate a new coupon
/stats - View usage statistics
/list_users - List users with usernames"""

    await message.answer(help_text)


async def process_link(message: Message, state: FSMContext, bot: Bot):
    url = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not check_user_limit(user_id, username):
        await message.answer(get_limit_exceeded_message())
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

    for plan, details in SUBSCRIPTION_PLANS.items():
        price_in_dollars = details['price'] / 100  # Convert cents to dollars
        button_text = f"{details['name']} - ${price_in_dollars:.2f}"
        checkout_url = create_checkout_session(plan, user_id)
        keyboard.append([types.InlineKeyboardButton(
            text=button_text, url=checkout_url)])

    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("Please choose a subscription plan:", reply_markup=reply_markup)


async def generate_coupon_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 month", callback_data="coupon_1month")],
        [InlineKeyboardButton(
            text="3 months", callback_data="coupon_3months")],
        [InlineKeyboardButton(
            text="Lifetime", callback_data="coupon_lifetime")]
    ])

    await message.answer("Please choose the coupon duration:", reply_markup=keyboard)
    await state.set_state(AdminActions.waiting_for_coupon_duration)


async def handle_coupon_generation(callback_query: types.CallbackQuery, state: FSMContext):
    duration_map = {
        'coupon_1month': '1month',
        'coupon_3months': '3months',
        'coupon_lifetime': 'lifetime'
    }
    duration = duration_map.get(callback_query.data)

    if not duration:
        await callback_query.message.answer("Invalid duration. Please use the provided buttons.")
        return

    coupon_code = create_coupon(duration)

    await callback_query.message.answer("Coupon generated successfully!")
    await callback_query.message.answer(f"`{coupon_code}`", parse_mode="Markdown")

    await callback_query.answer()
    await state.clear()


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
        await message.answer("Coupon successfully activated! You now have access to premium features.")
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


def register_handlers(dp):
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(send_help, Command(commands=['help']))
    dp.message.register(subscribe_command, Command(commands=['subscribe']))
    dp.message.register(generate_coupon_command,
                        Command(commands=['generate_coupon']))
    dp.message.register(stats_command, Command(commands=['stats']))
    dp.message.register(activate_coupon_command,
                        Command(commands=['activate_coupon']))
    dp.message.register(process_link, DownloadVideo.waiting_for_link)
    dp.callback_query.register(
        handle_coupon_generation, AdminActions.waiting_for_coupon_duration)
    dp.message.register(handle_coupon_activation,
                        AdminActions.waiting_for_coupon)
    dp.message.register(list_users_command, Command(commands=['list_users']))
