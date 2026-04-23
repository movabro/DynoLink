import requests
import yaml
import json

with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

api_key = config['dynalist']['api_key'] 
main_doc_id = config['dynalist']['document_ids'][0]['id']

headers = {'Content-Type': 'application/json'}
response = requests.post(
    "https://dynalist.io/api/v1/doc/read",
    headers=headers,
    json={'token': api_key, 'file_id': main_doc_id}
)

if response.status_code == 200:
    data = response.json()
    nodes = data.get('nodes', [])
    print(f"Total nodes in main document: {len(nodes)}")
    
    # 2월 10일 (260210화) 관련 노드를 검색해보자
    target_date = "260210화"
    
    target_node = None
    node_map = {n['id']: n for n in nodes}
    
    for n in nodes:
        content = n.get('content', '')
        if target_date in content:
            target_node = n
            break
            
    if target_node:
        print("\nFound Target Node:")
        print(json.dumps(target_node, indent=2, ensure_ascii=False))
        
        print("\nParent Node:")
        # 부모 노드를 찾자 (node_map을 순회하여 현재 노드를 children으로 가진 놈 찾기)
        parent_node = None
        for n in nodes:
            if target_node['id'] in n.get('children', []):
                parent_node = n
                break
        if parent_node:
            print(json.dumps(parent_node, indent=2, ensure_ascii=False))
        else:
            print("No Parent found (Root)")
            
        print("\nChild Nodes:")
        for child_id in target_node.get('children', []):
            if child_id in node_map:
                print(json.dumps(node_map[child_id], indent=2, ensure_ascii=False))
    else:
        print(f"Could not find node containing {target_date}")
        
    print("\nSample top 5 nodes for reference:")
    for n in nodes[:5]:
        print(json.dumps(n, indent=2, ensure_ascii=False))
        
else:
    print(f"Error {response.status_code}: {response.text}")
