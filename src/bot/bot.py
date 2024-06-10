import logging
import os
from typing import Tuple

import openai
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UnauthorizedError

from src.handlers import (
    clear_handler,
    start_handler,
    security_check,
    user_chat_handler,
)


# Load  keys
def load_keys() -> Tuple[str, int, str]:
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    openai.organization = os.getenv("OPENAI_ORG")
    bot_token = os.getenv("BOTTOKEN")
    return api_id, api_hash, bot_token


async def bot() -> None:
    while True:
        api_id, api_hash, bot_token = load_keys()
        try:
            client = await TelegramClient(None, api_id, api_hash).start(
                bot_token=bot_token
            )
            logging.info("Successfully initiate bot")
        except UnauthorizedError:
            logging.error(
                "Unauthorized access. Please check your Telethon API ID, API hash"
            )
        except Exception as e:
            logging.error(f"Error occurred: {e}")

        client.add_event_handler(security_check)

        # Clear and Reset Session
        client.add_event_handler(clear_handler)

        # Clear and Reset Session
        client.add_event_handler(start_handler)

        # User and group chat
        #client.add_event_handler(group_chat_handler)
        client.add_event_handler(user_chat_handler)

        print("Bot is running")
        await client.run_until_disconnected()
