import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 從 .env 檔案中讀取資料庫連線資訊
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
GROUP_PREFIX = os.getenv("GROUP_PREFIX", "group4_")  # 預設為 group4_

# 建立資料庫連接
def get_db_connection():
    """建立並返回資料庫連接"""
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    return engine

def get_all_materials():
    """取得所有材料"""
    engine = get_db_connection()
    query = text(f"SELECT * FROM {GROUP_PREFIX}materials ORDER BY material_type, material_name")
    
    # 使用 pandas 讀取資料
    df = pd.read_sql(query, engine)
    return df

def get_material_by_code(material_code):
    """根據編號取得特定材料"""
    engine = get_db_connection()
    query = text(f"SELECT * FROM {GROUP_PREFIX}materials WHERE material_code = :code")
    
    # 使用 pandas 讀取資料
    df = pd.read_sql(query, engine, params={"code": material_code})
    
    # 如果找到資料，返回第一筆，否則返回 None
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def get_all_recipes():
    """取得所有配方"""
    engine = get_db_connection()
    query = text(f"SELECT * FROM {GROUP_PREFIX}bom ORDER BY recipe_type, recipe_name")
    
    df = pd.read_sql(query, engine)
    return df

def get_recipe_by_id(recipe_id):
    """根據編號取得特定配方"""
    engine = get_db_connection()
    query = text(f"SELECT * FROM {GROUP_PREFIX}bom WHERE recipe_id = :id")
    
    df = pd.read_sql(query, engine, params={"id": recipe_id})
    
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def get_recipe_steps(recipe_id):
    """取得配方的所有步驟"""
    engine = get_db_connection()
    
    # 修改查詢，為相同名稱的欄位添加別名，避免欄位名稱衝突
    query = text(f"""
        SELECT s.step_id, s.recipe_id, s.step_order, s.material_code, 
               s.unit, s.quantity, s.product_base, s.notes,
               m.material_name, m.material_type, m.specification as material_spec
        FROM {GROUP_PREFIX}recipe_step s
        LEFT JOIN {GROUP_PREFIX}materials m ON s.material_code = m.material_code
        WHERE s.recipe_id = :recipe_id
        ORDER BY s.step_order
    """)
    
    df = pd.read_sql(query, engine, params={"recipe_id": recipe_id})
    return df

def search_materials(keyword):
    """搜尋材料 (依名稱或編號)"""
    engine = get_db_connection()
    query = text(f"""
        SELECT * FROM {GROUP_PREFIX}materials 
        WHERE material_name LIKE :keyword OR material_code LIKE :keyword
        ORDER BY material_type, material_name
    """)
    
    df = pd.read_sql(query, engine, params={"keyword": f'%{keyword}%'})
    return df

def search_recipes(keyword):
    """搜尋配方 (依名稱或編號)"""
    engine = get_db_connection()
    query = text(f"""
        SELECT * FROM {GROUP_PREFIX}bom 
        WHERE recipe_name LIKE :keyword OR recipe_id LIKE :keyword
        ORDER BY recipe_type, recipe_name
    """)
    
    df = pd.read_sql(query, engine, params={"keyword": f'%{keyword}%'})
    return df

def get_recipe_with_steps(recipe_id):
    """取得配方及其所有步驟的完整資訊"""
    recipe = get_recipe_by_id(recipe_id)
    
    if recipe:
        # 取得配方步驟
        steps = get_recipe_steps(recipe_id)
        
        # 將步驟轉換為 Python 字典列表
        steps_list = steps.to_dict('records')
        
        # 將步驟加入配方字典
        recipe['steps'] = steps_list
        
    return recipe

def get_bom_tree(recipe_id, level=0, max_level=10):
    """取得配方的完整 BOM 樹狀結構 (包括子配方)"""
    if level >= max_level:  # 防止無限遞迴
        return None
    
    # 取得配方基本資訊
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return None
    
    # 取得配方步驟
    steps = get_recipe_steps(recipe_id)
    steps_list = []
    
    # 遍歷每個步驟
    for _, step in steps.iterrows():
        step_dict = step.to_dict()
        
        # 檢查材料是否為半成品 (存在於 BOM 表中)
        sub_recipe = get_recipe_by_id(step['material_code'])
        
        if sub_recipe:
            # 如果是半成品，遞迴取得其 BOM 結構
            step_dict['sub_recipe'] = get_bom_tree(step['material_code'], level + 1, max_level)
        
        steps_list.append(step_dict)
    
    # 將步驟加入配方字典
    recipe['steps'] = steps_list
    
    return recipe

def get_recipes_by_type(recipe_type):
    """根據類型取得配方列表 (G 或 F)"""
    engine = get_db_connection()
    query = text(f"""
        SELECT * FROM {GROUP_PREFIX}bom 
        WHERE recipe_type = :type
        ORDER BY recipe_name
    """)
    
    df = pd.read_sql(query, engine, params={"type": recipe_type})
    return df

def get_materials_by_type(material_type):
    """根據類型取得材料列表 (A 或 B)"""
    engine = get_db_connection()
    query = text(f"""
        SELECT * FROM {GROUP_PREFIX}materials 
        WHERE material_type = :type
        ORDER BY material_name
    """)
    
    df = pd.read_sql(query, engine, params={"type": material_type})
    return df

def get_recipe_material_usage(material_code):
    """取得特定材料被使用的所有配方"""
    engine = get_db_connection()
    query = text(f"""
        SELECT r.*, b.recipe_name, b.recipe_type, b.version, 
               r.quantity, r.product_base, r.unit
        FROM {GROUP_PREFIX}recipe_step r
        JOIN {GROUP_PREFIX}bom b ON r.recipe_id = b.recipe_id
        WHERE r.material_code = :material_code
        ORDER BY b.recipe_type, b.recipe_name
    """)
    
    df = pd.read_sql(query, engine, params={"material_code": material_code})
    return df

def get_recipes_with_filtered_materials(material_type=None, supplier_id=None):
    """取得使用特定類型材料或特定供應商材料的配方"""
    engine = get_db_connection()
    
    conditions = []
    params = {}
    
    if material_type:
        conditions.append("m.material_type = :material_type")
        params["material_type"] = material_type
    
    if supplier_id:
        conditions.append("m.supplier_id = :supplier_id")
        params["supplier_id"] = supplier_id
    
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    query = text(f"""
        SELECT DISTINCT b.*
        FROM {GROUP_PREFIX}bom b
        JOIN {GROUP_PREFIX}recipe_step s ON b.recipe_id = s.recipe_id
        JOIN {GROUP_PREFIX}materials m ON s.material_code = m.material_code
        {where_clause}
        ORDER BY b.recipe_type, b.recipe_name
    """)
    
    df = pd.read_sql(query, engine, params=params)
    return df
def get_recipe_details_by_name(recipe_name: str):
    """根據配方名稱取得配方詳細資訊"""
    try:
        recipes_df = search_recipes(recipe_name)
        
        if recipes_df.empty:
            return None
        
        # 取得第一個匹配的配方 ID
        recipe_row = recipes_df.iloc[0]
        recipe_id = recipe_row['recipe_id']
        
        # 取得完整配方資訊（包含步驟）
        recipe_with_steps = get_recipe_with_steps(recipe_id)
        
        return recipe_with_steps
        
    except Exception as e:
        print(f"❌ 取得配方詳細資訊時發生錯誤: {e}")
        return None

# 使用範例
if __name__ == "__main__":
    # 取得所有材料
    print("== 取得所有材料 ==")
    materials = get_all_materials()
    print(f"找到 {len(materials)} 筆材料資料")
    print(materials.head())
    
    # 搜尋特定材料
    print("\n== 搜尋含 '巧克力' 的材料 ==")
    choco_materials = search_materials("巧克力")
    print(f"找到 {len(choco_materials)} 筆相關材料")
    print(choco_materials)
    
    # 取得所有配方
    print("\n== 取得所有配方 ==")
    recipes = get_all_recipes()
    print(f"找到 {len(recipes)} 筆配方資料")
    print(recipes.head())
    
    # 如果有配方資料，取得第一個配方的詳細資訊
    if not recipes.empty:
        first_recipe_id = recipes.iloc[0]['recipe_id']
        print(f"\n== 取得配方 {first_recipe_id} 的詳細資訊 ==")
        recipe_detail = get_recipe_with_steps(first_recipe_id)
        
        print(f"配方名稱: {recipe_detail['recipe_name']}")
        print(f"配方類型: {recipe_detail['recipe_type']}")
        print(f"配方版本: {recipe_detail['version']}")
        print(f"步驟數量: {len(recipe_detail['steps'])}")
        
        print("\n配方步驟:")
        for i, step in enumerate(recipe_detail['steps']):
            print(f"  步驟 {i+1}: 使用 {step['material_name']} {step['quantity']} {step['unit']}, 注意事項: {step.get('precaution')}")