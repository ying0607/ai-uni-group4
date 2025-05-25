// 動態新增表格行的函數（修改版）
function addTableRows(data) {
    const tbody = document.querySelector('.results-table tbody');
    
    // 清空現有內容
    tbody.innerHTML = '';
    
    // 遍歷資料並創建新行
    data.forEach(item => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.classList.add('clickable-row');
        
        // 添加點擊事件
        row.addEventListener('click', function() {
            if (item.id) {
                window.location.href = `/search/result/final/${item.id}`;
            }
        });
        
        const codeCell = document.createElement('td');
        codeCell.textContent = item.code || '';
        
        const companyCell = document.createElement('td');
        companyCell.textContent = item.name || '';
        
        const nameCell = document.createElement('td');
        nameCell.textContent = item.description || '';
        
        row.appendChild(codeCell);
        row.appendChild(companyCell);
        row.appendChild(nameCell);
        
        tbody.appendChild(row);
    });
}

// 修改現有的 loadData 函數以使用真實 API
async function loadData(keyword = '') {
    try {
        showLoading();
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keyword: keyword })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            addTableRows(data.results);
        } else {
            showNoData();
        }
        
    } catch (error) {
        console.error('載入資料時發生錯誤:', error);
        showNoData();
    }
}

// 從 URL 獲取搜尋關鍵字
function getSearchKeywordFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('q') || '';
}

// 頁面載入時執行
document.addEventListener('DOMContentLoaded', function() {
    const keyword = getSearchKeywordFromUrl();
    if (keyword) {
        loadData(keyword);
    } else {
        loadData(); // 載入預設資料
    }
});