from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS, SUBSCRIPTION_PLANS, REQUIRED_CHANNELS, PLATFORM_IDENTIFIERS
from handlers.social_media.utils import detect_platform_and_process
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
    get_user,
    increment_downloads,
    create_user,
    update_user_language,
    get_user_language,
    check_channel_subscription,
)


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


class AdminActions(StatesGroup):
    waiting_for_coupon_duration = State()
    waiting_for_coupon = State()
    waiting_for_broadcast_message = State()


async def send_welcome(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    language_code = message.from_user.language_code
    
    # Get or create user with language
    user = get_user(user_id)
    if user:
        # Update language if it changed
        if language_code and user.get('language') != language_code:
            update_user_language(user_id, language_code)
    else:
        create_user(user_id, username, language_code)
    
    welcome_message = f"""<b>👋 Welcome!</b>

Send me any video link to get started.
Use /help to see the list of supported platforms.

<b>Also check my free bots:</b>\n Translate bot <b>@Ninjatrbot</b>\n Speech-to-text <b>@voiceletbot</b>\n AI ChatGPT <b>@DockMixAIbot</b>"""
    
    await message.answer(welcome_message, parse_mode="HTML", disable_web_page_preview=True)
    await state.set_state(DownloadVideo.waiting_for_link)


async def create_subscription_keyboard():
    """Create a keyboard with subscription channel buttons"""
    keyboard = []
    row = []
    
    # Add subscription buttons horizontally in one row
    for channel_id, info in REQUIRED_CHANNELS.items():
        row.append(InlineKeyboardButton(text=f"{info['title']}", url=info['url']))
    
    # Add all subscription buttons in one row
    if row:
        keyboard.append(row)
    
    # Add a button to check subscription status in a separate row
    keyboard.append([InlineKeyboardButton(text="✅ Check subscription", callback_data="check_subscription")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def process_link(message: Message, state: FSMContext, bot: Bot):
    url = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    language_code = message.from_user.language_code
    
    # Получаем текущее состояние пользователя
    current_state = await state.get_state()
    
    # Если пользователь ещё не инициализирован (не нажал /start)
    if not current_state:
        # Создаем пользователя, если его нет
        user = get_user(user_id)
        if not user:
            create_user(user_id, username, language_code)
            # Отправляем краткое приветствие
            await message.answer("👋 Welcome to the Video Downloader Bot! Processing your link...")
        
        # Устанавливаем состояние
        await state.set_state(DownloadVideo.waiting_for_link)
    
    # Check if user is subscribed to required channels
    is_subscribed, not_subscribed_channels = await check_channel_subscription(user_id, bot)
    
    # If user is not subscribed to all required channels, show a message with subscription instructions
    if not is_subscribed:
        subscription_message = "<b>⚠️ You need to subscribe to these channels to use the bot:</b>\n\n"
        row = []

        
        keyboard = await create_subscription_keyboard()
        await message.answer(subscription_message, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
        return
    
    # Increment download counter but don't check for subscription
    if get_user(user_id):
        increment_downloads(user_id)
        # Update language if available
        if language_code:
            update_user_language(user_id, language_code)
    else:
        create_user(user_id, username, language_code)
        increment_downloads(user_id)

    progress_msg = await message.answer("⏳ Processing your link... 0%")
    
    try:
        # Use the new function to detect the platform and process the video
        platform_processed = await detect_platform_and_process(message, bot, url, progress_msg)
        
        if not platform_processed:
            await progress_msg.edit_text(
                "❌ Unsupported platform. Please use /help to see all supported platforms."
            )
            return
    except Exception as e:
        await progress_msg.edit_text(f"❌ Error processing video: {str(e)}")

    await state.set_state(DownloadVideo.waiting_for_link)


async def check_subscription_callback(callback_query: types.CallbackQuery, bot: Bot):
    """Handle callback for checking subscription status"""
    user_id = callback_query.from_user.id
    is_subscribed, not_subscribed_channels = await check_channel_subscription(user_id, bot)
    
    if is_subscribed:
        await callback_query.answer("✅ You are subscribed to all required channels!")
        await callback_query.message.answer("✅ You are subscribed to all required channels! You can now use the bot.")
    else:
        await callback_query.answer("❌ You need to subscribe to all required channels")
        subscription_message = "<b>⚠️ You are not subscribed to these channels:</b>\n\n"
        
        keyboard = await create_subscription_keyboard()
        await callback_query.message.answer(subscription_message, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
    
    await callback_query.answer()


async def donate_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = []

    plan = '1month'
    details = SUBSCRIPTION_PLANS[plan]
    price_in_dollars = details['price'] / 100  # Convert cents to dollars
    button_text = f"Donate ${price_in_dollars:.2f} to support us"
    checkout_url = create_checkout_session(plan, user_id)
    keyboard.append([types.InlineKeyboardButton(text=button_text, url=checkout_url)])

    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("Thank you for considering a donation! Your support helps us maintain our servers and continue providing this service:", reply_markup=reply_markup)


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
        f"Users With Language: {stats['users_with_language']}\n"
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
    user_list = "\n".join([
        f"ID: {user['user_id']}, Username: @{user['username']}, "
        f"Lang: {user.get('language', 'N/A')}, Downloads: {user['downloads_count']}"
        for user in users
    ])
    
    await message.answer(f"Users with usernames (showing first {len(users)}):\n\n{user_list}")


async def language_stats_command(message: Message):
    """Command to show statistics about users' languages."""
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return
    
    # Aggregate users by language
    pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    language_stats = list(users_collection.aggregate(pipeline))
    
    if not language_stats:
        await message.answer("No language statistics available.")
        return
    
    # Format the statistics message
    stats_message = "User language statistics:\n\n"
    for stat in language_stats:
        language = stat["_id"] if stat["_id"] else "Not specified"
        count = stat["count"]
        stats_message += f"{language}: {count} users\n"
    
    await message.answer(stats_message)


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


async def help_command(message: Message):
    """Display help information and list of supported platforms"""
    # Get a unique and sorted list of supported platforms
    supported_platforms = sorted(set(PLATFORM_IDENTIFIERS.values()))
    platforms_list = "\n".join(f"• {platform}" for platform in supported_platforms)
    
    help_message = f"""<b>📋 Supported Platforms:</b>

{platforms_list}

<b>How to use the bot:</b>
1. Subscribe to the required channels
2. Copy a video link from any supported platform
3. Paste the link in this chat
4. Wait for the bot to process and download the video

<b>Available commands:</b>
/start - Start the bot and see welcome message
/help - Show this help message with supported platforms
/donate - Support the developer

<b>Required channel subscriptions:</b>
"""
    
    # Add channel information to help message
    for channel_id, info in REQUIRED_CHANNELS.items():
        help_message += f"\n- <a href='{info['url']}'>{info['title']}</a>"
    
    await message.answer(help_message, parse_mode="HTML", disable_web_page_preview=True)


def register_handlers(dp):
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(help_command, Command(commands=['help']))
    dp.message.register(donate_command, Command(commands=['donate', 'subscribe']))
    dp.message.register(generate_coupon_command, Command(commands=['generate_coupon']))
    dp.message.register(stats_command, Command(commands=['stats']))
    dp.message.register(activate_coupon_command, Command(commands=['activate_coupon']))
    dp.message.register(broadcast_command, Command(commands=['broadcast']))
    dp.message.register(handle_coupon_activation, AdminActions.waiting_for_coupon)
    dp.message.register(handle_broadcast_message, AdminActions.waiting_for_broadcast_message)
    dp.message.register(list_users_command, Command(commands=['list_users']))
    dp.message.register(language_stats_command, Command(commands=['language_stats']))
    dp.callback_query.register(check_subscription_callback, lambda c: c.data == "check_subscription")
    
    # Обрабатывать ссылки в любом состоянии
    dp.message.register(process_link, lambda msg: msg.text and any(
        platform_id in msg.text.lower() for platform_id in PLATFORM_IDENTIFIERS
    ))
    
    # Также обрабатывать ссылки в состоянии waiting_for_link (для обратной совместимости)
    dp.message.register(process_link, DownloadVideo.waiting_for_link)
