from time_tool import *

def chat_log(message: str):
    with open("api/chat_log.txt", "a") as f:
        f.write(f"{message}\n")

def console_log(message: str):
    with open("api/console_log.txt", "a") as f:
        f.write(f"{get_time()} {message}\n")