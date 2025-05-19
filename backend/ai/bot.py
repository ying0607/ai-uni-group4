import os
import re
import traceback
from langchain.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import jieba
# 載入環境變數
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
SERVER_URL = os.getenv("SERVER_URL")  # 修正變數名稱拼寫錯誤
SIMPLIFIED_MD_FILENAME = os.getenv("SIMPLIFIED_MD_FILENAME")
TARGET_DESCRIPTION_KEYWORDS=["結塊", "過篩", "順序", "吸濕", "稠度", "黏稠", "流動性"] # 仍可輔助識別，但搜尋主要靠原料
CHINESE_STOP_WORDS={"的", "和", "與", "或", "了", "呢", "嗎", "喔", "啊", "關於", "有關", "請", "請問", " ", ""}
ALLOWED_WORKSHEET_IDENTIFIERS=[
    "工作表: 9", "工作表: 10"
]

llm = OllamaLLM(
    model=MODEL_NAME,   #  model名稱
    base_url=SERVER_URL  # 修正變數名稱
)

# --- SOP 查詢相關函式 ---

def load_markdown_sections(filename=SIMPLIFIED_MD_FILENAME):
    """讀取並解析 Markdown 檔案"""
    sections = []; print(f"正在嘗試載入檔案: {filename}")
    try:
        with open(filename, 'r', encoding='utf-8') as f: markdown_content = f.read()
        print(f"檔案 {filename} 讀取成功。")
    except FileNotFoundError: print(f"❌ 錯誤：找不到檔案 '{filename}'。"); return []
    except Exception as e: print(f"❌ 讀取檔案 '{filename}' 時發生錯誤：{e}"); return []
    parts = re.split(r'(## 工作表:.*)', markdown_content)
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            title = parts[i].strip(); content = parts[i + 1].strip().removeprefix("Here is the simplified content:").strip().removeprefix("Here is the simplified output:").strip()
            if title and content: sections.append({"title": title, "content": content})
        elif i < len(parts):
            title = parts[i].strip()
            if title: sections.append({"title": title, "content": ""})
    if not sections: print(f"⚠️ 警告：未能從檔案 '{filename}' 解析出任何工作表區塊。")
    return sections

def filter_sections_by_title(all_sections, allowed_identifiers=ALLOWED_WORKSHEET_IDENTIFIERS):
    """根據標題關鍵字過濾區塊列表"""
    if not all_sections: return []
    return [sec for sec in all_sections if any(allowed_id in sec.get("title", "") for allowed_id in allowed_identifiers)]

# --- *** 修改：基於規則的關鍵字提取函式 (更側重原料) *** ---
def extract_keywords_rule_based(user_input, target_keywords=TARGET_DESCRIPTION_KEYWORDS):
    """使用規則拆分和比對關鍵字，主要提取原料名稱。"""
    print(f"--- (階段0) 使用規則解析輸入 (主要提取原料): '{user_input}' ---")
    input_cleaned = user_input.strip().lower()
    if not input_cleaned:
        return None

    if jieba:
        tokens = list(jieba.cut_for_search(input_cleaned))
    else:
        input_no_punct = re.sub(r'[^\w\s]', ' ', input_cleaned)
        tokens = input_no_punct.split()
    print(f"   分詞結果: {tokens}")

    potential_materials = []
    identified_characteristics = set() # 仍然記錄特性詞，但它們不作為主要搜尋依據

    for token in tokens:
        token_clean = token.strip()
        if not token_clean or token_clean in CHINESE_STOP_WORDS:
            continue

        is_characteristic = False
        # 檢查是否為特性關鍵字 (完全匹配)
        for target_char in target_keywords:
            if token_clean == target_char.lower():
                identified_characteristics.add(target_char) # 記錄原始大小寫的特性關鍵字
                is_characteristic = True
                break

        # 如果不是特性詞，且不是數字，且長度大於0，則視為潛在原料
        if not is_characteristic:
            if not token_clean.isnumeric() and len(token_clean) > 0:
                potential_materials.append(token_clean)

    materials_list_unique = sorted(list(set(potential_materials)))
    characteristics_list_sorted = sorted(list(identified_characteristics))

    if not materials_list_unique:
        print("⚠️ 規則解析器：未能識別出任何潛在的原料名稱。")
        # 即使沒有原料，也返回結構，讓後續判斷
        # return {"原料名稱": [], "特性描述": characteristics_list_sorted}
        return None # 或者直接返回None，如果嚴格要求必須有原料名才能查詢

    result = {"原料名稱": materials_list_unique, "特性描述": characteristics_list_sorted}
    print(f"   規則解析結果 (主要為原料，輔助特性): {result}")
    return result
# --- *** 函式結束 *** ---

def search_sections(sections_to_search, keywords):
    """在已過濾的區塊中初步篩選包含【原料名稱】關鍵字的工作表"""
    relevant_sections = []
    if not keywords:  # 增加對 None 的檢查
        print("ℹ️ 關鍵字對象為空，無法執行搜尋。")
        return []
        
    # *** 修改：只使用原料名稱進行初步搜尋 ***
    material_keywords = keywords.get("原料名稱", [])
    all_keywords = [kw for kw in material_keywords if kw and isinstance(kw, str)]

    if not all_keywords:
        print("ℹ️ 沒有有效的【原料名稱】關鍵字可供搜尋。")
        return []
    print(f"DEBUG: 正在使用以下任一【原料名稱】關鍵字搜尋: {all_keywords}")
    for section in sections_to_search:
        text_to_search = section.get("title", "") + section.get("content", "")
        if any(keyword.lower() in text_to_search.lower() for keyword in all_keywords): # 忽略大小寫搜尋
            relevant_sections.append(section)
    return relevant_sections

# --- *** 修改：第一階段 LLM Prompt，強調小範圍、僅原料相關 *** ---
def extract_relevant_text(llm, sections, keywords):
    """(第一階段 LLM) 使用極度聚焦的 Prompt 提取與指定【原料名稱】最直接相關的【小範圍文字片段】。"""
    if not keywords:  # 增加對 None 的檢查
        print("ℹ️ extract_relevant_text: 關鍵字對象為空。")
        return []
        
    material_names = keywords.get('原料名稱', [])
    if not material_names:
        print("ℹ️ extract_relevant_text: 查詢中未提供原料名稱。")
        return []
    material_name_str = "、".join(material_names)

    # 特性描述可以作為輔助上下文，幫助LLM理解，但提取焦點是原料
    characteristics_list = keywords.get('特性描述', [])
    description_keywords_str = ', '.join(characteristics_list)

    if characteristics_list:
        # 雖然主要搜原料，但告知LLM使用者也提到了這些特性，可能有助於LLM理解上下文
        keywords_str_display_for_prompt = f"主要查詢的原料名稱：【{material_name_str}】。(使用者同時提及了這些相關詞彙，供參考：{description_keywords_str})"
    else:
        keywords_str_display_for_prompt = f"主要查詢的原料名稱：【{material_name_str}】"

    prompt_base = """
        你的任務是作為一個精確的文字提取器。
        在下方提供的「工作表內容」中，僅找出與「主要查詢的原料名稱」最直接相關的【一個或多個簡短文字片段、句子或列表項】。

        {keywords_str_display_for_prompt}

        工作表內容：
        ```markdown
        {text}
        ```

        輸出要求：
        1.  精確定位到包含「主要查詢的原料名稱」的句子、操作步驟或其非常緊密的上下文。
        2.  **【直接輸出】** 找到的相關內容。提取的範圍應盡可能小而精準。例如，僅提取包含該原料名稱的那個步驟、那句描述或相關的列表項。
        3.  **【避免提取】** 過長的段落或整個子標題下的所有內容，除非該原料名稱在整個段落/子標題中都高度相關且內容不可分割。優先提取最小的有效資訊單位。
        4.  **【絕對禁止】** 包含 '## 工作表: ...' 這個最高級別的標題。
        5.  **【絕對禁止】** 包含任何 '製表日期', '製表人' 等頁腳資訊。
        6.  **【絕對禁止】** 進行任何摘要、改寫或添加任何【解釋性文字、前言、結語】(例如不要說 "以下是找到的內容：" 或 "根據關鍵字..." 等)。輸出結果必須直接就是提取的內容本身。
        7.  如果在此「工作表內容」中找不到直接與「主要查詢的原料名稱」相關的內容，【只輸出】以下固定文字：「在此文件中未找到與此原料直接相關的內容」。
        8.  必須使用【繁體中文】輸出 (如果提取的內容本身是中文)。
        再次強調：直接輸出提取的、與原料直接相關的【小範圍】內容，不要加任何其他文字。
        """

    # 使用帶有所有預期輸入變量的模板
    prompt_template = ChatPromptTemplate.from_template(prompt_base)
    chain = prompt_template | llm | StrOutputParser()

    relevant_texts = []
    # 顯示一次完整的 keywords_str_display_for_prompt，因為它對於所有 section 都是一樣的
    print(f"--- (階段1) 使用 LLM 定位並提取子章節，使用的查詢上下文: {keywords_str_display_for_prompt} ---")

    for section in sections:
        section_title = section.get("title", "無標題區塊")
        section_content = section.get("content", "")
        section_full_text = f"{section_content}" # 簡化，只傳遞內容讓 LLM 專注

        print(f"   正在處理區塊: {section_title} (搜尋原料 '{material_name_str}')...")
        try:
            relevant_text = chain.invoke({
                "keywords_str_display_for_prompt": keywords_str_display_for_prompt,
                "text": section_full_text
            })
            relevant_text = relevant_text.strip()

            # 基本的後處理，移除 LLM 可能不小心加上的 markdown 標籤或引導詞
            if relevant_text.startswith("根據關鍵字") or relevant_text.startswith("以下是找到"):
                lines = relevant_text.splitlines()
                relevant_text = "\n".join(lines[1:]).strip()
            if relevant_text.startswith("```markdown"):
                relevant_text = relevant_text.removeprefix("```markdown").removesuffix("```").strip()

            is_found_message = "在此文件中未找到與此原料直接相關的內容" in relevant_text

            if is_found_message or not relevant_text: # 如果是 "未找到" 或提取結果為空
                print(f"     ↳ 在區塊 '{section_title}' 中未找到或提取到空內容關於原料 '{material_name_str}'。LLM回應: '{relevant_text}'")
                relevant_texts.append({"title": section_title, "text": relevant_text if relevant_text else "內容提取為空", "found": False})
            else:
                print(f"     ↳ 從 '{section_title}' 提取到內容 (前100字): \"{relevant_text[:100].replace(os.linesep, ' ')}...\"")
                relevant_texts.append({"title": section_title, "text": relevant_text, "found": True})

        except Exception as e:
            print(f"❌ 從區塊 '{section_title}' 提取時出錯: {e}")
            traceback.print_exc()
            relevant_texts.append({"title": section_title, "text": "LLM 提取失敗", "found": False})
    return relevant_texts
# --- *** 函式結束 *** ---

# --- *** 修改：第二階段 LLM Prompt，強調原文呈現、不修飾、統一列表 *** ---
def synthesize_results(llm, keywords, extracted_texts):
    """(第二階段 LLM) 將提取出的【小範圍文字片段】整合成【極簡且原文呈現的統一格式列表】。"""
    if not keywords:  # 增加對 None 的檢查
        return "無效的關鍵字，無法整合結果。"
        
    if not extracted_texts:
        return "未能提取到任何相關內容以供整合。"

    valid_extractions = [
        item['text'] for item in extracted_texts
        if item.get("found", False) and \
           "LLM 提取失敗" not in item['text'] and \
           "在此文件中未找到與此原料直接相關的內容" not in item['text'] and \
           item['text'] and item['text'].strip() # 確保文本本身不為空或僅包含空白
    ]

    if not valid_extractions:
        material_names_list = keywords.get('原料名稱', [])
        material_name_str = "、".join(material_names_list) if material_names_list else "所查詢的項目"
        # 檢查是否所有嘗試提取的區塊都返回了 "未找到" 或類似訊息
        all_attempted_but_not_found = all(
            not item.get("found") or \
            "在此文件中未找到與此原料直接相關的內容" in item['text'] or \
            item['text'].strip() == ""
            for item in extracted_texts
        )
        if extracted_texts and all_attempted_but_not_found: # 確保 extracted_texts 不是空的
            return f"已檢查所有相關SOP文件區塊，但均未找到關於原料【{material_name_str}】的直接操作說明或注意事項。"
        return f"雖然初步定位到可能相關的SOP區塊，但在其中未能找到關於原料【{material_name_str}】的具體操作說明或注意事項。"


    print(f"\n🔄 (階段2) 正在整合 {len(valid_extractions)} 份提取的重點內容並統一格式 (力求原文、簡潔)...")
    # 將所有提取片段組合，用特殊分隔符明確告知LLM這是不同來源的獨立片段
    combined_extracted_text = "\n\n片段分隔線 (請將每個片段視為獨立資訊來源)\n\n".join(valid_extractions)

    material_names_list = keywords.get('原料名稱', [])
    material_name = "、".join(material_names_list) if material_names_list else "未指定原料"

    characteristics_list = keywords.get('特性描述', [])
    if characteristics_list:
        keywords_str_for_prompt = f"使用者主要查詢的原料名稱為【{material_name}】。(使用者查詢時提及的相關詞彙，供您理解上下文：{', '.join(characteristics_list)})"
    else:
        keywords_str_for_prompt = f"使用者主要查詢的原料名稱為【{material_name}】。"

    synthesis_prompt_template_str = """
        您是一位SOP內容整理員。您的任務是將下方提供的、已從SOP文件中提取出的、與指定原料相關的【多個獨立的簡短文字片段】，整理成一個【極簡的、統一格式的數字編號列表】。

        {keywords_str_for_prompt}

        已提取的相關SOP片段 (這些片段來自不同地方，請將它們視為獨立的資訊點，使用「片段分隔線」隔開)：
        ---
        {combined_extracted_text}
        ---

        您的任務與輸出要求：
        1.  仔細閱讀所有「已提取的相關SOP片段」。每個片段都是關於上述「主要查詢的原料名稱」的直接相關內容。
        2.  **【核心任務】：將這些片段中的【每一個獨立的資訊點、操作步驟、或注意事項】整理出來，作為列表中的一個獨立項目。**
        3.  **【格式統一】：** 使用從 1 開始的數字編號列表 (格式如：1., 2., 3., ...)。
        4.  **【原文呈現】：** 盡最大可能【直接使用】提取片段中的【原文表述】。**【嚴格禁止】任何形式的改寫、摘要、解釋、歸納或添加您自己的文字或評論。** 您的工作是「彙整原文」和「格式化為列表」，而不是「再創作」或「解釋」。
        5.  如果原始片段本身就是一個短列表或包含子步驟，請在新的數字編號下，盡可能保持其原始結構，例如使用縮排和 '-' 或 '*' 來表示層級關係。
        6.  **【極簡輸出】：** 您的最終輸出【必須直接是這個數字編號列表本身】。**【嚴格禁止】** 包含任何前言（例如 "好的，這是整理後的列表：" 或 "關於您查詢的..."）、標題、引導語或結語。
        7.  如果多個片段描述的是【完全相同或幾乎完全重複】的資訊，請只選擇其中一個最清晰的表述放入列表，以避免不必要的冗餘。但若有些微差異或補充，寧可保留兩者，避免資訊遺失。**判斷重複的標準要非常嚴格。**
        8.  使用**繁體中文**。
        9.  即使最終整理出來的資訊點很少（例如只有一兩條），也直接按列表格式輸出。
        10. **【絕對禁止】** 在輸出中提及任何「工作表標題」、「SOP文件來源」或「片段分隔線」等元信息。
        11. **【絕對禁止】** 添加任何超出所提供片段內容之外的資訊或建議。

        請直接開始輸出列表：
        """
    synthesis_prompt_template = ChatPromptTemplate.from_template(synthesis_prompt_template_str)
    synthesis_chain = synthesis_prompt_template | llm | StrOutputParser()

    try:
        final_response = synthesis_chain.invoke({
            "keywords_str_for_prompt": keywords_str_for_prompt,
            "combined_extracted_text": combined_extracted_text
        })
        final_response = final_response.strip()

        # 後處理：強力移除已知的前綴 (LLM有時還是會忍不住加上)
        unwanted_prefixes = [
            "好的，這是整理後的列表：", "這是為您整理的列表：", "以下是整理後的列表：",
            "根據您提供的資訊：", "關於您查詢的原料", "關於您查詢的",
            "Okay, here is the list:", "Here is the list:", "Here is the output:",
            "這是您查詢的結果：", "這是相關的資訊：", "查詢結果如下：",
            "1. " # 有時LLM會自己加列表編號，但我們的prompt要求它從1開始，所以如果它以 "1. " 開頭，通常是正確的
        ]
        # 移除前綴的邏輯需要小心，避免誤刪正常的列表開頭
        cleaned_response = final_response
        for prefix in unwanted_prefixes:
            # 確保 prefix 不是 "1. " 這種可能與正確輸出衝突的
            if prefix.strip().startswith("1.") and cleaned_response.strip().startswith("1."):
                continue
            if final_response.lower().startswith(prefix.lower()):
                # 計算前綴實際長度，移除此前綴及其後的空白和冒號
                prefix_len = len(prefix)
                temp_response = final_response[prefix_len:].lstrip("：: ").strip()
                # 只有當移除後還有內容，或者移除的是明確的引導語時才更新
                if temp_response or prefix.lower() not in ["1."]: # 避免 "1. " 被錯誤移除後變空
                    cleaned_response = temp_response
                    print(f"   DEBUG: (Synthesize) 移除了不需要的前綴 '{prefix}'")
                    break # 找到並移除一個就不再檢查其他前綴

        # 再一次檢查是否以數字列表開頭，如果不是，且內容看起來像引言，嘗試移除
        lines = cleaned_response.splitlines()
        if lines and not re.match(r"^\s*\d+\.\s*", lines[0]): # 如果第一行不是 "數字." 開頭
            # 並且第一行看起來像是一句簡短的引言而不是實際內容
            first_line_lower = lines[0].lower()
            is_likely_intro = True
            # 如果第一行包含原料名，可能不是引言，除非非常短
            for mat_kw in keywords.get("原料名稱", []):
                if mat_kw.lower() in first_line_lower:
                    if len(lines[0]) > 20 : # 如果包含原料名但較長，可能就是內容
                        is_likely_intro = False
                    break
            if len(lines[0]) > 50: # 如果第一行很長，不像引言
                is_likely_intro = False

            if is_likely_intro and len(lines) > 1 : # 確保有多行，移除後還有內容
                print(f"   DEBUG: (Synthesize) 輸出首行 '{lines[0]}' 並非標準列表項，嘗試移除作為引言。")
                cleaned_response = "\n".join(lines[1:]).strip()
            elif is_likely_intro and len(lines) == 1: # 只有一行且不像列表項
                print(f"   DEBUG: (Synthesize) 輸出只有一行 '{lines[0]}' 且並非標準列表項，可能LLM未遵循指示。")
                # 此時可以考慮返回一個固定訊息或原始提取內容的簡單組合
                # cleaned_response = "LLM未能按要求格式化資訊，請重試或檢查日誌。"

        if not cleaned_response.strip() and valid_extractions:
            print(f"   ⚠️ 警告: (Synthesize) LLM 最終輸出為空或僅含空白，但之前有 {len(valid_extractions)} 條有效提取內容。可能整合失敗。")
            return f"已找到關於原料【{material_name}】的相關資訊，但在最終整理格式時出現問題。請稍後再試。"

        # 如果清理後 response 變空，但 valid_extractions 有內容，說明 LLM 可能完全沒按指示輸出
        if not cleaned_response and valid_extractions:
             return f"已找到關於原料【{material_name}】的相關資訊片段，但無法按預期格式化呈現。請稍後重試。"
         
        print(f"   整合結果 (前100字): \"{cleaned_response[:100].replace(os.linesep, ' ')}...\"")
        return cleaned_response

    except Exception as e:
        print(f"❌ 整合結果時發生嚴重錯誤：{e}")
        traceback.print_exc()
        return "整合結果時發生嚴重錯誤，請檢查系統日誌。"
# --- *** 函式結束 *** ---

def main():
    # 1. 載入 Markdown 檔案並過濾工作表
    all_sections = load_markdown_sections()
    filtered_sections = filter_sections_by_title(all_sections)
    
    if not filtered_sections:
        print("⚠️ 未找到符合條件的工作表，請檢查ALLOWED_WORKSHEET_IDENTIFIERS設定或Markdown文件。")
        return

    # 2. 使用者輸入查詢關鍵字
    user_input = input("請輸入查詢的原料名稱或特性描述：")
    keywords = extract_keywords_rule_based(user_input)

    if not keywords:
        print("⚠️ 無法識別任何有效的原料名稱或特性描述，請檢查輸入。")
        return

    # 3. 在已過濾的區塊中搜尋關鍵字
    relevant_sections = search_sections(filtered_sections, keywords)

    if not relevant_sections:
        print("⚠️ 在所有工作表中未找到與查詢相關的內容。")
        return

    # 4. 提取相關文本
    extracted_texts = extract_relevant_text(llm, relevant_sections, keywords)

    # 5. 整合結果
    final_response = synthesize_results(llm, keywords, extracted_texts)
    
    print(f"\n🔄 最終整合結果：\n{final_response}")

if __name__ == "__main__":
    main()