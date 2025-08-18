from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import PLATFORM_IDENTIFIERS, SUBSCRIPTION_PLANS
from handlers.social_media.video_processor import detect_platform_and_process
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

<b>Also check my free bots:</b>\n Translate bot <b>@Ninjatrbot</b>\n Speech-to-text <b>@voiceletbot</b>\n AI ChatGPT <b>@DockMixAIbot</b>"""

    await message.answer(welcome_message, parse_mode="HTML", disable_web_page_preview=True)
    await state.set_state(DownloadVideo.waiting_for_link)


async def create_subscription_keyboard():
    """Subscription keyboard disabled in main branch

    Channel subscription functionality is available in 'channel-subscription-feature' branch.
    """
    return None


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

    # Channel subscription check disabled in main branch
    # All users have access without subscription requirements

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
    """Subscription callback disabled in main branch

    Channel subscription functionality is available in 'channel-subscription-feature' branch.
    """
    await callback_query.answer("Subscription checking is disabled in this version.")


async def donate_command(message: types.Message, state: FSMContext):
    """Donation functionality disabled in main branch

    Payment functionality is available in 'stripe-payments-feature' branch.
    In main branch, all features are free without payment requirements.
    """
    await message.answer(
        "💝 Thank you for your interest in supporting the bot!\n\n"
        "Currently, all features are completely free to use. "
        "Payment functionality is available in a separate branch for those who want to contribute.\n\n"
        "Enjoy unlimited video downloads! 🎉"
    )


async def activate_coupon_command(message: Message, state: FSMContext):
    await message.answer("Please enter your coupon code:")
    await state.set_state(AdminActions.waiting_for_coupon)


async def handle_coupon_activation(message: Message, state: FSMContext):
    coupon_code = message.text.strip()
    activation_result = activate_coupon(message.from_user.id, coupon_code)

    if activation_result:
        await message.answer(
            "Coupon successfully activated! Thank you for supporting the bot. All features remain free for everyone!"
        )
    else:
        await message.answer(
            "Invalid or already used coupon code. Please try again or contact the admin."
        )

    await state.set_state(DownloadVideo.waiting_for_link)


async def help_command(message: Message):
    """Display help information and list of supported platforms"""

    help_message = f"""

<b>How to use the bot:</b>
1. Copy a video link from any supported platform
2. Paste the link in this chat
3. Wait for the bot to process and download the video

"""

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
