#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原料查詢系統
從 CSV 檔案中載入以 'G' 開頭的原料資料，並透過外部 API 進行相關性查詢
"""

import pandas as pd
import os
import re
import requests
import json
from typing import List, Optional
from dotenv import load_dotenv
from langchain_ollama.llms import OllamaLLM  # type: ignore

# 載入環境變數
load_dotenv()

# --- Configuration Constants ---
CSV_FILENAME = "GBOM_product_data_name_20250522.csv"
COLUMN_MATERIAL_ID = "產品編號"        # Material ID column
COLUMN_MATERIAL_NAME = "產品名稱"      # Material Name column

# --- 常數設定  ---
MODEL_NAME = os.getenv("MODEL_NAME")
SERVER_URL = os.getenv("SERVER_URL")

# --- LLM 初始化  ---
print(f"正在初始化 Ollama LLM: Model='{MODEL_NAME}', Server='{SERVER_URL}'")
if not MODEL_NAME or not SERVER_URL:
    print("❌ 錯誤: MODEL_NAME 或 SERVER_URL 未在 .env 檔案中設定。無法初始化 LLM。")
    llm = None  # 確保 llm 為 None，以便後續檢查
else:
    try:
        llm = OllamaLLM(
            model=MODEL_NAME,
            base_url=SERVER_URL
        )
        print("   ✅ Ollama LLM 初始化成功。")
    except Exception as e:
        print(f"❌ 初始化 Ollama LLM 時發生錯誤: {e}")
        llm = None  # 初始化失敗，設為 None

def load_and_filter_g_materials(csv_filepath: str, id_column: str, name_column: str) -> Optional[List[str]]:
    """
    載入 CSV 檔案，篩選出以 'G' 開頭的原料編號對應的原料名稱
    
    Args:
        csv_filepath: CSV 檔案路徑
        id_column: 原料編號欄位名稱
        name_column: 原料名稱欄位名稱
        
    Returns:
        以 'G' 開頭的原料名稱列表，或 None（如果載入失敗）
    """
    print(f"\n2. 讀取並篩選 CSV 檔案: {csv_filepath}")
    
    try:
        df = pd.read_csv(csv_filepath)
        print(f"   ✅ CSV 讀取成功，共 {len(df)} 行。")
    except FileNotFoundError:
        print(f"❌ 錯誤: CSV 檔案 '{csv_filepath}' 找不到。")
        return None
    except Exception as e:
        print(f"❌ 讀取 CSV 時發生錯誤: {e}")
        return None

    # 檢查必要欄位是否存在
    if id_column not in df.columns:
        print(f"❌ 錯誤: CSV 中找不到「原料編號」欄位 '{id_column}'。可用欄位: {df.columns.tolist()}")
        return None
    if name_column not in df.columns:
        print(f"❌ 錯誤: CSV 中找不到「原料名稱」欄位 '{name_column}'。可用欄位: {df.columns.tolist()}")
        return None

    # 確保原料編號欄位為字串型態以便篩選
    df[id_column] = df[id_column].astype(str)

    # 篩選以 'G' 開頭的原料編號（不區分大小寫）
    g_materials_df = df[df[id_column].str.upper().str.startswith('G')]

    if g_materials_df.empty:
        print(f"   ℹ️ 在 '{id_column}' 欄位中未找到任何以 'G' 開頭的原料編號。")
        return []

    # 取得不重複的原料名稱列表
    material_names_list = g_materials_df[name_column].dropna().unique().tolist()
    print(f"   ✅ 找到 {len(material_names_list)} 個以 'G' 開頭的獨立原料名稱。")
    return material_names_list

def get_related_materials_with_api(search_term: str, g_material_names_list: List[str], api_client: MaterialSearchClient) -> List[str]:
    """
    使用外部 API 從 G 開頭的原料列表中找出與搜尋詞相關的項目
    
    Args:
        search_term: 搜尋詞彙
        g_material_names_list: G 開頭的原料名稱列表
        api_client: API 客戶端實例
        
    Returns:
        相關原料名稱列表
    """
    if not g_material_names_list:
        return ["沒有以 'G' 開頭的原料名稱可供查詢。"]

    print(f"\n3. 使用外部 API 從 'G' 開頭的原料列表中尋找與 '{search_term}' 相關的項目...")
    
    try:
        related_materials = api_client.search_materials(search_term, g_material_names_list)
        
        if not related_materials:
            return []
        
        # 驗證 API 回傳的結果是否都在原始列表中
        original_g_names_set = set(g_material_names_list)
        validated_related_names = []
        
        for name in related_materials:
            if isinstance(name, str) and name.strip():
                clean_name = name.strip()
                if clean_name in original_g_names_set:
                    validated_related_names.append(clean_name)
                else:
                    # API 回傳的項目不在原始列表中，可能是 API 的變化或錯誤
                    print(f"   ⚠️ API 回傳項目 '{clean_name}' 不在原始 G 開頭列表中")
        
        if not validated_related_names and related_materials:
            print("   ⚠️ API 回應的項目經過驗證後，未發現有效對應原始 G 開頭列表中的項目。")
        
        return validated_related_names
        
    except Exception as e:
        print(f"❌ API 查詢時發生錯誤: {e}")
        return [f"API 查詢失敗: {str(e)[:100]}"]

def main():
    """主程式"""
    print("=" * 50)
    print("原料查詢系統 - 外部 API 版本")
    print("=" * 50)
    
    # 1. 初始化 API 客戶端
    print("1. 初始化外部 API 連線...")
    
    # 從環境變數或直接設定 API 相關資訊
    api_url = os.environ.get('MATERIAL_API_URL', API_BASE_URL)
    api_key = os.environ.get('MATERIAL_API_KEY', API_KEY)
    
    api_client = MaterialSearchClient(api_url, api_key)
    
    # 簡單的連線測試（可選）
    try:
        # 您可以實作一個 health check 端點來測試連線
        test_response = api_client.session.get(f"{api_url}/health", timeout=5)
        if test_response.status_code == 200:
            print(f"   ✅ API Server 連線成功: {api_url}")
        else:
            print(f"   ⚠️ API Server 回應異常: {test_response.status_code}")
    except:
        print(f"   ⚠️ 無法測試 API Server 連線，將繼續執行程式")
    
    # 2. 載入並篩選 G 開頭原料資料
    print("\n" + "=" * 50)
    print("程式啟動：正在預先載入及篩選 'G' 開頭原料資料，請稍候...")
    
    g_materials_master_list = load_and_filter_g_materials(
        CSV_FILENAME,
        COLUMN_MATERIAL_ID,
        COLUMN_MATERIAL_NAME
    )
    
    print("=" * 50)
    
    if g_materials_master_list is None:  # CSV 載入失敗
        print("因讀取或解析 CSV 檔案失敗，無法啟動查詢迴圈。請檢查檔案和欄位名稱設定。")
        return
    elif not g_materials_master_list:  # CSV 載入成功但沒有 G 開頭的資料
        print(f"CSV 檔案已載入，但在 '{COLUMN_MATERIAL_ID}' 欄位未找到以 'G' 開頭的有效原料，")
        print(f"或其對應的 '{COLUMN_MATERIAL_NAME}' 為空。無法進行後續查詢。")
        return
    else:
        print(f"\n✅ 'G' 開頭原料資料載入完成，共找到 {len(g_materials_master_list)} 筆獨立原料名稱。")
        print("✅ 系統已就緒，可以開始查詢。")
    
    # 3. 進入查詢迴圈
    while True:
        print("-" * 50)
        try:
            user_search_term = input("\n➡️ 請輸入您要查詢的原料相關詞彙 (或輸入 'exit'/'quit' 離開): ").strip()
        except KeyboardInterrupt:
            print("\n\n使用者中斷程式執行。")
            break
        except EOFError:
            print("\n\n輸入結束，程式即將結束。")
            break
        
        if not user_search_term:
            print("⚠️ 您沒有輸入查詢詞彙，請重新輸入。")
            continue
        
        if user_search_term.lower() in ['exit', 'quit', '離開', '結束']:
            print("\n感謝使用，程式即將結束。")
            break
        
        print(f"\n您輸入的查詢詞是: '{user_search_term}'")
        
        # 使用預先載入的 g_materials_master_list 進行 API 查詢
        related_g_materials = get_related_materials_with_api(
            user_search_term, 
            g_materials_master_list, 
            api_client
        )
        
        # 顯示查詢結果
        print("\n--- 查詢結果 ---")
        if related_g_materials:
            # 檢查是否為錯誤訊息
            is_error_message = (
                len(related_g_materials) == 1 and
                isinstance(related_g_materials[0], str) and
                any(keyword in related_g_materials[0] for keyword in ["錯誤", "失敗", "超時", "連線"])
            )
            
            if is_error_message:
                print(f"❗ 查詢過程中發生問題: {related_g_materials[0]}")
            elif not any(related_g_materials):  # 處理空字串列表的情況
                print(f"✅ API 分析完成，但未在 'G' 開頭的原料中找到與 '{user_search_term}' 明確相關的項目。")
            else:
                print(f"與 '{user_search_term}' 相關且原料編號以 'G' 開頭的原料名稱有：")
                for i, name in enumerate(related_g_materials, 1):
                    print(f"{i:2d}. {name}")
        else:
            print(f"未能在 'G' 開頭的原料中找到與 '{user_search_term}' 相關的項目。")
    
    print("\n--- 程式執行完畢 ---")

if __name__ == "__main__":
    main()