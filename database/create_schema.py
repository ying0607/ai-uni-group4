import os
import pymysql # type: ignore
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

def create_database_schema():
    """建立資料庫結構"""
    print("開始建立資料庫結構...")
    
    # 建立資料庫連接
    connection = pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASS,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # 建立資料庫（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            cursor.execute(f"USE `{DB_NAME}`")
            
            # 設定字符集
            cursor.execute("SET NAMES utf8mb4")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 建立 BOM 表格
            cursor.execute(f"""DROP TABLE IF EXISTS `{GROUP_PREFIX}bom`""")
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{GROUP_PREFIX}bom` (
              `recipe_id` varchar(50) NOT NULL COMMENT '產品編號',
              `recipe_name` varchar(100) NOT NULL COMMENT '產品名稱',
              `recipe_type` enum('G','F') NOT NULL COMMENT '配方類型',
              `version` varchar(20) NOT NULL COMMENT '版本別',
              `standard_hours` varchar(50) COMMENT '標準工時',
              `specification` varchar(255) COMMENT '規格',
              `notes` text COMMENT '單據備註',
              `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
              `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
              PRIMARY KEY (`recipe_id`),
              INDEX `idx_recipe_type` (`recipe_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方主檔'
            """)
            
            # 建立 MATERIALS 表格
            cursor.execute(f"""DROP TABLE IF EXISTS `{GROUP_PREFIX}materials`""")
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{GROUP_PREFIX}materials` (
              `material_id` int NOT NULL AUTO_INCREMENT COMMENT '原料唯一識別碼',
              `material_code` varchar(50) NOT NULL COMMENT '貨品編號',
              `material_name` varchar(100) NOT NULL COMMENT '貨品名稱',
              `material_type` enum('A','B') NOT NULL COMMENT '材料類型(A一般/B管制)',
              `specification` varchar(255) COMMENT '規格',
              `unit` varchar(20) COMMENT '單位',
              `unit_price_wo_tax` float COMMENT '單價未稅',
              `characteristic` text COMMENT '特性描述',
              `supplier_id` varchar(50) COMMENT '供應商號',
              `supplier_name` varchar(100) COMMENT '供應商',
              `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
              `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
              PRIMARY KEY (`material_id`),
              INDEX `idx_material_type` (`material_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='原料主檔'
            """)
            
            # 建立 RECIPE_STEP 表格
            cursor.execute(f"""DROP TABLE IF EXISTS `{GROUP_PREFIX}recipe_step`""")
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{GROUP_PREFIX}recipe_step` (
              `step_id` int NOT NULL COMMENT '步驟唯一識別碼',
              `recipe_id` varchar(50) NOT NULL COMMENT '所屬配方ID',
              `step_order` int NOT NULL COMMENT '步驟順序',
              `material_code` varchar(50) NOT NULL COMMENT '原料編號',
              `unit` varchar(20) COMMENT '單位',
              `quantity` float NOT NULL DEFAULT 0 COMMENT '原料用量',
              `product_base` float NOT NULL DEFAULT 1 COMMENT '產品基數',
              `notes` text COMMENT '附註',
              PRIMARY KEY (`step_id`),
              INDEX `idx_recipe_id` (`recipe_id`),
              INDEX `idx_material_code` (`material_code`),
              CONSTRAINT `fk_step_bom` FOREIGN KEY (`recipe_id`) REFERENCES `{GROUP_PREFIX}bom` (`recipe_id`) ON DELETE CASCADE ON UPDATE CASCADE,
              CONSTRAINT `fk_step_material` FOREIGN KEY (`material_code`) REFERENCES `{GROUP_PREFIX}materials` (`material_code`) ON DELETE RESTRICT ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方步驟明細'
            """)
            
            # 建立觸發器 - 檢查 BOM 參照
            cursor.execute(f"""
            DROP TRIGGER IF EXISTS `{GROUP_PREFIX}check_material_is_bom_recipe`
            """)
            
            cursor.execute(f"""
            CREATE TRIGGER `{GROUP_PREFIX}check_material_is_bom_recipe` BEFORE INSERT ON `{GROUP_PREFIX}recipe_step`
            FOR EACH ROW
            BEGIN
              DECLARE material_exists INT DEFAULT 0;
              
              -- 檢查材料是否存在於 materials 表中
              SELECT COUNT(*) INTO material_exists 
              FROM `{GROUP_PREFIX}materials` 
              WHERE `material_code` = NEW.material_code;
              
              -- 如果材料不存在但在 BOM 中存在，則拋出錯誤
              IF material_exists = 0 THEN
                -- 檢查是否為 BOM 中的配方
                SELECT COUNT(*) INTO material_exists 
                FROM `{GROUP_PREFIX}bom` 
                WHERE `recipe_id` = NEW.material_code;
                
                IF material_exists = 0 THEN
                  SIGNAL SQLSTATE '45000' 
                  SET MESSAGE_TEXT = '錯誤：所指定的材料編號既不存在於 materials 表中，也不存在於 bom 表中';
                END IF;
              END IF;
            END
            """)
            
            # 重新啟用外鍵檢查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            connection.commit()
            print("資料庫結構建立完成！")
    
    except Exception as e:
        print(f"建立資料庫結構時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connection.close()

if __name__ == "__main__":
    create_database_schema()