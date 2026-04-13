import requests
from notion_client import Client as NotionClientAPI

class NotionClient:
    def __init__(self, api_key, database_id):
        self.client = NotionClientAPI(auth=api_key)
        self.api_key = api_key
        self.database_id = database_id
        self.properties = self._load_database_properties()
        self.title_property_name = self._find_title_property()
        self.date_property_name = self._find_property_name(['날짜', 'Date'])
        # 3단계 계층 구조 필드
        self.domain_property_name = self._find_property_name(['대분류', '영역', 'Domain'])
        self.category_property_name = self._find_property_name(['중분류', '카테고리', 'Category'])
        self.tags_property_name = self._find_property_name(['소분류', '태그', 'Tags'])

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

    def _split_text_by_limit(self, text, limit=2000):
        """텍스트를 지정된 길이로 분할 (Notion API 제한: 2000자)"""
        if len(text) <= limit:
            return [text]
        
        chunks = []
        current_pos = 0
        while current_pos < len(text):
            chunk = text[current_pos:current_pos + limit]
            chunks.append(chunk)
            current_pos += limit
        return chunks

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

            # 대분류 (Domain)
            if record.get('domain') and self.domain_property_name:
                properties[self.domain_property_name] = {
                    "select": {"name": record['domain']}
                }

            # 중분류 (Category)
            if record.get('category') and self.category_property_name:
                properties[self.category_property_name] = {
                    "select": {"name": record['category']}
                }

            # 소분류+ (Tags - Multi-select)
            if record.get('sub_tags') and self.tags_property_name:
                properties[self.tags_property_name] = {
                    "multi_select": [{"name": tag} for tag in record['sub_tags']]
                }

            # 메모는 페이지 내용으로 저장 (2000자 초과 시 자동으로 분할)
            children = []
            if record.get('memo'):
                memo_chunks = self._split_text_by_limit(record['memo'], limit=2000)
                for i, chunk in enumerate(memo_chunks):
                    prefix = f"[{i+1}/{len(memo_chunks)}] " if len(memo_chunks) > 1 else ""
                    children.append({
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": prefix + chunk}}]
                        }
                    })

            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children if children else None
            )
            responses.append(response)
        return responses


class NotionMultiClient:
    """다중 Notion 데이터베이스를 관리하는 클라이언트 (db_purpose 기반)"""
    
    def __init__(self, api_key, databases_config):
        """
        api_key: Notion API 키
        databases_config: 데이터베이스 설정 리스트
            [
                {
                    "name": "개념_단어_용어", 
                    "database_id": "...", 
                    "purpose": "concept"
                },
                {
                    "name": "업무관련", 
                    "database_id": "...", 
                    "purpose": "work",
                    "tag_filter": "#업무관련"
                },
                ...
            ]
        """
        self.api_key = api_key
        self.databases_config = databases_config
        self.clients = {}
        self.purpose_to_db = {}
        
        # 각 데이터베이스에 대한 NotionClient 초기화
        for db_config in databases_config:
            purpose = db_config['purpose']
            db_id = db_config['database_id']
            self.clients[purpose] = NotionClient(api_key, db_id)
            self.purpose_to_db[purpose] = db_config
    
    def add_pages_to_all_databases(self, records):
        """모든 적절한 데이터베이스에 페이지 추가"""
        results = {}
        
        for record in records:
            purpose = record.get('db_purpose', 'concept')
            
            if purpose and purpose in self.clients:
                if purpose not in results:
                    results[purpose] = {'success': 0, 'failed': 0, 'records': []}
                
                try:
                    response = self.clients[purpose].add_pages_to_database([record])
                    results[purpose]['success'] += 1
                    results[purpose]['records'].append(record['title'])
                except Exception as e:
                    results[purpose]['failed'] += 1
                    print(f"Error adding record '{record['title']}' to {purpose}: {str(e)}")
        
        return results