# File: backend/ai/bot.py

## Function: load_markdown_sections

- **Purpose**:  
  讀取並解析 Markdown 檔案，將文件內容按工作表區塊分割
- **Note**:
  預設讀取 simplified_output_by_section.md 檔案

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | filename   | String  | Markdown檔案名稱 (可選，預設使用環境變數) |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[Dict] | 包含標題和內容的區塊列表，格式: [{"title": "工作表標題", "content": "內容"}] |

- **Example**:
  ```python
  sections = load_markdown_sections("simplified_output_by_section.md")
  ```

---

## Function: filter_sections_by_title

- **Purpose**:  
  根據允許的工作表識別符過濾區塊列表
- **Note**:
  預設只保留「工作表: 9」和「工作表: 10」

- **Input Parameters**:
  | Name                 | Type       | Description              |
  |---------------------|------------|--------------------------|
  | all_sections        | List[Dict] | 所有工作表區塊列表        |
  | allowed_identifiers | List[String] | 允許的工作表識別符列表 (可選) |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[Dict] | 過濾後的工作表區塊列表                |

- **Example**:
  ```python
  filtered = filter_sections_by_title(all_sections, ["工作表: 9", "工作表: 10"])
  ```

---

## Function: extract_keywords_rule_based

- **Purpose**:  
  使用規則和jieba分詞從使用者輸入中提取原料名稱和特性描述關鍵字
- **Note**:
  主要提取原料名稱，輔助識別特性描述詞彙

- **Input Parameters**:
  | Name             | Type       | Description              |
  |------------------|------------|--------------------------|
  | user_input       | String     | 使用者查詢輸入           |
  | target_keywords  | List[String] | 目標特性描述關鍵字列表 (可選) |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | Dict/None  | 包含原料名稱和特性描述的字典，格式: {"原料名稱": [...], "特性描述": [...]} |

- **Example**:
  ```python
  keywords = extract_keywords_rule_based("食鹽 結塊問題")
  # 返回: {"原料名稱": ["食鹽"], "特性描述": ["結塊"]}
  ```

---

## Function: search_sections

- **Purpose**:  
  在已過濾的區塊中搜尋包含指定原料名稱的工作表
- **Note**:
  只搜尋原料名稱關鍵字，不搜尋特性描述

- **Input Parameters**:
  | Name                      | Type       | Description              |
  |---------------------------|------------|--------------------------|
  | sections_to_search_local  | List[Dict] | 要搜尋的工作表區塊列表    |
  | keywords_data            | Dict       | 包含原料名稱的關鍵字資料  |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[Dict] | 包含指定原料名稱的相關工作表區塊列表 |

- **Example**:
  ```python
  relevant = search_sections(sections, {"原料名稱": ["食鹽"], "特性描述": ["結塊"]})
  ```

---

## Function: extract_relevant_text

- **Purpose**:  
  使用LLM從工作表區塊中提取與指定原料最直接相關的文字片段
- **Note**:
  第一階段LLM處理，專注於精準定位和提取小範圍相關內容

- **Input Parameters**:
  | Name         | Type       | Description              |
  |--------------|------------|--------------------------|
  | current_llm  | OllamaLLM  | 已初始化的LLM模型        |
  | sections     | List[Dict] | 要處理的工作表區塊列表    |
  | keywords_data| Dict       | 包含原料名稱和特性的關鍵字資料 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[Dict] | 提取結果列表，格式: [{"title": "區塊標題", "text": "提取內容", "found": True/False}] |

- **Example**:
  ```python
  extracted = extract_relevant_text(llm, sections, keywords_data)
  ```

---

## Function: synthesize_results

- **Purpose**:  
  使用LLM將提取的文字片段整合成統一格式的數字編號列表
- **Note**:
  第二階段LLM處理，將多個片段整理成簡潔的列表格式

- **Input Parameters**:
  | Name           | Type       | Description              |
  |----------------|------------|--------------------------|
  | current_llm    | OllamaLLM  | 已初始化的LLM模型        |
  | keywords_data  | Dict       | 包含原料名稱的關鍵字資料  |
  | extracted_texts| List[Dict] | 從extract_relevant_text獲得的提取結果 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | String     | 整合後的數字編號列表格式回應        |

- **Example**:
  ```python
  final_result = synthesize_results(llm, keywords_data, extracted_texts)
  ```

---

## Function: initialize_system

- **Purpose**:  
  初始化系統資源，載入和過濾SOP文件
- **Note**:
  設定全域變數 sections_to_search 和 initialization_success

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 使用全域變數和環境設定    |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | Boolean    | 初始化是否成功                      |

- **Example**:
  ```python
  success = initialize_system()
  ```

---

## Function: process_query

- **Purpose**:  
  處理單一使用者查詢並返回SOP相關結果
- **Note**:
  主要查詢處理函式，整合所有子功能

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | user_query | String  | 使用者輸入的查詢內容      |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | String     | 與查詢相關的SOP操作說明或注意事項   |

- **Example**:
  ```python
  result = process_query("食鹽 結塊")
  # 返回關於食鹽結塊問題的SOP操作說明
  ```

## 系統工作流程

1. **初始化階段**: `initialize_system()` 載入和過濾SOP文件
2. **查詢處理**: `process_query()` 處理使用者輸入
3. **關鍵字提取**: `extract_keywords_rule_based()` 解析原料名稱
4. **區塊搜尋**: `search_sections()` 找到相關工作表區塊
5. **內容提取**: `extract_relevant_text()` 使用LLM提取相關文字
6. **結果整合**: `synthesize_results()` 使用LLM整合成最終回應

## 主要特色

- **兩階段LLM處理**: 先精準提取，再統一整合
- **中文分詞支援**: 使用jieba進行中文文本處理
- **工作表過濾**: 只搜尋指定的工作表區塊
- **錯誤處理**: 完整的異常處理和日誌記錄
- **原文保持**: 盡可能保持SOP原文內容不變

# File: backend/ai/material_search.py

## Function: load_g_recipes_from_database

- **Purpose**:  
  從資料庫載入以 'G' 開頭的配方名稱
- **Note**:
  使用 database.operations 模組的 get_recipes_by_type() 函數

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 直接查詢資料庫            |

- **Returns**:
  | Type                | Description                        |
  |--------------------|------------------------------------|
  | Optional[List[str]] | G 類型配方名稱列表，失敗時返回 None |

- **Example**:
  ```python
  g_recipes = load_g_recipes_from_database()
  # 返回: ["G001_蛋糕粉", "G002_餅乾粉", ...] 或 None
  ```

---

## Function: create_search_prompt

- **Purpose**:  
  建立給 LLM 的搜尋提示詞，用於分析配方相關性
- **Note**:
  格式化搜尋詞彙和配方批次為 LLM 可處理的提示

- **Input Parameters**:
  | Name           | Type       | Description              |
  |----------------|------------|--------------------------|
  | search_term    | String     | 使用者輸入的搜尋詞彙      |
  | materials_batch| List[String] | 要分析的配方名稱批次     |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | String     | 格式化的 LLM 提示詞                |

- **Example**:
  ```python
  prompt = create_search_prompt("蛋糕", ["G001_蛋糕粉", "G002_餅乾粉"])
  # 返回格式化的提示詞字串
  ```

---

## Function: parse_llm_response

- **Purpose**:  
  解析 LLM 的回應，提取並驗證有效的配方名稱
- **Note**:
  清理 LLM 回應中的格式符號，驗證配方名稱有效性

- **Input Parameters**:
  | Name            | Type       | Description              |
  |-----------------|------------|--------------------------|
  | response        | String     | LLM 的原始回應文字        |
  | valid_materials | List[String] | 有效的配方名稱列表用於驗證 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[String] | 經過驗證的相關配方名稱列表        |

- **Example**:
  ```python
  valid_names = parse_llm_response("1. G001_蛋糕粉\n2. G003_麵包粉", all_recipes)
  # 返回: ["G001_蛋糕粉", "G003_麵包粉"]
  ```

---

## Function: get_related_materials_with_llm

- **Purpose**:  
  使用 LLM 從 G 類型配方列表中找出與搜尋詞相關的項目
- **Note**:
  支援分批處理大量配方，避免 LLM 輸入長度限制

- **Input Parameters**:
  | Name                | Type       | Description              |
  |---------------------|------------|--------------------------|
  | search_term         | String     | 搜尋詞彙                 |
  | g_recipe_names_list | List[String] | G 類型的配方名稱列表     |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[String] | 相關配方名稱列表或錯誤訊息        |

- **Example**:
  ```python
  related = get_related_materials_with_llm("蛋糕", g_recipe_list)
  # 返回: ["G001_蛋糕粉", "G005_海綿蛋糕基底"] 或錯誤訊息
  ```

---

## Function: get_recipe_details_by_name

- **Purpose**:  
  根據配方名稱取得配方詳細資訊，包含步驟
- **Note**:
  使用 database.operations 的搜尋和取得配方功能

- **Input Parameters**:
  | Name        | Type   | Description              |
  |-------------|--------|--------------------------|
  | recipe_name | String | 配方名稱                 |

- **Returns**:
  | Type           | Description                        |
  |----------------|------------------------------------|
  | Optional[dict] | 配方詳細資訊字典，失敗時返回 None  |

- **Example**:
  ```python
  details = get_recipe_details_by_name("G001_蛋糕粉")
  # 返回: {"recipe_id": 1, "recipe_name": "G001_蛋糕粉", "steps": [...]}
  ```

---

## Function: display_recipe_details

- **Purpose**:  
  顯示配方的詳細資訊，包含基本資訊和製作步驟
- **Note**:
  輸出格式化的配方資訊到控制台

- **Input Parameters**:
  | Name        | Type   | Description              |
  |-------------|--------|--------------------------|
  | recipe_name | String | 配方名稱                 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | None       | 無返回值，直接輸出到控制台          |

- **Example**:
  ```python
  display_recipe_details("G001_蛋糕粉")
  # 輸出配方的完整資訊到控制台
  ```

---

## Function: test_llm_connection

- **Purpose**:  
  測試 LLM 連線是否正常運作
- **Note**:
  發送簡單測試請求確認 Ollama 服務可用性

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 使用全域 llm 變數        |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | Boolean    | True 表示連線正常，False 表示失敗   |

- **Example**:
  ```python
  is_connected = test_llm_connection()
  # 返回: True 或 False
  ```

---

## Function: test_database_connection

- **Purpose**:  
  測試資料庫連線是否正常，並顯示配方總數
- **Note**:
  使用 database.operations 的 get_all_recipes() 測試連線

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 直接測試資料庫連線        |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | Boolean    | True 表示連線正常，False 表示失敗   |

- **Example**:
  ```python
  db_ok = test_database_connection()
  # 返回: True 或 False，並輸出配方總數
  ```

---

## Function: main

- **Purpose**:  
  主程式執行入口，處理完整的配方查詢流程
- **Note**:
  包含系統初始化、連線測試、資料載入和查詢迴圈

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 主程式入口                |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | None       | 無返回值，執行完整的查詢流程        |

- **Example**:
  ```python
  if __name__ == "__main__":
      main()
  # 啟動完整的配方查詢系統
  ```

## 系統工作流程

1. **初始化階段**: 
   - 測試資料庫和 LLM 連線
   - 載入所有 G 類型配方資料

2. **查詢處理**: 
   - 接收使用者搜尋詞彙
   - 使用 LLM 分析配方相關性
   - 分批處理大量配方避免超時

3. **結果展示**: 
   - 顯示相關配方列表
   - 可選擇查看詳細配方資訊

4. **錯誤處理**: 
   - 連線失敗檢測
   - LLM 回應解析錯誤處理
   - 使用者中斷處理

## 主要特色

- **智慧搜尋**: 使用 LLM 進行語意相關性分析
- **分批處理**: 支援大量配方的分批查詢
- **完整資訊**: 提供配方基本資訊和詳細製作步驟
- **連線檢測**: 啟動前檢測資料庫和 LLM 服務狀態
- **使用者友善**: 互動式查詢介面和清晰的結果展示
- **錯誤恢復**: 完整的異常處理和錯誤訊息提示

## 核心查詢函式 (相當於 bot3)

如果要建立一個簡化的 `bot3` 函式，應該整合以下核心功能：

```python
def bot3(search_term: str) -> List[str]:
    """
    配方智慧搜尋核心函式
    
    Args:
        search_term: 搜尋詞彙
        
    Returns:
        相關的 G 類型配方名稱列表
    """
    # 1. 載入 G 類型配方
    g_recipes = load_g_recipes_from_database()
    if not g_recipes:
        return ["無法載入配方資料"]
    
    # 2. 使用 LLM 搜尋相關配方
    related_recipes = get_related_materials_with_llm(search_term, g_recipes)
    
    return related_recipes
```

## Function: bot3

- **Purpose**:  
  使用 LLM 從資料庫中的 G 類型配方中找出與搜尋詞相關的配方
- **Note**:
  整合載入資料庫資料和 LLM 智慧搜尋功能

- **Input Parameters**:
  | Name        | Type   | Description              |
  |-------------|--------|--------------------------|
  | search_term | String | 想要搜尋的配方相關詞彙    |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | List[String] | 與搜尋詞相關的 G 類型配方名稱列表 |

- **Example**:
  ```python
  related_recipes = bot3("蛋糕")
  # 返回: ["G001_蛋糕粉", "G005_海綿蛋糕基底", "G010_奶油蛋糕預拌粉"]
  ```

# File: database/operations.py

## Function: get_db_connection

- **Purpose**:  
  建立並返回資料庫連接引擎
- **Note**:
  使用環境變數中的資料庫連線資訊，支援 MySQL 資料庫

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 使用環境變數中的資料庫設定 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | Engine     | SQLAlchemy 資料庫連接引擎對象       |

- **Example**:
  ```python
  engine = get_db_connection()
  ```

---

## Function: get_all_materials

- **Purpose**:  
  取得所有材料資料，依類型和名稱排序
- **Note**:
  從 materials 資料表讀取完整材料清單

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 查詢所有材料資料          |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 包含所有材料資料的 pandas DataFrame |

- **Example**:
  ```python
  materials_df = get_all_materials()
  print(f"共有 {len(materials_df)} 種材料")
  ```

---

## Function: get_material_by_code

- **Purpose**:  
  根據材料編號取得特定材料的詳細資訊
- **Note**:
  精確匹配材料編號，返回單一材料資料

- **Input Parameters**:
  | Name          | Type   | Description              |
  |---------------|--------|--------------------------|
  | material_code | String | 材料編號                 |

- **Returns**:
  | Type           | Description                        |
  |----------------|------------------------------------|
  | dict/None      | 材料資料字典，找不到時返回 None     |

- **Example**:
  ```python
  material = get_material_by_code("A001")
  if material:
      print(f"材料名稱: {material['material_name']}")
  ```

---

## Function: get_all_recipes

- **Purpose**:  
  取得所有配方資料，依類型和名稱排序
- **Note**:
  從 bom 資料表讀取完整配方清單

- **Input Parameters**:
  | Name       | Type    | Description              |
  |------------|---------|--------------------------|
  | 無參數      | -       | 查詢所有配方資料          |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 包含所有配方資料的 pandas DataFrame |

- **Example**:
  ```python
  recipes_df = get_all_recipes()
  print(f"共有 {len(recipes_df)} 個配方")
  ```

---

## Function: get_recipe_by_id

- **Purpose**:  
  根據配方編號取得特定配方的基本資訊
- **Note**:
  精確匹配配方編號，不包含製作步驟

- **Input Parameters**:
  | Name      | Type   | Description              |
  |-----------|--------|--------------------------|
  | recipe_id | String | 配方編號                 |

- **Returns**:
  | Type           | Description                        |
  |----------------|------------------------------------|
  | dict/None      | 配方基本資料字典，找不到時返回 None |

- **Example**:
  ```python
  recipe = get_recipe_by_id("G001")
  if recipe:
      print(f"配方名稱: {recipe['recipe_name']}")
  ```

---

## Function: get_recipe_steps

- **Purpose**:  
  取得指定配方的所有製作步驟，包含材料資訊
- **Note**:
  JOIN materials 表格，提供完整的步驟和材料資訊

- **Input Parameters**:
  | Name      | Type   | Description              |
  |-----------|--------|--------------------------|
  | recipe_id | String | 配方編號                 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 包含步驟詳細資訊的 pandas DataFrame |

- **Example**:
  ```python
  steps_df = get_recipe_steps("G001")
  print(f"配方有 {len(steps_df)} 個步驟")
  ```

---

## Function: search_materials

- **Purpose**:  
  搜尋材料，支援依名稱或編號進行模糊查詢
- **Note**:
  使用 LIKE 語法進行模糊匹配搜尋

- **Input Parameters**:
  | Name    | Type   | Description              |
  |---------|--------|--------------------------|
  | keyword | String | 搜尋關鍵字               |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 符合搜尋條件的材料 DataFrame      |

- **Example**:
  ```python
  materials = search_materials("巧克力")
  print(f"找到 {len(materials)} 個相關材料")
  ```

---

## Function: search_recipes

- **Purpose**:  
  搜尋配方，支援依名稱或編號進行模糊查詢
- **Note**:
  使用 LIKE 語法進行模糊匹配搜尋

- **Input Parameters**:
  | Name    | Type   | Description              |
  |---------|--------|--------------------------|
  | keyword | String | 搜尋關鍵字               |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 符合搜尋條件的配方 DataFrame      |

- **Example**:
  ```python
  recipes = search_recipes("蛋糕")
  print(f"找到 {len(recipes)} 個相關配方")
  ```

---

## Function: get_recipe_with_steps

- **Purpose**:  
  取得配方及其所有步驟的完整資訊
- **Note**:
  整合配方基本資訊和詳細製作步驟

- **Input Parameters**:
  | Name      | Type   | Description              |
  |-----------|--------|--------------------------|
  | recipe_id | String | 配方編號                 |

- **Returns**:
  | Type           | Description                        |
  |----------------|------------------------------------|
  | dict/None      | 包含步驟列表的完整配方字典         |

- **Example**:
  ```python
  complete_recipe = get_recipe_with_steps("G001")
  if complete_recipe:
      print(f"配方有 {len(complete_recipe['steps'])} 个步驟")
  ```

---

## Function: get_bom_tree

- **Purpose**:  
  取得配方的完整 BOM 樹狀結構，包括子配方的遞迴展開
- **Note**:
  支援多層級 BOM 結構，有最大遞迴深度限制防止無限循環

- **Input Parameters**:
  | Name      | Type   | Description              |
  |-----------|--------|--------------------------|
  | recipe_id | String | 配方編號                 |
  | level     | int    | 當前遞迴層級 (預設 0)    |
  | max_level | int    | 最大遞迴深度 (預設 10)   |

- **Returns**:
  | Type           | Description                        |
  |----------------|------------------------------------|
  | dict/None      | 包含完整 BOM 樹狀結構的字典       |

- **Example**:
  ```python
  bom_tree = get_bom_tree("G001", max_level=5)
  # 返回包含子配方結構的完整 BOM 樹
  ```

---

## Function: get_recipes_by_type

- **Purpose**:  
  根據配方類型取得配方列表 (例如 G 類型或 F 類型)
- **Note**:
  精確匹配配方類型，結果依名稱排序

- **Input Parameters**:
  | Name        | Type   | Description              |
  |-------------|--------|--------------------------|
  | recipe_type | String | 配方類型 (如 'G', 'F')   |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 指定類型的配方 DataFrame          |

- **Example**:
  ```python
  g_recipes = get_recipes_by_type('G')
  print(f"G 類型配方有 {len(g_recipes)} 個")
  ```

---

## Function: get_materials_by_type

- **Purpose**:  
  根據材料類型取得材料列表 (例如 A 類型或 B 類型)
- **Note**:
  精確匹配材料類型，結果依名稱排序

- **Input Parameters**:
  | Name          | Type   | Description              |
  |---------------|--------|--------------------------|
  | material_type | String | 材料類型 (如 'A', 'B')   |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 指定類型的材料 DataFrame          |

- **Example**:
  ```python
  a_materials = get_materials_by_type('A')
  print(f"A 類型材料有 {len(a_materials)} 種")
  ```

---

## Function: get_recipe_material_usage

- **Purpose**:  
  取得特定材料被使用的所有配方清單
- **Note**:
  顯示材料在各配方中的用量和使用資訊

- **Input Parameters**:
  | Name          | Type   | Description              |
  |---------------|--------|--------------------------|
  | material_code | String | 材料編號                 |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 使用該材料的配方和用量資訊 DataFrame |

- **Example**:
  ```python
  usage = get_recipe_material_usage("A001")
  print(f"材料 A001 被 {len(usage)} 個配方使用")
  ```

---

## Function: get_recipes_with_filtered_materials

- **Purpose**:  
  取得使用特定類型材料或特定供應商材料的配方
- **Note**:
  支援多條件篩選，可同時指定材料類型和供應商

- **Input Parameters**:
  | Name          | Type       | Description              |
  |---------------|------------|--------------------------|
  | material_type | String     | 材料類型 (可選)          |
  | supplier_id   | String     | 供應商編號 (可選)        |

- **Returns**:
  | Type       | Description                        |
  |------------|------------------------------------|
  | DataFrame  | 符合篩選條件的配方 DataFrame      |

- **Example**:
  ```python
  # 取得使用 A 類型材料的所有配方
  recipes = get_recipes_with_filtered_materials(material_type='A')
  
  # 取得使用特定供應商材料的配方
  recipes = get_recipes_with_filtered_materials(supplier_id='SUP001')
  ```

## 資料庫結構概覽

根據程式碼分析，系統使用以下主要資料表：

### 主要資料表
- **`{GROUP_PREFIX}materials`**: 材料主檔
  - `material_code`: 材料編號
  - `material_name`: 材料名稱
  - `material_type`: 材料類型 (A, B 等)
  - `specification`: 規格說明
  - `supplier_id`: 供應商編號

- **`{GROUP_PREFIX}bom`**: 配方主檔
  - `recipe_id`: 配方編號
  - `recipe_name`: 配方名稱
  - `recipe_type`: 配方類型 (G, F 等)
  - `version`: 版本
  - `specification`: 規格說明
  - `standard_hours`: 標準工時

- **`{GROUP_PREFIX}recipe_step`**: 配方步驟明細
  - `step_id`: 步驟編號
  - `recipe_id`: 所屬配方編號
  - `step_order`: 步驟順序
  - `material_code`: 材料編號
  - `quantity`: 用量
  - `unit`: 單位
  - `product_base`: 產品基礎
  - `notes`: 備註

## 系統特色

- **環境變數配置**: 支援透過 .env 檔案配置資料庫連線
- **群組前綴**: 支援多群組資料表前綴 (GROUP_PREFIX)
- **完整 CRUD**: 提供材料和配方的完整查詢功能
- **關聯查詢**: 支援材料與配方的關聯查詢
- **樹狀結構**: 支援多層級 BOM 結構展開
- **模糊搜尋**: 提供關鍵字模糊搜尋功能
- **類型篩選**: 支援依類型篩選材料和配方
- **使用追蹤**: 可追蹤材料在各配方中的使用情況

## 核心查詢模式

1. **基本查詢**: `get_all_*()` - 取得完整清單
2. **精確查詢**: `get_*_by_id()` - 依編號精確查詢
3. **模糊搜尋**: `search_*()` - 關鍵字搜尋
4. **類型篩選**: `get_*_by_type()` - 依類型篩選
5. **關聯查詢**: `get_recipe_with_steps()` - 包含關聯資料
6. **樹狀展開**: `get_bom_tree()` - 遞迴結構展開
7. **使用分析**: `get_recipe_material_usage()` - 使用情況分析