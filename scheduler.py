import time
import schedule
import pytz
from datetime import datetime
from worker import run_scan

def is_market_open():
    """
    미국 주식 시장이 현재 열려 있는지 확인합니다.
    (월~금, 뉴욕 시간 기준 09:30 ~ 16:00)
    """
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    
    # 주말(토=5, 일=6)인지 확인
    if now.weekday() >= 5:
        return False
        
    # 현재 시간 확인
    current_time = now.time()
    market_open = datetime.strptime("09:30", "%H:%M").time()
    market_close = datetime.strptime("16:00", "%H:%M").time()
    
    return market_open <= current_time <= market_close

def job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 스케줄러 실행 시도...")
    if is_market_open():
        print("미국 장이 열려있습니다. 스캔을 시작합니다.")
        try:
            run_scan()
        except Exception as e:
            print(f"스캔 중 에러 발생: {e}")
    else:
        print("미국 장이 닫혀있습니다. 스캔을 생략합니다.")

def main():
    print("스케줄러를 시작합니다. (30분 간격 실행 대기 중...)")
    
    # 시작하자마자 일단 한번 체크 (장중이면 실행)
    job()
    
    # 30분마다 작업 실행 예약
    schedule.every(30).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
