//配方資料表自動新增資料
class IngredientsTableController {
    constructor(tableSelector) {
        this.table = document.querySelector(tableSelector);
        this.thead = this.table.querySelector('thead tr');
        this.tbody = this.table.querySelector('tbody') || this.createTbody();
        
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
        // 使用事件委託，監聽表格點擊事件
        this.tbody.addEventListener('click', (e) => {
            const row = e.target.closest('tr');
            if (row) {
                const materialCode = row.getAttribute('data-material-code');
                if (materialCode) {
                    this.showDetailPanel(materialCode, row);
                }
            }
        });
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
        
        // 設置資料屬性和可點擊樣式
        row.setAttribute('data-material-code', item.material_code || '');
        row.classList.add('clickable-row');
        
        // 根據原料編號設置背景色
        if (item.material_code) {
            if (item.material_code.startsWith('F')) {
                row.setAttribute('data-code', item.material_code);
            } else if (item.material_code.startsWith('M')) {
                row.setAttribute('data-code', item.material_code);
            }
        }
        
        // 根據現有表頭順序建立儲存格
        this.columns.forEach(column => {
            const td = document.createElement('td');
            td.textContent = this.getCellValue(column.title, item, index);
            row.appendChild(td);
        });
        
        this.tbody.appendChild(row);
    }

    // 根據欄位標題取得對應的資料值
    getCellValue(columnTitle, item, index) {
        switch(columnTitle) {
            case '序號':
                return index + 1;
            case '原料編號':
                return item.material_code || '';
            case '原料名稱':
                return item.material_name || '';
            case '單位':
                return item.unit || '';
            case '原料用量':
                return item.quantity || '';
            case '產品數量':
                return item.product_base || '';
            case '附註':
                return item.notes || '';
            case '單價未稅':
                return item.unit_price || '';
            case '成本':
                // 計算成本：用量 × 單價
                if (item.quantity && item.unit_price) {
                    return (parseFloat(item.quantity) * parseFloat(item.unit_price)).toFixed(2);
                }
                return '';
            default:
                return '';
        }
    }

    // 顯示詳細面板
    showDetailPanel(materialCode, row) {
        // 從當前資料中找到對應的原料資訊
        const materialData = this.findMaterialData(materialCode);
        
        if (!materialData) {
            console.warn('找不到原料資料:', materialCode);
            return;
        }

        // 更新詳細面板內容
        this.updateDetailPanelContent(materialData);
        
        // 顯示詳細面板
        this.openDetailPanel();
    }

    // 從目前資料中尋找原料資料
    findMaterialData(materialCode) {
        // 這裡需要存儲完整的資料，或從後端重新獲取
        // 暫時從表格行中提取資料
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
            // 額外的詳細資訊（通常來自後端）
            material_details: this.getMaterialDetails(materialCode),
            material_properties: this.getMaterialProperties(materialCode)
        };
    }

    // 獲取原料詳細資訊（模擬後端資料）
    getMaterialDetails(materialCode) {
        // 這裡應該從後端API獲取詳細資訊
        // 暫時提供模擬資料
        const detailsMap = {
            'M001': {
                supplier: '統一麵粉廠',
                origin: '台灣',
                shelf_life: '12個月',
                storage_condition: '常溫乾燥處保存',
                protein_content: '12.5%',
                moisture_content: '14%'
            },
            'M002': {
                supplier: '統一食品',
                origin: '紐西蘭',
                shelf_life: '6個月',
                storage_condition: '冷藏保存',
                fat_content: '82%',
                salt_content: '1.2%'
            },
            'M003': {
                supplier: '大成食品',
                origin: '台灣',
                shelf_life: '28天',
                storage_condition: '冷藏保存',
                grade: 'AA級',
                weight: '60g/顆'
            }
        };
        
        return detailsMap[materialCode] || {
            supplier: '資料待補充',
            origin: '資料待補充',
            shelf_life: '資料待補充',
            storage_condition: '資料待補充'
        };
    }

    // 獲取原料特性（模擬後端資料）
    getMaterialProperties(materialCode) {
        const propertiesMap = {
            'M001': [
                '高筋麵粉適合製作麵包類產品',
                '蛋白質含量高，筋性強',
                '使用前需過篩，去除雜質',
                '建議在乾燥環境下使用'
            ],
            'M002': [
                '奶油需在室溫下軟化後使用',
                '含有豐富的乳脂肪',
                '可增加產品香味和口感',
                '開封後請盡快使用完畢'
            ],
            'M003': [
                '新鮮雞蛋，品質優良',
                '可提供蛋白質和結合性',
                '使用前請確認新鮮度',
                '建議在使用前回溫至室溫'
            ]
        };
        
        return propertiesMap[materialCode] || [
            '詳細特性資料待補充',
            '請聯繫品管部門了解更多資訊'
        ];
    }

    // 更新詳細面板內容
    updateDetailPanelContent(materialData) {
        // 更新標題
        const detailTitle = document.getElementById('detailTitle');
        if (detailTitle) {
            detailTitle.textContent = `${materialData.material_name} (${materialData.material_code})`;
        }

        // 更新原料基本資料
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
                <strong>單價：</strong>$${materialData.unit_price}
            `;
            basicInfoElement.innerHTML = basicInfoHTML;
        }

        // 更新原料特性
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
        const overlay = document.getElementById('detailPanelOverlay');
        
        if (detailPanel) {
            detailPanel.classList.add('open');
        }
        
        if (overlay) {
            overlay.classList.add('show');
        }
        
        // 防止背景滾動
        document.body.style.overflow = 'hidden';
    }

    // 清空所有資料列
    clearData() {
        this.tbody.innerHTML = '';
    }

    // 取得目前資料列數量
    getRowCount() {
        return this.tbody.querySelectorAll('tr').length;
    }

    // 測試用假資料
    getTestData() {
        return [
            {
                material_code: 'M001',
                material_name: '高筋麵粉',
                unit: 'kg',
                quantity: 2.5,
                product_base: 100,
                notes: '過篩使用',
                unit_price: 45.00
            },
            {
                material_code: 'M002',
                material_name: '奶油',
                unit: 'g',
                quantity: 500,
                product_base: 100,
                notes: '室溫軟化',
                unit_price: 0.25
            },
            {
                material_code: 'M003',
                material_name: '雞蛋',
                unit: '顆',
                quantity: 3,
                product_base: 100,
                notes: '全蛋',
                unit_price: 8.00
            }
        ];
    }

    // 載入測試資料
    loadTestData() {
        const testData = this.getTestData();
        this.addDataRows(testData);
        console.log('測試資料載入完成！');
    }
}

// 關閉詳細資料視窗 
function closeDetailPanel() {
    const detailPanel = document.getElementById('detailPanel');
    const overlay = document.getElementById('detailPanelOverlay');
    
    if (detailPanel) {
        detailPanel.classList.remove('open');
    }
    
    if (overlay) {
        overlay.classList.remove('show');
    }
    
    // 恢復背景滾動
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
    
    // 載入測試資料（在實際使用時移除）
    window.ingredientsController.loadTestData();
});