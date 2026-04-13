import re
from datetime import datetime

class Transformer:
    def dynalist_to_notion_records(self, today_items, all_nodes, doc_type_map=None):
        """
        Dynalist 아이템을 Notion 레코드로 변환
        doc_type_map: {item_id: "concept"|"tagged"}
        """
        if doc_type_map is None:
            doc_type_map = {}
        
        node_map = {node['id']: node for node in all_nodes}
        parent_map = self._build_parent_map(all_nodes)
        records = []
        for item in today_items:
            record = self._build_record(item, node_map, parent_map, doc_type_map)
            records.append(record)
        return records

    def _build_parent_map(self, nodes):
        parent_map = {}
        for node in nodes:
            for child_id in node.get('children', []):
                parent_map[child_id] = node['id']
        return parent_map

    def _build_path(self, node_id, node_map, parent_map):
        """노드부터 루트까지의 경로 생성"""
        path_nodes = []
        current_id = node_id
        while current_id and current_id in node_map:
            current_node = node_map[current_id]
            path_nodes.append(current_node)
            current_id = parent_map.get(current_id)
        return list(reversed(path_nodes))

    def _extract_tags(self, text):
        """텍스트에서 #태그 추출"""
        if not text:
            return []
        tags = re.findall(r"#([^\s#]+)", text)
        return [f"#{tag}" for tag in tags]

    def _build_hierarchical_tags(self, path_nodes):
        """경로를 기반으로 계층적 태그 추출 (3단계: 대-중-소)"""
        # 경로의 모든 노드에서 태그 추출
        all_tags = []
        for path_node in path_nodes:
            tags = self._extract_tags(path_node.get('content', ''))
            all_tags.extend(tags)
        
        # 3단계로 분류
        domain = all_tags[0] if len(all_tags) > 0 else ""
        category = all_tags[1] if len(all_tags) > 1 else ""
        sub_tags = all_tags[2:] if len(all_tags) > 2 else []
        
        return domain, category, sub_tags

    def _build_record(self, item, node_map, parent_map, doc_type_map):
        path_nodes = self._build_path(item['id'], node_map, parent_map)
        
        created_timestamp = item.get('created', 0) / 1000
        created = datetime.fromtimestamp(created_timestamp)
        date_str = created.date().isoformat()
        
        # 콘텐츠에서 태그 추출 및 정제
        raw_content = item.get('content', '').strip()
        content_tags = self._extract_tags(raw_content)
        content_without_tags = re.sub(r'#[^\s#]+', '', raw_content).strip()
        
        item_id = item['id']
        doc_type = doc_type_map.get(item_id, 'tagged')
        
        # 기본값 설정
        domain = ""
        category = ""
        sub_tags = []
        db_purpose = "concept"  # 기본값
        
        if doc_type == 'concept':
            # 개념 타입: 모든 항목이 concept DB로 가감, 태그 정보는 사용하지 않음
            db_purpose = "concept"
            domain = ""
            category = ""
            sub_tags = []
        else:
            # tagged 타입: 계층적 태그 + DB 분류 기준 확인
            path_tags = []
            for path_node in path_nodes:
                path_tags.extend(self._extract_tags(path_node.get('content', '')))
            
            # 경로 태그가 있으면 사용, 없으면 콘텐츠 태그 사용
            if path_tags:
                domain, category, sub_tags = self._build_hierarchical_tags(path_nodes)
                item_tags = path_tags
            else:
                item_tags = content_tags
                domain = item_tags[0] if len(item_tags) > 0 else ""
                category = item_tags[1] if len(item_tags) > 1 else ""
                sub_tags = item_tags[2:] if len(item_tags) > 2 else []
            
            # DB 선택: 특정 태그 기반
            if "#업무관련" in item_tags or "#업무관련" in [t.lower() for t in domain.lower() if t]:
                db_purpose = "work"
            elif "#개인용무" in item_tags or "#개인용무" in [t.lower() for t in domain.lower() if t]:
                db_purpose = "personal"
            else:
                db_purpose = "concept"  # 기본값

        return {
            'title': content_without_tags or '(No content)',
            'date': date_str,
            'domain': domain,  # 대분류 (Select)
            'category': category,  # 중분류 (Select)
            'sub_tags': list(dict.fromkeys(sub_tags)),  # 소분류+ (Multi-select)
            'memo': item.get('note', '').strip(),
            'db_purpose': db_purpose  # Notion DB 선택 기준
        }