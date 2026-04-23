from src.transformer import Transformer

transformer = Transformer()

all_nodes = [
    {"id": "node_1", "content": "260423목 - #업무관련"},
    {"id": "node_2", "content": "#홈로봇 / #청소기"},
    {"id": "node_3", "content": "필터 교체 - 먼지 많았음", "note": "먼지 필터를 세척했음."},
    {"id": "node_4", "content": "먼지 털기"},
    {"id": "node_5", "content": "260423목 - #개인용무"},
    {"id": "node_6", "content": "#가족관련 / #로운이 - 자전거 탔음", "note": "공원에서 자전거"}
]

# Set up children relationships
all_nodes[0]['children'] = ["node_2"]
all_nodes[1]['children'] = ["node_3", "node_4"]
all_nodes[4]['children'] = ["node_6"]

today_items = [all_nodes[0], all_nodes[4]]

doc_type_map = {"node_1": "tagged", "node_5": "tagged"}

records = transformer.dynalist_to_notion_records(today_items, all_nodes, doc_type_map)

print(f"Generated {len(records)} records")
for i, r in enumerate(records):
    print(f"\n--- Record {i+1} ---")
    print(f"Title: {r['title']}")
    print(f"Domain: {r['domain']}")
    print(f"Category: {r['category']}")
    print(f"Sub Tags: {r['sub_tags']}")
    print(f"Memo: {r['memo'][:50]}")
    print(f"DB Purpose: {r['db_purpose']}")
