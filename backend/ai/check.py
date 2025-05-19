import requests
import time
import json
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

def check_ollama_server(server_url=None, retries=3, retry_delay=2):
    """
    檢查 Ollama 伺服器連線狀態並獲取可用模型列表
    
    參數:
        server_url (str): Ollama 伺服器 URL，如果為 None 則從環境變數或默認值讀取
        retries (int): 重試次數
        retry_delay (int): 重試間隔（秒）
        
    返回:
        tuple: (連線狀態 (bool), 可用模型列表 (list), 錯誤信息 (str))
    """
    # 獲取伺服器 URL
    if server_url is None:
        server_url = os.getenv("SERVER_URL")
        
    print(f"伺服器 URL: {server_url}")
    
    # 確保 URL 以 http:// 或 https:// 開頭
    if not server_url.startswith(("http://", "https://")):
        server_url = f"http://{server_url}"
    
    # 移除尾部斜線
    server_url = server_url.rstrip("/")
    
    # Ollama API 端點
    models_endpoint = f"{server_url}/api/tags"
    
    print(f"正在檢查 Ollama 伺服器連線狀態：{server_url}")
    
    # 嘗試連接
    for attempt in range(retries):
        try:
            response = requests.get(models_endpoint, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    models = [model.get('name') for model in data.get('models', [])]
                    
                    if models:
                        print(f"✅ Ollama 伺服器連線成功！可用模型：{', '.join(models)}")
                        return True, models, ""
                    else:
                        print(f"⚠️ Ollama 伺服器連線成功，但未找到任何可用模型。")
                        return True, [], "未找到可用模型"
                except json.JSONDecodeError:
                    print(f"⚠️ Ollama 伺服器回應格式錯誤。")
                    return False, [], "伺服器回應格式錯誤"
            else:
                print(f"⚠️ 嘗試 {attempt+1}/{retries}: 伺服器回應狀態碼 {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️ 嘗試 {attempt+1}/{retries}: 無法連接到 Ollama 伺服器")
        except requests.exceptions.Timeout:
            print(f"⚠️ 嘗試 {attempt+1}/{retries}: 連接超時")
        except Exception as e:
            print(f"⚠️ 嘗試 {attempt+1}/{retries}: 發生未知錯誤 - {str(e)}")
        
        if attempt < retries - 1:
            print(f"將在 {retry_delay} 秒後重試...")
            time.sleep(retry_delay)
    
    print("❌ 無法連接到 Ollama 伺服器。請確認伺服器是否運行，以及 URL 是否正確。")
    return False, [], "無法連接到伺服器"


def check_model_availability(server_url=None, model_name=None, retries=2):
    """
    檢查指定模型在 Ollama 伺服器上是否可用
    
    參數:
        server_url (str): Ollama 伺服器 URL
        model_name (str): 要檢查的模型名稱
        retries (int): 重試次數
        
    返回:
        tuple: (模型是否可用 (bool), 錯誤信息 (str))
    """
    # 先檢查伺服器連線
    server_available, available_models, error_msg = check_ollama_server(server_url, retries)
    
    if not server_available:
        return False, f"伺服器連線失敗: {error_msg}"
    
    # 獲取模型名稱
    if model_name is None:
        model_name = os.getenv("MODEL_NAME")
        
    if not model_name:
        return False, "未指定模型名稱"
    
    # 檢查模型是否可用
    model_exists = any(model.lower() == model_name.lower() for model in available_models)
    
    if model_exists:
        print(f"✅ 模型 '{model_name}' 在伺服器上可用")
        return True, ""
    else:
        error_message = f"⚠️ 模型 '{model_name}' 在伺服器上不可用。可用模型: {', '.join(available_models)}"
        print(error_message)
        return False, error_message


# 使用範例
if __name__ == "__main__":
    # 從環境變數獲取
    server_url = os.getenv("SERVER_URL")
    model_name = os.getenv("MODEL_NAME")
    
    # 檢查伺服器連線
    connected, models, error = check_ollama_server(server_url)
    
    if connected:
        # 檢查模型是否可用
        model_available, model_error = check_model_availability(server_url, model_name)
        
        if model_available:
            print("🚀 伺服器和模型檢查通過，應用程序可以正常運行。")
        else:
            print(f"⛔ 模型檢查失敗: {model_error}")
            # 可以建議使用可用的模型之一
            if models:
                print(f"💡 建議：您可以嘗試使用以下可用模型之一: {', '.join(models)}")
                print("   或者使用 'ollama pull MODEL_NAME' 命令下載所需模型。")
    else:
        print(f"⛔ 伺服器連線檢查失敗: {error}")
        print("💡 建議：請確認 Ollama 伺服器已啟動，或檢查環境變數 SERVER 設置。")