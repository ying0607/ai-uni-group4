import os
import re
import traceback
import time  # Added for timing process_query
from langchain.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM  # type: ignore
from langchain_core.output_parsers import StrOutputParser  # type: ignore
from dotenv import load_dotenv
import jieba  # type: ignore

# 載入環境變數
load_dotenv()

# --- 常數設定  ---
MODEL_NAME = os.getenv("MODEL_NAME")
SERVER_URL = os.getenv("SERVER_URL")
# 確保 SIMPLIFIED_MD_FILENAME 有一個預設值，以防 .env 中未設定
SIMPLIFIED_MD_FILENAME = os.getenv("SIMPLIFIED_MD_FILENAME", "simplified_output_by_section.md")
TARGET_DESCRIPTION_KEYWORDS = ["結塊", "過篩", "順序", "吸濕", "稠度", "黏稠", "流動性"]
CHINESE_STOP_WORDS = {"的", "和", "與", "或", "了", "呢", "嗎", "喔", "啊", "關於", "有關", "請", "請問", " ", ""}
ALLOWED_WORKSHEET_IDENTIFIERS = [
    "工作表: 9", "工作表: 10"
]

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

# --- 全域變數 (新增/管理) ---
sections_to_search = []
initialization_success = False


# --- SOP 查詢相關函式  ---

def load_markdown_sections(filename=None):  # 讓 filename 可以被外部傳入
    """讀取並解析 Markdown 檔案"""
    # 如果 filename 未傳入，則使用全域變數
    if filename is None:
        filename = SIMPLIFIED_MD_FILENAME

    sections = [];
    print(f"正在嘗試載入檔案: {filename}")
    if not filename:  # 如果 SIMPLIFIED_MD_FILENAME 也未設定
        print(f"❌ 錯誤：未指定 Markdown 檔案名稱。")
        return []

    if not os.path.exists(filename):
        print(
            f"❌ 錯誤：檔案 '{filename}' 不存在於當前目錄 '{os.getcwd()}'。請確保檔案路徑正確或 .env 中的 SIMPLIFIED_MD_FILENAME 設定正確。")
        return []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        print(f"檔案 {filename} 讀取成功。")
    except FileNotFoundError:
        print(
            f"❌ 錯誤：找不到檔案 '{filename}' (再次檢查)。"); return []  # FileNotFoundError 已被 os.path.exists 處理，但保留以防萬一
    except Exception as e:
        print(f"❌ 讀取檔案 '{filename}' 時發生錯誤：{e}"); return []

    parts = re.split(r'(## 工作表:.*)', markdown_content)
    parsed_sections_count = 0
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            title = parts[i].strip()
            content = parts[i + 1].strip().removeprefix("Here is the simplified content:").strip().removeprefix(
                "Here is the simplified output:").strip()
            if title and content:  # 要求標題和內容都存在
                sections.append({"title": title, "content": content})
                parsed_sections_count += 1
        elif i < len(parts):  # 處理最後一個標題可能沒有內容的情況
            title = parts[i].strip()
            if title:  # 即使內容為空也加入，但通常我們期望有內容
                sections.append({"title": title, "content": ""})  # 標記為無內容
                # parsed_sections_count +=1 # 如果也計入無內容的區塊
    if not sections:
        print(f"⚠️ 警告：未能從檔案 '{filename}' 解析出任何工作表區塊。")
    else:
        print(f"   從 '{filename}' 解析出 {len(sections)} 個區塊 ({parsed_sections_count} 個有內容)。")
    return sections


def filter_sections_by_title(all_sections, allowed_identifiers=ALLOWED_WORKSHEET_IDENTIFIERS):
    """根據標題關鍵字過濾區塊列表"""
    if not all_sections: return []
    return [sec for sec in all_sections if
            any(allowed_id in sec.get("title", "") for allowed_id in allowed_identifiers)]


def extract_keywords_rule_based(user_input, target_keywords=TARGET_DESCRIPTION_KEYWORDS):
    """使用規則拆分和比對關鍵字，主要提取原料名稱。"""
    print(f"--- (階段0) 使用規則解析輸入 (主要提取原料): '{user_input}' ---")
    input_cleaned = user_input.strip().lower()
    if not input_cleaned:
        return None

    try:
        if 'jieba' in globals() and jieba is not None:  # 確保 jieba 已正確載入
            tokens = list(jieba.cut_for_search(input_cleaned))
        else:  # 基本分詞
            print("   ⚠️ 警告: jieba 未載入，使用基本空格分詞。")
            input_no_punct = re.sub(r'[^\w\s]', ' ', input_cleaned)
            tokens = input_no_punct.split()
    except Exception as e:
        print(f"   ⚠️ 分詞時發生錯誤: {e}。將使用基本空格分詞。")
        input_no_punct = re.sub(r'[^\w\s]', ' ', input_cleaned)
        tokens = input_no_punct.split()

    print(f"   分詞結果: {tokens}")
    potential_materials = []
    identified_characteristics = set()
    for token in tokens:
        token_clean = token.strip()
        if not token_clean or token_clean in CHINESE_STOP_WORDS: continue
        is_characteristic = False
        for target_char in target_keywords:
            if token_clean == target_char.lower():
                identified_characteristics.add(target_char);
                is_characteristic = True;
                break
        if not is_characteristic:
            if not token_clean.isnumeric() and len(token_clean) > 0:
                potential_materials.append(token_clean)
    materials_list_unique = sorted(list(set(potential_materials)))
    characteristics_list_sorted = sorted(list(identified_characteristics))
    if not materials_list_unique:
        print("⚠️ 規則解析器：未能識別出任何潛在的原料名稱。");
        return None
    result = {"原料名稱": materials_list_unique, "特性描述": characteristics_list_sorted}
    print(f"   規則解析結果 (主要為原料，輔助特性): {result}")
    return result


def search_sections(sections_to_search_local, keywords_data):  # 避免與全域變數衝突
    """在已過濾的區塊中初步篩選包含【原料名稱】關鍵字的工作表"""
    relevant_sections = []
    if not keywords_data: print("ℹ️ 關鍵字對象為空，無法執行搜尋。"); return []
    material_keywords = keywords_data.get("原料名稱", [])
    all_keywords = [kw for kw in material_keywords if kw and isinstance(kw, str)]
    if not all_keywords: print("ℹ️ 沒有有效的【原料名稱】關鍵字可供搜尋。"); return []
    print(f"DEBUG: 正在使用以下任一【原料名稱】關鍵字搜尋: {all_keywords} (在 {len(sections_to_search_local)} 個區塊中)")
    for section in sections_to_search_local:
        text_to_search = section.get("title", "") + section.get("content", "")
        if any(keyword.lower() in text_to_search.lower() for keyword in all_keywords):
            relevant_sections.append(section)
    return relevant_sections


def extract_relevant_text(current_llm, sections, keywords_data):  # 傳入 current_llm
    """(第一階段 LLM) 使用極度聚焦的 Prompt 提取與指定【原料名稱】最直接相關的【小範圍文字片段】。"""
    if not current_llm: print("❌ extract_relevant_text: LLM 未提供。"); return []
    if not keywords_data: print("ℹ️ extract_relevant_text: 關鍵字對象為空。"); return []
    material_names = keywords_data.get('原料名稱', [])
    if not material_names: print("ℹ️ extract_relevant_text: 查詢中未提供原料名稱。"); return []
    material_name_str = "、".join(material_names)
    characteristics_list = keywords_data.get('特性描述', [])
    description_keywords_str = ', '.join(characteristics_list)
    if characteristics_list:
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
    prompt_template = ChatPromptTemplate.from_template(prompt_base)
    chain = prompt_template | current_llm | StrOutputParser()
    relevant_texts = []
    print(f"--- (階段1) 使用 LLM 定位並提取子章節，使用的查詢上下文: {keywords_str_display_for_prompt} ---")
    for section in sections:
        section_title = section.get("title", "無標題區塊");
        section_content = section.get("content", "")
        section_full_text = f"{section_content}"
        print(f"   正在處理區塊: {section_title} (搜尋原料 '{material_name_str}')...")
        try:
            relevant_text = chain.invoke(
                {"keywords_str_display_for_prompt": keywords_str_display_for_prompt, "text": section_full_text})
            relevant_text = relevant_text.strip()
            if relevant_text.startswith("根據關鍵字") or relevant_text.startswith("以下是找到"):
                lines = relevant_text.splitlines();
                relevant_text = "\n".join(lines[1:]).strip()
            if relevant_text.startswith("```markdown"): relevant_text = relevant_text.removeprefix(
                "```markdown").removesuffix("```").strip()
            is_found_message = "在此文件中未找到與此原料直接相關的內容" in relevant_text
            if is_found_message or not relevant_text:
                print(
                    f"     ↳ 在區塊 '{section_title}' 中未找到或提取到空內容關於原料 '{material_name_str}'。LLM回應: '{relevant_text}'")
                relevant_texts.append(
                    {"title": section_title, "text": relevant_text if relevant_text else "內容提取為空",
                     "found": False})
            else:
                print(
                    f"     ↳ 從 '{section_title}' 提取到內容 (前100字): \"{relevant_text[:100].replace(os.linesep, ' ')}...\"")
                relevant_texts.append({"title": section_title, "text": relevant_text, "found": True})
        except Exception as e:
            print(f"❌ 從區塊 '{section_title}' 提取時出錯: {e}");
            traceback.print_exc()
            relevant_texts.append({"title": section_title, "text": "LLM 提取失敗", "found": False})
    return relevant_texts


def synthesize_results(current_llm, keywords_data, extracted_texts):  # 傳入 current_llm
    """(第二階段 LLM) 將提取出的【小範圍文字片段】整合成【極簡且原文呈現的統一格式列表】。"""
    if not current_llm: print("❌ synthesize_results: LLM 未提供。"); return "LLM未就緒，無法整合結果。"
    if not keywords_data: return "無效的關鍵字，無法整合結果。"
    if not extracted_texts: return "未能提取到任何相關內容以供整合。"
    valid_extractions = [
        item['text'] for item in extracted_texts
        if item.get("found", False) and "LLM 提取失敗" not in item['text'] and \
           "在此文件中未找到與此原料直接相關的內容" not in item['text'] and \
           item['text'] and item['text'].strip()
    ]
    if not valid_extractions:
        material_names_list = keywords_data.get('原料名稱', [])
        material_name_str = "、".join(material_names_list) if material_names_list else "所查詢的項目"
        all_attempted_but_not_found = all(
            not item.get("found") or "在此文件中未找到與此原料直接相關的內容" in item['text'] or item[
                'text'].strip() == ""
            for item in extracted_texts
        )
        if extracted_texts and all_attempted_but_not_found:
            return f"已檢查所有相關SOP文件區塊，但均未找到關於原料【{material_name_str}】的直接操作說明或注意事項。"
        return f"雖然初步定位到可能相關的SOP區塊，但在其中未能找到關於原料【{material_name_str}】的具體操作說明或注意事項。"
    print(f"\n🔄 (階段2) 正在整合 {len(valid_extractions)} 份提取的重點內容並統一格式 (力求原文、簡潔)...")
    combined_extracted_text = "\n\n片段分隔線 (請將每個片段視為獨立資訊來源)\n\n".join(valid_extractions)
    material_names_list = keywords_data.get('原料名稱', [])
    material_name = "、".join(material_names_list) if material_names_list else "未指定原料"
    characteristics_list = keywords_data.get('特性描述', [])
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
    synthesis_chain = synthesis_prompt_template | current_llm | StrOutputParser()
    try:
        final_response = synthesis_chain.invoke(
            {"keywords_str_for_prompt": keywords_str_for_prompt, "combined_extracted_text": combined_extracted_text})
        final_response = final_response.strip()
        unwanted_prefixes = [
            "好的，這是整理後的列表：", "這是為您整理的列表：", "以下是整理後的列表：", "根據您提供的資訊：",
            "關於您查詢的原料", "關於您查詢的", "Okay, here is the list:", "Here is the list:",
            "Here is the output:", "這是您查詢的結果：", "這是相關的資訊：", "查詢結果如下：",
        ]
        cleaned_response = final_response
        for prefix in unwanted_prefixes:
            if prefix.strip().startswith("1.") and cleaned_response.strip().startswith("1."): continue
            if final_response.lower().startswith(prefix.lower()):
                prefix_len = len(prefix);
                temp_response = final_response[prefix_len:].lstrip("：: ").strip()
                if temp_response or prefix.lower() not in ["1."]:
                    cleaned_response = temp_response
                    print(f"   DEBUG: (Synthesize) 移除了不需要的前綴 '{prefix}'");
                    break
        lines = cleaned_response.splitlines()
        if lines and not re.match(r"^\s*\d+\.\s*", lines[0]):
            first_line_lower = lines[0].lower();
            is_likely_intro = True
            for mat_kw in keywords_data.get("原料名稱", []):
                if mat_kw.lower() in first_line_lower:
                    if len(lines[0]) > 20: is_likely_intro = False; break
            if len(lines[0]) > 50: is_likely_intro = False
            if is_likely_intro and len(lines) > 1:
                print(f"   DEBUG: (Synthesize) 輸出首行 '{lines[0]}' 並非標準列表項，嘗試移除作為引言。")
                cleaned_response = "\n".join(lines[1:]).strip()
            elif is_likely_intro and len(lines) == 1:
                print(f"   DEBUG: (Synthesize) 輸出只有一行 '{lines[0]}' 且並非標準列表項，可能LLM未遵循指示。")
        if not cleaned_response.strip() and valid_extractions:
            print(f"   ⚠️ 警告: (Synthesize) LLM 最終輸出為空，但之前有 {len(valid_extractions)} 條有效提取。")
            return f"已找到關於原料【{material_name}】的相關資訊，但在最終整理格式時出現問題。"
        if not cleaned_response and valid_extractions:
            return f"已找到關於原料【{material_name}】的相關資訊片段，但無法按預期格式化呈現。"
        # print(f"   整合結果 (前100字): \"{cleaned_response[:100].replace(os.linesep, ' ')}...\"") # 已移到 process_query
        return cleaned_response
    except Exception as e:
        print(f"❌ 整合結果時發生嚴重錯誤：{e}");
        traceback.print_exc()
        return "整合結果時發生嚴重錯誤，請檢查系統日誌。"


# --- 新增/修改：系統初始化、查詢處理、主執行區塊 ---

def initialize_system():
    """初始化系統資源，如載入SOP文件。"""
    global sections_to_search, initialization_success, llm  # llm 是從外部傳入的

    print("--- 開始執行系統初始化 ---")
    initialization_success = False

    # 1. 檢查 LLM 是否已初始化 (由外部腳本完成)
    if llm is None:
        print("❌ 錯誤：LLM 模型未在腳本開頭成功初始化。無法繼續。")
        return False
    print("   ✅ LLM 已由外部初始化。")

    # 2. 載入並過濾 SOP 文件區塊
    print("2. 載入並過濾 SOP 文件區塊...")
    # SIMPLIFIED_MD_FILENAME 已是全域變數
    all_loaded_sections = load_markdown_sections(SIMPLIFIED_MD_FILENAME)
    if all_loaded_sections:
        original_count = len(all_loaded_sections)
        # ALLOWED_WORKSHEET_IDENTIFIERS 已是全域變數
        filtered_sections = filter_sections_by_title(all_loaded_sections, ALLOWED_WORKSHEET_IDENTIFIERS)
        if filtered_sections:
            sections_to_search = filtered_sections  # 使用過濾後的
            allowed_titles_str = ', '.join([s.get('title', '?') for s in sections_to_search])
            print(
                f"   ✅ 成功載入 {original_count} 區塊，已過濾出 {len(sections_to_search)} 個目標區塊: [{allowed_titles_str}]")
        else:
            print(f"   ⚠️ 警告：成功載入 {original_count} 區塊，但根據 ALLOWED_WORKSHEET_IDENTIFIERS 未過濾出目標區塊。")
            print(f"   將嘗試在所有 {original_count} 個已載入區塊中搜尋 (如果這是預期行為)。")
            sections_to_search = all_loaded_sections  # 若無過濾結果，則搜尋全部已載入區塊
            if not sections_to_search:  # 如果 all_loaded_sections 本身就為空
                print(f"❌ 錯誤：未能從 '{SIMPLIFIED_MD_FILENAME}' 解析出任何區塊，且過濾結果也為空。")
                return False
    else:
        print(f"❌ 錯誤：未能從 '{SIMPLIFIED_MD_FILENAME}' 載入任何 SOP 文件區塊。系統無法處理查詢。")
        sections_to_search = []
        return False

    initialization_success = True
    print("--- 系統初始化成功完成 ---")
    return True


def process_query(user_query):
    """處理單一使用者查詢並返回結果。"""
    global llm, sections_to_search, initialization_success  # 使用全域 llm 和 sections_to_search

    if not initialization_success:
        error_message = "系統初始化失敗，無法處理查詢。"
        print(f"❌ {error_message}")
        return error_message
    if not llm:  # 再次確認，雖然 initialize_system 已檢查
        error_message = "LLM 模型未就緒。"
        print(f"❌ {error_message}")
        return error_message
    if not sections_to_search:
        error_message = "沒有可供查詢的SOP文件區塊。"
        print(f"❌ {error_message}")
        return error_message

    print(f"\n處理查詢: '{user_query}'")
    start_time = time.time()
    reply_text = "抱歉，處理您的請求時發生內部問題。"

    try:
        keywords_data = extract_keywords_rule_based(user_query, TARGET_DESCRIPTION_KEYWORDS)

        if keywords_data and keywords_data.get("原料名稱"):
            # search_sections 使用全域 sections_to_search
            relevant_sop_sections = search_sections(sections_to_search, keywords_data)

            if relevant_sop_sections:
                print(
                    f"   初步找到 {len(relevant_sop_sections)} 個可能相關區塊，針對原料: {keywords_data.get('原料名稱')}")
                # extract_relevant_text 和 synthesize_results 使用全域 llm
                extracted_texts = extract_relevant_text(llm, relevant_sop_sections, keywords_data)
                final_summary = synthesize_results(llm, keywords_data, extracted_texts)
                reply_text = final_summary
            else:
                material_name_str = "、".join(keywords_data.get("原料名稱", ["未知原料"]))
                reply_text = f"在SOP文件 ({SIMPLIFIED_MD_FILENAME}) 中，找不到與原料【{material_name_str}】直接相關的內容。"
                print(f"   在已載入和過濾的區塊中未找到與原料【{material_name_str}】相關的內容。")
        else:
            reply_text = "無法從您的訊息中解析出有效的原料名稱進行查詢。請嘗試輸入明確的原料名。"
            print("   未能從輸入解析出有效的原料名稱 (規則解析失敗或無原料結果)。")
    except Exception as e:
        print(f"!!!!!!!!!! 處理查詢 '{user_query}' 時發生嚴重錯誤 !!!!!!!!!!")
        traceback.print_exc()
        reply_text = f"處理查詢 '{user_query}' 時遇到未預期的錯誤，請檢查日誌。"

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"查詢 \"{user_query}\" 處理完成，耗時 {processing_time:.2f} 秒。")

    if not reply_text or not reply_text.strip():
        print("⚠️警告：最終回覆內容為空，將返回通用提示訊息。")
        reply_text = "抱歉，未能找到明確的資訊或處理時發生問題。請嘗試更換查詢詞或稍後再試。"

    print(f"   最終回覆 (前100字): \"{reply_text[:100].replace(os.linesep, ' ')}...\"")
    return reply_text


if __name__ == "__main__":
    print("--- SOP 查詢系統 (控制台版本) ---")

    # 執行系統初始化
    if initialize_system():
        print("\n--- 系統已就緒 ---")
        print(f"將從 '{SIMPLIFIED_MD_FILENAME}' 檔案中查詢。")
        if ALLOWED_WORKSHEET_IDENTIFIERS:
            print(f"限定查詢的工作表範圍關鍵字: {ALLOWED_WORKSHEET_IDENTIFIERS}")
        else:
            print("未設定特定工作表範圍，將搜尋所有解析出的區塊。")
        print("輸入您的查詢 (例如：'食鹽 結塊')")
        print("輸入 'exit' 或 'quit' 來結束程式。")

        while True:
            try:
                user_input = input("\n您的查詢: ")
                if user_input.strip().lower() in ['exit', 'quit']:
                    print("正在結束程式...")
                    break
                if not user_input.strip():
                    continue

                result = process_query(user_input)
                print("\n========== 查詢結果 ==========")
                print(result)
                print("==============================")

            except KeyboardInterrupt:
                print("\n偵測到使用者中斷 (Ctrl+C)，正在結束程式...")
                break
            except Exception as e:
                print(f"\n在主查詢迴圈中發生未預期錯誤: {e}")
                traceback.print_exc()
                # 選擇是否繼續或中斷
                # break
    else:
        print("\n❌ 因系統初始化失敗，無法啟動 SOP 查詢系統。請檢查上方的錯誤訊息。")

    print("--- 程式執行完畢 ---")