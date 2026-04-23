import re
from datetime import datetime

class Transformer:
    def dynalist_to_notion_records(self, today_items, all_nodes, doc_type_map=None):
        """
        Dynalist 아이템을 Notion 레코드로 변환 (Tree Traversal 방식)
        doc_type_map: {item_id: "concept"|"tagged"}
        """
        if doc_type_map is None:
            doc_type_map = {}
        
        node_map = {node['id']: node for node in all_nodes}
        records = []
        
        # today_items는 주로 '260423목 - #태그'와 같은 Level 3 노드들
        for item in today_items:
            item_id = item['id']
            doc_type = doc_type_map.get(item_id, 'tagged')
            
            # Level 3 노드에서 타겟 날짜 추출 시도
            target_date_str = self._extract_date_from_text(item.get('content', ''))
            if not target_date_str:
                created_ts = item.get('created', 0) / 1000
                target_date_str = datetime.fromtimestamp(created_ts).date().isoformat()
            
            # 재귀적으로 하위 노드 탐색 및 Notion 레코드 생성 시작
            self._extract_items_recursively(
                node_id=item_id, 
                node_map=node_map, 
                current_tags=[], 
                records=records, 
                target_date_str=target_date_str, 
                doc_type=doc_type
            )
            
        return records

    def _extract_tags(self, text):
        """텍스트에서 #태그 추출 및 '/' 구분 다중 태그 처리 (순서 유지)"""
        if not text:
            return []
        
        parts = text.split('/')
        tags = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            hashtags = re.findall(r"#([^\s#]+)", part)
            if hashtags:
                tags.extend([f"#{tag}" for tag in hashtags])
        
        return [t.replace(',', '_') for t in tags]

    def _extract_date_from_text(self, text):
        """'YYMMDDday' 패턴 날짜 추출 후 ISO 형식 반환"""
        if not text:
            return None
        
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일']
        pattern = r'(\d{6})([' + ''.join(weekday_kr) + r'])'
        match = re.search(pattern, text)
        
        if not match:
            return None
        
        date_str = match.group(1)
        extracted_day = match.group(2)
        
        try:
            yy = int(date_str[:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:6])
            yyyy = 2000 + yy if yy < 100 else yy
            date_obj = datetime(yyyy, mm, dd)
            return date_obj.date().isoformat()
        except (ValueError, IndexError):
            return None

    def _extract_items_recursively(self, node_id, node_map, current_tags, records, target_date_str, doc_type):
        if node_id not in node_map:
            return
            
        node = node_map[node_id]
        raw_content = node.get('content', '').strip()
        
        # 1. Rule A: 태그 추출 및 부모 태그 상속
        extracted_tags = self._extract_tags(raw_content)
        tags_for_children = list(dict.fromkeys(current_tags + extracted_tags))
        
        # 2. Rule B: 제목 추출 (필요 없는 패턴/특수문자 제거)
        title_text = raw_content
        
        # Level 3 등의 노드에서 나타나는 날짜 패턴 제거
        date_pattern = r'^\d{6}[월화수목금토일]\s*-\s*'
        if re.search(date_pattern, title_text):
            title_text = re.sub(date_pattern, '', title_text).strip()
        elif re.search(r'^\d{6}[월화수목금토일]', title_text):
            title_text = re.sub(r'^\d{6}[월화수목금토일]', '', title_text).strip()
            
        # 태그 제거
        title_text = re.sub(r'#[^\s#]+', '', title_text).strip()
        # 앞부분에 남은 구분자( - , / 등) 제거
        title_text = re.sub(r'^[/\-\s]+', '', title_text).strip()
        
        # 3. Notion 페이지 생성 여부 결정
        # Title 문자열이 있거나, 문자열은 없지만 Note 필드에 내용이 있는 경우 생성 대상 (아이템)
        if title_text or node.get('note', '').strip():
            db_classification_tags = {"#업무관련", "#개인용무"}
            pure_tags = []
            
            domain_tag = ""
            category_tag = ""
            sub_tags = []
            db_purpose = "concept"
            
            # 1. 태그 분배 (분류 태그 감지 및 스트리핑)
            for t in tags_for_children:
                if t in db_classification_tags:
                    # DB 분류 규칙 적용
                    if t == "#업무관련":
                        db_purpose = "work"
                    elif t == "#개인용무":
                        db_purpose = "personal"
                    # 분류 태그는 속성에 포함하지 않기 위해 pure_tags에 넣지 않음 (스트리핑 처리)
                else:
                    pure_tags.append(t)
            
            if doc_type == "concept":
                db_purpose = "concept"
                
            # 2. 동적 속성 할당 (Dynamic Property Assignment)
            if pure_tags:
                domain_tag = pure_tags.pop(0)
            
            if pure_tags:
                category_tag = pure_tags.pop(0)
                
            sub_tags = list(dict.fromkeys(pure_tags))
            
            title = title_text if title_text else "(제목 없음)"
            
            record = {
                'title': title,
                'date': target_date_str,
                'domain': domain_tag,
                'category': category_tag,
                'sub_tags': sub_tags,
                'memo': node.get('note', '').strip(),  # Rule B: 컨텐츠는 Note 필드 적용
                'db_purpose': db_purpose
            }
            records.append(record)
            
        # 4. 다운로드된 자식 노드들에 대해서도 재귀적으로 파싱 실행 (Rule C)
        for child_id in node.get('children', []):
            self._extract_items_recursively(
                child_id, node_map, tags_for_children, records, target_date_str, doc_type
            )