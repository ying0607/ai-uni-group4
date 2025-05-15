import os
import time
from langchain.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
# 載入環境變數
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
SEVER_URL = os.getenv("SERVER")

llm = OllamaLLM(
    model=MODEL_NAME,   #  model名稱
    base_url=SEVER_URL
)

print(f"LLM 模型初始化: {'成功' if llm else '失敗'}")

# --- 範例測試 (可選) ---
if llm:
    print("執行 API 連線與 Langchain 整合測試...")
    try:
        # 測試 Langchain 整合
        prompt_template = ChatPromptTemplate.from_template("用一句話總結 Langchain。")
        chain = prompt_template | llm | StrOutputParser()
        langchain_response = chain.invoke({})
        print("   - Langchain 整合測試成功。")
        # print(langchain_response) # 可取消註解查看回應

    except Exception as test_error:
        print(f"\n--- 測試失敗 ---")
        print(f"   測試過程中發生錯誤：{test_error}")
        print("   請檢查您的 API 金鑰有效性、網路連線，以及模型名稱是否正確。")
        print("------------------\n")
else:
    print("\n--- 由於 client 或 llm 未成功初始化，跳過測試。 ---")
    print("---------------\n")
    
# --- 訊息處理函式定義 ---
def handle_message(material_name, characteristic):
    global llm, sections_to_search, line_bot_api, initialization_success
    msg = event.message.text
    reply_token = event.reply_token
    user_id = event.source.user_id
    print(f"收到來自 {user_id} 的訊息: '{msg}'")
    start_time = time.time()
    reply_text = "抱歉，處理您的請求時發生內部問題，請稍後再試。" # 預設錯誤訊息

    if not initialization_success or not llm or not sections_to_search: # 檢查初始化狀態
        reply_text = "系統正在初始化或遇到啟動問題，請稍後再試。如果問題持續，請聯繫管理員。"
        print("❌ 錯誤：系統未完全初始化 (LLM 或 SOP sections 未就緒，或初始化過程失敗)。")
    else:
        try:
            # --- 使用修改後的規則解析輸入 ---
            keywords_extraction_result = extract_keywords_rule_based(msg, TARGET_DESCRIPTION_KEYWORDS) # Stage 0

            if keywords_extraction_result and keywords_extraction_result.get("原料名稱"):
                # 主要使用原料名稱進行搜尋
                # search_query_keywords 傳給 search_sections
                # keywords_extraction_result (包含原料和可能的特性) 傳給 LLM 階段作為完整上下文

                # ** 修改：直接使用 keywords_extraction_result 給 search_sections，讓其內部決定用哪些關鍵字 **
                # search_sections 內部已修改為只用 "原料名稱"
                relevant_sections = search_sections(sections_to_search, keywords_extraction_result) # Stage 1 Search

                if relevant_sections:
                    print(f"   初步找到 {len(relevant_sections)} 個可能相關區塊，針對查詢: {keywords_extraction_result.get('原料名稱')}")
                    # 傳遞完整的 keywords_extraction_result 給 LLM，讓 LLM 有更完整的上下文
                    extracted_texts = extract_relevant_text(llm, relevant_sections, keywords_extraction_result) # Stage 2 Extract
                    final_summary = synthesize_results(llm, keywords_extraction_result, extracted_texts) # Stage 3 Synthesize
                    reply_text = final_summary
                else:
                    material_name_str = "、".join(keywords_extraction_result.get("原料名稱", ["未知原料"]))
                    reply_text = f"在指定的工作表範圍內，找不到與原料【{material_name_str}】直接相關的SOP內容。"
                    print(f"   在指定範圍內未找到與原料【{material_name_str}】相關的區塊。")
            else:
                reply_text = "無法從您的訊息中解析出有效的原料名稱進行查詢。請嘗試輸入明確的原料名。"
                print("   未能從輸入解析出有效的原料名稱 (規則解析失敗或無原料結果)。")
        except Exception as e:
            print(f"!!!!!!!!!! 處理訊息 '{msg}' 時發生嚴重錯誤 !!!!!!!!!!")
            traceback.print_exc()
            reply_text = "抱歉，處理您的查詢時遇到未預期的錯誤，工程師已收到通知，請稍後再試。"

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"訊息 \"{msg}\" 處理完成，耗時 {processing_time:.2f} 秒。最終回覆 (前100字): {reply_text[:100].replace(os.linesep, ' ')}")

    # 檢查 reply_text 是否為空，如果是空，給一個通用訊息
    if not reply_text or not reply_text.strip():
        print("⚠️警告：最終回覆內容為空，將發送通用提示訊息。")
        reply_text = "抱歉，未能找到明確的資訊或處理時發生問題。請嘗試更換查詢詞或稍後再試。"

    return reply_text