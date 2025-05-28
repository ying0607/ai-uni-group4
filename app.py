from flask import Flask, render_template, request, jsonify, redirect, url_for
from api import api_bp
from database import operations as db_ops
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

# ----- 路由設定 ----

# 登入畫面
@app.route('/')
def index():
    """首頁 - 主要入口"""
    return render_template('Index.html')

# 首頁
@app.route('/homepage')
def home():
    """首頁路由"""
    request.page_name = 'homepage'
    return render_template('homepage.html')

# 搜尋頁面
@app.route('/search')
def search():
    """搜尋頁面"""
    request.page_name = 'search'
    return render_template('search.html')

# 第一階段搜尋結果
@app.route('/search/result')
def search_result():
    """搜尋結果頁面"""
    query = request.args.get('q', '')
    request.page_name = 'search'
    
    try:
        if query:
            # 使用關鍵字搜尋配方
            results_df = db_ops.search_recipes(query)
        else:
            # 如果沒有關鍵字，顯示所有配方
            results_df = db_ops.get_all_recipes()
        
        # 轉換DataFrame為字典列表，只取需要的欄位
        results = []
        for _, row in results_df.iterrows():
            results.append({
                'code': row['recipe_id'],  # 貨品編號對應 recipe_id
                'company': row['recipe_name'],  # 公司對應 recipe_name（之後改為配方名稱）
                'name': row['recipe_type']  # 食品名稱對應 recipe_type（之後改為配方類型）
            })
        
        return render_template('search_result.html', 
                             query=query, 
                             results=results,
                             page_name='search')
    
    except Exception as e:
        print(f"搜尋錯誤: {e}")
        return render_template('search_result.html', 
                             query=query, 
                             results=[], 
                             error="搜尋時發生錯誤",
                             page_name='search')

# 最終階段搜尋結果
@app.route('/search/result/final/<recipe_id>')
def search_result_final_detail(recipe_id):
    """最終搜尋結果頁面（含配方ID）"""
    request.page_name = 'search'
    return render_template('search_result_final.html', 
                         recipe_id=recipe_id,
                         page_name='search')

# AI 聊天機器人
@app.route('/chatbot')
def chatbot():
    """聊天機器人頁面"""
    request.page_name = 'chatbot'
    return render_template('chatbot.html')

app.register_blueprint(api_bp)

# 啟動伺服器
if __name__ == '__main__':
    app.run(debug=True)