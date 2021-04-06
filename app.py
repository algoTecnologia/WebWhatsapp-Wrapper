import json
import os
import sys
import time
from datetime import datetime
from pprint import pprint
from webwhatsapi import WhatsAPIDriver

from traceback import print_exc
import requests

import json

from app_functions import *


start_monitor = datetime.now()
end_monitor = None


def end_program():
    error_data = {
        "error": True,
        "message": "O programa foi finalizado devido a um erro durante sua execução",
        "start_monitor": str(start_monitor),
        "end_monitor": str(datetime.now()),
        "log_type": Messages["SERVICE_LOG"]
    }

    send_url_log(error_data)

    driver.close()
    sys.exit(1)

# check env variables
try:
    check_env()
except KeyError:
    end_monitor = datetime.now()
    error_data = {
        "error": True,
        "message": "Missing environment variables",
        "start_monitor": str(start_monitor),
        "end_monitor": str(end_monitor),
        "log_type": Messages["ERROR_LOG"]
    }
    send_url_log(error_data)
    print("Missing environment variables")
    end_program()


# check questionnaire
questionnaire = os.environ['QUESTIONNAIRE_JSON']
questionnaire = json.loads(questionnaire)
if questionnaire is None:
    end_monitor = datetime.now()
    error_data = {
        "error": True,
        "message": "Não foi possivel carregar o questionario",
        "end_monitor": str(end_monitor),
        "start_monitor": str(start_monitor),
        "log_type": Messages["ERROR_LOG"]
    }
    send_url_log(error_data)
    end_program()

##Save session on "/firefox_cache/localStorage.json".
##Create the directory "/firefox_cache", it's on .gitignore
##The "app" directory is internal to docker, it corresponds to the root of the project.
##The profile parameter requires a directory not a file.
profiledir = os.path.join(".", "firefox_cache")
if not os.path.exists(profiledir):
    os.makedirs(profiledir)





## API ROUTINE
try:
    driver = WhatsAPIDriver(
        profile=profiledir, headless=True,
        client="remote", command_executor=os.environ["SELENIUM"]
    )
except Exception as e:
    print(e)
    print("could not start webdriver")
    end_monitor = datetime.now()
    error_log = {
        "error": True,
        "message": "Não foi possivel inicializar o chatbot",
        "end_monitor": str(end_monitor),
        "start_monitor": str(start_monitor),
        "log_type": Messages["ERROR_LOG"]
    }
    send_url_log(error_log)
    end_program()

# QR code capture
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
    "end_monitor": str(end_monitor),
    "start_monitor": str(start_monitor),
    'error': False
}
try:
    send_qr_code(qr_code_data)
except Exception as e:
    qr_code_data['error'] = True
    qr_code_data['message'] = "Não foi possivel enviar o QR Code"
    qr_code_data["log_type"] =  Messages["ERROR_LOG"]
    print(e)
    send_url_log(qr_code_data)
    end_program()

while(driver.get_status() == 'NotLoggedIn'):
    print("Waiting for QR login")
    driver.wait_for_login()

# save session on volume
# todo: verify if a profile is presents, else get qr code
#print("Saving session")
#driver.save_firefox_profile(remove_old=False)

# dict where the sessions are saved
sessions = {}

class NewMessageObserver:
    def on_message_received(self, new_messages):
        for message in new_messages:
            # check if there is any new session to be created
            if message.type == "chat":
                try:
                    # each contact has a unique dict of messages from current session
                    sessions[message.sender.id]["block"]
                except KeyError:
                    # start conditions to session
                    sessions[message.sender.id] = {
                        "chat_id": message.sender.id,
                        "start_time": None,
                        "end_time": None,
                        "question_id": None,
                        "messages": [],
                        "answers": [],
                        "result": "",
                        "send_message": False,
                        "open": False,
                        "block": True,
                    }



# apply function to every message received
driver.subscribe_new_messages(NewMessageObserver())

# send log to indicate it has been created
log_session_data = {
    "start_monitor": str(start_monitor),
    "end_monitor": str(end_monitor),
    "message": "O código QR foi lido com sucesso e a sessão foi iniciada",
    "error": False,
    "log_type": Messages["SERVICE_LOG"]
}
send_url_log(data=log_session_data)
print("Bot started")


def main():

    while True:
        time.sleep(2)
        if driver.get_status() == 'NotLoggedIn':
            print("Not logged In, smartphone disconnected")
            driver.wait_for_login()

        # for each session

        unread_messages = driver.get_unread()

        for session in list(sessions):
            #time.sleep(3)

            # get session chat
            #chat = driver.get_chat_from_id(session)

            # if session is open and should send node messages
            if sessions[session].get('send_message'):
                # logic to send node text(s)
                text = ""
                #print("sending message")
                # get current_node of session
                current_node = next(
                    (item for item in questionnaire["nodes"] if item["id"] == sessions[session]["question_id"]),
                    None)

                # check if node is final and exists
                if current_node is None or current_node["type"] == "final":
                    #print("{{end_node}}")
                    text += current_node.get("text")
                    text += "\nSessão encerrada"

                    end_session(sessions[session])
                    driver.send_message_to_id(session, text)
                    #chat.send_message(text)
                    continue # jump to next contact
                # TODO redirect logic
                # if current_node["type"] == "direct":
                #     text += current_node.get("text")
                #     text += "\nA sua sessão será redirecionada para outro contato, aguarde um momento,"
                #     chat.send_message(text)
                #
                #     redirect_message = "Sessão com o número {}, foi redirecionada para você"
                #     driver.send_message_to_id(session, redirect_message.format(session))
                #     end_session(sessions[session])
                #     continue
                elif current_node["type"] == "publication":  # if publication print node text
                    text += "\n" + current_node["text"]

                #pprint(current_node)

                # print edges
                # get all edges from node
                current_edges = (item for item in questionnaire["edges"] if
                                 item["source"] == sessions[session]["question_id"])

                # flag to check if there is any edge returned from the generator
                loop_block = True
                ordered_options = []
                for edge in current_edges:
                    #print("visit")
                    loop_block = False
                    # get target node of edge
                    question = next((item for item in questionnaire["nodes"] if item["id"] == edge["target"]), None)

                    # if there is no node, error, end session
                    if question is None:
                        end_session(sessions[session])
                        text += "\nSessão encerrada"
                        break

                    # if is a option
                    if question["type"] == "option":
                        # add node text to message
#                        text +=  "\n" + str(question["order"]) + "\n" + question["text"]
                        sessions[session]["send_message"] = False
                        ordered_options.append({"order":question["order"], "text": question["text"]})
                    else: # if not a option, jump to this node
                        sessions[session]["question_id"] = edge["target"]
                        sessions[session]["send_message"] = True

                if loop_block:
                    end_session(sessions[session])
                    text += "\nSessão encerrada"


                # sort options
                if len(ordered_options) > 0:
                    ordered_options = sorted(ordered_options, key=lambda a:a["order"])
                    for it in ordered_options:
                        text+= "\n" + str(it["order"]) + " - " + it["text"]

                # send text after
                if text != "":
                    driver.send_message_to_id(session, text)
                    # chat.send_message(text)


            else:
                # captura correct chat
                chat_messages = []
                for a in unread_messages:
                    if a.chat.id == session:
                        chat_messages = a.messages
                        break

                # iterate over chat messages
                for message in chat_messages:
                    # check if there is plain text
                    if message.type == "chat":
                        received = str(message.safe_content)

                        ## UTILS FOR TESTING
                        # util to start/ping/end chat log
                        if sessions[session]["start_time"] is None and received.find("=!start") != -1:
                            sessions[session]["block"] = False
                            text = "log started, send a message to start"
                            driver.send_message_to_id(session, text)
                            # chat.send_message(text)

                            break
                        if sessions[session]["end_time"] is None and received.find("=!end") != -1:
                            end_session(sessions[session])
                            sessions[session]["block"] = True
                            text = "log ended"
                            driver.send_message_to_id(session, text)
                            # chat.send_message(text)

                            break
                        if received.find("=!ping") != -1:
                            text = "=!pong " + str(os.environ['SESSION_ID']) + "/" + str(
                                message.sender.id) + " -> " + str(message.sender.id) + " / " + str(message.timestamp)
                            driver.send_message_to_id(session, text)
                            # chat.send_message(text)
                        ## END UTILS FOR TESTING

                        # conditional used for testing:
                        if not sessions[session]["block"]:
                            #print("receiving messages")
                            # check if the session is open
                            if sessions[session].get('open'):
                                #print("reading")
                                # save message
                                new_message = {
                                    "message": received,
                                    "time": str(message.timestamp)
                                }
                                sessions[session]["messages"].append(new_message)

                                # apply questionnaire
                                # get all edges from current Node
                                current_edges = (item for item in questionnaire["edges"] if
                                                 item["source"] == sessions[session]["question_id"])
                                for edge in current_edges:
                                    # for each edge that is a question
                                    if edge["type"] == "publicationToOption" or edge["type"] == "optionToOption":
                                        node_of_edge = next(
                                            (item for item in questionnaire["nodes"] if item["id"] == edge["target"]), None)

                                        # check if response is node text
                                        if node_of_edge and received.find(str(node_of_edge["order"])) != -1 or node_of_edge and received.find(node_of_edge["text"]) != -1  :
                                            #print("choosed: " + node_of_edge["text"])

                                            next_edge = next((item for item in questionnaire["edges"] if
                                                 item["source"] == node_of_edge["id"]), None)

                                            if next_edge:
                                                sessions[session]["question_id"] = next_edge["target"]
                                            else:
                                                sessions[session]["question_id"] = node_of_edge["id"]
                                            break
                                # should send message after comparing the response
                                sessions[session]["send_message"] = True
                            else:
                                # if received message but session is not open, start new session
                                #print("a new session has been started")
                                start_session(sessions[session])



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_exc()
        print(e)
        end_monitor = datetime.now()
        data = {
            "start_monitor": str(start_monitor),
            "end_monitor": str(end_monitor),
            "error": True,
            "message": "Ocorreram errors durante a execução do programa",
            "log_type": Messages["ERROR_LOG"]
        }

        send_url_log(data)
        print("Ocorreram erros durante a execução do programa")
        end_program()


