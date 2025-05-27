# AI-UNI-GROUP4: AI-Powered Manufacturing Management System
# 小江解 - AI 配方管理系統

## 專案簡介

本專案是一個針對食品製造業的 AI 智慧配方管理系統，整合了配方查詢、原料管理、成本計算以及 AI 助理功能。系統提供直覺的網頁介面，讓使用者能夠快速查詢配方、追蹤原料成本，並透過 AI 助理「小江解」獲得 SOP 操作指引。

## 主要功能

### 1. 配方查詢系統
- 🔍 **快速搜尋**：支援配方名稱、編號的即時搜尋
- 📊 **詳細資訊**：顯示配方步驟、原料用量、成本計算
- 🔗 **多層級 BOM**：支援半成品配方的遞迴展開
- 💰 **成本分析**：自動計算配方總成本

### 2. AI 助理「小江解」
- 💬 **智慧問答**：回答配方相關問題
- 📋 **SOP 查詢**：提供原料操作注意事項
- 🤖 **LLM 整合**：使用 Ollama 本地部署的語言模型

### 3. 資料管理
- 📦 **原料管理**：A 類（一般）、B 類（管制）原料分類
- 📑 **配方管理**：G 類（成品）、F 類（半成品）配方分類
- 🏢 **供應商追蹤**：原料供應商資訊管理

## 技術架構

### 後端技術
- **框架**：Flask (Python)
- **資料庫**：MySQL
- **ORM**：SQLAlchemy
- **AI 框架**：LangChain + Ollama
- **中文處理**：jieba 分詞

### 前端技術
- **HTML5 + CSS3**
- **原生 JavaScript**
- **響應式設計**

### AI 模組
- **LLM**：Ollama (支援多種模型)
- **向量搜尋**：基於規則的關鍵字提取
- **文檔處理**：Markdown 格式的 SOP 文件

## 安裝指南

### 1. 環境需求
- Python 3.8+
- MySQL 5.7+
- Ollama (用於 AI 功能)

### 2. 安裝步驟

```bash
# 1. 克隆專案
git clone https://github.com/your-repo/AI-UNI-GROUP4.git
cd AI-UNI-GROUP4

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，填入資料庫連線資訊
```

### 3. 環境變數設定

在 `.env` 檔案中設定以下參數：

```env
# 資料庫設定
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASS=your_password
DB_NAME=your_database
GROUP_PREFIX=group4_

# AI 模型設定
MODEL_NAME=llama3.2
SERVER_URL=http://localhost:11434
SIMPLIFIED_MD_FILENAME=simplified_output_by_section.md
```

### 4. 資料庫初始化

```bash
# 1. 建立資料庫結構
python database/create_schema.py

# 2. 匯入種子資料
python database/import_seed.py

# 3. 新增約束（可選）
python database/add_constraints.py
```

### 5. 啟動 Ollama 服務

```bash
# 安裝 Ollama (如果尚未安裝)
# 參考: https://ollama.ai/

# 啟動 Ollama 服務
ollama serve

# 下載所需模型
ollama pull llama3.2
```

## 使用方式

### 啟動應用程式

```bash
python app.py
```

應用程式將在 `http://localhost:5000` 啟動

### 頁面導覽

1. **首頁** (`/`)：登入頁面
2. **主頁** (`/homepage`)：系統主頁面
3. **配方查詢** (`/search`)：搜尋配方功能
4. **AI 助理** (`/chatbot`)：與小江解對話

### API 端點

- `POST /api/search`：搜尋配方
- `GET /api/recipe/<recipe_id>`：取得配方詳細資訊
- `POST /api/chat`：AI 聊天功能

## 專案結構

```
AI-UNI-GROUP4/
├── app.py                 # 主應用程式
├── requirements.txt       # Python 依賴
├── .env.example          # 環境變數範例
├── backend/              # 後端模組
│   ├── ai/              # AI 相關功能
│   │   ├── bot.py       # SOP 查詢機器人
│   │   ├── material_search.py  # 原料搜尋
│   │   └── check.py     # 連線檢查
│   └── utils.py         # 工具函數
├── database/            # 資料庫相關
│   ├── operations.py    # 資料庫操作
│   ├── create_schema.py # 建立資料表
│   └── import_seed.py   # 匯入種子資料
├── static/              # 靜態資源
│   ├── css/            # 樣式表
│   ├── JS/             # JavaScript
│   └── image/          # 圖片資源
└── templates/           # HTML 模板
```

## 功能說明

### 配方查詢流程

1. 使用者在搜尋框輸入關鍵字
2. 系統搜尋匹配的配方
3. 顯示配方列表
4. 點擊配方查看詳細資訊
5. 自動計算成本並顯示 BOM 結構

### AI 助理功能

1. **SOP 查詢** (`bot.py`)
   - 解析使用者輸入的原料名稱
   - 搜尋相關 SOP 文件
   - 使用 LLM 提取相關內容
   - 整合並格式化回覆

2. **原料搜尋** (`material_search.py`)
   - 從資料庫載入 G 類配方
   - 使用 LLM 分析相關性
   - 返回相關配方建議

## 注意事項

1. **資料庫連線**：確保 MySQL 服務正在運行
2. **Ollama 服務**：AI 功能需要 Ollama 服務在背景運行
3. **種子資料**：請將 CSV 檔案放在 `database/seeds/` 目錄下
4. **SOP 文件**：確保 `simplified_output_by_section.md` 存在於 `backend/ai/` 目錄

## 開發團隊

- AI-UNI-GROUP4 團隊

## 聯絡資訊

如有任何問題或建議，請聯絡系統管理員。

---

*最後更新：2025年5月*