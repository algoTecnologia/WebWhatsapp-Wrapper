import json
import os
import sys
import time
from datetime import datetime
from pprint import pprint
from webwhatsapi import WhatsAPIDriver

import requests

import json



post_header ={
    "Accept": "application/json",
    "Content-Type": "application/json",
}
#res3 = requests.post(os.environ["URL_REQUEST_REFRESH_TOKEN"], data=json.dumps({"url":os.environ["URL_REQUEST_REFRESH_TOKEN"]}),headers=header)


db_uri = os.environ['DB_URI']
print('BANCO DE DADOS: ' + db_uri)

## API ROUTINE

print("Environment", os.environ)
try:
    os.environ["SELENIUM"]
except KeyError:
    print("Please set the environment variable SELENIUM to Selenium URL")
    sys.exit(1)

##Save session on "/firefox_cache/localStorage.json".
##Create the directory "/firefox_cache", it's on .gitignore
##The "app" directory is internal to docker, it corresponds to the root of the project.
##The profile parameter requires a directory not a file.

profiledir = os.path.join(".", "firefox_cache")
if not os.path.exists(profiledir):
    os.makedirs(profiledir)

driver = WhatsAPIDriver(
    profile=profiledir, client="remote", command_executor=os.environ["SELENIUM"]
)


qr = None
while qr is None:
    time.sleep(2)
    try:
        qr = driver.get_qr_plain()
        print(qr)
    except Exception as e:
        print(e)


qr_code_data = {
    "id": os.environ['SESSION_ID'],
    "qr_code": qr,
	"timestamp": str(datetime.now()),
}
# TODO create exceptions
try:
    requests.post(os.environ["URL_REQUEST_QR_CODE"], data=json.dumps(qr_code_data),headers=post_header)
except Exception as e:
    print(e)
    print("falha ao enviar o qr code")


#while(driver.get_status() == 'NotLoggedIn'):
#    print("Waiting for QR")
driver.wait_for_login()
#    time.sleep(5)

print("Saving session")
driver.save_firefox_profile(remove_old=False)
print("Bot started")


# sessions structure
'''
sessions = {
    "contact_id": {
        # indicate start and end of log
        "start_time": "2020-01-01 10:00:00",
        "end_time": "2020-01-01 10:00:00",
        # indicate if should read from this contact
        "block": True,
        # each contact has a unique dict of messages from current session
        "messages": [
            {"message": "Mensagem", "time": "2020-01-01 10:00:00"},
            {"message": "Mensagem", "time": "2020-01-01 10:00:00"},
        ]
    }
}


'''

# send log_time to backend
log_session_data = {
    "session_chat_id": os.environ['SESSION_ID'],
    "start_monitor": str(datetime.now()),
    "error": False,
}

# TODO create exceptions
try:
    requests.post(os.environ["URL_LOG"], data=json.dumps(log_session_data),headers=post_header)
except Exception as e:
    print(e)
    print("falha ao enviar data de log")

sessions = {}

while True:
    time.sleep(3)

    if driver.get_status() == 'NotLoggedIn':
        print("Not legged In")
        driver.wait_for_login()


    # for each chat with unread_messages
    for contact in driver.get_unread():

        # check if contact_session exists
        try:
            sessions[contact.chat.id]["block"]
        except KeyError:
            # start conditions to session
            sessions[contact.chat.id] = {
                "start_time": None,
                "end_time": None,
                "block": True,
                # each contact has a unique dict of messages from current session
                "messages": []
            }

        # for each unread message from specific chat
        for message in contact.messages:
            # check if there is plain text
            if message.content is not None:
                received = str(message.content)

                # util to start/ping/end chat log
                if sessions[contact.chat.id]["start_time"] is None and received.find("!start") != -1:
                    sessions[contact.chat.id]["start_time"] = datetime.now()
                    sessions[contact.chat.id]["block"] = False
                    contact.chat.send_message("log started")

                if sessions[contact.chat.id]["end_time"] is None and received.find("!end") != -1:
                    sessions[contact.chat.id]["end_time"] = datetime.now()
                    sessions[contact.chat.id]["block"] = True

                    # send extract to backend
                    session_data = {
                        "session_chat_id": os.environ['SESSION_ID'],
                        "date": str(datetime.now()),
                        "answer_data": sessions[contact.chat.id]["messages"],
                        "contact": contact.chat.id
                    }
                    # TODO create exceptions
                    try:
                        requests.post(os.environ["URL_EXTRACT"], data=json.dumps(session_data),headers=post_header)
                    except Exception as e:
                        print(e)
                        print("falha ao enviar extração")

                    contact.chat.send_message("log ended")
                    # return logged session and delete data
                    pprint(sessions[contact.chat.id])
                    sessions[contact.chat.id]["start_time"] = None
                    sessions[contact.chat.id]["end_time"] = None
                    sessions[contact.chat.id]["messages"] = []

                if received.find("!ping") != -1:
                    text = "!pong " + str(os.environ['SESSION_ID']) + "/" + str(message.sender.id) + " -> " + str(message.sender.id) + " / " + str(message.timestamp)
                    contact.chat.send_message(text)

                # if should answer chat
                if not sessions[contact.chat.id]["block"]:

                    print("logged message:")
                    print("id: " + str(contact.chat.id))
                    print("message: " + received)

                    new_message = {
                        "message": received,
                        "time": str(message.timestamp)
                    }
                    sessions[contact.chat.id]["messages"].append(new_message)









            '''
            #print(json.dumps(message.get_js_obj(), indent=4))
            print("class", message.__class__.__name__)
            print("message", message)
            print("id", message.id)
            print("type", message.type)
            print("timestamp", message.timestamp)
            print("chat_id", message.chat_id)
            print("sender", message.sender)
            print("sender.id", message.sender.id)
            print("sender.safe_name", message.sender.get_safe_name())
            if message.type == "chat":
                print("-- Chat")
                print("safe_content", message.safe_content)
                print("content", message.content)
                # contact.chat.send_message(message.safe_content)
            elif message.type == "image" or message.type == "video":
                print("-- Image or Video")
                print("filename", message.filename)
                print("size", message.size)
                print("mime", message.mime)
                print("caption", message.caption)
                print("client_url", message.client_url)
                message.save_media("./")
            else:
                print("-- Other")
            '''