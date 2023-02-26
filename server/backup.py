import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

from time_tool import get_time_for_file, get_time


class GoogleDriveManager:
    def __init__(self):
        # 인증 토큰 파일 경로
        token_file = 'api/token.json'

        # API 키 파일 경로
        api_key_file = 'api/api_key.json'

        # OAuth 2.0 인증 토큰 생성
        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    api_key_file, ['https://www.googleapis.com/auth/drive'])
                creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        # Google Drive API 클라이언트 생성
        self.service = build('drive', 'v3', credentials=creds)

    def upload_log(self):
        # 구글 드라이브 폴더 ID
        f = open("api/folder_id.txt", 'r')
        folder_id = f.read()
        f.close()

        # 업로드 할 파일 경로
        file_path = 'api/chat_log.txt'

        # 로그 파일 업로드
        file_name = get_time_for_file() + "_chatlog.txt"
        # file_name = "chat_log.txt"
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(file_name + " 으로 복구됨. 파일 아이디: " + file.get('id'))
        with open("api/console_log.txt", "a") as f:
            f.write(get_time() + file_name + " 으로 복구됨. 파일 아이디: " + file.get('id') + "\n")
