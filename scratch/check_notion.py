import requests
import yaml
import json

with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

notion_api_key = config['notion']['api_key']
# concept DB
database_id = "33e3d5953cda80f0afa1e5580b2fbe61"

headers = {
    'Authorization': f'Bearer {notion_api_key}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

response = requests.post(
    f'https://api.notion.com/v1/databases/{database_id}/query',
    headers=headers,
    json={"page_size": 10}
)

if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    print(f"Found {len(results)} recent items in 'concept' DB:")
    for r in results:
        title_val = "Unknown"
        domain_val, cat_val, tags_val, date_val = "", "", [], ""
        for prop_name, prop_data in r['properties'].items():
            if prop_data['type'] == 'title':
                title_val = prop_data['title'][0]['plain_text'] if prop_data['title'] else "(Empty Title)"
            elif prop_data['type'] == 'select':
                if prop_name in ['대분류', '영역', 'Domain']:
                    domain_val = prop_data['select']['name'] if prop_data['select'] else ""
                elif prop_name in ['중분류', '카테고리', 'Category']:
                    cat_val = prop_data['select']['name'] if prop_data['select'] else ""
            elif prop_data['type'] == 'multi_select':
                tags_val = [t['name'] for t in prop_data['multi_select']]
            elif prop_data['type'] == 'date':
                date_val = prop_data['date']['start'] if prop_data['date'] else ""
        
        # 블록 내용(Children) 조회하기 위해 API 한번 더 호출 (요약)
        block_resp = requests.get(f"https://api.notion.com/v1/blocks/{r['id']}/children", headers=headers)
        children_count = 0
        if block_resp.status_code == 200:
            children_count = len(block_resp.json().get('results', []))
            
        print(f"- Title: {title_val}")
        print(f"  Date: {date_val}, Domain: {domain_val}, Category: {cat_val}, Tags: {tags_val}")
        print(f"  Content Blocks: {children_count}")
        print("---")
else:
    print(f"Error {response.status_code}: {response.text}")
