import argparse
import schedule
import time
import logging
from datetime import datetime
from dynalist_client import DynalistClient
from notion_sync_client import NotionClient
from transformer import Transformer
import yaml

# 설정 로드
with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 로깅 설정
logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def sync_daily_notes(target_date=None):
    try:
        # Dynalist 클라이언트 초기화
        dynalist = DynalistClient(config['dynalist']['api_key'], config['dynalist']['document_id'])
        
        # 지정된 날짜의 기록 가져오기 (기본: 오늘)
        if target_date is None:
            target_date = datetime.now().date()
        else:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        today_items, all_nodes = dynalist.get_items_by_date(target_date)
        logging.info(f"Found {len(today_items)} today items with memos")
        
        # Transformer 초기화
        transformer = Transformer()
        
        # Notion 데이터베이스 레코드로 변환
        notion_records = transformer.dynalist_to_notion_records(today_items, all_nodes)
        logging.info(f"Transformed to {len(notion_records)} Notion records")
        
        # Notion 클라이언트 초기화
        notion = NotionClient(config['notion']['api_key'], config['notion']['database_id'])
        
        # Notion에 데이터베이스 페이지로 추가
        notion.add_pages_to_database(notion_records)
        
        logging.info("Daily notes synced successfully.")
    except Exception as e:
        logging.error(f"Error syncing daily notes: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DynoLink daily sync runner')
    parser.add_argument('--once', action='store_true', help='Run sync immediately once instead of waiting for scheduled time')
    parser.add_argument('--date', type=str, help='Specify date to sync (YYYY-MM-DD format, default: today)')
    args = parser.parse_args()

    if args.once:
        logging.info("Running one-time sync...")
        sync_daily_notes(args.date)
    else:
        # 스케줄 설정: 매일 자정 실행
        schedule.every().day.at(config['schedule']['time']).do(sync_daily_notes)
        
        logging.info("Scheduler started. Waiting for midnight...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크