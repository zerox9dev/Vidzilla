from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import PLATFORM_IDENTIFIERS, REQUIRED_CHANNELS, SUBSCRIPTION_PLANS
from handlers.social_media.utils import detect_platform_and_process
from utils.stripe_utils import create_checkout_session
from utils.user_management import (
    activate_coupon,
    check_channel_subscription,
    create_user,
    get_user,
    increment_downloads,
    update_user_language,
)


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


class AdminActions(StatesGroup):
    waiting_for_coupon = State()


async def send_welcome(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    language_code = message.from_user.language_code

    # Get or create user with language
    user = get_user(user_id)
    if user:
        # Update language if it changed
        if language_code and user.get("language") != language_code:
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
        row.append(InlineKeyboardButton(text=f"{info['title']}", url=info["url"]))

    # Add all subscription buttons in one row
    if row:
        keyboard.append(row)

    # Add a button to check subscription status in a separate row
    keyboard.append(
        [InlineKeyboardButton(text="✅ Check subscription", callback_data="check_subscription")]
    )

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
        subscription_message = (
            "<b>⚠️ You need to subscribe to these channels to use the bot:</b>\n\n"
        )
        row = []

        keyboard = await create_subscription_keyboard()
        await message.answer(
            subscription_message,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
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
        await callback_query.message.answer(
            "✅ You are subscribed to all required channels! You can now use the bot."
        )
    else:
        await callback_query.answer("❌ You need to subscribe to all required channels")
        subscription_message = "<b>⚠️ You are not subscribed to these channels:</b>\n\n"

        keyboard = await create_subscription_keyboard()
        await callback_query.message.answer(
            subscription_message,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    await callback_query.answer()


async def donate_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = []

    plan = "1month"
    details = SUBSCRIPTION_PLANS[plan]
    price_in_dollars = details["price"] / 100  # Convert cents to dollars
    button_text = f"Donate ${price_in_dollars:.2f} to support us"
    checkout_url = create_checkout_session(plan, user_id)
    keyboard.append([types.InlineKeyboardButton(text=button_text, url=checkout_url)])

    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        "Thank you for considering a donation! Your support helps us maintain our servers and continue providing this service:",
        reply_markup=reply_markup,
    )


async def activate_coupon_command(message: Message, state: FSMContext):
    await message.answer("Please enter your coupon code:")
    await state.set_state(AdminActions.waiting_for_coupon)


async def handle_coupon_activation(message: Message, state: FSMContext):
    coupon_code = message.text.strip()
    activation_result = activate_coupon(message.from_user.id, coupon_code)

    if activation_result:
        await message.answer(
            "Coupon successfully activated! You now have access to the bot for one month."
        )
    else:
        await message.answer(
            "Invalid or already used coupon code. Please try again or contact the admin."
        )

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
    dp.message.register(send_welcome, Command(commands=["start"]))
    dp.message.register(help_command, Command(commands=["help"]))
    dp.message.register(donate_command, Command(commands=["donate", "subscribe"]))
    dp.message.register(activate_coupon_command, Command(commands=["activate_coupon"]))
    dp.message.register(handle_coupon_activation, AdminActions.waiting_for_coupon)
    dp.callback_query.register(
        check_subscription_callback, lambda c: c.data == "check_subscription"
    )

    # Обрабатывать ссылки в любом состоянии
    dp.message.register(
        process_link,
        lambda msg: msg.text
        and any(platform_id in msg.text.lower() for platform_id in PLATFORM_IDENTIFIERS),
    )

    # Также обрабатывать ссылки в состоянии waiting_for_link (для обратной совместимости)
    dp.message.register(process_link, DownloadVideo.waiting_for_link)
