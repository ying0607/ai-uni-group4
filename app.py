from flask import Flask, render_template, request, jsonify, redirect, url_for
from database.operations import *
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



#最終階段搜尋結果

@app.route('/search/result/final/<recipe_id>')
def search_result_final_detail(recipe_id):
    """最終搜尋結果頁面（含配方ID）"""
    return render_template('search_result_final.html', recipe_id=recipe_id)


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

# 搜尋API 
@app.route('/api/search', methods=['POST'])
def api_search():
    """搜尋 API - 第一階段搜尋（只搜尋配方）"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    
    if not keyword:
        return jsonify({"error": "請輸入搜尋關鍵字"}), 400
    
    # 只搜尋配方
    recipes = search_recipes(keyword)
    results = []
    
    if not recipes.empty:
        for _, recipe in recipes.iterrows():
            results.append({
                "id": recipe['recipe_id'],
                "type": "recipe",
                "code": recipe['recipe_id'],
                "name": recipe['recipe_name'],
                "description": f"{recipe['recipe_type']} - 版本: {recipe.get('version', 'N/A')}"
            })
    
    return jsonify({"results": results, "keyword": keyword})


def calculate_sub_recipe_cost(recipe_id):
    """計算半成品配方的總成本"""
    try:
        sub_steps_df = get_recipe_steps(recipe_id)
        sub_total_cost = 0
        
        for _, sub_step in sub_steps_df.iterrows():
            sub_material_code = sub_step.get('material_code', '')
            if sub_material_code and not sub_material_code.startswith('F'):  # 避免無限遞迴
                material_info = get_material_by_code(sub_material_code)
                if material_info:
                    sub_unit_price = material_info.get('unit_price_wo_tax', 0) or 0
                    sub_quantity = sub_step.get('quantity', 0) or 0
                    
                    try:
                        sub_unit_price = float(sub_unit_price)
                        sub_quantity = float(sub_quantity)
                        sub_total_cost += sub_unit_price * sub_quantity
                    except (ValueError, TypeError):
                        pass
        
        return sub_total_cost
    except Exception as e:
        print(f"計算半成品 {recipe_id} 成本時發生錯誤: {e}")
        return 0

# 新增配方詳細資料 API
@app.route('/api/recipe/<recipe_id>')
def get_recipe_detail(recipe_id):
    """取得配方詳細資料 API"""
    try:
        # 取得配方基本資訊
        recipe = get_recipe_with_steps(recipe_id)
        
        if not recipe:
            return jsonify({"error": "找不到該配方"}), 404
        
        # 取得配方步驟（包含材料資訊）  
        steps_df = get_recipe_steps(recipe_id)
        

        f_ingredients_total_cost = 0
        f_ingredients_total_quantity = 0
        for _, step in steps_df.iterrows():
            material_code = step.get('material_code', '')
            
            if material_code and material_code.startswith('F'):
                # 取得半成品的詳細配方並計算其成本
                sub_recipe_cost = calculate_sub_recipe_cost(material_code)  # 新函數
                quantity = step.get('quantity', 0) or 0
                
                try:
                    quantity = float(quantity)
                    f_ingredients_total_cost += sub_recipe_cost * quantity
                    f_ingredients_total_quantity += quantity
                except (ValueError, TypeError):
                    pass
        
        # 計算F開頭的平均單價
        f_average_unit_price = f_ingredients_total_cost / f_ingredients_total_quantity if f_ingredients_total_quantity > 0 else 0
        
        # 處理步驟資料
        ingredients = []
        total_cost = 0
        
        for _, step in steps_df.iterrows():
            material_code = step.get('material_code', '')
            unit_price = 0
            characteristic = ''
            material_name = step.get('material_name', '')
            is_sub_recipe = False

            if material_code:
                if material_code.startswith('F'):
                    # F開頭的是半成品，從 BOM 表取得名稱
                    sub_recipe = get_recipe_by_id(material_code)
                    if sub_recipe:
                        material_name = sub_recipe.get('recipe_name', material_name)
                        is_sub_recipe = True
                        print(f"半成品 {material_code} 的配方名稱: {material_name}") 
                    else:
                        print(f"找不到半成品配方: {material_code}")  # 調試用
                    
                    unit_price = f_average_unit_price
                    characteristic = '此為半成品配方'

                else:
                    # 一般材料處理
                    material_info = get_material_by_code(material_code)
                    if material_info:
                        unit_price = material_info.get('unit_price_wo_tax', 0) or 0
                        characteristic = material_info.get('characteristic', '') or ''
            #成本計算
            quantity = step.get('quantity', 0) or 0
            
            # 加強數值驗證，避免 NaN
            try:
                unit_price = float(unit_price) if unit_price and str(unit_price).lower() != 'nan' else 0
                quantity = float(quantity) if quantity and str(quantity).lower() != 'nan' else 0
                cost = unit_price * quantity if not (unit_price == 0 and quantity == 0) else 0
                
                # 確保不是 NaN
                if str(cost).lower() == 'nan' or cost != cost:  # NaN != NaN 為 True
                    cost = 0
                    
                total_cost += cost
            except (ValueError, TypeError):
                cost = 0
            
            ingredients.append({
                "step_order": step.get('step_order', ''),
                "material_code": material_code,
                "material_name":material_name,
                "unit": step.get('unit', ''),
                "quantity": quantity,
                "product_base": step.get('product_base', ''),
                "notes": step.get('notes', ''),
                "unit_price": unit_price,
                "cost": round(cost, 2),  # 確保是數字
                "characteristic": characteristic,
                "is_sub_recipe": is_sub_recipe
            })
        
        # 組裝回應資料
        response_data = {
            "recipe_details": {
                "recipe_id": recipe.get('recipe_id', ''),
                "recipe_name": recipe.get('recipe_name', ''),
                "version": recipe.get('version', ''),
                "standard_hours": recipe.get('standard_hours', ''),
                "specification": recipe.get('specification', ''),
                "notes": recipe.get('notes', ''),
                "created_at": recipe.get('created_at', '').strftime('%Y-%m-%d') if recipe.get('created_at') else ''
            },
            "ingredients": ingredients,
            "total_cost": round(total_cost, 2)
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    

 # 啟動伺服器

if __name__ == '__main__':
    app.run(debug=True) 