import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

# 從 .env 檔案中讀取資料庫連線資訊
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
GROUP_PREFIX = os.getenv("GROUP_PREFIX")

# 建立資料庫連接
connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)
print("資料庫連接成功！")

try:
    # 1. 匯入材料資料 (整合 A 類和 B 類)
    print("匯入 A 類材料資料...")
    df_material_a = pd.read_csv('seeds/material_a.csv')
    df_material_a = df_material_a.rename(columns={
        '貨品編號': 'material_code',
        '貨品名稱': 'material_name',
        '規格': 'specification',
        '單位': 'unit',
        '單價未稅': 'unit_price_wo_tax',
        '特性描述': 'characteristic',
        '供應商號': 'supplier_id',
        '供應商': 'supplier_name'
    })
    
    # 添加材料類型
    df_material_a['material_type'] = 'A'
    
    print("匯入 B 類材料資料...")
    df_material_b = pd.read_csv('seeds/material_b.csv')
    df_material_b = df_material_b.rename(columns={
        '貨品編號': 'material_code',
        '貨品名稱': 'material_name',
        '規格': 'specification',
        '單位': 'unit',
        '單價未稅': 'unit_price_wo_tax',
        '特性描述': 'characteristic',
        '供應商號': 'supplier_id',
        '供應商': 'supplier_name'
    })
    
    # 添加材料類型
    df_material_b['material_type'] = 'B'
    
    # 合併 A 類和 B 類材料到同一個表
    df_materials = pd.concat([df_material_a, df_material_b])
    
    # 寫入 materials 表
    df_materials.to_sql(f'{GROUP_PREFIX}materials', con=engine, if_exists='append', index=False)
    print(f"成功寫入 {len(df_materials)} 筆材料資料")

    # 2. 匯入配方資料 (BOM)
    print("匯入配方資料...")
    df_g_bom = pd.read_csv('seeds/g_bom.csv')
    df_g_bom = df_g_bom.rename(columns={
        '產品編號': 'recipe_id',
        '產品名稱': 'recipe_name',
        '版本別': 'version',
        '標準工時': 'standard_hours',
        '規格': 'specification',
        '單據備註': 'notes'
    })
    
    # 過濾掉多餘的欄位
    df_g_bom = df_g_bom[[
        'recipe_id', 'recipe_name', 'version', 'standard_hours','specification','notes'
    ]]
    
    # 添加配方類型
    df_g_bom['recipe_type'] = 'G'
    
    # 讀取 F 類配方數據 (如果有)
    df_f_bom = pd.read_csv('seeds/f_bom.csv')
    df_f_bom = df_f_bom.rename(columns={
        '產品編號': 'recipe_id',
        '產品名稱': 'recipe_name',
        '版本別': 'version',
        '標準工時': 'standard_hours',
        '規格': 'specification',
        '單據備註': 'notes'
    })
    
    # 過濾掉多餘的欄位
    df_f_bom = df_f_bom[[
        'recipe_id', 'recipe_name', 'version', 'standard_hours','specification','notes'
    ]]
    
    # 添加配方類型
    df_f_bom['recipe_type'] = 'F'
    
    # 合併 G 類和 F 類配方到同一個表
    df_bom = pd.concat([df_g_bom, df_f_bom])
    
    # 寫入 BOM 表
    df_bom.to_sql(f'{GROUP_PREFIX}bom', con=engine, if_exists='append', index=False)
    print(f"成功寫入 {len(df_bom)} 筆配方資料")

    # 3. 匯入配方步驟
    print("匯入配方步驟資料...")
    df_recipe_step_f = pd.read_csv('seeds/recipe_step_f.csv')
    df_recipe_step_f = df_recipe_step_f.rename(columns={
        '產品編號': 'recipe_id',
        '序號(PK)': 'step_id',
        '步驟': 'step_order',
        '原料編號': 'material_code',
        '原料名稱': 'material_name',
        '單位': 'unit',
        '原料用量': 'quantity',
        '產品基數': 'product_base',
        '附註': 'notes'
    })
    df_recipe_step_f = df_recipe_step_f[[
        'recipe_id', 'step_id', 'step_order', 'material_code', 'material_name', 'unit',
        'quantity', 'product_base', 'notes'
    ]]
    
    df_recipe_step_g = pd.read_csv('seeds/recipe_step_g.csv')
    df_recipe_step_g = df_recipe_step_g.rename(columns={
        '產品編號': 'recipe_id',
        '序號(PK)': 'step_id',
        '步驟': 'step_order',
        '原料編號': 'material_code',
        '原料名稱': 'material_name',
        '單位': 'unit',
        '原料用量': 'quantity',
        '產品基數': 'product_base',
        '附註': 'notes'
    })
    df_recipe_step_g = df_recipe_step_g[[
        'recipe_id', 'step_id', 'step_order', 'material_code', 'material_name', 'unit',
        'quantity', 'product_base', 'notes'
    ]]
    
    # 合併 F 類和 G 類配方步驟到同一個表
    df_recipe_step = pd.concat([df_recipe_step_f, df_recipe_step_g])
    
    # 將步驟順序轉換為整數
    df_recipe_step['step_order'] = df_recipe_step['step_order'].astype(int)
    
    # 寫入 recipe_step 表
    df_recipe_step.to_sql(f'{GROUP_PREFIX}recipe_step', con=engine, if_exists='append', index=False)
    print(f"成功寫入 {len(df_recipe_step)} 筆配方步驟資料")

    print("所有資料匯入完成！")

except Exception as e:
    print(f"匯入資料時發生錯誤: {e}")
    import traceback
    traceback.print_exc()