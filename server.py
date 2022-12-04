"""Make some requests to OpenAI's chatbot"""

import time
import re
import os
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright



load_dotenv()

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
    last_page_element_text = PAGE.query_selector_all("div[class*='ConversationItem__Message']")[-1].inner_text()
    time.sleep(1)
    last_page_element_text_latest = PAGE.query_selector_all("div[class*='ConversationItem__Message']")[-1].inner_text()
    if last_page_element_text == last_page_element_text_latest:
        return last_page_element_text
    else:
        # print(f"Last message changed from '{last_page_element_text}' to '{last_page_element_text_latest}'")
        return get_last_message()

def send_and_receive(message, trial=1):
    if trial == 1:
        print(f"Sending message to chatGPT: '{message}'")
        send_message(message)
    time.sleep(5*trial) # TODO: there are about ten million ways to be smarter than this
    response = str(get_last_message()).strip()
    print(f"Response from chatGPT: '{response}'")
    # its important to use a regex to check if the response is empty or not
    if (not response or re.match(r"^[^a-zA-Z0-9]$", response)) and trial <= 3:
        print("No response from chatGPT, trying again")
        return send_and_receive(message, trial=trial*1.5)
    elif trial > 3:
        print("No response from chatGPT, giving up")
        return "<ChatGPT is not responding.>"
    return response

# Telegram Methods
last_update = 0
url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}"
def send_message_to_telegram(message, chat_id, message_id):
    """Check for updates"""
    global url
    params = {"chat_id": chat_id, "reply_to_message_id": message_id, "text": message}

    response = requests.get(url+"/sendMessage", params)
    if response.status_code == 200:
        print("Sent response to telegram successfully")
    else:
        print("Error sending response to telegram:", response.text)
    return None

# checks if the chat_id is allowed or not, returns true if chat_id is invalid or not set
def check_chat_id(chat_id):
    try:
        chat_id_env = os.environ['CHAT_ID']
    except:
        return True
    if chat_id_env == "":
        return True
    chat_id_list = chat_id_env.split(',')
    chat_id_list = [x.strip() for x in chat_id_list]
    return str(chat_id) in chat_id_list
    
def check_for_new_updates():
    """Check for updates"""
    print("Checking for updates")
    params = {"allowed_updates": ["message"]}
    global last_update
    if last_update != 0:
        params['offset'] = last_update + 1
        # params['offset'] = -2

    response = requests.get(url+"/getUpdates", params)
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            if data["result"]:
                #  print updates
                for update in data["result"]:
                    print(update)
                    try:
                        key = 'message' if 'message' in update else 'edited_message'

                        try:
                            #  get the chat id
                            chat_id = update[key]["chat"]["id"]
                            message_id = update[key]["message_id"]
                            #  get the message
                            message = update[key]["text"]
                        except:
                            last_update = update['update_id']
                            print("This update is not a valid message or edited_message")
                            continue
                        # print chat id and message id
                        # print(f"Chat ID: {chat_id}, Message ID: {message_id}")
                        if not check_chat_id(chat_id):
                            last_update = update['update_id']
                            print("Chat ID not allowed")
                            continue
                        #  send the message to openai and receive a response
                        response = send_and_receive(message)
                        # #  send the response to telegram
                        send_message_to_telegram(response, chat_id, message_id)
                        last_update = update['update_id']
                    except Exception as e:
                        print("Error processing update", update['update_id'], e)
                return data["result"][0]
            else:
                print("No new updates")
                return None
    # print an error message with the response
    print("Error getting updates:", response.text)

def check_for_new_updates_periodically():
    while True:
        check_for_new_updates()
        time.sleep(5)


def start_browser():
    # start the browser
    global PAGE
    PLAY = sync_playwright().start()
    BROWSER = PLAY.chromium.launch_persistent_context(
        user_data_dir="/tmp/playwright",
        headless=False, # set to False to see the browser. This is required for login
    )
    PAGE = BROWSER.new_page()
    PAGE.goto("https://chat.openai.com/")
    if not is_logged_in():
        print("Please log in to OpenAI Chat")
        print("Press enter when you're done")
        input()
    else:        
        check_for_new_updates_periodically()

if __name__ == "__main__":
    while True:
        try:
            start_browser()
        except Exception as e:
            print("Error:", e)
            time.sleep(5)