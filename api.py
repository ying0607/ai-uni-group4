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
            """計算半成品配方的總成本 - 改進版"""
            try:
                print(f"計算半成品 {recipe_id} 的成本...")
                
                sub_steps_df =  db_ops.get_recipe_steps(recipe_id)
                if sub_steps_df.empty:
                    print(f"半成品 {recipe_id} 沒有配方步驟")
                    return 0
                
                sub_total_cost = 0
                
                for _, sub_step in sub_steps_df.iterrows():
                    sub_material_code = sub_step.get('material_code', '')
                    sub_quantity = sub_step.get('quantity', 0)
                    
                    # 嚴格的數值驗證
                    try:
                        sub_quantity = float(sub_quantity) if sub_quantity and str(sub_quantity).lower() != 'nan' else 0
                    except (ValueError, TypeError):
                        sub_quantity = 0
                        
                    if sub_quantity <= 0:
                        continue
                        
                    if sub_material_code:
                        if sub_material_code.startswith('F'):
                            # 遞迴計算F配方成本 (需要設定遞迴深度限制)
                            sub_recipe_cost = calculate_sub_recipe_cost(sub_material_code)
                            sub_total_cost += sub_recipe_cost * sub_quantity
                            print(f"  F配方 {sub_material_code}: 成本 {sub_recipe_cost}, 用量 {sub_quantity}, 小計 {sub_recipe_cost * sub_quantity}")
                        else:
                            # 一般材料
                            material_info =  db_ops.get_material_by_code(sub_material_code)
                            if material_info:
                                sub_unit_price = material_info.get('unit_price_wo_tax', 0) or 0
                                try:
                                    sub_unit_price = float(sub_unit_price) if sub_unit_price and str(sub_unit_price).lower() != 'nan' else 0
                                except (ValueError, TypeError):
                                    sub_unit_price = 0
                                    
                                item_cost = sub_unit_price * sub_quantity
                                sub_total_cost += item_cost
                                print(f"  一般材料 {sub_material_code}: 單價 {sub_unit_price}, 用量 {sub_quantity}, 小計 {item_cost}")
                
                print(f"半成品 {recipe_id} 總成本: {sub_total_cost}")
                return sub_total_cost
                
            except Exception as e:
                print(f"計算半成品 {recipe_id} 成本時發生錯誤: {e}")
                return 0

        # 處理步驟資料
        ingredients = []
        total_cost = 0
        
        for _, step in steps_df.iterrows():
            material_code = step.get('material_code', '')
            material_name = step.get('material_name', '')
            quantity = step.get('quantity', 0)
            unit_price = 0
            characteristic = ''
            is_sub_recipe = False
            
            # 嚴格的數量驗證
            try:
                quantity = float(quantity) if quantity and str(quantity).lower() != 'nan' else 0
            except (ValueError, TypeError):
                quantity = 0

            if material_code:
                if material_code.startswith('F'):
                    # F開頭的是半成品配方
                    sub_recipe = db_ops.get_recipe_by_id(material_code)
                    if sub_recipe:
                        material_name = sub_recipe.get('recipe_name', material_name)
                        is_sub_recipe = True
                        
                        # 計算該半成品的單位成本
                        if quantity > 0:
                            sub_recipe_total_cost = calculate_sub_recipe_cost(material_code)
                            unit_price = sub_recipe_total_cost  # F配方的"單價"就是其總成本
                        else:
                            unit_price = 0
                            
                        characteristic = '此為半成品配方'
                        print(f"半成品 {material_code}: 總成本 {unit_price}, 用量 {quantity}")

                elif material_code.startswith('G'):
                    # G開頭的是成品配方 (通常不會在配方中出現，但以防萬一)
                    sub_recipe = db_ops.get_recipe_by_id(material_code)
                    if sub_recipe:
                        material_name = sub_recipe.get('recipe_name', material_name)
                        is_sub_recipe = True
                        characteristic = '此為成品配方'
                        unit_price = 0  # G配方通常不計入成本
                else:
                    # 一般材料處理
                    material_info = db_ops.get_material_by_code(material_code)
                    if material_info:
                        unit_price = material_info.get('unit_price_wo_tax', 0) or 0
                        characteristic = material_info.get('characteristic', '') or ''
                        
                        # 嚴格的單價驗證
                        try:
                            unit_price = float(unit_price) if unit_price and str(unit_price).lower() != 'nan' else 0
                        except (ValueError, TypeError):
                            unit_price = 0
            
            # 成本計算
            try:
                cost = unit_price * quantity if unit_price > 0 and quantity > 0 else 0
                
                # 確保不是 NaN
                if str(cost).lower() == 'nan' or cost != cost:
                    cost = 0
                    
                total_cost += cost
                print(f"項目 {material_code}: 單價 {unit_price}, 用量 {quantity}, 成本 {cost}")
                
            except (ValueError, TypeError):
                cost = 0
            
            ingredients.append({
                "step_order": step.get('step_order', ''),
                "material_code": material_code,
                "material_name": material_name,
                "unit": step.get('unit', ''),
                "quantity": quantity,
                "product_base": step.get('product_base', ''),
                "notes": step.get('notes', ''),
                "unit_price": unit_price,
                "cost": round(cost, 2),
                "characteristic": characteristic,
                "is_sub_recipe": is_sub_recipe
            })
        
        print(f"配方 {recipe_id} 總成本: {total_cost}")
        
        # 處理注意事項 - 過濾空值和重複內容（修正版）
        print(f"\n=== 🔍 開始處理配方 {recipe_id} 的注意事項 ===")
        print(f"steps_df 基本資訊:")
        print(f"   - 資料筆數: {len(steps_df)}")
        print(f"   - 是否包含 precaution 欄位: {'precaution' in steps_df.columns}")

        notices = []
        precaution_raw_data = []

        # 修正：確保能看到所有步驟的處理過程
        for index, step in steps_df.iterrows():
            precaution = step.get('precaution', '')
            material_code = step.get('material_code', '')
            material_name = step.get('material_name', '')
            
            # 記錄每一步的原始資料
            precaution_raw_data.append({
                'step': len(precaution_raw_data) + 1,  # 使用序號而非 index
                'material_code': material_code,
                'material_name': material_name,
                'precaution_raw': repr(precaution),
                'precaution_type': type(precaution).__name__
            })
            
            print(f"步驟 {len(precaution_raw_data)} - {material_code}: 原始注意事項 = {repr(precaution)} (類型: {type(precaution).__name__})")
            
            if precaution and str(precaution).strip() and str(precaution).lower() != 'nan':
                precaution_clean = str(precaution).strip()
                print(f"  ✅ 有效注意事項: '{precaution_clean}'")
                
                if precaution_clean not in notices:
                    notices.append(precaution_clean)
                    print(f"  ➕ 新增到列表 (目前共 {len(notices)} 項)")
                else:
                    print(f"  ⚠️  重複內容，已跳過")
            else:
                print(f"  ❌ 無效注意事項 (空值、null 或 NaN)")

        print(f"\n📊 注意事項處理結果:")
        print(f"   - 總步驟數: {len(steps_df)}")
        print(f"   - 有效注意事項數量: {len(notices)}")
        print(f"   - 最終注意事項列表: {notices}")

        # ✅ 修正：顯示所有原始資料
        print(f"\n📋 原始資料詳細報告:")
        for item in precaution_raw_data:
            print(f"   步驟 {item['step']}: {item['material_code']} | 類型: {item['precaution_type']} | 值: {item['precaution_raw']}")

        print(f"=== 注意事項處理完成 ===\n")
        
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
            "total_cost": round(total_cost, 2),
            "notices": notices  # 新增這行
            
        }
        print(f"🚀 API 回應資料中的 notices: {response_data.get('notices', 'NOT_FOUND')}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"取得配方詳細資料時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500   