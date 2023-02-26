import socket
import threading
import datetime
import time
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import schedule
global chat_min
global chat_min2
global chat_stop
global job1
global backup


# Google Drive 백업 여부
backup = False

# 인증 토큰 파일 경로
TOKEN_FILE = 'api/token.json'

# API 키 파일 경로
API_KEY_FILE = 'api/api_key.json'

# OAuth 2.0 인증 토큰 생성
creds = None
if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            API_KEY_FILE, ['https://www.googleapis.com/auth/drive'])
        creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

# Google Drive API 클라이언트 생성
service = build('drive', 'v3', credentials=creds)

# 처음 서버 실행시 저장
firstsave = 0
chat_min = 0
chat_min2 = 0
chat_stop = True

# 서버 주소와 포트 번호를 지정합니다.
HOST = '192.168.0.104'
PORT = 44990

# 소켓 객체를 생성합니다.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 서버 소켓을 바인딩합니다.
server_socket.bind((HOST, PORT))

# 클라이언트와 연결할 때까지 대기합니다.
server_socket.listen()

# 연결된 클라이언트 리스트를 저장합니다.
clients = []

# 채팅 로그 업로드
def upload_log():
    global backup
    if backup == True:
        # 구글 드라이브 폴더 ID
        f = open("api/folder_id.txt", 'r')
        FOLDER_ID = f.read()
        f.close()

        # 업로드 할 파일 경로
        FILE_PATH = 'api/chat_log.txt'

        # 로그 파일 업로드
        file_name = str(datetime.datetime.now())[0:19].replace('-','_').replace(' ','_') + "_chatlog.txt"
        #file_name = "chat_log.txt"
        file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(FILE_PATH, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(file_name + " 으로 복구됨. 파일 아이디: " + file.get('id'))
        with open("api/console_log.txt", "a") as f:
            f.write(str(datetime.datetime.now())[0:19] + file_name + " 으로 복구됨. 파일 아이디: " + file.get('id') + "\n")
    else:
        print("복구옵션 꺼짐")
        with open("api/console_log.txt", "a") as f:
            f.write("복구옵션 꺼짐")

def addmin():
    global chat_min
    global chat_min2
    chat_min = chat_min + 1
    chat_min2 = chat_min2 + 1

def Detect_Chat():
    global chat_stop
    global chat_min
    global chat_min2
    global job1

    job1 = schedule.every(60).seconds.do(addmin)

    while True:
        if chat_stop == True:
            if chat_min == 1:
                chat_min = 2
                chat_min2 = 0
                upload_log()
            else:
                chat_min2 = 0
        elif chat_stop == False:
            if chat_min2 == 10:
                chat_min2 = 0
                upload_log()
            elif chat_min == 1:
                chat_stop = True

        schedule.run_pending()
        time.sleep(1)

# 클라이언트로부터 메시지를 받아서 다른 클라이언트에게 보내는 함수
def handle_client(client_socket, addr):
    global chat_stop
    global chat_min
    global job1
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                print(f'{addr}에서 온 메시지: {message.decode()}')

                # 로그 파일에 채팅 내용을 추가합니다.
                with open("api/chat_log.txt", "a") as f:
                    f.write(f"{message.decode()}\n")
                with open("api/console_log.txt", "a") as f:
                    f.write(f"{str(datetime.datetime.now())[0:19]} {message.decode()}\n")

                # 모든 클라이언트에게 메시지를 전송합니다.
                broadcast_message(message, client_socket)
                chat_stop = False
                chat_min = 0
                schedule.cancel_job(job1)
                job1 = schedule.every(60).seconds.do(addmin)


        except:
            print(f'{addr}이(가) 나갔습니다.')
            clients.remove(client_socket)
            client_socket.close()
            with open("api/console_log.txt", "a") as f:
                f.write(f"{str(datetime.datetime.now())[0:19]} {addr}이(가) 나갔습니다.\n")
            break

# 다른 클라이언트에게 메시지를 보내는 함수
def broadcast_message(message, sender):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except:
                clients.remove(client)
                client.close()


# 클라이언트를 대기하며 연결을 처리하는 함수
def accept_clients():
    while True:
        client_socket, addr = server_socket.accept()
        print(f'{addr}이(가) 접속했습니다.')
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()
        with open("api/console_log.txt", "a") as f:
            f.write(f"{str(datetime.datetime.now())[0:19]} {addr}이(가) 접속했습니다.\n")
        with open('api/chat_log.txt', mode='r') as f:
            line = f.read()
        client_socket.send(line.encode())
        msg = "[Server]  Welcome to AKRT Messenger"
        client_socket.send(msg.encode())





# 첫번째 로그 파일을 업로드 합니다.
if firstsave == 0:
    upload_log()
    firstsave = 1
else:
    pass

# 클라이언트 연결을 대기합니다.
print('채팅 서버를 시작합니다.')
print(f'서버 주소: {HOST}, 포트 번호: {PORT}')
with open("api/console_log.txt", "a") as f:
    f.write(f"{str(datetime.datetime.now())[0:19]} 채팅 서버를 시작합니다.\n")
    f.write(f"{str(datetime.datetime.now())[0:19]} 서버 주소: {HOST}, 포트 번호: {PORT}\n")
detect_chat_thread = threading.Thread(target=Detect_Chat)
detect_chat_thread.start()
accept_thread = threading.Thread(target=accept_clients)
accept_thread.start()