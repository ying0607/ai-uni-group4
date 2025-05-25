from flask import Flask, render_template, request, jsonify, redirect, url_for
from database.operations import search_recipes, get_all_recipes
import os

app = Flask(__name__)
app.secret_key = 'value-project-2025'  

# 登入畫面
@app.route('/')
def index():
    """首頁 - 主要入口"""
    return render_template('Index.html')

#首頁
@app.route('/homepage')
def home():
    """首頁路由"""
    return render_template('homepage.html')

# 搜尋頁面
@app.route('/search')
def search():
    """搜尋頁面"""
    return render_template('search.html')


#第一階段搜尋結果  (ver01)
@app.route('/search/result')
def search_result():
    """搜尋結果頁面"""
    query = request.args.get('q', '')
    
    try:
        if query:
            # 使用關鍵字搜尋配方
            results_df = search_recipes(query)
        else:
            # 如果沒有關鍵字，顯示所有配方
            results_df = get_all_recipes()
        
        # 轉換DataFrame為字典列表，只取需要的欄位
        results = []
        for _, row in results_df.iterrows():
            results.append({
                'code': row['recipe_id'],  # 貨品編號對應 recipe_id
                'company': row['recipe_name'],  # 公司對應 recipe_name（之後改為配方名稱）
                'name': row['recipe_type']  # 食品名稱對應 recipe_type（之後改為配方類型）
            })
        
        return render_template('search_result.html', query=query, results=results)
    
    except Exception as e:
        print(f"搜尋錯誤: {e}")
        return render_template('search_result.html', query=query, results=[], error="搜尋時發生錯誤")


#(暫用)
# 在 app.py 中新增這些除錯路由：

@app.route('/debug/db')
def debug_db():
    """測試資料庫連線"""
    try:
        from database.operations import get_db_connection
        engine = get_db_connection()
        
        # 測試連線
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            test_result = result.fetchone()
            
        return jsonify({
            'status': 'success',
            'message': '資料庫連線成功',
            'test_query': test_result[0] if test_result else None
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'資料庫連線失敗: {str(e)}'
        })

@app.route('/debug/tables')
def debug_tables():
    """檢查資料表是否存在"""
    try:
        from database.operations import get_db_connection
        engine = get_db_connection()
        
        with engine.connect() as conn:
            # 檢查 BOM 表是否存在
            result = conn.execute("SHOW TABLES LIKE 'group4_bom'")
            bom_exists = result.fetchone() is not None
            
            # 檢查 materials 表是否存在
            result = conn.execute("SHOW TABLES LIKE 'group4_materials'")
            materials_exists = result.fetchone() is not None
            
            # 如果表存在，檢查資料數量
            bom_count = 0
            materials_count = 0
            
            if bom_exists:
                result = conn.execute("SELECT COUNT(*) FROM group4_bom")
                bom_count = result.fetchone()[0]
            
            if materials_exists:
                result = conn.execute("SELECT COUNT(*) FROM group4_materials")
                materials_count = result.fetchone()[0]
        
        return jsonify({
            'status': 'success',
            'tables': {
                'group4_bom': {
                    'exists': bom_exists,
                    'count': bom_count
                },
                'group4_materials': {
                    'exists': materials_exists,
                    'count': materials_count
                }
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'檢查資料表失敗: {str(e)}'
        })

@app.route('/debug/sample')
def debug_sample():
    """取得樣本資料"""
    try:
        from database.operations import get_all_recipes
        
        # 取得前 5 筆資料
        df = get_all_recipes()
        
        if df.empty:
            return jsonify({
                'status': 'warning',
                'message': '資料表是空的',
                'data': []
            })
        
        # 轉換為字典格式
        sample_data = df.head(5).to_dict('records')
        
        return jsonify({
            'status': 'success',
            'message': f'找到 {len(df)} 筆資料',
            'sample_data': sample_data,
            'columns': list(df.columns)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'取得樣本資料失敗: {str(e)}'
        })

#(暫用結束)
#最終階段搜尋結果
@app.route('/search/result/final')
def search_result_final():
    """最終搜尋結果頁面"""
    return render_template('search_result_final.html')


# AI 聊天機器人
@app.route('/chatbot')
def chatbot():
    """聊天機器人頁面"""
    return render_template('chatbot.html')


#其他-------------------------------------------------------------
@app.route('/api/chat', methods=['POST'])
def chat_api():
    """聊天機器人 API"""
    data = request.get_json()
    message = data.get('message', '')
    # 這裡整合 AI 聊天邏輯
    response = {"response": f"您說: {message}"}
    return jsonify(response)

# API 路由
@app.route('/api/search', methods=['POST'])
def api_search():
    """搜尋 API"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    # 這裡整合搜尋邏輯
    results = [
        {"id": 1, "name": "咖啡粉", "description": "高品質咖啡粉"},
        {"id": 2, "name": "拿鐵沖泡包", "description": "方便沖泡的拿鐵包"}
    ]
    return jsonify({"results": results, "keyword": keyword})

 # 啟動伺服器
if __name__ == '__main__':
    app.run(debug=True) 
