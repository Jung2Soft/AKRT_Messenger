import socket
import threading
import datetime

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

# 클라이언트로부터 메시지를 받아서 다른 클라이언트에게 보내는 함수
def handle_client(client_socket, addr):
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                print(f'{addr}에서 온 메시지: {message.decode()}')

                # 로그 파일에 채팅 내용을 추가합니다.
                with open("chat_log.txt", "a") as f:
                    f.write(f"{datetime.datetime.now()} {addr}: {message.decode()}\n")

                # 모든 클라이언트에게 메시지를 전송합니다.
                broadcast_message(message, client_socket)

        except:
            print(f'{addr}이(가) 나갔습니다.')
            clients.remove(client_socket)
            client_socket.close()
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

# 클라이언트 연결을 대기합니다.
print('채팅 서버를 시작합니다.')
print(f'서버 주소: {HOST}, 포트 번호: {PORT}')
accept_thread = threading.Thread(target=accept_clients)
accept_thread.start()