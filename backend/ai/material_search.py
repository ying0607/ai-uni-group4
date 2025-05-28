#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原料查詢系統
從資料庫中載入以 'G' 開頭的配方資料，並透過 LLM 進行相關性查詢
"""

import os
import sys
import re
from typing import List, Optional
from dotenv import load_dotenv
from langchain_ollama.llms import OllamaLLM

# 將專案根目錄加入到 PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from database import operations as db_ops

# 載入環境變數
load_dotenv()

# --- 常數設定  ---
MODEL_NAME = os.getenv("MODEL_NAME")  # 預設模型
SERVER_URL = os.getenv("SERVER_URL")  # 預設 Ollama 伺服器

def _default_output_callback(msg):
    print(msg)

def _init_llm(output_callback=_default_output_callback):
    output_callback(f"正在初始化 Ollama LLM: Model='{MODEL_NAME}', Server='{SERVER_URL}'")
    if not MODEL_NAME or not SERVER_URL:
        output_callback("❌ 錯誤: MODEL_NAME 或 SERVER_URL 未在 .env 檔案中設定。無法初始化 LLM。")
        return None
    else:
        try:
            llm = OllamaLLM(
                model=MODEL_NAME,
                base_url=SERVER_URL,
                temperature=0.1,  # 降低溫度以獲得更一致的結果
                num_predict=500,  # 限制回應長度
            )
            # 測試連線
            test_response = llm.invoke("測試連線")
            output_callback("   ✅ Ollama LLM 初始化成功。")
            return llm
        except Exception as e:
            output_callback(f"❌ 初始化 Ollama LLM 時發生錯誤: {e}")
            return None

# 預設初始化一次供全域功能使用
# llm = _init_llm()

def load_g_recipes_from_database() -> Optional[List[str]]:
    """
    從資料庫載入以 'G' 開頭的配方名稱
    
    Returns:
        以 'G' 開頭的配方名稱列表，或 None（如果載入失敗）
    """
    print(f"\n2. 從資料庫載入以 'G' 開頭的配方資料...")
    
    try:
        # 使用 operations.py 的函數取得 G 類型的配方
        g_recipes_df = db_ops.get_recipes_by_type('G')
        
        if g_recipes_df.empty:
            print(f"   ℹ️ 在資料庫中未找到任何 'G' 類型的配方。")
            return []
        
        # 取得不重複的配方名稱列表
        recipe_names_list = g_recipes_df['recipe_name'].dropna().unique().tolist()
        print(f"   ✅ 找到 {len(recipe_names_list)} 個 'G' 類型的獨立配方名稱。")
        return recipe_names_list
        
    except Exception as e:
        print(f"❌ 從資料庫載入配方時發生錯誤: {e}")
        return None

def create_search_prompt(search_term: str, materials_batch: List[str]) -> str:
    """
    建立給 LLM 的搜尋提示詞
    
    Args:
        search_term: 搜尋詞彙
        materials_batch: 原料名稱批次
        
    Returns:
        格式化的提示詞
    """
    materials_text = "\n".join([f"- {material}" for material in materials_batch])
    
    prompt = f"""請分析以下配方清單，找出與「{search_term}」相關的配方。

配方清單：
{materials_text}

請只回傳相關的配方名稱，每個一行。如果沒有相關的配方，請回答「無」。

判斷相關性的標準：
1. 配方名稱中包含搜尋詞或其相關詞彙
2. 配方功能或用途與搜尋詞相關
3. 配方類別與搜尋詞相關

請直接列出相關配方名稱，不需要解釋原因。"""
    
    return prompt

def parse_llm_response(response: str, valid_materials: List[str]) -> List[str]:
    """
    解析 LLM 的回應，提取有效的配方名稱
    
    Args:
        response: LLM 的回應文字
        valid_materials: 有效的配方名稱列表
        
    Returns:
        經過驗證的相關配方名稱列表
    """
    if not response or response.strip().lower() in ['無', '沒有', 'none', 'no']:
        return []
    
    # 將有效配方轉換為集合以加快查找
    valid_set = set(valid_materials)
    related_materials = []
    
    # 按行分割回應
    lines = response.strip().split('\n')
    
    for line in lines:
        # 清理每一行（移除項目符號、編號等）
        cleaned_line = re.sub(r'^[-•*\d.]+\s*', '', line.strip())
        
        # 檢查是否為有效的配方名稱
        if cleaned_line and cleaned_line in valid_set:
            related_materials.append(cleaned_line)
    
    return related_materials

def get_related_materials_with_llm(search_term: str, g_recipe_names_list: List[str]) -> List[str]:
    """
    使用 LLM 從 G 類型的配方列表中找出與搜尋詞相關的項目
    
    Args:
        search_term: 搜尋詞彙
        g_recipe_names_list: G 類型的配方名稱列表
        
    Returns:
        相關配方名稱列表
    """
    llm = _init_llm()  # 確保 LLM 已初始化
    
    if not g_recipe_names_list:
        return ["沒有 'G' 類型的配方名稱可供查詢。"]
    
    if llm is None:
        return ["LLM 未初始化，無法進行查詢。"]
    
    print(f"\n3. 使用 LLM 從 'G' 類型的配方列表中尋找與 '{search_term}' 相關的項目...")
    
    try:
        # 如果配方列表太長，分批處理
        batch_size = 50  # 每批處理的配方數量
        all_related_materials = []
        
        for i in range(0, len(g_recipe_names_list), batch_size):
            batch = g_recipe_names_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(g_recipe_names_list) + batch_size - 1) // batch_size
            
            print(f"   處理批次 {batch_num}/{total_batches}...")
            
            # 建立提示詞
            prompt = create_search_prompt(search_term, batch)
            
            # 呼叫 LLM
            response = llm.invoke(prompt)
            
            # 解析回應
            batch_related = parse_llm_response(response, batch)
            all_related_materials.extend(batch_related)
            
            print(f"   批次 {batch_num} 找到 {len(batch_related)} 個相關項目")
        
        # 去除重複項目
        all_related_materials = list(set(all_related_materials))
        
        return all_related_materials
        
    except Exception as e:
        print(f"❌ LLM 查詢時發生錯誤: {e}")
        return [f"LLM 查詢失敗: {str(e)[:100]}"]

def get_recipe_details_by_name(recipe_name: str) -> Optional[dict]:
    """
    根據配方名稱取得配方詳細資訊
    
    Args:
        recipe_name: 配方名稱
        
    Returns:
        配方詳細資訊字典，或 None
    """
    try:
        # 使用 operations.py 的搜尋功能
        recipes_df = db_ops.search_recipes(recipe_name)
        
        if recipes_df.empty:
            return None
        
        # 取得第一個匹配的配方
        recipe_row = recipes_df.iloc[0]
        recipe_id = recipe_row['recipe_id']
        
        # 取得配方完整資訊（包含步驟）
        recipe_with_steps = db_ops.get_recipe_with_steps(recipe_id)
        
        return recipe_with_steps
        
    except Exception as e:
        print(f"❌ 取得配方詳細資訊時發生錯誤: {e}")
        return None

def display_recipe_details(recipe_name: str):
    """
    顯示配方的詳細資訊
    
    Args:
        recipe_name: 配方名稱
    """
    print(f"\n--- 配方 '{recipe_name}' 詳細資訊 ---")
    
    recipe_details = get_recipe_details_by_name(recipe_name)
    
    if not recipe_details:
        print(f"❌ 無法找到配方 '{recipe_name}' 的詳細資訊")
        return
    
    print(f"配方編號: {recipe_details['recipe_id']}")
    print(f"配方名稱: {recipe_details['recipe_name']}")
    print(f"配方類型: {recipe_details['recipe_type']}")
    print(f"版本: {recipe_details['version']}")
    if recipe_details.get('specification'):
        print(f"規格: {recipe_details['specification']}")
    if recipe_details.get('standard_hours'):
        print(f"標準工時: {recipe_details['standard_hours']}")
    
    if 'steps' in recipe_details and recipe_details['steps']:
        print(f"\n配方步驟 (共 {len(recipe_details['steps'])} 個步驟):")
        for i, step in enumerate(recipe_details['steps'], 1):
            material_name = step.get('material_name', '未知材料')
            quantity = step.get('quantity', 0)
            unit = step.get('unit', '')
            notes = step.get('notes', '')
            
            print(f"  步驟 {i}: {material_name} - {quantity} {unit}")
            if notes:
                print(f"         備註: {notes}")
    else:
        print("   此配方沒有步驟資訊")

def test_llm_connection() -> bool:
    """
    測試 LLM 連線是否正常
    
    Returns:
        True 如果連線正常，False 否則
    """
    llm = _init_llm()  # 確保 LLM 已初始化
    
    if llm is None:
        return False
    
    try:
        response = llm.invoke("回答「OK」")
        return "OK" in response.upper()
    except Exception as e:
        print(f"❌ 測試 LLM 連線失敗: {e}")
        return False

def test_database_connection() -> bool:
    """
    測試資料庫連線是否正常
    
    Returns:
        True 如果連線正常，False 否則
    """
    try:
        # 嘗試取得所有配方來測試連線
        recipes = db_ops.get_all_recipes()
        print(f"   ✅ 資料庫連線成功，共找到 {len(recipes)} 個配方")
        return True
    except Exception as e:
        print(f"   ❌ 資料庫連線失敗: {e}")
        return False

def main(search_name):
    # """主程式"""
    # print("=" * 60)
    # print("配方查詢系統 - LLM 版本 (使用資料庫)")
    # print("=" * 60)
    
    # # 1. 測試資料庫連線
    # print("1. 測試資料庫連線...")
    # if not test_database_connection():
    #     print("   請檢查資料庫設定和連線")
    #     return
    
    # # 2. 測試 LLM 連線
    # print("\n2. 測試 LLM 連線...")
    # if test_llm_connection():
    #     print("   ✅ LLM 連線測試成功")
    # else:
    #     print("   ❌ LLM 連線測試失敗，請檢查 Ollama 服務是否正在運行")
    #     print("   提示：請確認已執行 'ollama serve' 並下載所需模型")
    #     return
    
    # 3. 載入 G 類型配方資料
    print("\n" + "=" * 60)
    print("程式啟動：正在預先載入 'G' 類型配方資料，請稍候...")
    
    g_recipes_master_list = load_g_recipes_from_database()
    
    print("=" * 60)
    
    if g_recipes_master_list is None:  # 資料庫載入失敗
        print("因讀取資料庫失敗，無法啟動查詢迴圈。請檢查資料庫連線和設定。")
        return
    elif not g_recipes_master_list:  # 資料庫載入成功但沒有 G 類型的資料
        print("資料庫已連線，但未找到 'G' 類型的配方。無法進行後續查詢。")
        return
    else:
        print(f"\n✅ 'G' 類型配方資料載入完成，共找到 {len(g_recipes_master_list)} 筆獨立配方名稱。")
        print("✅ 系統已就緒，可以開始查詢。")
    
    user_search_term = search_name.strip()
    
    print(f"\n您輸入的查詢詞是: '{user_search_term}'")
        
    # 使用預先載入的 g_recipes_master_list 進行 LLM 查詢
    related_g_recipes = get_related_materials_with_llm(
        user_search_term, 
        g_recipes_master_list
    )
    
    # 顯示查詢結果
    print("\n--- 查詢結果 ---")
    if related_g_recipes:
        # 檢查是否為錯誤訊息
        is_error_message = (
            len(related_g_recipes) == 1 and
            isinstance(related_g_recipes[0], str) and
            any(keyword in related_g_recipes[0] for keyword in ["錯誤", "失敗", "超時", "連線"])
        )
        
        if is_error_message:
            print(f"❗ 查詢過程中發生問題: {related_g_recipes[0]}")
        elif not any(related_g_recipes):  # 處理空字串列表的情況
            print(f"✅ LLM 分析完成，但未在 'G' 類型的配方中找到與 '{user_search_term}' 明確相關的項目。")
        else:
            print(f"與 '{user_search_term}' 相關且類型為 'G' 的配方名稱有：")
            for i, name in enumerate(related_g_recipes, 1):
                print(f"{i:2d}. {name}")
            
            # # 詢問是否要查看詳細資訊
            # if len(related_g_recipes) <= 5:  # 只有在結果不太多時才提供詳細資訊選項
            #     try:
            #         show_details = input(f"\n是否要查看配方的詳細資訊？(y/n): ").strip().lower()
            #         if show_details in ['y', 'yes', '是', '要']:
            #             for recipe_name in related_g_recipes:
            #                 display_recipe_details(recipe_name)
            #                 print("-" * 40)
            #     except (KeyboardInterrupt, EOFError):
            #         print("\n跳過詳細資訊顯示")
    else:
        print(f"未能在 'G' 類型的配方中找到與 '{user_search_term}' 相關的項目。")
    
    return related_g_recipes

if __name__ == "__main__":
    main("咖啡")

