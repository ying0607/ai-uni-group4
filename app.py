from flask import Flask, render_template, request, jsonify, redirect, url_for,session
from functools import wraps
from api import api_bp
from database import operations as db_ops
from backend.ai import material_search
import os

app = Flask(__name__)
app.secret_key = 'value-project-2025'  

# 全域模板變數
@app.context_processor
def inject_globals():
    return {
        'page_name': getattr(request, 'page_name', ''),
        'query': request.args.get('q', '')
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ----- 路由設定 ----

# 登入畫面
@app.route('/')
def index():
    """首頁 - 主要入口"""
    return render_template('Index.html')

# 首頁
@app.route('/homepage')
@login_required
def home():
    """首頁路由"""
    request.page_name = 'homepage'
    return render_template('homepage.html')

# 搜尋頁面
@app.route('/search')
@login_required
def search():
    """搜尋頁面"""
    request.page_name = 'search'
    return render_template('search.html')

# 第一階段搜尋結果
@app.route('/search/result')
@login_required
def search_result():
    """搜尋結果頁面"""
    query = request.args.get('q', '')
    request.page_name = 'search'
    
    try:
        results = []
        
        if query:
            print(f"🔍 開始混合搜尋，關鍵字: {query}")
            
            # === 第一階段：AI 智慧搜尋 ===
            print("📊 階段1：AI 智慧搜尋")
            ai_results = []
            try:
                related_recipe_names = material_search.main(query)
                
                if related_recipe_names and isinstance(related_recipe_names, list):
                    for recipe_name in related_recipe_names:
                        # 過濾錯誤訊息
                        if not isinstance(recipe_name, str) or any(keyword in recipe_name for keyword in ["錯誤", "失敗", "超時", "連線", "LLM", "無法"]):
                            continue
                        
                        # 查詢完整配方資訊
                        recipes_df = db_ops.search_recipes(recipe_name)
                        
                        for _, row in recipes_df.iterrows():
                            ai_results.append({
                                'code': row['recipe_id'],
                                'company': row['recipe_name'], 
                                'name': row['recipe_type'],
                                'source': 'AI'  # 標記來源
                            })
                
                print(f"✅ AI 搜尋找到 {len(ai_results)} 個結果")
                
            except Exception as e:
                print(f"❌ AI 搜尋發生錯誤: {e}")
            
            # === 第二階段：傳統 LIKE 搜尋（備援機制）===
            # 🚨 [可移除區塊 - 開始] 🚨
            print("📋 階段2：傳統 LIKE 搜尋（備援）")
            like_results = []
            try:
                # 使用傳統 SQL LIKE 搜尋作為備援
                like_recipes_df = db_ops.search_recipes(query)
                
                for _, row in like_recipes_df.iterrows():
                    like_results.append({
                        'code': row['recipe_id'],
                        'company': row['recipe_name'], 
                        'name': row['recipe_type'],
                        'source': 'LIKE'  # 標記來源
                    })
                
                print(f"✅ LIKE 搜尋找到 {len(like_results)} 個結果")
                
            except Exception as e:
                print(f"❌ LIKE 搜尋發生錯誤: {e}")
            # 🚨 [可移除區塊 - 結束] 🚨
            
            # === 第三階段：結果合併與去重 ===
            print("🔄 階段3：結果合併")
            
            # 優先使用 AI 結果
            if ai_results:
                results = ai_results
                print(f"📊 使用 AI 搜尋結果: {len(results)} 筆")
            elif like_results:
                # 🚨 [可移除邏輯 - 開始] 🚨
                results = like_results
                print(f"📋 使用 LIKE 備援結果: {len(results)} 筆")
                # 🚨 [可移除邏輯 - 結束] 🚨
            else:
                results = []
                print("❌ 兩種搜尋都沒有找到結果")
            
            # 可選：合併兩種結果（去重）
            # combined_results = ai_results + like_results
            # seen_codes = set()
            # results = []
            # for result in combined_results:
            #     if result['code'] not in seen_codes:
            #         results.append(result)
            #         seen_codes.add(result['code'])
            
        else:
            # 無關鍵字時顯示所有 G 類型配方
            print("📂 無搜尋關鍵字，顯示所有 G 類型配方")
            results_df = db_ops.get_recipes_by_type('G')
            
            for _, row in results_df.iterrows():
                results.append({
                    'code': row['recipe_id'],
                    'company': row['recipe_name'], 
                    'name': row['recipe_type'],
                    'source': 'DEFAULT'
                })
        
        print(f"🎯 最終搜尋結果: {len(results)} 筆")
        
        return render_template('search_result.html', 
                             query=query, 
                             results=results,
                             page_name='search')
    
    except Exception as e:
        print(f"💥 搜尋系統錯誤: {e}")
        return render_template('search_result.html', 
                             query=query, 
                             results=[], 
                             error="搜尋時發生系統錯誤",
                             page_name='search')

# 最終階段搜尋結果
@app.route('/search/result/final/<recipe_id>')
@login_required
def search_result_final_detail(recipe_id):
    """最終搜尋結果頁面（含配方ID）"""
    request.page_name = 'search'
    return render_template('search_result_final.html', 
                         recipe_id=recipe_id,
                         page_name='search')

# AI 聊天機器人
@app.route('/chatbot')
@login_required
def chatbot():
    """聊天機器人頁面"""
    request.page_name = 'chatbot'
    return render_template('chatbot.html')

app.register_blueprint(api_bp)

# 啟動伺服器
if __name__ == '__main__':
    app.run(debug=True)