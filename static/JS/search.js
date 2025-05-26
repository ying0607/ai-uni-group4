/**
 * 簡化版 search.js - 保留核心功能，移除冗餘代碼
 */

// =============================================================================
// 工具函數
// =============================================================================
function safeGetElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element '${id}' not found`);
    }
    return element;
}

function safeExecute(fn, context = 'operation') {
    try {
        return fn();
    } catch (error) {
        console.error(`Error in ${context}:`, error);
    }
}

// =============================================================================
// 側邊欄功能
// =============================================================================
class SidebarController {
    constructor() {
        this.sidebar = safeGetElement('sidebar');
        this.navLeft = safeGetElement('nav-left');
        this.logo = safeGetElement('logo');
        this.init();
    }

    init() {
        // 側邊欄收合按鈕
        const toggleBtn = safeGetElement('sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }

        // 搜尋功能
        const searchToggle = safeGetElement('search-toggle');
        const searchContainer = safeGetElement('sidebar-search-container');
        const searchInput = safeGetElement('sidebar-search-input');
        
        if (searchToggle && searchContainer) {
            searchToggle.addEventListener('click', () => {
                const isVisible = searchContainer.style.display === 'block';
                searchContainer.style.display = isVisible ? 'none' : 'block';
                if (!isVisible && searchInput) {
                    searchInput.focus();
                }
            });
        }
    }

    toggle() {
        if (!this.sidebar) return;
        
        const isCollapsed = this.sidebar.classList.contains('sidebar-collapsed');
        
        if (isCollapsed) {
            this.sidebar.classList.remove('sidebar-collapsed');
            if (this.navLeft) this.navLeft.innerHTML = '';
        } else {
            this.sidebar.classList.add('sidebar-collapsed');
            this.createNavElements();
        }
    }

    createNavElements() {
        if (!this.navLeft || !this.logo) return;
        
        // 建立導航區域的元素
        const clonedToggle = document.querySelector('#sidebar-toggle').cloneNode(true);
        clonedToggle.id = 'nav-sidebar-toggle';
        clonedToggle.addEventListener('click', () => this.toggle());
        
        const clonedLogo = this.logo.cloneNode(true);
        clonedLogo.id = 'nav-logo';
        
        this.navLeft.innerHTML = '';
        this.navLeft.appendChild(clonedToggle);
        this.navLeft.appendChild(clonedLogo);
    }
}

// =============================================================================
// 子選單功能
// =============================================================================
class SubmenuController {
    constructor() {
        this.init();
    }

    init() {
        // 展開/收合按鈕
        const expandBtn = document.querySelector('.expand-icon');
        const submenu = safeGetElement('xiaojiangjie-submenu');
        
        if (expandBtn && submenu) {
            expandBtn.addEventListener('click', () => {
                const isExpanded = expandBtn.getAttribute('data-expanded') === 'true';
                expandBtn.setAttribute('data-expanded', !isExpanded);
                submenu.style.display = isExpanded ? 'none' : 'block';
            });
            
            // 初始狀態
            const initialExpanded = expandBtn.getAttribute('data-expanded') === 'true';
            submenu.style.display = initialExpanded ? 'block' : 'none';
        }

        // 新增對話按鈕
        const addBtn = document.querySelector('.add-icon');
        if (addBtn) {
            addBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.addNewChat();
            });
        }

        // 綁定現有項目的動作選單
        this.bindActionMenus();
    }

    addNewChat() {
        const submenu = safeGetElement('xiaojiangjie-submenu');
        if (!submenu) return;
        
        const newChatName = prompt('請輸入新對話名稱:', '新對話');
        if (newChatName && newChatName.trim()) {
            this.createSubmenuItem(submenu, newChatName.trim());
        }
    }

    createSubmenuItem(container, text) {
        const item = document.createElement('div');
        item.className = 'submenu-item';
        item.innerHTML = `
            <span class="submenu-item-text">${text}</span>
            <div class="more-actions">⋯
                <div class="action-menu">
                    <div class="action-item rename-btn" title="重新命名">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.499.499 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11l.178-.178z"/>
                        </svg>
                    </div>
                    <div class="action-item delete-btn" title="刪除">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                            <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                        </svg>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(item);
        this.bindActionMenu(item);
    }

    bindActionMenus() {
        document.querySelectorAll('.submenu-item').forEach(item => {
            this.bindActionMenu(item);
        });
    }

    bindActionMenu(item) {
        const moreBtn = item.querySelector('.more-actions');
        const actionMenu = item.querySelector('.action-menu');
        const renameBtn = item.querySelector('.rename-btn');
        const deleteBtn = item.querySelector('.delete-btn');
        const textElement = item.querySelector('.submenu-item-text');

        // 更多選項按鈕
        if (moreBtn) {
            moreBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // 關閉其他選單
                document.querySelectorAll('.action-menu').forEach(menu => {
                    if (menu !== actionMenu) menu.classList.remove('show');
                });
                actionMenu.classList.toggle('show');
            });
        }

        // 重新命名
        if (renameBtn) {
            renameBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const currentName = textElement.textContent;
                const newName = prompt('請輸入新名稱:', currentName);
                if (newName && newName.trim()) {
                    textElement.textContent = newName.trim();
                }
                actionMenu.classList.remove('show');
            });
        }

        // 刪除
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const name = textElement.textContent;
                if (confirm(`確定要刪除 "${name}" 嗎？`)) {
                    item.style.transition = 'opacity 0.3s ease';
                    item.style.opacity = '0';
                    setTimeout(() => item.remove(), 300);
                }
                actionMenu.classList.remove('show');
            });
        }

        // 項目點擊
        item.addEventListener('click', (e) => {
            if (!e.target.closest('.more-actions')) {
                console.log('選擇對話:', textElement.textContent);
                // 這裡可以加入跳轉到聊天頁面的邏輯
            }
        });
    }
}

// =============================================================================
// 會員選單功能
// =============================================================================
class MemberMenuController {
    constructor() {
        const memberIcon = safeGetElement('member-icon');
        const memberDropdown = safeGetElement('member-dropdown');
        
        if (memberIcon && memberDropdown) {
            memberIcon.addEventListener('click', () => {
                memberDropdown.classList.toggle('show');
            });
        }
    }
}

// =============================================================================
// 搜尋功能
// =============================================================================
class SearchController {
    constructor() {
        this.init();
    }

    init() {
        // 主要搜尋按鈕
        const searchButton = document.querySelector('.search-button');
        if (searchButton) {
            searchButton.addEventListener('click', () => this.performSearch());
        }

        // 搜尋輸入框 Enter 鍵
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }

    performSearch() {
        const searchInput = document.querySelector('.search-input');
        if (!searchInput) {
            alert('搜尋功能暫時無法使用');
            return;
        }
        
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
            window.location.href = `/search/result?q=${encodeURIComponent(searchTerm)}`;
        } else {
            window.location.href = '/search/result';
        }
    }
}

// =============================================================================
// 彈窗功能
// =============================================================================
class ModalController {
    constructor() {
        this.modal = safeGetElement('modalOverlay');
        this.init();
    }

    init() {
        // 進階搜尋按鈕
        const advancedBtn = document.querySelector('.advanced-search-icon');
        if (advancedBtn) {
            advancedBtn.addEventListener('click', () => this.openModal());
        }

        // 彈窗背景點擊關閉
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.closeModal();
                }
            });
        }

        // ESC 鍵關閉
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // 彈窗內的按鈕
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-cancel')) {
                this.closeModal();
            } else if (e.target.classList.contains('btn-submit')) {
                this.submitAdvancedSearch();
            }
        });
    }

    openModal() {
        if (this.modal) {
            this.modal.classList.add('show');
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('show');
        }
    }

    submitAdvancedSearch() {
        const productCode = safeGetElement('productCode')?.value || '';
        const customerName = safeGetElement('customerName')?.value || '';
        
        const params = new URLSearchParams();
        if (productCode) params.append('product_code', productCode);
        if (customerName) params.append('customer_name', customerName);
        
        if (params.toString()) {
            window.location.href = `/search/result?${params.toString()}`;
            this.closeModal();
        } else {
            alert('請至少填寫一個搜尋條件');
        }
    }
}

// =============================================================================
// 初始化
// =============================================================================
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有控制器
    new SidebarController();
    new SubmenuController();
    new MemberMenuController();
    new SearchController();
    new ModalController();

    // 關閉所有動作選單（點擊其他地方時）
    document.addEventListener('click', () => {
        document.querySelectorAll('.action-menu').forEach(menu => {
            menu.classList.remove('show');
        });
    });

    // 關閉會員下拉選單（點擊其他地方時）
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.member-dropdown')) {
            const memberDropdown = safeGetElement('member-dropdown');
            if (memberDropdown) {
                memberDropdown.classList.remove('show');
            }
        }
    });
});

// =============================================================================
// 全域函數（為了兼容現有 HTML 中的 onclick）
// =============================================================================
function openModal() {
    const modalController = new ModalController();
    modalController.openModal();
}

function closeModal() {
    const modalController = new ModalController();
    modalController.closeModal();
}

function performSearch() {
    const searchController = new SearchController();
    searchController.performSearch();
}

function submitAdvancedSearch() {
    const modalController = new ModalController();
    modalController.submitAdvancedSearch();
}