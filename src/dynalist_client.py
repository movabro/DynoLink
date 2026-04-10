import requests
from datetime import datetime, timedelta

class DynalistClient:
    def __init__(self, api_key, document_id=None):
        self.api_key = api_key
        self.document_id = document_id
        self.base_url = "https://dynalist.io/api/v1"
    
    def get_today_items(self):
        # 오늘 날짜 계산
        today = datetime.now().date()
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 문서 리스트 가져오기
        response = requests.post(f"{self.base_url}/file/list", headers=headers, json={'token': self.api_key})
        if response.status_code != 200:
            raise Exception(f"Failed to fetch documents: {response.text}")
        
        data = response.json()
        if data.get('_code') != 'Ok':
            raise Exception(f"API Error: {data.get('_code')} - {data.get('_msg')}")
        
        documents = data.get('files', [])
        
        # 특정 문서 또는 전체 처리
        items = []
        all_nodes = []
        for doc in documents:
            if self.document_id and doc['id'] != self.document_id:
                continue
            
            # 문서 내용 가져오기
            doc_response = requests.post(f"{self.base_url}/doc/read", 
                                       headers=headers, 
                                       json={'token': self.api_key, 'file_id': doc['id']})
            if doc_response.status_code == 200:
                content = doc_response.json()
                if content.get('_code') != 'Ok':
                    continue  # skip this document
                nodes = content.get('nodes', [])
                all_nodes.extend(nodes)
                # 오늘 생성된 항목 추출 (created 필터링)
                today_items = self._filter_today_items(content, today)
                items.extend(today_items)
        
        return items, all_nodes
    
    def _filter_today_items(self, content, today):
        # Dynalist의 노드 구조에서 오늘 생성된 항목 필터링
        nodes = content.get('nodes', [])
        today_items = []
        for node in nodes:
            created_timestamp = node.get('created', 0) / 1000  # milliseconds to seconds
            created_time = datetime.fromtimestamp(created_timestamp).date()
            if created_time == today:
                today_items.append(node)
        return today_items

# 테스트 함수
def test_dynalist_api():
    import yaml
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    client = DynalistClient(config['dynalist']['api_key'], config['dynalist']['document_id'])
    try:
        items = client.get_today_items()
        print("Today's items:")
        for item in items:
            print(f"- {item.get('content', '')}")
        if not items:
            print("(오늘 생성된 항목이 없습니다.)")
    except Exception as e:
        print(f"Error: {e}")
        # 추가 디버깅: API 응답 전체 출력 시도
        try:
            # 간단히 재호출해서 응답 확인 (실제로는 로깅으로 대체)
            headers = {'Authorization': f'Bearer {config["dynalist"]["api_key"]}', 'Content-Type': 'application/json'}
            response = requests.post("https://dynalist.io/api/v1/file/list", headers=headers, json={'token': config['dynalist']['api_key']})
            print(f"Debug - Status Code: {response.status_code}")
            print(f"Debug - Response: {response.text}")
        except Exception as debug_e:
            print(f"Debug failed: {debug_e}")

if __name__ == "__main__":
    test_dynalist_api()