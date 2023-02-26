import json
import os
import socket
import threading
from backup import GoogleDriveManager
from log import *

EOL = b"</EOL/>"
class RepeatableTimer(object):
    from typing import Iterable

    def __init__(self, interval, function, args: Iterable | None):
        self._interval = interval
        self._function = function
        self._args = args
        self.t: None | threading.Timer = None

    def start(self):
        if self.t is not None:
            self.t.cancel()

        self.t = threading.Timer(self._interval, self._function, self._args, None)
        self.t.start()

    def cancel(self):
        if self.t is not None:
            self.t.cancel()
            self.t = None

    def is_started(self):
        return self.t is not None


class Server:
    def __init__(self, backup: bool, host: str, port: int):
        self.backup = backup

        base_interval = 60.0
        self.not_writing_timer = RepeatableTimer(base_interval, self.google_drive_log, None)
        self.when_writing_timer = RepeatableTimer(base_interval * 10.0, self.google_drive_log, None)

        # 처음 서버 실행시 저장
        self.first_save = 0

        if backup:
            self.google_drive = GoogleDriveManager()

            if self.first_save == 0:
                self.google_drive.upload_log()
                self.first_save = 1
            else:
                pass
        else:
            print("복구옵션 꺼짐")
            console_log("복구옵션 꺼짐")

        # 소켓 객체를 생성합니다.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 서버 소켓을 바인딩합니다.
        self.server_socket.bind((host, port))

        # 클라이언트와 연결할 때까지 대기합니다.
        self.server_socket.listen()

        # 연결된 클라이언트 리스트를 저장합니다.
        self.clients = []

    def when_chat(self):  # 채팅 입력 받으면
        if not self.when_writing_timer.is_started():  # 채팅할때 타이머 돌아감
            self.when_writing_timer.start()

        if self.not_writing_timer.is_started():  # 채팅끝남 감지 타이머는 채팅할 때 마다 초기화 됨
            self.not_writing_timer.cancel()
        self.not_writing_timer.start()  # 채팅끝남 감지 타이머도 돌아감

    def google_drive_log(self):
        self.google_drive.upload_log()
        self.not_writing_timer.cancel()
        self.when_writing_timer.cancel()  # 채팅 하지 않을때는 한번 업로드하고 그대로 타이머 멈춤

    # 클라이언트로부터 메시지를 받아서 다른 클라이언트에게 보내는 함수
    def handle_client(self, client_socket, addr):
        while True:
            try:
                message = client_socket.recv(1024)
                if message:
                    print(f'{addr}에서 온 메시지: {message.decode()}')

                    # 로그 파일에 채팅 내용을 추가합니다.
                    chat_log(message.decode())
                    console_log(message.decode())

                    # 모든 클라이언트에게 메시지를 전송합니다.
                    self.broadcast_message(message, client_socket)
                    if self.backup:
                        self.when_chat()
            except:
                print(f'{addr}이(가) 나갔습니다.')
                console_log(f"{addr}이(가) 나갔습니다.")
                self.clients.remove(client_socket)
                client_socket.close()

                break

    # 다른 클라이언트에게 메시지를 보내는 함수
    def broadcast_message(self, message, sender):
        for client in self.clients:
            if client != sender:
                try:
                    client.send(message)
                except:
                    self.clients.remove(client)
                    client.close()

    # 클라이언트를 대기하며 연결을 처리하는 함수
    def accept_clients(self):
        global EOL

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f'{addr}이(가) 접속했습니다.')
            self.clients.append(client_socket)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()
            console_log(f"{addr}이(가) 접속했습니다.")
            with open('api/chat_log.txt', mode='r') as f:
                log = f.read()
                for line in log.encode('utf8').splitlines():
                    client_socket.send(line + EOL)
            msg = "[Server]  Welcome to AKRT Messenger"
            client_socket.send(msg.encode('utf8'))

    def run(self):
        # 클라이언트 연결을 대기합니다.
        print('채팅 서버를 시작합니다.')
        print(f'서버 주소: {HOST}, 포트 번호: {PORT}')

        console_log("채팅 서버를 시작합니다.")
        console_log(f"서버 주소: {HOST}, 포트 번호: {PORT}")

        accept_thread = threading.Thread(target=self.accept_clients)
        accept_thread.start()


if __name__ == "__main__":

    BACKUP = False
    HOST = '127.0.0.1'
    PORT = 8080

    if os.path.isfile("settings.json"):
        with open('settings.json', mode='r') as f:
            file = json.load(f)
            HOST = file["HOST"]
            PORT = file["PORT"]
            BACKUP = file["BACKUP"]

    server = Server(BACKUP, HOST, PORT)
    server.run()
