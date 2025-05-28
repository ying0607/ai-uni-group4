from flask import Blueprint, request, jsonify, session
from database import operations as db_ops
from backend.ai.material_search import main as material_search

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/login', methods=['POST'])
def login_api():
    """登入驗證 API"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username == 'admin' and password == 'admin123':
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"success": True, "redirect": "/homepage"})
    else:
        return jsonify({"success": False, "message": "帳號或密碼錯誤"})

@api_bp.route('/logout', methods=['POST'])
def logout_api():
    """登出 API"""
    session.clear()
    return jsonify({"success": True, "redirect": "/"})

@api_bp.route('/chat', methods=['POST'])
def chat_api():
    """聊天機器人 API"""
    data = request.get_json()
    message = data.get('message', '')
    response = {"response": f"您說: {message}"}
    return jsonify(response)


@api_bp.route('/search', methods=['POST'])
def api_search():
    """搜尋 API - 第一階段搜尋（只搜尋配方）"""
    data = request.get_json()
    keyword = data.get('keyword', '')

    if not keyword:
        return jsonify({"error": "請輸入搜尋關鍵字"}), 400

    recipes = material_search.main(keyword)
    results = []

    if not recipes.empty:
        for _, row in recipes.iterrows():
            recipe_name = row['recipe_name']  # 假設有這個欄位
            df = db_ops.search_recipe(recipe_name)
            results.append({
                "id": df['recipe_id'],
                "type": "recipe",
                "code": df['recipe_id'],
                "name": df['recipe_name'],
                "description": f"{df['recipe_type']} - 版本: {df.get('version', 'N/A')}"
            })
            
    return jsonify({"results": results, "keyword": keyword})

@api_bp.route('/recipe/<recipe_id>')
def get_recipe_detail(recipe_id):
    """取得配方詳細資料 API"""
    try:
        recipe = db_ops.get_recipe_with_steps(recipe_id)
        if not recipe:
            return jsonify({"error": "找不到該配方"}), 404

        steps_df = db_ops.get_recipe_steps(recipe_id)

        def calculate_sub_recipe_cost(recipe_id):
            try:
                sub_steps_df = db_ops.get_recipe_steps(recipe_id)
                sub_total_cost = 0
                for _, sub_step in sub_steps_df.iterrows():
                    sub_material_code = sub_step.get('material_code', '')
                    if sub_material_code and not sub_material_code.startswith('F'):
                        material_info = db_ops.get_material_by_code(sub_material_code)
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

        f_ingredients_total_cost = 0
        f_ingredients_total_quantity = 0
        for _, step in steps_df.iterrows():
            material_code = step.get('material_code', '')
            if material_code and material_code.startswith('F'):
                sub_recipe_cost = calculate_sub_recipe_cost(material_code)
                quantity = step.get('quantity', 0) or 0
                try:
                    quantity = float(quantity)
                    f_ingredients_total_cost += sub_recipe_cost * quantity
                    f_ingredients_total_quantity += quantity
                except (ValueError, TypeError):
                    pass

        f_average_unit_price = f_ingredients_total_cost / f_ingredients_total_quantity if f_ingredients_total_quantity > 0 else 0

        ingredients = []
        total_cost = 0
        # 🔥 收集注意事項
        all_precaution = []

        for _, step in steps_df.iterrows():
            material_code = step.get('material_code', '')
            unit_price = 0
            characteristic = ''
            material_name = step.get('material_name', '')
            is_sub_recipe = False

            if material_code:
                if material_code.startswith('F'):
                    sub_recipe = db_ops.get_recipe_by_id(material_code)
                    if sub_recipe:
                        material_name = sub_recipe.get('recipe_name', material_name)
                        is_sub_recipe = True
                        # 🔥 收集半成品的注意事項
                        sub_recipe_notes = sub_recipe.get('notes', '')
                        if sub_recipe_notes and sub_recipe_notes.strip():
                            all_precaution.append(f"【{material_name}】{sub_recipe_notes.strip()}")
                    unit_price = f_average_unit_price
                    characteristic = '此為半成品配方'
                else:
                    material_info = db_ops.get_material_by_code(material_code)
                    if material_info:
                        unit_price = material_info.get('unit_price_wo_tax', 0) or 0
                        characteristic = material_info.get('characteristic', '') or ''

            quantity = step.get('quantity', 0) or 0
            try:
                unit_price = float(unit_price) if unit_price and str(unit_price).lower() != 'nan' else 0
                quantity = float(quantity) if quantity and str(quantity).lower() != 'nan' else 0
                cost = unit_price * quantity if not (unit_price == 0 and quantity == 0) else 0
                if str(cost).lower() == 'nan' or cost != cost:
                    cost = 0
                total_cost += cost
            except (ValueError, TypeError):
                cost = 0

            # 🔥 收集當前步驟的注意事項
            step_precaution = step.get('precaution', '')
            if step_precaution and step_precaution.strip():
                all_precaution.append(step_precaution.strip())

            ingredients.append({
                "step_order": step.get('step_order', ''),
                "material_code": material_code,
                "material_name": material_name,
                "unit": step.get('unit', ''),
                "quantity": quantity,
                "product_base": step.get('product_base', ''),
                "notes": step.get('notes', ''),
                "precaution": step.get('precaution', ''),
                "unit_price": unit_price,
                "cost": round(cost, 2),
                "characteristic": characteristic,
                "is_sub_recipe": is_sub_recipe
            })

        # 🔥 加入主配方的注意事項
        main_recipe_notes = recipe.get('notes', '')
        if main_recipe_notes and main_recipe_notes.strip():
            all_precaution.insert(0, f"【主配方】{main_recipe_notes.strip()}")

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
            "total_cost": round(total_cost, 2),
            # 🔥 新增注意事項列表
            "precaution": all_precaution
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500