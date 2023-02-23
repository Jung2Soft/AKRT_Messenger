import sys
import os
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import socket
import threading
import requests
import time
import urllib.request

url = 'http://www.google.com'


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form1 = resource_path("connect.ui")
form2 = resource_path("chat.ui")
form_class1 = uic.loadUiType(form1)[0]
form_class2 = uic.loadUiType(form2)[0]

class WindowClass1(QMainWindow, form_class1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.CONNECT.mousePressEvent = self.connect_server
        self.exit.mousePressEvent = self.close

    def connect_server(self, event):
        # 서버 주소와 포트 번호를 지정합니다.
        HOST = self.IPedit.text().replace(" ", "") # 공백 지움
        PORT = int(self.PORTedit.text().replace(" ", "")) # 동일

        # 서버에 연결합니다.
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 소켓 객체를 생성합니다.
            self.client_socket.connect((HOST, PORT))
            myWindow2 = WindowClass2(self.client_socket)  # client_socket 변수를 WindowClass2로 전달합니다.
            myWindow2.show()
            myWindow1.close()
        except ConnectionError:
            print("연결할 수 없습니다.")

    def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        try:
            if self.offset is not None and event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.pos() - self.offset)
            else:
                super().mouseMoveEvent(event)
        except:
            pass

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


class WindowClass2(QMainWindow, form_class2):
    def __init__(self, client_socket):  # client_socket 변수를 인자로 받습니다.
        super().__init__()
        self.setupUi(self)

        self.client_socket = client_socket  # 전달받은 client_socket 변수를 인스턴스 변수로 저장합니다.
        #self.myip.setText(self.client_socket.getsockname()[0]) #내 내부 IP 확인
        self.setWindowFlags(Qt.FramelessWindowHint)
        ip = requests.get("http://ip.jsontest.com").json()['ip']
        self.myip.setText(ip)
        self.model = QStandardItemModel(self)
        self.chatview.setModel(self.model)
        self.chatview.setVerticalScrollBar(self.chatscroll)
        self.chatview.setHorizontalScrollBar(self.chatscroll2)
        self.mychat.setVerticalScrollBar(self.mychatscroll)

        self.send.mousePressEvent = self.send_message
        self.exit.mousePressEvent = self.close
        self.mychat.installEventFilter(self)

        self.chatview.scrollToBottom()



        # 스레드
        self.send_thread = threading.Thread(target=self.send_message)
        self.get_thread = threading.Thread(target=self.get_message)
        self.send_thread.start()
        self.get_thread.start()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj is self.mychat:
            if event.key() == Qt.Key_Return and self.mychat.hasFocus():
                self.send_message(None)
                return True
        return False  # 이 부분을 추가

    def send_message(self, event):
        date = urllib.request.urlopen(url).headers['Date'][5:-4]
        hour, min = date[12:14], date[15:17]
        hour = int(hour) + 9
        if hour >= 24:
            hour = hour - 24
            hour = "0" + str(hour)
        else:
            pass
        sendtime = (f'[{hour}:{min}]  ')
        message = self.mychat.toPlainText()
        sendmessage = sendtime + message
        if len(message.replace(' ', '')) < 1:
            pass
        else:
            self.client_socket.sendall(sendmessage.encode())  # self.client_socket을 이용해 메시지를 전송합니다.
            self.model.appendRow(QStandardItem(sendmessage))
            self.mychat.clear()
            self.chatview.scrollToBottom()

    def get_message(self):
        while True:
            final_message = b''
            while True:
                message = self.client_socket.recv(1024)
                if not message:
                    break
                final_message += message
                if len(message) < 1024:
                    break
            decoded_message = final_message.decode()
            self.model.appendRow(QStandardItem(decoded_message)) # 1024바이트가 넘어도 유연하게 데이터를 받음


    def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        try:
            if self.offset is not None and event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.pos() - self.offset)
            else:
                super().mouseMoveEvent(event)
        except:
            pass

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow1 = WindowClass1()
    myWindow1.show()
    app.exec_()

# 클라이언트 소켓 닫기
myWindow1.client_socket.close() # 인스턴스 변수로 변경 후 호출