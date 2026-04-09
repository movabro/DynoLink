from datetime import datetime

class Transformer:
    def dynalist_to_notion_blocks(self, dynalist_items):
        blocks = []
        for item in dynalist_items:
            # Dynalist 노드를 Notion 블록으로 변환
            # 예: 불렛 포인트 -> to_do 또는 bulleted_list_item
            block = {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": item.get('content', '')}}],
                    "checked": item.get('checked', False)
                }
            }
            blocks.append(block)
        return blocks