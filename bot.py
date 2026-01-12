

import asyncio
import logging
import os
import time
from typing import Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, PORT, HOST, TEMP_DIRECTORY

from handlers.handlers import register_handlers
from handlers.admin import register_admin_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VidZillaBot:

    def __init__(self):
        self.bot: Bot = None
        self.dp: Dispatcher = None
        self.app: web.Application = None
        self.runner: web.AppRunner = None
        self.cleanup_task: asyncio.Task = None

    async def _create_bot_and_dispatcher(self) -> None:
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher()

        # Clean up any existing webhooks
        logger.info("Deleting existing webhook")
        await self.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted")

    async def _register_handlers(self) -> None:
        register_handlers(self.dp)
        register_admin_handlers(self.dp)
        logger.info("All handlers registered")

    async def _create_web_app(self) -> None:
        self.app = web.Application()
        self.app["bot"] = self.bot

        # Setup webhook handler
        webhook_handler = SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot,
        )
        webhook_handler.register(self.app, path=WEBHOOK_PATH)
        setup_application(self.app, self.dp, bot=self.bot)

        # Add routes
        self.app.router.add_get("/", self._handle_root)
        self.app.router.add_get(WEBHOOK_PATH, self._handle_webhook_status)

        # Setup lifecycle handlers
        self.app.on_startup.append(self._on_startup)
        self.app.on_shutdown.append(self._on_shutdown)

    async def _handle_root(self, request: web.Request) -> web.Response:
        return web.Response(text="Vidzilla Bot - FREE Version is running!")

    async def _handle_webhook_status(self, request: web.Request) -> web.Response:
        return web.Response(text="Webhook is active and working")

    async def _on_startup(self, app: web.Application) -> None:
        webhook_url = WEBHOOK_URL + WEBHOOK_PATH
        logger.info(f"Setting webhook to {webhook_url}")
        await self.bot.set_webhook(webhook_url)
        logger.info("Webhook set successfully")
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_old_files())
        logger.info("Cleanup task started")

    async def _on_shutdown(self, app: web.Application) -> None:
        logger.info("Shutting down bot...")
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.bot:
            await self.bot.session.close()
        logger.info("Bot shutdown complete")
    
    async def _cleanup_old_files(self) -> None:
        """Remove temp files older than 1 hour"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                if not os.path.exists(TEMP_DIRECTORY):
                    continue
                    
                now = time.time()
                cleaned = 0
                for filename in os.listdir(TEMP_DIRECTORY):
                    filepath = os.path.join(TEMP_DIRECTORY, filename)
                    if os.path.isfile(filepath):
                        if now - os.path.getmtime(filepath) > 3600:  # 1 hour
                            os.unlink(filepath)
                            cleaned += 1
                
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} old temp files")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def create_app(self) -> web.Application:
        await self._create_bot_and_dispatcher()
        await self._register_handlers()
        await self._create_web_app()

        logger.info("Application created successfully")
        return self.app

    async def run(self) -> None:
        try:
            app = await self.create_app()
            self.runner = web.AppRunner(app)
            await self.runner.setup()

            site = web.TCPSite(self.runner, HOST, PORT)
            logger.info(f"Starting web application on {HOST}:{PORT}")
            await site.start()

            logger.info("Vidzilla Bot - FREE Version started successfully!")

            # Run forever
            await asyncio.Event().wait()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        logger.info("Cleaning up resources...")
        if self.runner:
            await self.runner.cleanup()
        logger.info("Cleanup complete")


async def main() -> None:
    logger.info("Starting Vidzilla Bot - FREE Version")

    bot_app = VidZillaBot()
    try:
        await bot_app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        exit(1)
