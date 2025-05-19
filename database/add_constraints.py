import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 從 .env 檔案中讀取資料庫連線資訊
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
GROUP_PREFIX = os.getenv("GROUP_PREFIX", "group4_")  # 預設為 group4_

def add_constraints():
    """添加外鍵約束和觸發器"""
    try:
        # 建立資料庫連接
        connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string, pool_recycle=3600, pool_pre_ping=True)
        print("資料庫連接成功！")

        # 第一步：確保表格有正確的主鍵或唯一索引
        with engine.connect() as conn:
            # 禁用外鍵檢查
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # 檢查並添加主鍵到 materials 表
            print("確保 materials 表有正確的主鍵...")
            try:
                # 先查詢資料表的主鍵信息
                result = conn.execute(text(f"""
                SELECT COUNT(*) as pk_count 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = '{DB_NAME}' 
                  AND TABLE_NAME = '{GROUP_PREFIX}materials' 
                  AND CONSTRAINT_TYPE = 'PRIMARY KEY'
                """))
                row = result.fetchone()
                has_pk = row[0] > 0
                
                if not has_pk:
                    # 如果沒有主鍵，添加主鍵
                    conn.execute(text(f"""
                    ALTER TABLE {GROUP_PREFIX}materials 
                    ADD PRIMARY KEY (material_code)
                    """))
                    print("已為 materials 表添加主鍵")
                else:
                    print("materials 表已有主鍵，無需添加")
            except Exception as e:
                print(f"檢查/添加 materials 表主鍵時發生錯誤: {e}")
                
                # 嘗試添加唯一索引
                try:
                    conn.execute(text(f"""
                    ALTER TABLE {GROUP_PREFIX}materials 
                    ADD UNIQUE INDEX idx_material_code (material_code)
                    """))
                    print("已為 materials 表添加唯一索引")
                except Exception as e:
                    print(f"添加唯一索引時發生錯誤 (可能已存在): {e}")
            
            # 檢查並添加主鍵到 bom 表
            print("確保 bom 表有正確的主鍵...")
            try:
                # 先查詢資料表的主鍵信息
                result = conn.execute(text(f"""
                SELECT COUNT(*) as pk_count 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = '{DB_NAME}' 
                  AND TABLE_NAME = '{GROUP_PREFIX}bom' 
                  AND CONSTRAINT_TYPE = 'PRIMARY KEY'
                """))
                row = result.fetchone()
                has_pk = row[0] > 0
                
                if not has_pk:
                    # 如果沒有主鍵，添加主鍵
                    conn.execute(text(f"""
                    ALTER TABLE {GROUP_PREFIX}bom 
                    ADD PRIMARY KEY (recipe_id)
                    """))
                    print("已為 bom 表添加主鍵")
                else:
                    print("bom 表已有主鍵，無需添加")
            except Exception as e:
                print(f"檢查/添加 bom 表主鍵時發生錯誤: {e}")
                
                # 嘗試添加唯一索引
                try:
                    conn.execute(text(f"""
                    ALTER TABLE {GROUP_PREFIX}bom 
                    ADD UNIQUE INDEX idx_recipe_id (recipe_id)
                    """))
                    print("已為 bom 表添加唯一索引")
                except Exception as e:
                    print(f"添加唯一索引時發生錯誤 (可能已存在): {e}")
            
            # 確保變更已提交
            conn.commit()
        
        print("表格主鍵/索引檢查完成，連接將重新建立以避免超時問題")
        
        # 重新連接以避免超時問題
        with engine.connect() as conn:
            # 禁用外鍵檢查
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # 添加外鍵約束
            print("添加外鍵約束...")
            try:
                conn.execute(text(f"""
                ALTER TABLE {GROUP_PREFIX}recipe_step 
                ADD CONSTRAINT fk_step_bom 
                FOREIGN KEY (recipe_id) 
                REFERENCES {GROUP_PREFIX}bom (recipe_id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE
                """))
                print("已添加 recipe_id 外鍵約束")
            except Exception as e:
                print(f"添加 recipe_id 外鍵約束時發生錯誤 (可能已存在): {e}")
            
            try:
                conn.execute(text(f"""
                ALTER TABLE {GROUP_PREFIX}recipe_step 
                ADD CONSTRAINT fk_step_material 
                FOREIGN KEY (material_code) 
                REFERENCES {GROUP_PREFIX}materials (material_code) 
                ON DELETE RESTRICT 
                ON UPDATE CASCADE
                """))
                print("已添加 material_code 外鍵約束")
            except Exception as e:
                print(f"添加 material_code 外鍵約束時發生錯誤: {e}")
            
            # 確保變更已提交
            conn.commit()
        
        print("外鍵約束添加完成，連接將重新建立以避免超時問題")
        
        # 再次重新連接以避免超時問題
        with engine.connect() as conn:
            # 創建觸發器
            print("創建觸發器...")
            try:
                # 先移除可能存在的觸發器
                conn.execute(text(f"DROP TRIGGER IF EXISTS {GROUP_PREFIX}check_material_is_bom_recipe"))
                
                # 創建新觸發器
                conn.execute(text(f"""
                CREATE TRIGGER {GROUP_PREFIX}check_material_is_bom_recipe 
                BEFORE INSERT ON {GROUP_PREFIX}recipe_step
                FOR EACH ROW
                BEGIN
                  DECLARE material_exists INT DEFAULT 0;
                  
                  -- 檢查材料是否存在於 materials 表中
                  SELECT COUNT(*) INTO material_exists 
                  FROM {GROUP_PREFIX}materials 
                  WHERE material_code = NEW.material_code;
                  
                  -- 如果材料不存在但在 BOM 中存在，則拋出錯誤
                  IF material_exists = 0 THEN
                    -- 檢查是否為 BOM 中的配方
                    SELECT COUNT(*) INTO material_exists 
                    FROM {GROUP_PREFIX}bom 
                    WHERE recipe_id = NEW.material_code;
                    
                    IF material_exists = 0 THEN
                      SIGNAL SQLSTATE '45000' 
                      SET MESSAGE_TEXT = '錯誤：所指定的材料編號既不存在於 materials 表中，也不存在於 bom 表中';
                    END IF;
                  END IF;
                END
                """))
                print("已創建觸發器")
            except Exception as e:
                print(f"創建觸發器時發生錯誤: {e}")
            
            # 重新啟用外鍵檢查
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            
            # 確保變更已提交
            conn.commit()
        
        print("所有約束和觸發器添加完成！")

    except Exception as e:
        print(f"執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_constraints()