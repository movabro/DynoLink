import yaml
from src.transformer import Transformer
from src.dynalist_client import DynalistClient
from datetime import datetime

with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Dynalist 클라이언트 초기화
document_ids = config['dynalist']['document_ids']
dynalist = DynalistClient(config['dynalist']['api_key'], document_ids)

target_date = datetime.strptime("2026-04-22", '%Y-%m-%d').date()
today_items, all_nodes, doc_type_map = dynalist.get_items_by_date(target_date)

print(f"Found {len(today_items)} items for {target_date}")
for item in today_items:
    print(f"Item ID: {item['id']}")
    print(f"Content: {item.get('content')}")
    print(f"Doc Type: {doc_type_map.get(item['id'])}")

print("\n--- Transformer Test ---")
transformer = Transformer()
records = transformer.dynalist_to_notion_records(today_items, all_nodes, doc_type_map)

for r in records:
    print(f"Title: {r['title']}")
    print(f"DB Purpose: {r['db_purpose']}")
    print(f"Date: {r['date']}")
    print(f"Format: [{r['domain']}] > [{r['category']}] > {r.get('sub_tags', [])}")
    print(f"Memo length: {len(r['memo'])}")
    print("---")

