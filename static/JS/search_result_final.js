//配方資料表自動新增資料
class IngredientsTableController {
    constructor(tableSelector) {
        this.table = document.querySelector(tableSelector);
        this.thead = this.table.querySelector('thead tr');
        this.tbody = this.table.querySelector('tbody') || this.createTbody();
        this.tfoot = this.table.querySelector('tfoot') || this.createTfoot();
        
        // 取得現有的表頭欄位
        this.columns = this.getExistingColumns();
        
        // 初始化點擊事件
        this.initClickEvents();
    }

    createTbody() {
        const tbody = document.createElement('tbody');
        this.table.appendChild(tbody);
        return tbody;
    }

    createTfoot() {
        const tfoot = document.createElement('tfoot');
        tfoot.innerHTML = `
            <tr class="total-row">
                <th colspan="8">總成本</th>
                <th id="total-cost">$0.00</th>
            </tr>
        `;
        this.table.appendChild(tfoot);
        return tfoot;
    }

    // 取得現有表頭的欄位配置
    getExistingColumns() {
        const ths = this.thead.querySelectorAll('th');
        return Array.from(ths).map(th => ({
            title: th.textContent.trim(),
            element: th
        }));
    }

    // 初始化點擊事件
    initClickEvents() {
    this.tbody.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (row && !row.classList.contains('sub-recipe-row')) {  // 🔥 排除半成品行
            const materialCode = row.getAttribute('data-material-code');
            if (materialCode) {
                this.showDetailPanel(materialCode, row);
            }
        }
    });
}

    // 處理後端資料
    loadRecipeData(recipeId) {
        if (!recipeId) {
            console.error('Recipe ID not provided');
            return;
        }

        // 顯示載入狀態
        this.showLoading();

        // 從後端獲取配方詳細資料
        fetch(`/api/recipe/${recipeId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                this.updateRecipeDetails(data.recipe_details);
                this.addDataRows(data.ingredients);
                this.updateTotalCost(data.total_cost);
            })
            .catch(error => {
                console.error('Error loading recipe data:', error);
                this.showError('載入配方資料時發生錯誤: ' + error.message);
            });
    }

    // 更新配方詳細資料
    updateRecipeDetails(recipeDetails) {
        const updates = {
            'product-code': recipeDetails.recipe_id,
            'product-name': recipeDetails.recipe_name,
            'version': recipeDetails.version || 'N/A',
            'standard-hours': recipeDetails.standard_hours || 'N/A',
            'specification': recipeDetails.specification || 'N/A',
            'document-note': recipeDetails.notes || 'N/A',
            'create-date': recipeDetails.created_at || 'N/A'
        };

        Object.entries(updates).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    // 更新總成本
    updateTotalCost(totalCost) {
        const totalElement = document.getElementById('total-cost');
        if (totalElement) {
            totalElement.textContent = `$${totalCost.toFixed(2)}`;
        }
    }

    // 顯示載入狀態
    showLoading() {
        this.tbody.innerHTML = '<tr class="loading"><td colspan="9">載入中...</td></tr>';
        
        // 更新配方詳細資料為載入中
        ['product-code', 'product-name', 'version', 'standard-hours', 
         'specification', 'document-note', 'create-date'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '載入中...';
            }
        });
    }

    // 顯示錯誤
    showError(message) {
        this.tbody.innerHTML = `<tr class="error"><td colspan="9" style="text-align: center; color: #ff4444;">${message}</td></tr>`;
    }

    // 處理後端資料，只新增資料列
    addDataRows(backendData) {
        if (!backendData || !Array.isArray(backendData)) {
            console.warn('無效資料');
            return;
        }

        // 清空現有資料
        this.tbody.innerHTML = '';
        
        // 新增每一列資料
        backendData.forEach((item, index) => {
            this.addRow(item, index);
        });
    }

    // 新增單一資料列
    addRow(item, index = 0) {
        const row = document.createElement('tr');
        row.setAttribute('data-material-code', item.material_code || '');
        row.classList.add('clickable-row');
        
        // 🔥 如果是半成品，添加特殊標記和點擊處理
        if (item.is_sub_recipe) {
            row.classList.add('sub-recipe-row');
            row.setAttribute('data-sub-recipe', item.material_code);
            
            // 🔥 為半成品行添加特殊點擊事件
            row.addEventListener('click', (e) => {
                e.stopPropagation(); // 防止觸發一般的詳細面板
                window.location.href = `/search/result/final/${item.material_code}`;
            });
        }
        
        row.dataset.materialData = JSON.stringify(item);
        
        const materialCode = item.material_code || '';
        if (materialCode && (materialCode.startsWith('F') || materialCode.startsWith('M'))) {
            row.setAttribute('data-code', materialCode);
        }
        
        this.columns.forEach(column => {
            const td = document.createElement('td');
            const cellValue = this.getCellValue(column.title, item, index);
            
            if (column.title === '原料名稱' && item.is_sub_recipe) {
                td.innerHTML = `${cellValue} `;
                td.style.cursor = 'pointer';
                td.style.fontWeight = '500';
            } else {
                td.textContent = cellValue;
            }
            
            row.appendChild(td);
        });
        
        this.tbody.appendChild(row);
    }

    // 根據欄位標題取得對應的資料值
    getCellValue(columnTitle, item, index) {
        switch(columnTitle) {
            case '步驟':
                return index + 1;
            case '原料編號':
                return item.material_code || '';
            case '原料名稱':
                return item.material_name || '';
            case '單位':
                return item.unit || '';
            case '原料用量':
                return item.quantity ? parseFloat(item.quantity).toString() : '';
            case '產品基數':
                return item.product_base ? parseFloat(item.product_base).toString() : '';
            case '附註':
                return item.notes || '';
            case '單價未稅':
                return item.unit_price ? `$${parseFloat(item.unit_price).toFixed(2)}` : '$0.00';
            case '成本':
                return item.cost ? `$${parseFloat(item.cost).toFixed(2)}` : '$0.00';
            default:
                return '';
        }
    }

    // 顯示詳細面板
    showDetailPanel(materialCode, row) {
        const cells = row.querySelectorAll('td');
        
        // 取得完整資料
        let itemData = {};
        try {
            itemData = JSON.parse(row.dataset.materialData);
        } catch (e) {
            console.warn('無法解析完整資料');
        }
        
        // 更新標題
        document.getElementById('detailTitle').textContent = 
            `${cells[2]?.textContent} (${cells[1]?.textContent})`;
        
        // 更新基本資料欄位
        const updates = {
            'detail-step': cells[0]?.textContent || '',
            'detail-code': cells[1]?.textContent || '',
            'detail-name': cells[2]?.textContent || '',
            'detail-unit': cells[3]?.textContent || '',
            'detail-quantity': cells[4]?.textContent || '',
            'detail-base': cells[5]?.textContent || '',
            'detail-notes': cells[6]?.textContent || '無',
            'detail-price': cells[7]?.textContent || '',
            'detail-cost': cells[8]?.textContent || ''
        };
        
        Object.entries(updates).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        // 🔥 更新原料特性
        const characteristicElement = document.getElementById('more-info');
            if (characteristicElement) {
                const characteristic = itemData.characteristic || '暫無特性資料';
                characteristicElement.textContent = characteristic;

                const keywords = ['標示', '過敏原', '特性','甜度', '顆粒', '溶解性', '食品添加物'];
                let formattedText = characteristic;

                keywords.forEach(keyword => {
                    const regex = new RegExp(`(${keyword}[:：]\\s*)`, 'g');
                    formattedText = formattedText.replace(regex, '<br>$1');
                });

                formattedText = formattedText
                    .replace(/^<br>/, '')  // 移除開頭換行
                    .replace(/<br>\s*<br>/g, '<br>')  // 移除重複換行
                    .trim();

                characteristicElement.innerHTML = formattedText;
            } else {
                console.warn('找不到 detail-characteristic 元素');
        }
        
        // 顯示面板
        document.getElementById('detailPanel').classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    // 從目前資料中尋找原料資料
    findMaterialData(materialCode) {
        const row = this.tbody.querySelector(`tr[data-material-code="${materialCode}"]`);
        if (!row) return null;

        const cells = row.querySelectorAll('td');
        return {
            material_code: materialCode,
            material_name: cells[2]?.textContent || '',
            unit: cells[3]?.textContent || '',
            quantity: cells[4]?.textContent || '',
            product_base: cells[5]?.textContent || '',
            notes: cells[6]?.textContent || '',
            unit_price: cells[7]?.textContent || '',
            cost: cells[8]?.textContent || '',
            material_details: this.getMaterialDetails(materialCode),
            material_properties: this.getMaterialProperties(materialCode)
        };
    }

    // 獲取原料詳細資訊（模擬資料）
    getMaterialDetails(materialCode) {
        return {
            supplier: '資料待補充',
            origin: '資料待補充',
            shelf_life: '資料待補充',
            storage_condition: '資料待補充'
        };
    }

    // 獲取原料特性（模擬資料）
    getMaterialProperties(materialCode) {
        return [
            '詳細特性資料待補充',
            '請聯繫品管部門了解更多資訊'
        ];
    }

    // 更新詳細面板內容
    updateDetailPanelContent(materialData) {
        const detailTitle = document.getElementById('detailTitle');
        if (detailTitle) {
            detailTitle.textContent = `${materialData.material_name} (${materialData.material_code})`;
        }

        const basicInfoElement = document.querySelector('.detail-info:first-child p');
        if (basicInfoElement && materialData.material_details) {
            const details = materialData.material_details;
            const basicInfoHTML = `
                <strong>原料編號：</strong>${materialData.material_code}<br>
                <strong>原料名稱：</strong>${materialData.material_name}<br>
                <strong>供應商：</strong>${details.supplier}<br>
                <strong>產地：</strong>${details.origin}<br>
                <strong>保存期限：</strong>${details.shelf_life}<br>
                <strong>儲存條件：</strong>${details.storage_condition}<br>
                <strong>單位：</strong>${materialData.unit}<br>
                <strong>單價：</strong>${materialData.unit_price}
            `;
            basicInfoElement.innerHTML = basicInfoHTML;
        }

        const propertiesElement = document.querySelector('.detail-info:last-child p');
        if (propertiesElement && materialData.material_properties) {
            const propertiesHTML = materialData.material_properties
                .map(property => `• ${property}`)
                .join('<br>');
            propertiesElement.innerHTML = propertiesHTML;
        }
    }

    // 開啟詳細面板
    openDetailPanel() {
        const detailPanel = document.getElementById('detailPanel');
        if (detailPanel) {
            detailPanel.classList.add('open');
        }
        document.body.style.overflow = 'hidden';
    }
}

// 從 URL 獲取配方 ID
function getRecipeIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    const finalIndex = pathParts.indexOf('final');
    if (finalIndex !== -1 && finalIndex < pathParts.length - 1) {
        return pathParts[finalIndex + 1];
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('recipe_id');
}

// 關閉詳細資料視窗 
function closeDetailPanel() {
    const detailPanel = document.getElementById('detailPanel');
    if (detailPanel) {
        detailPanel.classList.remove('open');
    }
    document.body.style.overflow = '';
}

// 點擊背景關閉面板
function setupOverlayClick() {
    const overlay = document.getElementById('detailPanelOverlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeDetailPanel();
            }
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化配方表格控制器
    window.ingredientsController = new IngredientsTableController('.ingredients-table');
    
    // 設置背景點擊關閉功能
    setupOverlayClick();
    
    // 獲取配方 ID 並載入真實資料
    const recipeId = getRecipeIdFromUrl();
    if (recipeId) {
        window.ingredientsController.loadRecipeData(recipeId);
    } else {
        console.warn('No recipe ID found in URL');
    }
});