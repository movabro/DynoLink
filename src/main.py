import schedule
import time
import logging
from dynalist_client import DynalistClient
from notion_client import NotionClient
from transformer import Transformer
import yaml

# 설정 로드
with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 로깅 설정
logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def sync_daily_notes():
    try:
        # Dynalist 클라이언트 초기화
        dynalist = DynalistClient(config['dynalist']['api_key'], config['dynalist']['document_id'])
        
        # 오늘의 기록 가져오기
        today_items = dynalist.get_today_items()
        
        # Transformer 초기화
        transformer = Transformer()
        
        # Notion 블록으로 변환
        notion_blocks = transformer.dynalist_to_notion_blocks(today_items)
        
        # Notion 클라이언트 초기화
        notion = NotionClient(config['notion']['api_key'], config['notion']['database_id'])
        
        # Notion에 추가
        notion.add_blocks_to_page(notion_blocks)
        
        logging.info("Daily notes synced successfully.")
    except Exception as e:
        logging.error(f"Error syncing daily notes: {str(e)}")

if __name__ == "__main__":
    # 스케줄 설정: 매일 자정 실행
    schedule.every().day.at(config['schedule']['time']).do(sync_daily_notes)
    
    logging.info("Scheduler started. Waiting for midnight...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크