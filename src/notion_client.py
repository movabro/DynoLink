from datetime import datetime
from notion_client import Client

class NotionClient:
    def __init__(self, api_key, database_id):
        self.client = Client(auth=api_key)
        self.database_id = database_id
    
    def add_blocks_to_page(self, blocks):
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "title": {
                    "title": [{"text": {"content": f"Daily Notes - {today}"}}]
                }
            },
            children=blocks
        )
        return response