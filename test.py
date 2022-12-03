"""Make some requests to OpenAI's chatbot"""

import time
import asyncio
import nest_asyncio
import os
import requests
import logging
import flask
from flask import g
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
# from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from playwright.sync_api import sync_playwright

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)



load_dotenv()
# start the browser
APP = flask.Flask(__name__)
PLAY = sync_playwright().start()
BROWSER = PLAY.chromium.launch_persistent_context(
    user_data_dir="/tmp/playwright",
    headless=False,
)
PAGE = BROWSER.new_page()

# chatGPT methods
def get_input_box():
    """Get the child textarea of `PromptTextarea__TextareaWrapper`"""
    return PAGE.query_selector("textarea")

def is_logged_in():
    # See if we have a textarea with data-id="root"
    return get_input_box() is not None

def send_message(message):
    # Send the message
    box = get_input_box()
    box.click()
    box.fill(message)
    box.press("Enter")

def get_last_message():
    """Get the latest message"""
    page_elements = PAGE.query_selector_all("div[class*='ConversationItem__Message']")
    last_element = page_elements[-1]
    return last_element.inner_text()

async def send_and_receive(message):
    print("Sending message to chatGPT: ", message)
    send_message(message)
    time.sleep(10) # TODO: there are about ten million ways to be smarter than this
    response = get_last_message()
    print("Response from chatGPT: ", response)
    return response

# Telegram Methods
last_update = 0
url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/getUpdates"
async def send_to_Telegram(message, chat_id, message_id):
    """Check for updates"""
    print("Sending to telegram")
    global url
    params = {"chat_id": chat_id, "message_id": message_id, "text": message}
    global last_update
    if last_update != 0:
        # params['offset'] = last_update + 1
        params['offset'] = -2

    response = requests.get(url, params)
    if response.status_code == 200:
        print("Response from telegram: ", response)
    else:
        print("Error sending message:", response.text)

async def check_for_new_updates():
    """Check for updates"""
    print("Checking for updates")
    global url
    params = {"allowed_updates": ["message"]}
    global last_update
    if last_update != 0:
        # params['offset'] = last_update + 1
        params['offset'] = -2

    response = requests.get(url, params)
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            if data["result"]:
                #  print updates
                for update in data["result"]:
                    print(update)
                    last_update = update['update_id']
                    #{'update_id': 38532680, 'message': {'message_id': 10706, 'from': {'id': 564733099, 'is_bot': False, 'first_name': 'Anon', 'username': 'A_Little_Anon', 'language_code': 'en'}, 'chat': {'id': 564733099, 'first_name': 'Anon', 'username': 'A_Little_Anon', 'type': 'private'}, 'date': 1670021704, 'text': 'Ugh. HI again'}}
                    # {'update_id': 38532681, 'message': {'message_id': 10707, 'from': {'id': 564733099, 'is_bot': False, 'first_name': 'Anon', 'username': 'A_Little_Anon', 'language_code': 'en'}, 'chat': {'id': -614125039, 'title': 'LOKI EXTENSION LOGS GROUP', 'type': 'group', 'all_members_are_administrators': True}, 'date': 1670022564, 'text': 'Hi'}}
                    # {'update_id': 38532682, 'message': {'message_id': 10708, 'from': {'id': 564733099, 'is_bot': False, 'first_name': 'Anon', 'username': 'A_Little_Anon', 'language_code': 'en'}, 'chat': {'id': 564733099, 'first_name': 'Anon', 'username': 'A_Little_Anon', 'type': 'private'}, 'date': 1670022620, 'text': 'Finally, Xup?'}}

                    #  get the chat id
                    chat_id = update["message"]["chat"]["id"]
                    message_id = update["message"]["message_id"]
                    # print chat id and message id
                    print(f"Chat ID: {chat_id}, Message ID: {message_id}")
                    #  get the message
                    message = update["message"]["text"]
                    #  send the message to openai and receive a response
                    response = await send_and_receive(message)
                    print("Response to be sent to telegram: ", response)
                    # #  send the response to telegram
                    # send_message_to_telegram(chat_id, response)
                return data["result"][0]
            else:
                print("No new updates")
                return None
    # print an error message with the response
    print("Error getting updates or:", response.text)
    return None

async def check_for_new_updates_periodically():
    """Check for new updates every 2 seconds"""
    while True:
        await check_for_new_updates()
        time.sleep(5)


@APP.route("/chat", methods=["GET"])
async def chat():
    message = flask.request.args.get("q")
    return await send_and_receive(message)

def start_browser():
    PAGE.goto("https://chat.openai.com/")
    if not is_logged_in():
        print("Please log in to OpenAI Chat")
        print("Press enter when you're done")
        input()
    else:        
        nest_asyncio.apply()
        asyncio.run(check_for_new_updates_periodically())
        # check_for_new_updates_periodically()
        APP.run(port=5001, threaded=False)

if __name__ == "__main__":
    start_browser()
