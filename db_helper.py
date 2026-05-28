import sqlite3
from datetime import datetime

# 定義資料庫的檔案名稱
DB_NAME = "stock_assistant.db"

def init_db():
    """
    【任務 2 核心】初始化資料庫，建立用來累積歷史數據的資料表
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 建立歷史價格表：每次你查股票，股價就會被存到這裡累積起來
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT,
            stock_name TEXT,
            price REAL,
            query_time TIMESTAMP
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

# 如果你在電腦直接執行這隻檔案，它會幫你把資料庫建立好
if __name__ == "__main__":
    init_db()