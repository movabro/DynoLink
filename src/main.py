import argparse
import schedule
import time
import logging
from datetime import datetime, timedelta
from dynalist_client import DynalistClient
from notion_sync_client import NotionMultiClient
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
        # Dynalist 클라이언트 초기화 (2개 document_id 지원)
        document_ids = config['dynalist'].get('document_ids') or [config['dynalist']['document_id']]
        dynalist = DynalistClient(config['dynalist']['api_key'], document_ids)
        
        # 지정된 날짜의 기록 가져오기 (기본: 오늘)
        if target_date is None:
            target_date = datetime.now().date()
        else:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        today_items, all_nodes, doc_type_map = dynalist.get_items_by_date(target_date)
        logging.info(f"Found {len(today_items)} today items from {len(document_ids)} documents")
        
        # Transformer 초기화 및 변환
        transformer = Transformer()
        notion_records = transformer.dynalist_to_notion_records(today_items, all_nodes, doc_type_map)
        logging.info(f"Transformed to {len(notion_records)} Notion records")
        
        # 다중 Notion 클라이언트 초기화 및 동기화
        if 'databases' in config['notion']:
            notion = NotionMultiClient(config['notion']['api_key'], config['notion']['databases'])
            results = notion.add_pages_to_all_databases(notion_records)
            
            # 결과 로깅
            for purpose, result in results.items():
                logging.info(f"Database [{purpose}]: {result['success']} added, {result['failed']} failed")
                if result['records']:
                    logging.info(f"  Records: {', '.join(result['records'][:5])}{'...' if len(result['records']) > 5 else ''}")
            logging.info("Daily notes synced to all databases successfully.")
        else:
            logging.error("Database configuration not found in settings.yaml")
            
    except Exception as e:
        logging.error(f"Error syncing daily notes: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DynoLink daily sync runner')
    parser.add_argument('--once', action='store_true', help='Run sync immediately once instead of waiting for scheduled time')
    parser.add_argument('--date', type=str, help='Specify date to sync (YYYY-MM-DD format, default: today)')
    parser.add_argument('--date-range', type=str, help='Specify date range to sync (YYYY-MM-DD:YYYY-MM-DD format, e.g., 2026-04-01:2026-04-07)')
    parser.add_argument('--last-days', type=int, help='Sync last N days (e.g., --last-days 7 for last 7 days)')
    args = parser.parse_args()

    if args.once:
        logging.info("Running one-time sync...")
        if args.date_range:
            # 날짜 범위 처리
            try:
                start_date_str, end_date_str = args.date_range.split(':')
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                current = start_date
                total_synced = 0
                while current <= end_date:
                    logging.info(f"Syncing {current.isoformat()}...")
                    sync_daily_notes(current.isoformat())
                    current += timedelta(days=1)
                    total_synced += 1
                
                logging.info(f"Finished syncing {total_synced} days")
            except Exception as e:
                logging.error(f"Error processing date range: {str(e)}")
        elif args.last_days:
            # 최근 N일 처리
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=args.last_days - 1)
            
            current = start_date
            total_synced = 0
            while current <= end_date:
                logging.info(f"Syncing {current.isoformat()}...")
                sync_daily_notes(current.isoformat())
                current += timedelta(days=1)
                total_synced += 1
            
            logging.info(f"Finished syncing {total_synced} days")
        else:
            sync_daily_notes(args.date)
    else:
        # 스케줄 설정: 매일 자정 실행
        schedule.every().day.at(config['schedule']['time']).do(sync_daily_notes)
        
        logging.info("Scheduler started. Waiting for midnight...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크