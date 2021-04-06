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

Messages = {
    'CONTACT_LOG' : 'CONTACT_LOG',  # Logs referentes ao contanto da API com os usuários
    'SERVICE_LOG' : 'SERVICE_LOG',  # Logs referentes ao tempo de serviço (inicio e fim do serviço)
    'ERROR_LOG' : 'ERROR_LOG',  # Logs referentes aos erros ocorridos no serviço
}


post_header ={
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def check_env():
    # use this to check if env has been sent
    print("Environment", os.environ)
    os.environ["SELENIUM"]
    os.environ['QUESTIONNAIRE_JSON']
    os.environ["URL_REQUEST_QR_CODE"]
    os.environ["URL_REQUEST_REFRESH_TOKEN"]
    os.environ["URL_LOG"]
    os.environ["SESSION_ID"]
    os.environ["URL_EXTRACT"]


def send_url_log(data):
    # TODO better exception treatment or send error_log to backend
    try:
        if data.get("id") is None:
            data["id"] = os.environ['SESSION_ID']
        requests.post(os.environ["URL_LOG"], data=json.dumps(data), headers=post_header)
    except Exception as e:
        print(e)
        print("Falha ao enviar dados de log")
        sys.exit(1)


def send_qr_code(data):
    # TODO better exception treatment or send error_log to backend
    if data.get("id") is None:
        data["id"] = os.environ['SESSION_ID']

    requests.post(os.environ["URL_REQUEST_QR_CODE"], data=json.dumps(data), headers=post_header)


def start_session(session):
    session["start_time"] = str(datetime.now())
    session["question_id"] = "ROOT"
    session["send_message"] = True
    #session["messages"] = []
    #ession["answers"] = []
    session["result"] = None
    session["open"] = True
    session["timeout_counter"] = None

    log = {
        "error": False,
        "message": "Conversa inciada",
        "end_monitor": str(session["end_time"]),
        "start_monitor": str(session["start_time"]),
        "contact": session["chat_id"],
        "log_type": Messages["CONTACT_LOG"]
    }
    send_url_log(log)


# end chatbot session and send request
def end_session(session):

    session["end_time"] = datetime.now()
    # send extract to backend
    session_data = {
        "id": os.environ['SESSION_ID'],
        "date": str(session["end_time"]),
        "answer_data": json.dumps({
            "messages": session["messages"],
            "answers": session["answers"],
            "result": session["result"]
        }),
        "contact": session['chat_id']
    }

    # TODO create exceptions
    try:
        requests.post(os.environ["URL_EXTRACT"], data=json.dumps(session_data),
                      headers=post_header)
    except Exception as e:
        print(e)
        print("falha ao enviar extração")



    error_log = {
        "error": False,
        "message": "Conversa finalizada",
        "end_monitor": str(session["end_time"]),
        "start_monitor": str(session["start_time"]),
        "contact": session["chat_id"],
        "log_type": Messages["CONTACT_LOG"]
    }
    send_url_log(error_log)

    # reset session
    session["start_time"] = None
    session["end_time"] = None
    session["question_id"] = "ROOT"
    session["send_message"] = False
    session["messages"] = []
    session["answers"] = []
    session["result"] = None
    session["open"] = False
    session["timeout_counter"] = None


def get_token():
    # res3 = requests.post(os.environ["URL_REQUEST_REFRESH_TOKEN"], data=json.dumps({"url":os.environ["URL_REQUEST_REFRESH_TOKEN"]}),headers=header)
    print("TODO")


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