#!/usr/bin/env python
import sys
import yaml
from datetime import datetime
from src.dynalist_client import DynalistClient
from src.transformer import Transformer
from src.notion_client import NotionClient

def main():
    # 설정 로드
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("=" * 60)
    print("DynoLink 2단계: Notion 블록 생성 테스트")
    print("=" * 60)
    
    # 1단계: Dynalist에서 오늘 항목 가져오기
    print("\n[Step 1] Dynalist에서 오늘 항목 가져오기...")
    try:
        dynalist_client = DynalistClient(
            config['dynalist']['api_key'],
            config['dynalist']['document_id']
        )
        today_items = dynalist_client.get_today_items()
        print(f"✓ {len(today_items)}개 항목을 가져왔습니다.")
        
        if not today_items:
            print("⚠ 오늘 항목이 없습니다. 테스트를 계속 진행합니다.")
            today_items = [
                {"content": "테스트 항목 1", "checked": False},
                {"content": "테스트 항목 2", "checked": True},
                {"content": "테스트 항목 3", "checked": False}
            ]
            print(f"→ 테스트용 {len(today_items)}개 더미 항목을 생성했습니다.")
    except Exception as e:
        print(f"✗ Dynalist 에러: {e}")
        return False
    
    # 2단계: Transformer로 Notion 블록 변환
    print("\n[Step 2] Dynalist 데이터를 Notion 블록으로 변환...")
    try:
        transformer = Transformer()
        notion_blocks = transformer.dynalist_to_notion_blocks(today_items)
        print(f"✓ {len(notion_blocks)}개 블록을 생성했습니다.")
        print(f"  첫 번째 블록 미리보기:")
        if notion_blocks:
            print(f"    {notion_blocks[0]}")
    except Exception as e:
        print(f"✗ 변환 에러: {e}")
        return False
    
    # 3단계: Notion에 블록 생성
    print("\n[Step 3] Notion에 페이지 및 블록 생성...")
    try:
        notion_client = NotionClient(
            config['notion']['api_key'],
            config['notion']['database_id']
        )
        response = notion_client.add_blocks_to_page(notion_blocks)
        print(f"✓ Notion에 페이지가 생성되었습니다.")
        print(f"  페이지 ID: {response.get('id')}")
        print(f"  제목: {response.get('properties', {}).get('title')}")
    except Exception as e:
        print(f"✗ Notion 생성 에러: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 2단계 테스트 완료!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
