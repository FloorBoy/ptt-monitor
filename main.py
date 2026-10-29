import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ==================== 個人設定區 ====================
NTFY_TOPIC = "ptt"  # 請改成您在 ntfy App 設定的主題名稱 (例如: my-ticket-9527)
KEYWORDS = ["告五人", "周杰倫", "五月天", "張惠妹", "原價", "售"]  # 想監控的關鍵字
CHECK_INTERVAL = 3  # 掃描間隔秒數 (建議 3 秒避免被 PTT 封鎖 IP)
# ===================================================

# 紀錄已發送過通知的文章 URL，避免重複發送
notified_urls = set()

def get_today_ptt_date():
    """取得今日 PTT 日期格式 (例如: 10/30)"""
    now = datetime.now()
    return f"{now.month}/{now.day:02d}"

def send_ntfy_push(title, web_url, keyword):
    """發送 ntfy 推播"""
    try:
        push_url = f"https://ntfy.sh/{NTFY_TOPIC}"
        headers = {
            "Title": f"🎫 搶票命中: [{keyword}]".encode('utf-8'),
            "Click": web_url,
            "Tags": "ticket,warning"
        }
        response = requests.post(push_url, data=title.encode('utf-8'), headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 推播成功: {title}")
        else:
            print(f"推播失敗，狀態碼: {response.status_code}")
    except Exception as e:
        print(f"發送推播發生錯誤: {e}")

def check_ptt_drama_ticket():
    """抓取 PTT drama-ticket 板最新文章"""
    target_url = "https://www.ptt.cc/bbs/Drama-Ticket/index.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        res = requests.get(target_url, headers=headers, cookies={'over18': '1'}, timeout=5)
        if res.status_code != 200:
            print(f"無法抓取 PTT 頁面 (Status: {res.status_code})")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        rents = soup.find_all('div', class_='r-ent')
        today_str = get_today_ptt_date()

        for rent in rents:
            title_el = rent.find('div', class_='title')
            date_el = rent.find('div', class_='date')

            if not title_el or not title_el.find('a') or not date_el:
                continue

            title = title_el.find('a').text.strip()
            date = date_el.text.strip()
            web_href = "https://www.ptt.cc" + title_el.find('a')['href']

            # 只過濾「今天發布」且「尚未通知過」的文章
            if date == today_str and web_href not in notified_urls:
                # 檢查是否命中關鍵字
                for kw in KEYWORDS:
                    if kw.lower() in title.lower():
                        notified_urls.add(web_href)
                        print(f"🎯 命中目標: {title}")
                        send_ntfy_push(title, web_href, kw)
                        break

    except Exception as e:
        print(f"抓取 PTT 發生錯誤: {e}")

if __name__ == "__main__":
    print(f"🚀 PTT 搶票雲端監控已啟動！(ntfy 主題: {NTFY_TOPIC})")
    
    # 啟動時先發送一次成功連線通知
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}", 
        data="✅ PTT 雲端監控機器人已成功在伺服器上線運行！".encode('utf-8')
    )

    while True:
        check_ptt_drama_ticket()
        time.sleep(CHECK_INTERVAL)
