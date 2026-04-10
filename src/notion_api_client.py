import requests
import notion_client

class NotionClient:
    def __init__(self, api_key, database_id):
        self.client = notion_client.Client(auth=api_key)
        self.api_key = api_key
        self.database_id = database_id
        self.properties = self._load_database_properties()
        self.title_property_name = self._find_title_property()
        self.date_property_name = self._find_property_name(['날짜', 'Date'])
        self.top_tag_property_name = self._find_property_name(['상위 태그', '상위태그', 'Top Tag'])
        self.sub_tags_property_name = self._find_property_name(['하위 태그', '하위태그', 'Sub Tags', '태그'])
        self.path_property_name = self._find_property_name(['계층 경로', '계층경로', 'Path'])
        self.memo_property_name = self._find_property_name(['메모', 'Memo'])

    def _load_database_properties(self):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        response = requests.get(f'https://api.notion.com/v1/databases/{self.database_id}', headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('properties', {})

    def _find_title_property(self):
        for name, prop in self.properties.items():
            if prop.get('type') == 'title':
                return name
        return 'Name'

    def _find_property_name(self, candidates):
        normalized_props = {self._normalize_key(name): name for name in self.properties}
        for candidate in candidates:
            if self._normalize_key(candidate) in normalized_props:
                return normalized_props[self._normalize_key(candidate)]
        return None

    def _normalize_key(self, key):
        return ''.join(key.lower().split())

    def add_pages_to_database(self, records):
        responses = []
        for record in records:
            properties = {
                self.title_property_name: {
                    "title": [{"text": {"content": record['title']}}]
                }
            }

            if self.date_property_name:
                properties[self.date_property_name] = {
                    "date": {"start": record['date']}
                }

            if record.get('top_tag') and self.top_tag_property_name:
                properties[self.top_tag_property_name] = {
                    "select": {"name": record['top_tag']}
                }

            if record.get('sub_tags') and self.sub_tags_property_name:
                properties[self.sub_tags_property_name] = {
                    "multi_select": [{"name": tag} for tag in record['sub_tags']]
                }

            if record.get('hierarchy_path') and self.path_property_name:
                properties[self.path_property_name] = {
                    "rich_text": [{"type": "text", "text": {"content": record['hierarchy_path']}}]
                }

            if record.get('memo') and self.memo_property_name:
                properties[self.memo_property_name] = {
                    "rich_text": [{"type": "text", "text": {"content": record['memo']}}]
                }

            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            responses.append(response)
        return responses