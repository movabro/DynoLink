import requests
import re
from datetime import datetime, timedelta

class DynalistClient:
    def __init__(self, api_key, document_ids=None):
        """
        api_key: Dynalist API key
        document_ids: 문서 ID 배열 또는 단일 ID (구형 호환성)
                     [{"id": "...", "name": "...", "type": "..."}, ...]
        """
        self.api_key = api_key
        self.document_ids = self._normalize_document_ids(document_ids)
        self.base_url = "https://dynalist.io/api/v1"
    
    def _normalize_document_ids(self, document_ids):
        """다양한 입력 형식을 표준화"""
        if not document_ids:
            return []
        
        # 문자열 단일 ID인 경우 (구형 호환성)
        if isinstance(document_ids, str):
            return [{"id": document_ids, "name": document_ids, "type": "tagged"}]
        
        # 이미 배열인 경우
        if isinstance(document_ids, list):
            return document_ids
        
        return []
    
    def get_items_by_date(self, target_date):
        """모든 document_id에서 지정된 날짜의 항목 가져오기, 각각의 타입 정보 함께 반환"""
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
        document_id_set = {doc_config['id'] for doc_config in self.document_ids}
        
        # 결과: (아이템 리스트, 모든 노드, 문서 타입 맵)
        items = []
        all_nodes = []
        doc_type_map = {}  # {node_id: doc_type}
        
        for doc_config in self.document_ids:
            target_doc_id = doc_config['id']
            doc_type = doc_config.get('type', 'tagged')
            
            # 해당 document 찾기
            doc = next((d for d in documents if d['id'] == target_doc_id), None)
            if not doc:
                continue
            
            # 문서 내용 가져오기
            doc_response = requests.post(f"{self.base_url}/doc/read", 
                                       headers=headers, 
                                       json={'token': self.api_key, 'file_id': doc['id']})
            if doc_response.status_code == 200:
                content = doc_response.json()
                if content.get('_code') != 'Ok':
                    continue
                
                nodes = content.get('nodes', [])
                all_nodes.extend(nodes)
                
                # 지정된 날짜에 생성된 항목 추출
                target_items = self._filter_items_by_date(content, target_date)
                
                # 각 항목에 문서 타입 정보 추가
                for item in target_items:
                    item['_doc_type'] = doc_type
                    doc_type_map[item['id']] = doc_type
                
                items.extend(target_items)
        
        return items, all_nodes, doc_type_map
    
    def _filter_items_by_date(self, content, target_date):
        """텍스트 기반 날짜 탐색: 'YYMMDD요일' 패턴 매칭
        
        구조:
        - 월 (수준 1)
          - *월 *일 *요일 (수준 2)
            - 260102금 - #업무관련 (수준 3) ← 여기서 추출
            - 260102금 - #개인용무 / #유니콘 (수준 3)
        """
        nodes = content.get('nodes', [])
        target_items = []
        
        # target_date를 YYMMDD 문자열로 변환
        target_date_str = target_date.strftime('%y%m%d')
        
        # 한글 요일 목록
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일']
        
        for node in nodes:
            if not node.get('content'):
                continue
            
            content_text = node.get('content', '').strip()
            
            # "YYMMDDday" 패턴 찾기 (예: 260102금, 260105월)
            # 정규식: 6자리 숫자 + 한글 요일
            pattern = r'(\d{6})([' + ''.join(weekday_kr) + r'])'
            match = re.search(pattern, content_text)
            
            if match:
                extracted_date = match.group(1)
                extracted_day = match.group(2)
                
                # 추출한 날짜와 target_date가 일치하는지 확인
                if extracted_date == target_date_str:
                    # 요일도 검증 (선택사항이지만 정확성을 위해)
                    expected_day_index = target_date.weekday()  # 0=월, 6=일
                    if weekday_kr[expected_day_index] == extracted_day:
                        target_items.append(node)
        
        return target_items

# 테스트 함수
def test_dynalist_api():
    import yaml
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    document_ids = config['dynalist'].get('document_ids') or [config['dynalist']['document_id']]
    client = DynalistClient(config['dynalist']['api_key'], document_ids)
    try:
        from datetime import datetime
        items, all_nodes, doc_type_map = client.get_items_by_date(datetime.now().date())
        print("Today's items:")
        for item in items:
            doc_type = doc_type_map.get(item['id'], 'unknown')
            print(f"- {item.get('content', '')} (type: {doc_type})")
        if not items:
            print("(오늘 생성된 항목이 없습니다.)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dynalist_api()