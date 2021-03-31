from datetime import datetime
import json
from pprint import pprint

questionnaire = {
    "edges": [
        {
            "metadata": {},
            "source": "ROOT",
            "target": 1616187025756,
            "type": "publicationToOption"
        },
        {
            "metadata": {},
            "source": "ROOT",
            "target": 1616187043706,
            "type": "publicationToOption"
        },
        {
            "metadata": {},
            "source": 1616187025756,
            "target": 1616187067975,
            "type": "optionToPublication"
        },
        {
            "metadata": {},
            "source": 1616187067975,
            "target": 1616630645977,
            "type": "publicationToOption"
        },
        {
            "metadata": {},
            "source": 1616187067975,
            "target": 1616630651026,
            "type": "publicationToOption"
        },
        {
            "metadata": {},
            "source": 1616187067975,
            "target": 1616630656920,
            "type": "publicationToOption"
        },
        {
            "metadata": {},
            "source": 1616630645977,
            "target": 1616630697111,
            "type": "optionToFinal"
        },
        {
            "metadata": {},
            "source": 1616630651026,
            "target": 1616630786718,
            "type": "optionToFinal"
        },
        {
            "metadata": {},
            "source": 1616630656920,
            "target": 1616630832953,
            "type": "optionToFinal"
        },
        {
            "metadata": {},
            "source": 1616187043706,
            "target": 1616630858567,
            "type": "optionToFinal"
        },
        {
            "metadata": {},
            "source": 1616187067975,
            "target": 1616693137281,
            "type": "publicationToOption"
        }
    ],
    "nodes": [
        {
            "id": "ROOT",
            "metadata": {},
            "text": "Boa noite, você quer uma pizza?",
            "title": "Boa noite",
            "type": "publication",
            "x": 104.51683807373047,
            "y": -32.64238357543945
        },
        {
            "id": 1616187025756,
            "order": "1",
            "text": "Sim",
            "title": "1",
            "type": "option",
            "x": -374.498779296875,
            "y": -36.77231216430664
        },
        {
            "id": 1616187043706,
            "order": "2",
            "text": "Não",
            "title": "2",
            "type": "option",
            "x": 105.66666412353516,
            "y": 133
        },
        {
            "id": 1616187067975,
            "metadata": {},
            "text": "Qual o sabor da pizza?",
            "title": "Sabor",
            "type": "publication",
            "x": -364.4471740722656,
            "y": 121.25127410888672
        },
        {
            "id": 1616630645977,
            "metadata": {},
            "order": "1",
            "text": "Mussarela",
            "title": "1",
            "type": "option",
            "x": -754.0535278320312,
            "y": 273.1263122558594
        },
        {
            "id": 1616630651026,
            "metadata": {},
            "order": "2",
            "text": "Calabresa",
            "title": "2",
            "type": "option",
            "x": -488.2230224609375,
            "y": 285.9202880859375
        },
        {
            "id": 1616630656920,
            "metadata": {},
            "order": "3",
            "text": "Mista",
            "title": "3",
            "type": "option",
            "x": -243.7158660888672,
            "y": 297.292724609375
        },
        {
            "id": 1616630697111,
            "metadata": {},
            "text": "Pizza Mussarela",
            "title": "Final com mussarela",
            "type": "final",
            "x": -758.3181762695312,
            "y": 428.07562255859375
        },
        {
            "id": 1616630786718,
            "metadata": {},
            "text": "Pizza de Calabresa",
            "title": "Final com Calabresa",
            "type": "final",
            "x": -488.2230224609375,
            "y": 430.9187316894531
        },
        {
            "id": 1616630832953,
            "metadata": {},
            "text": "Pizza Mista",
            "title": "Final com Mista",
            "type": "final",
            "x": -235.18655395507812,
            "y": 428.07562255859375
        },
        {
            "id": 1616630858567,
            "metadata": {},
            "text": "Sem sucesso",
            "title": "Sem sucesso",
            "type": "final",
            "x": 112.2063980102539,
            "y": 304.65692138671875
        },
        {
            "id": 1616693137281,
            "metadata": {},
            "order": "4",
            "text": "Frango",
            "title": "4",
            "type": "option",
            "x": -37.59064483642578,
            "y": 308.6651306152344
        }
    ]
}


session = {
    "start_time": None,
    "end_time": None,
    "block": False,
    "question_id": "ROOT",
    # each contact has a unique dict of messages from current session
    "messages": [],
    "answers": [],
    "waiting_answer": False
}
'''
publicationToOption
optionToPublication
optionToFinal

option
final
publication
'''

# check if is waiting message
# if not
# get current node
# get all edges
# iter over all edges, if there is option, set waiting_message to true
# if there is publication set node to publiction
# if there is final set final node to final

# if waiting message
# compare message to all options
# if none equal, send response indicate invalid option
# if equal, check if there is any optionToPublication,
# if optionToPublication send response with publication and nodes text
# if not set waiting_message equal false


while True:

    # for each chat with unread_messages


    # util to start/ping/end chat log
    #####

    # if should read from chat

    if not session["block"]:

        # if chatbot aint waiting for answer, send question with options
        if session["waiting_answer"] is False:
            # get current_node to check type
            current_node = next((item for item in questionnaire["nodes"] if item["id"] == session["question_id"]), None)

            # switch for each node type
            # these break will end the session
            # if cant get node, restart session
            if current_node is None:
                print("{{Cant capture current_node}}")
                session["question_id"] = "ROOT"
                session["waiting_answer"] = False
                break
            elif current_node["type"] == "final": # if is final, end session
                print("message: " + current_node["text"])
                session["question_id"] = "ROOT"
                session["waiting_answer"] = False
                break
            elif current_node["type"] == "publication": # if publication print text
                print("message: " + current_node["text"])

            # finally, get all edges from node
            # get available edges
            current_edges = (item for item in questionnaire["edges"] if item["source"] == session["question_id"])

            # to check if loop has ocorred
            loop_block = True
            # iter over all edges
            while True:
                # get edge
                edge = next(current_edges, None)

                # if has iterated over all edges, break loop
                if edge is None:
                    # if edge is the same, end session
                    if loop_block:
                        print("{{no available path}}")
                        print("")
                        session["question_id"] = "ROOT"
                        session["waiting_answer"] = False
                    break

                # check if there is an valid edge
                #if edge["type"] == "publicationToOption" or edge["type"] == "optionToOption":
                    # get target node of edge
                question = next((item for item in questionnaire["nodes"] if item["id"] == edge["target"]), None)

                # if there is no edge, error, end session
                if question is None:
                    print("{{invalid edge}}")
                    loop_block = False
                    session["question_id"] = "ROOT"
                    session["waiting_answer"] = False
                    break

                    # guarantee if edge is option
                if question["type"] == "option":
                    print("option: " + question["text"])
                    session["waiting_answer"] = True
                    loop_block = False

                else: # if edge does not goes to option, go to edge, and break
                    loop_block = False
                    session["question_id"] = edge["target"]
                    session["waiting_answer"] = False
                    break;

        # else, read user input
        else:
            # loop inside unread_messages

            # for each unread message
            entrada = input("waiting answer: ")

            # check if there is plain text
            received = str(entrada)

            # save received message
            new_message = {
                "message": received,
                # "time": str(message.timestamp)
            }
            session["messages"].append(new_message)

            # get all edges from current Node
            current_edges = (item for item in questionnaire["edges"] if item["source"] == session["question_id"])

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

                    # guarantee if edge is option, if not send session to ROOT
                    if question["type"] != "option":
                        print("{{invalid edge on option check}}")
                        session["question_id"] = "ROOT"

                    # check if received answer is equal to node question
                    if received.find(question["text"]) != -1:
                        print("choosed: " + question["text"])
                        session["question_id"] = question["id"]
                        session["waiting_answer"] = False
                        break

                else:  # if edge does not goes to option, go to edge, and break
                    print("travou")
                    break

            # if got right answer or could no find, go to node and send question again
            session["waiting_answer"] = False




'''

    "start_time": None,
    "end_time": None,
    "block": True,
    "question_id": None,
    # each contact has a unique dict of messages from current session
    "messages": [],
    "answers": [],
    "result": "",
    "send_message": False,
    "chat_id": message.sender.id
    "open": False
    
    
    send_message
    
paraCadaMensagemRecebida:
    verificar se existe sessão aberta para ela
    caso contrario
        iniciar sessao    

while True:
    para cada sessao aberta
        
        verificar se deve enviar mensagem:
            enviar mensagens do no
        caso contrario
            para cada mensagem nao lida desse numero
                verificar utilitarios !ping/!start/!end
                
                caso exista sessao aberta:
                    aplicar respostas no questionario
                caso contrario:
                    iniciar nova sessao
                    # nao remover block
    

'''