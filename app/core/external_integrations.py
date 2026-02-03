import os
import requests
try:
    from notion_client import Client as NotionClient
    from notion_client.errors import APIResponseError as NotionAPIError
except ImportError:
    NotionClient = None
    NotionAPIError = Exception
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    gspread = None
    ServiceAccountCredentials = None
try:
    import trello
except ImportError:
    trello = None
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

class NotionIntegration:
    def __init__(self):
        if NotionClient is None:
            raise ImportError("notion_client not installed")
        self.token = os.environ.get('NOTION_TOKEN')
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable not set")
        self.client = NotionClient(auth=self.token)

    def create_page(self, database_id, properties, content=None):
        try:
            data = {
                "parent": {"database_id": database_id},
                "properties": properties
            }
            if content:
                data["children"] = content
            response = self.client.pages.create(**data)
            return {"status": "success", "page_id": response["id"], "url": response["url"]}
        except NotionAPIError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

    def update_page(self, page_id, properties=None, content=None):
        try:
            data = {}
            if properties:
                data["properties"] = properties
            if content:
                data["children"] = content
            response = self.client.pages.update(page_id, **data)
            return {"status": "success", "page_id": response["id"], "url": response["url"]}
        except NotionAPIError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

class GoogleSheetsIntegration:
    def __init__(self):
        if gspread is None or ServiceAccountCredentials is None:
            raise ImportError("gspread or oauth2client not installed")
        creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_json:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not set")
        creds_dict = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        self.client = gspread.authorize(creds)

    def append_row(self, spreadsheet_id, sheet_name, row_data):
        try:
            sheet = self.client.open_by_key(spreadsheet_id).worksheet(sheet_name)
            sheet.append_row(row_data)
            return {"status": "success", "message": f"Row appended to {sheet_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class TrelloIntegration:
    def __init__(self):
        if trello is None:
            raise ImportError("trello not installed")
        self.api_key = os.environ.get('TRELLO_API_KEY')
        self.token = os.environ.get('TRELLO_TOKEN')
        if not self.api_key or not self.token:
            raise ValueError("TRELLO_API_KEY and TRELLO_TOKEN environment variables not set")
        self.client = trello.TrelloClient(api_key=self.api_key, token=self.token)

    def create_card(self, board_id, list_name, name, desc=None):
        try:
            board = self.client.get_board(board_id)
            lists = board.get_lists()
            target_list = next((lst for lst in lists if lst.name == list_name), None)
            if not target_list:
                return {"status": "error", "message": f"List '{list_name}' not found"}
            card = target_list.add_card(name=name, desc=desc or "")
            return {"status": "success", "card_id": card.id, "url": card.url}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class EmailIntegration:
    def __init__(self):
        self.server = os.environ.get('SMTP_SERVER')
        self.port = int(os.environ.get('SMTP_PORT', 587))
        self.user = os.environ.get('SMTP_USER')
        self.password = os.environ.get('SMTP_PASS')
        if not all([self.server, self.user, self.password]):
            raise ValueError("SMTP_SERVER, SMTP_USER, SMTP_PASS environment variables not set")

    def send_email(self, to_email, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = SMTP(self.server, self.port)
            server.starttls()
            server.login(self.user, self.password)
            text = msg.as_string()
            server.sendmail(self.user, to_email, text)
            server.quit()
            return {"status": "success", "message": f"Email sent to {to_email}"}
        except SMTPException as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

class WebhookIntegration:
    def __init__(self):
        pass  # No auth needed

    def post_webhook(self, url, data):
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return {"status": "success", "response": response.json() if response.content else "No content"}
        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

class ExternalIntegrations:
    def __init__(self):
        self.integrations = {}

    def get_integration(self, app_name):
        if app_name not in self.integrations:
            if app_name == 'notion':
                self.integrations[app_name] = NotionIntegration()
            elif app_name == 'googlesheets':
                self.integrations[app_name] = GoogleSheetsIntegration()
            elif app_name == 'trello':
                self.integrations[app_name] = TrelloIntegration()
            elif app_name == 'email':
                self.integrations[app_name] = EmailIntegration()
            elif app_name == 'webhook':
                self.integrations[app_name] = WebhookIntegration()
            else:
                raise ValueError(f"Unknown app: {app_name}")
        return self.integrations[app_name]