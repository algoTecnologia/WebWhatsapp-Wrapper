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

def send_url_log(data):
    # TODO better exception treatment or send error_log to backend
    try:
        requests.post(os.environ["URL_LOG"], data=json.dumps(data), headers=post_header)
    except Exception as e:
        print(e)
        print("Falha ao enviar dados de log")
        sys.exit(1)


#res3 = requests.post(os.environ["URL_REQUEST_REFRESH_TOKEN"], data=json.dumps({"url":os.environ["URL_REQUEST_REFRESH_TOKEN"]}),headers=header)

# use this to check if env has been sent
print("Environment", os.environ)
try:
    os.environ["SELENIUM"]
    os.environ['QUESTIONNAIRE_JSON']
    os.environ["URL_REQUEST_QR_CODE"]
    os.environ["URL_REQUEST_REFRESH_TOKEN"]
    os.environ["URL_LOG"]
    os.environ["SESSION_ID"]
    os.environ["URL_EXTRACT"]
except KeyError:
    error_data = {
        "error": True,
        "message": "Missing environment variables"
    }
    send_url_log()
    print("Missing environment variables")
    sys.exit(1)

# check questionnaire
questionnaire = os.environ['QUESTIONNAIRE_JSON']
questionnaire = json.loads(questionnaire)
if questionnaire is None:
    error_data = {
        "session_chat_id": os.environ['SESSION_ID'],
        "error": True,
        "message": "Não foi possivel carregar o questionario"
    }
    send_url_log(error_data)
    sys.exit(1)

pprint(questionnaire)


##Save session on "/firefox_cache/localStorage.json".
##Create the directory "/firefox_cache", it's on .gitignore
##The "app" directory is internal to docker, it corresponds to the root of the project.
##The profile parameter requires a directory not a file.
profiledir = os.path.join(".", "firefox_cache")
if not os.path.exists(profiledir):
    os.makedirs(profiledir)

## API ROUTINE

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
    print("Falha ao enviar o qr code")

while(driver.get_status() == 'NotLoggedIn'):
    print("Waiting for QR login")
    driver.wait_for_login()


# save session on volume
# todo: verify if a profile is presents, else get qr code
#print("Saving session")
#driver.save_firefox_profile(remove_old=False)


# sessions structure
'''
sessions = {
    "contact_id": {
        # question id
        "question_id": "ROOT",
        # indicate start and end of log
        "start_time": "2020-01-01 10:00:00",
        "end_time": "2020-01-01 10:00:00",
        # indicate if should read from this contact
        "block": True,
        # each contact has a unique dict of messages from current session
        "messages": [
            {"message": "Mensagem", "time": "2020-01-01 10:00:00"},
            {"message": "Mensagem", "time": "2020-01-01 10:00:00"},
        ],
        # answers
        "answers": [
        
        ]
        # final answer
        "result": "",
        # flag to check if is waiting user answer or not
        "waiting_answer": False
    }
}
'''

sessions = {}

# end chatbot session and send request
def end_session(data):
    # send extract to backend
    pprint(data)

    session_data = {
        "session_chat_id": os.environ['SESSION_ID'],
        "date": str(datetime.now()),
        "end_time": str(datetime.now()),
        "messages": json.dumps(data['messages']),
        "answers": json.dumps(data['answers']),
        "concise_result": json.dumps(data['result']),
        "contact": data['chat_id']
    }

    # TODO create exceptions
    try:
        requests.post(os.environ["URL_EXTRACT"], data=json.dumps(session_data),
                      headers=post_header)
    except Exception as e:
        print(e)
        print("falha ao enviar extração")

    # return logged session and delete data
    pprint(data)
    sessions.pop(data['chat_id'])

# send log_time to backend
log_session_data = {
    "session_chat_id": os.environ['SESSION_ID'],
    "start_monitor": str(datetime.now()),
    "error": False,
}

send_url_log(data=log_session_data)
print("Bot started")




class NewMessageObserver:
    def on_message_received(self, new_messages):
        for message in new_messages:
            # check if there is any new session to be created
            if message.type == "chat":
                try:
                    sessions[message.sender.id]["block"]
                except KeyError:
                    # start conditions to session
                    sessions[message.sender.id] = {
                        "start_time": None,
                        "end_time": None,
                        "block": True,
                        "question_id": None,
                        # each contact has a unique dict of messages from current session
                        "messages": [],
                        "answers": [],
                        "result": "",
                        "waiting_answer": False,
                        "chat_id": message.sender.id
                    }

driver.subscribe_new_messages(NewMessageObserver())

def main():

    while True:
        time.sleep(3)

        if driver.get_status() == 'NotLoggedIn':
            print("Not logged In, smartphone disconnected")
            driver.wait_for_login()

        # for each open session
        # questionnaire application logic:

        for contact_session in sessions:
            chat = driver.get_chat_from_id(contact_session)

            # if chatbot aint waiting for answer, send question with options
            if sessions[chat.id]["waiting_answer"] is False and not sessions[chat.id]["block"]:
                # text to be sent
                text = ""
                print("sending message")
                # get current_node to check type
                current_node = next((item for item in questionnaire["nodes"] if item["id"] == sessions[chat.id]["question_id"]),
                                    None)

                # switch for each node type
                # these break will end the session
                # if cant get node or if is final, end session
                if current_node is None or current_node["type"] == "final":
                    print("{{end_node}}")
                    text += "\nSessão encerrada"
                    end_session(sessions[chat.id])
                    # jump to next contact
                    continue
                elif current_node["type"] == "publication":  # if publication print text
                    text += "\n" + current_node["text"]

                # get all edges from node
                current_edges = (item for item in questionnaire["edges"] if item["source"] == sessions[chat.id]["question_id"])

                # flag to check if loop has ocorred
                loop_block = True

                # iterate over all edges
                while True:
                    # get edge
                    edge = next(current_edges, None)

                    # if has iterated over all edges, break loop
                    if edge is None:
                        # if edge is the same, end session
                        if loop_block:
                            print("{{no available path}}")
                            print("")
                            sessions[chat.id]["question_id"] = "ROOT"
                            sessions[chat.id]["waiting_answer"] = False
                        break

                    # check if there is an valid edge
                    if edge["type"] == "publicationToOption" or edge["type"] == "optionToOption":
                        # get target node of edge
                        question = next((item for item in questionnaire["nodes"] if item["id"] == edge["target"]), None)

                        # if there is no edge, error, end session
                        if question is None:
                            print("{{invalid edge}}")
                            loop_block = False
                            sessions[chat.id]["question_id"] = "ROOT"
                            sessions[chat.id]["waiting_answer"] = False
                            break

                        # guarantee if edge is option
                        if question["type"] == "option":
                            text += "\n" + question["text"]
                            sessions[chat.id]["waiting_answer"] = True
                            loop_block = False

                    else:  # if edge does not goes to option, go to edge, and break
                        loop_block = False
                        sessions[chat.id]["question_id"] = edge["target"]
                        sessions[chat.id]["waiting_answer"] = False
                        break

                # send text after
                if text != "":
                    ## fix send
                    chat.send_message(text)


            # if should wait user answer
            else:
                # loop inside unread_messages
                for message in driver.get_unread_messages_in_chat(chat.id):
                    # check if there is plain text
                    if message.content is not None:
                        received = str(message.content)

                        ## UTILS FOR TESTING
                        # util to start/ping/end chat log
                        if sessions[chat.id]["start_time"] is None and received.find("!start") != -1:
                            sessions[chat.id]["start_time"] = str(datetime.now())
                            sessions[chat.id]["block"] = False
                            sessions[chat.id]["question_id"] = "ROOT"
                            sessions[chat.id]["waiting_answer"] = False

                            chat.send_message("log started")
                            # break to send bot to start
                            break

                        if sessions[chat.id]["end_time"] is None and received.find("!end") != -1:
                            end_session(sessions[chat.id])
                            chat.send_message("log ended")

                        if received.find("!ping") != -1:
                            text = "!pong " + str(os.environ['SESSION_ID']) + "/" + str(
                                message.sender.id) + " -> " + str(message.sender.id) + " / " + str(message.timestamp)
                            chat.send_message(text)
                        ## END UTILS FOR TESTING


                        # conditional used for testing:
                        if not sessions[chat.id]["block"]:
                            print("receiving message")
                            # save received message
                            new_message = {
                                "message": received,
                                "time": str(message.timestamp)
                            }
                            sessions[chat.id]["messages"].append(new_message)

                            # get all edges from current Node
                            current_edges = (item for item in questionnaire["edges"] if item["source"] == sessions[chat.id]["question_id"])

                            # check message with options
                            while True:
                                edge = next(current_edges, None)

                                # if all edges are visited and there was no valid response
                                if edge is None:
                                    print("{{all edges visited}}")
                                    print("{{invalid option}}")
                                    break

                                if edge["type"] == "publicationToOption" or edge["type"] == "optionToOption":
                                    question = next((item for item in questionnaire["nodes"] if item["id"] == edge["target"]), None)

                                    if question is None:
                                        print("{{could not find the question to check}}")
                                        break

                                    # guarantee if edge is option, if not send sessions[chat.id] to ROOT
                                    if question["type"] != "option":
                                        print("{{invalid edge on option check}}")
                                        sessions[chat.id]["question_id"] = "ROOT"

                                    # check if received answer is equal to node question
                                    if received.find(question["text"]) != -1:
                                        print("choosed: " + question["text"])
                                        sessions[chat.id]["answers"].append(new_message)
                                        sessions[chat.id]["question_id"] = question["id"]
                                        sessions[chat.id]["waiting_answer"] = False
                                        break

                                else:  # if edge does not goes to option, go to edge, and break
                                    break

                            # if got right answer or could no find, go to node and send question again
                            sessions[chat.id]["waiting_answer"] = False

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        data = {
            "error": True,
            "message": "Ocorreram errors durante a execução do programa"
        }

        send_url_log(data)

        print("Ocorreram erros durante a execução do programa")

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

# reset session
session["start_time"] = None
session["question_id"] = "ROOT"
session["send_message"] = False
session["messages"] = []
session["answers"] = []
session["result"] = None
session["open"] = False

# start session
session["start_time"] = str(datetime.now())
session["question_id"] = "ROOT"
session["send_message"] = True
# session["messages"] = []
# ession["answers"] = []
session["result"] = None
session["open"] = True