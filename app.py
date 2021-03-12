import json
import os
import sys
import time
from pprint import pprint
from webwhatsapi import WhatsAPIDriver


from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as db




db_uri = "postgresql://postgres:123@postgres_docker:5432/chatbot"

base = declarative_base()
engine = db.create_engine(db_uri)
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker())(bind=engine)



class Contato(base):
    __tablename__ = "contato"

    id = db.Column(db.BigInteger, primary_key=True)

    chat_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(50), nullable=False)
    qr_code = db.Column(db.String(255), nullable=True)



contato_id = os.environ['CONTATO_ID']
print('ID UTILIZADO: ' + contato_id)
contato_telefone = os.environ['CONTATO_TELEFONE']
print('Telefone UTILIZADO: ' + contato_telefone)


contato = session.query(Contato).get(contato_id)

if contato is None:
    print("Registro não encontrado")
    sys.exit(1)




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



contato.qr_code = qr
try:
    session.commit()
except Exception as e:
    print(e)
    print("Nao foi possivel salvar o QR")
    session.rollback()
    sys.exit(1)



while(driver.get_status() == 'NotLoggedIn'):
    print("Waiting for QR")
    driver.wait_for_login()
    time.sleep(5)

print("Saving session")
driver.save_firefox_profile(remove_old=False)
print("Bot started")

while True:
    time.sleep(3)

    #print("Checking for more messages, status", driver.get_status())
    # print("User : " + contato_id)

    if driver.get_status() == 'NotLoggedIn':
        print("Not legged In")
        driver.wait_for_login()

    for contact in driver.get_unread():

        #pprint(contact)
        for message in contact.messages:
            received = str(message.content)

            if received.find("!ping") != -1:
                text = "!pong " + str(contato_id) + "/" + str(contato_telefone) + " -> " + str(message.sender.id) + " / " + str(message.timestamp)
                driver.send_message_to_id(message.chat_id, text)

            if received.find("!pong") != -1:
                text = "!ping " + str(contato_id) + "/" + str(contato_telefone) + " -> " + str(message.sender.id) + " / " + str(message.timestamp)
                driver.send_message_to_id(message.chat_id, text)

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
