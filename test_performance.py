import time
import requests
import json
header = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
info = {
    "url_log": "http://chatbot-backend:5000/session/test",
    "url_extract": "http://chatbot-backend:5000/session/test",
    "url_request_qr_code": "http://chatbot-backend:5000/session/edit/request",
    "url_request_refresh_token": "http://chatbot-backend:5000/session/edit/request",
    "token": "http://chatbot-backend:5000/session/edit/request",
    "refresh_token": "asd8asdfa89s76df",
    "questionnaire_json": {"text":"tes"}
}

url = "http://localhost:5001"

for i in range(30, 100):
    time.sleep(2)
    session_id_name = "chatbot_" + str(id)

    try:
        response = requests.post(url=url + "/session/start/" + str(i), data=json.dumps(info), headers=header)
        data = response.json()

        print(data)
        if data.get('error') is True:

            raise Exception("Erro na criação")

        print("CRIADO: " + str(i))

    except Exception as e:
        print(e)
        print("ERROR: " + str(i))