import os
import pymysql # type: ignore
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 從 .env 檔案中讀取資料庫連線資訊
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
GROUP_PREFIX = os.getenv("GROUP_PREFIX", "group1_")

# 建立資料庫連接
connection = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 查看資料表結構
def check_table_structure():
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # 獲取配方步驟表的結構
            cursor.execute(f"DESCRIBE {GROUP_PREFIX}recipe_step")
            columns = cursor.fetchall()
            print("配方步驟表結構:")
            for col in columns:
                print(f"- {col['Field']} ({col['Type']})")
            
            # 查看表中是否有數據
            cursor.execute(f"SELECT COUNT(*) as total FROM {GROUP_PREFIX}recipe_step")
            count = cursor.fetchone()
            print(f"配方步驟表中總記錄數: {count['total']}")
            
            # 列出所有表，確認命名
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("資料庫中的表格:")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"- {table_name}")
    finally:
        connection.close()

check_table_structure()