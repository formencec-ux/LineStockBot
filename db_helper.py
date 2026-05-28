import sqlite3
from datetime import datetime
import re

# 定義資料庫的檔案名稱
DB_NAME = "stock_assistant.db"

def init_db():
    """
    【任務 2 核心】初始化資料庫，建立用來累積歷史數據與對話記憶的資料表
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # A. 建立歷史價格表：每次查詢股價，數據就會累積在這裡
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT,
            stock_name TEXT,
            price REAL,
            query_time TIMESTAMP
        )
    ''')
    
    # B. 建立對話紀錄表：用來實作對話接力，記住上下文
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_msg TEXT,
            ai_reply TEXT,
            timestamp TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[DB] 成功！stock_assistant.db 資料庫與資料表已初始化完成。")

def record_price(stock_id, stock_name, price):
    """
    【數據累積】把當前抓到的最新股價，正式寫入資料庫保存
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_history (stock_id, stock_name, price, query_time) VALUES (?, ?, ?, ?)",
        (stock_id, stock_name, price, datetime.now())
    )
    conn.commit()
    conn.close()

def get_last_price(stock_id):
    """
    【數據對比】去資料庫撈出「上一次」查詢的價格，用來跟這一次做對比
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 排序並跳過最新的一筆(OFFSET 1)，撈出倒數第二筆（也就是真正的上一次查詢）
    cursor.execute(
        "SELECT price FROM price_history WHERE stock_id = ? ORDER BY query_time DESC LIMIT 1 OFFSET 1",
        (stock_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_chat_log(user_id, user_msg, ai_reply):
    """
    【對話記憶】儲存用戶與 AI 的歷史對話內容
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_id, user_msg, ai_reply, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, user_msg, ai_reply, datetime.now())
    )
    conn.commit()
    conn.close()

def get_user_last_stock(user_id):
    """
    【對話接力核心】查詢該使用者最近 5 次對話中，最後提及的 4 位數股票代號
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 撈出此用戶最近的對話訊息
    cursor.execute(
        "SELECT user_msg FROM chat_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    # 從最近的對話紀錄中，用正則表達式往回尋找最後出現的 4 位數代號
    for row in rows:
        msg = row[0]
        match = re.search(r'\d{4}', msg)
        if match:
            return match.group()  # 找到了就回傳代號（例如 3189）
    return None

# 如果你在電腦直接執行這隻檔案，它會幫你把資料庫建立好
if __name__ == "__main__":
    init_db()