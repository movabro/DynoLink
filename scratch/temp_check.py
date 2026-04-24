import requests
import yaml

with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

notion_api_key = config['notion']['api_key']
database_id = "3413d5953cda805286fedf8c5e50d1d1" # personal

headers = {
    'Authorization': f'Bearer {notion_api_key}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

response = requests.post(
    f'https://api.notion.com/v1/databases/{database_id}/query',
    headers=headers,
    json={
        "page_size": 10,
        "sorts": [
            {
                "property": "날짜",
                "direction": "descending"
            }
        ]
    }
)

if response.status_code == 200:
    for r in response.json().get('results', []):
        props = r['properties']
        title = props.get('Name', props.get('제목', props.get('title', {}))).get('title', [{}])[0].get('plain_text', '') if props.get('Name', props.get('제목', props.get('title', {}))).get('title') else "(Empty)"
        date = props.get('날짜', props.get('Date', {})).get('date', {})
        date_start = date.get('start', '') if date else ""
        print(f"Title: {title}, Date: {date_start}")
else:
    print(response.text)
