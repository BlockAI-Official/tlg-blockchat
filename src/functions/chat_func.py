import asyncio
import json
import logging
import os
from typing import List, Tuple
from datetime import datetime

import openai
from openai import OpenAI
from langchain_openai import ChatOpenAI

from src.utils import (
    LOG_PATH,
    SYS_MESS,
    Prompt,
    num_tokens_from_messages,
    read_existing_conversation,
    split_text,
)
from telethon.events import NewMessage

async def generate_sid(
    event: NewMessage, message: str, chat_id: int
) -> Tuple[str, Prompt]:
    try:
        curr_dt = datetime.now()
        dt = curr_dt.strftime("%Y%m%d%H%M%S")
        sess_id = f"{chat_id}_{dt}"
        data = {"session": sess_id}
        with open(f"{LOG_PATH}{chat_id}_session.json", "w") as f:
            json.dump(data, f)
        logging.debug(f"Done generating new session")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return sess_id


async def start_and_check(
    event: NewMessage, message: str, chat_id: int
) -> Tuple[str, Prompt]:
    try:
        prompt = []
        if not os.path.exists(f"{LOG_PATH}{chat_id}_session.json"):
            str_ch = await generate_sid(event,message,chat_id)
        else:
            with open(f"{LOG_PATH}{chat_id}_session.json", "r") as f:
                data = json.load(f)
            str_ch = data["session"]
        filename = f"{LOG_PATH}chats/{chat_id}_{str_ch}.json"
        logging.info(f"Session ID used {str_ch}")
        # file_num, filename, prompt = await read_existing_conversation(chat_id)
        prompt.append({"role": "user", "content": message, "session_id": str_ch})
        logging.debug(f"Done start and check")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return filename, prompt


def get_response(prompt: Prompt, filename: str) -> List[str]:
    try:
        #client = OpenAI()
        client = OpenAI(
            base_url="https://blockchatapi.azurewebsites.net/"
            #base_url = "http://localhost:8000"
        )
        completion = client.chat.completions.create(
            model="gpt-1337-turbo-pro-max",
            messages=prompt
        )
        logging.info(completion.choices[0].message)
        result = completion.choices[0].message
        num_tokens = completion.usage.total_tokens
        responses = f"{result.content}\n\n__({num_tokens} tokens used)__"
        prompt.append({"role": result.role, "content": result.content})
        data = {"messages": prompt}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logging.debug("Received response from openai")
    except Exception as e:
        responses = "💩 Blocky is being stupid, please try again "
        logging.error(f"Error occurred while getting response from Blocky: {e}")
    return responses


async def process_and_send_mess(event, text: str, limit=500) -> None:
    text_lst = text.split("```")
    cur_limit = 4096
    for idx, text in enumerate(text_lst):
        if idx % 2 == 0:
            mess_gen = split_text(text, cur_limit)
            for mess in mess_gen:
                await event.client.send_message(
                    event.chat_id, mess, background=True, silent=True
                )
                await asyncio.sleep(1)
        else:
            mess_gen = split_text(text, cur_limit, prefix="```\n", sulfix="\n```")
            for mess in mess_gen:
                await event.client.send_message(
                    event.chat_id, mess, background=True, silent=True
                )
                await asyncio.sleep(1)
