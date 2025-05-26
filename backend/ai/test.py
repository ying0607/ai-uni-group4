import sys
import os

# 將專案根目錄加入到 PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from database import operations as db_ops

def test_db_ops():
    print("測試 `db_ops` 匯入是否成功...")
    
    # 檢查 db_ops 是否有內容
    if not hasattr(db_ops, '__dict__'):
        print("❌ `db_ops` 匯入失敗，請檢查 `operations.py` 是否存在或有內容。")
        return
    
    # 列出 db_ops 中的所有屬性和函式
    print("`db_ops` 中的可用屬性和函式:")
    for attr in dir(db_ops):
        if not attr.startswith("__"):  # 過濾掉內建屬性
            print(f"- {attr}")
    
    # 測試呼叫某個函式（假設 operations.py 中有 `get_material_by_id` 函式）
    if hasattr(db_ops, 'get_material_by_id'):
        try:
            result = db_ops.get_material_by_id("G12345")  # 測試用的原料 ID
            print(f"✅ 呼叫 `get_material_by_id` 成功，回傳結果: {result}")
        except Exception as e:
            print(f"❌ 呼叫 `get_material_by_id` 時發生錯誤: {e}")
    else:
        print("⚠️ `db_ops` 中沒有找到 `get_material_by_id` 函式，請確認 `operations.py` 的內容。")

# 執行測試
test_db_ops()