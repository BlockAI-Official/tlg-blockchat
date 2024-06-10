import asyncio
import logging
import random

from telethon.events import NewMessage, StopPropagation, register
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction

from src.functions.chat_func import get_response, process_and_send_mess, start_and_check, generate_sid
from src.utils import RANDOM_ACTION, check_chat_type


@register(NewMessage())
async def security_check(event: NewMessage) -> None:
    client = event.client
    chat_id = event.chat_id
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    # if chat_id not in ALLOW_USERS:
    #     await client.send_message(
    #         chat_id, f"This is personal property, you are not allowed to proceed!"
    #     )
    #     raise StopPropagation

@register(NewMessage(pattern="/clear"))
async def clear_handler(event: NewMessage) -> None:
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "User":
        return
    else:
        logging.info(str(chat_id) + " - " + message)
        logging.info("Check chat type User done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    session_id = await generate_sid (event, message, chat_id)
    raise StopPropagation

@register(NewMessage(pattern="/start"))
async def start_handler(event: NewMessage) -> None:
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "User":
        return
    else:
        logging.info(str(chat_id) + " - " + message)
        logging.info("Check chat type User done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    try:
        wcm_msg="Hi I'm Blocky, How can I help you?"
        await process_and_send_mess(event, wcm_msg)
        logging.info(f"Sent Hi message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling user chat: {e}")
        await event.reply("**Fail to get response**")
    raise StopPropagation


@register(NewMessage)
async def user_chat_handler(event: NewMessage) -> None:
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "User":
        return
    else:
        logging.info(str(chat_id) + " - " + message)
        logging.info("Check chat type User done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    filename, prompt = await start_and_check(event, message, chat_id)
    
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, get_response, prompt, filename)
    while not future.done():
        random_choice = random.choice(RANDOM_ACTION)
        await asyncio.sleep(2)
        await client(SetTypingRequest(peer=chat_id, action=random_choice))
    response = await future
    # # Get response from openai and send to chat_id
    # response = get_response(prompt, filename)
    try:
        await process_and_send_mess(event, response)
        logging.info(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling user chat: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")