
//側邊欄收合
const sidebarToggle = safeGetElement('sidebar-toggle', 'sidebar initialization');
const sidebar = safeGetElement('sidebar', 'sidebar initialization');
const logo = safeGetElement('logo', 'sidebar initialization');
const navLeft = safeGetElement('nav-left', 'sidebar initialization');

// Function to create cloned elements for the nav bar
function createNavElements() {
    return safeExecute(() => {
        if (!sidebarToggle || !logo || !navLeft) {
            console.warn('Cannot create nav elements: missing required elements');
            return;
        }
        
        // Clone the sidebar toggle button
        const clonedToggle = sidebarToggle.cloneNode(true);
        clonedToggle.id = 'nav-sidebar-toggle';
        clonedToggle.addEventListener('click', toggleSidebar);
        
        // Clone the logo
        const clonedLogo = logo.cloneNode(true);
        clonedLogo.id = 'nav-logo';
        
        // Clear existing elements
        navLeft.innerHTML = '';
        
        // Add the cloned elements to the nav
        navLeft.appendChild(clonedToggle);
        navLeft.appendChild(clonedLogo);
    }, 'createNavElements');
}

function toggleSidebar() {
    return safeExecute(() => {
        if (!sidebar) {
            console.warn('Cannot toggle sidebar: sidebar element not found');
            return;
        }
        
        sidebar.classList.toggle('sidebar-collapsed');
        
        if (sidebar.classList.contains('sidebar-collapsed')) {
            createNavElements();
        } else {
            if (navLeft) {
                navLeft.innerHTML = ''; // Clear the nav left area when sidebar is expanded
            }
        }
    }, 'toggleSidebar');
}

// Safely add event listener
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
}

// 側邊欄搜尋功能
const searchToggle = safeGetElement('search-toggle', 'search initialization');
const sidebarSearchContainer = safeGetElement('sidebar-search-container', 'search initialization');
const sidebarSearchInput = safeGetElement('sidebar-search-input', 'search initialization');

if (searchToggle && sidebarSearchContainer && sidebarSearchInput) {
    searchToggle.addEventListener('click', () => {
        safeExecute(() => {
            sidebarSearchContainer.style.display = sidebarSearchContainer.style.display === 'block' ? 'none' : 'block';
            if (sidebarSearchContainer.style.display === 'block') {
                sidebarSearchInput.focus();
            }
        }, 'search toggle');
    });
}

/// Enhanced hover effects for icons (optional)
document.querySelectorAll('.action-item').forEach(item => {
    // Add hover effect to show tooltip
    item.addEventListener('mouseenter', function() {
        // You can add custom tooltip logic here if needed
        // The tooltip is already handled by the title attribute
    });
    
    item.addEventListener('mouseleave', function() {
        // Clean up any custom tooltip logic here
    });
});

// Update the "Add new conversation" button functionality for 小江解
const addNewChatBtn = document.querySelector('.add-icon');
if (addNewChatBtn) {
    addNewChatBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        
        const submenu = safeGetElement('xiaojiangjie-submenu', 'add new chat');
        if (submenu) {
            const newChatName = prompt('請輸入新對話名稱:', '新對話');
            if (newChatName && newChatName.trim() !== '') {
                addNewSubmenuItem(submenu, newChatName.trim());
            }
        }
    });
}

// Function to dynamically add new submenu items with icon actions
function addNewSubmenuItem(parentSubmenu, itemText) {
    return safeExecute(() => {
        const newItem = document.createElement('div');
        newItem.className = 'submenu-item';
        
        newItem.innerHTML = `
            <span class="submenu-item-text">${itemText}</span>
            <div class="more-actions">⋯
                <div class="action-menu">
                    <div class="action-item" title="重新命名">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.499.499 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11l.178-.178z"/>
                        </svg>
                    </div>
                    <div class="action-item delete" title="刪除">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                            <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                        </svg>
                    </div>
                </div>
            </div>
        `;
        
        parentSubmenu.appendChild(newItem);
        
        // Attach event listeners to the new item
        attachActionMenuListeners(newItem);
        
    }, 'addNewSubmenuItem');
}

// Function to attach event listeners to action menu items
function attachActionMenuListeners(containerElement) {
    return safeExecute(() => {
        // Attach more-actions button listener
        const moreActionsBtn = containerElement.querySelector('.more-actions');
        if (moreActionsBtn) {
            moreActionsBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                
                // Close all other menus first
                document.querySelectorAll('.action-menu').forEach(menu => {
                    if (menu !== this.querySelector('.action-menu')) {
                        menu.classList.remove('show');
                    }
                });
                
                // Toggle this menu
                this.querySelector('.action-menu').classList.toggle('show');
            });
        }
        
        // Attach rename action listener
        const renameBtn = containerElement.querySelector('.action-item:not(.delete)');
        if (renameBtn) {
            renameBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const menuItem = this.closest('.submenu-item');
                const textElement = menuItem.querySelector('.submenu-item-text');
                const currentName = textElement.textContent;
                
                const newName = prompt('請輸入新名稱:', currentName);
                if (newName && newName.trim() !== '') {
                    textElement.textContent = newName;
                }
                
                this.closest('.action-menu').classList.remove('show');
            });
        }
        
        // Attach delete action listener
        const deleteBtn = containerElement.querySelector('.action-item.delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const menuItem = this.closest('.submenu-item');
                const textElement = menuItem.querySelector('.submenu-item-text');
                
                if (confirm(`確定要刪除 "${textElement.textContent}" 嗎？`)) {
                    menuItem.style.transition = 'opacity 0.3s ease';
                    menuItem.style.opacity = '0';
                    
                    setTimeout(() => {
                        menuItem.remove();
                    }, 300);
                }
                
                this.closest('.action-menu').classList.remove('show');
            });
        }
        
        //Attach submenu item click listener
        containerElement.addEventListener('click', function(e) {
            // Only trigger if not clicking on more-actions or action menu items
            if (!e.target.closest('.more-actions') && !e.target.closest('.action-menu')) {
                const textElement = this.querySelector('.submenu-item-text');
                console.log('Clicked on:', textElement.textContent);
                // Add your submenu item click logic here
            }
        });
        
    }, 'attachActionMenuListeners');

}


// Close menus when clicking elsewhere
document.addEventListener('click', function() {
    document.querySelectorAll('.action-menu').forEach(menu => {
        menu.classList.remove('show');
    });
});

// 對話紀錄_重新命名
document.querySelectorAll('.action-item:not(.delete)').forEach(item => {
    item.addEventListener('click', function(e) {
        e.stopPropagation();
        const menuItem = this.closest('.submenu-item');
        const textElement = menuItem.querySelector('.submenu-item-text');
        const currentName = textElement.textContent;
        
        const newName = prompt('請輸入新名稱:', currentName);
        if (newName && newName.trim() !== '') {
            textElement.textContent = newName;
        }
        
        // Close the menu
        this.closest('.action-menu').classList.remove('show');
    });
});

// 對話紀錄_刪除
document.querySelectorAll('.action-item.delete').forEach(item => {
    item.addEventListener('click', function(e) {
        e.stopPropagation();
        const menuItem = this.closest('.submenu-item');
        const textElement = menuItem.querySelector('.submenu-item-text');
        
        if (confirm(`確定要刪除 "${textElement.textContent}" 嗎？`)) {
            // Add fade out animation before removing
            menuItem.style.transition = 'opacity 0.3s ease';
            menuItem.style.opacity = '0';
            
            setTimeout(() => {
                menuItem.remove();
            }, 300);
        }
        
        // Close the menu
        this.closest('.action-menu').classList.remove('show');
    });
});

// Add click event to submenu items
document.querySelectorAll('.submenu-item').forEach(item => {
    item.addEventListener('click', function() {
        console.log('Clicked on:', this.querySelector('.submenu-item-text').textContent);
        // Add your submenu item click logic here
    });
});

// Member dropdown functionality
const memberIcon = safeGetElement('member-icon', 'member dropdown initialization');
const memberDropdown = safeGetElement('member-dropdown', 'member dropdown initialization');

if (memberIcon && memberDropdown) {
    memberIcon.addEventListener('click', () => {
        safeExecute(() => {
            memberDropdown.classList.toggle('show');
        }, 'member dropdown toggle');
    });
}

// Close the dropdown if clicked outside
window.addEventListener('click', (event) => {
    safeExecute(() => {
        if (!event.target.matches('.member-icon') && !event.target.closest('.member-icon')) {
            if (memberDropdown && memberDropdown.classList.contains('show')) {
                memberDropdown.classList.remove('show');
            }
        }
    }, 'outside click handler');
});

// Handle expand/collapse for submenu with chevron arrow
const expandIcon = document.querySelector('.expand-icon');
const submenu = safeGetElement('xiaojiangjie-submenu', 'submenu initialization');

if (expandIcon && submenu) {
    expandIcon.addEventListener('click', () => {
        safeExecute(() => {
            const isExpanded = expandIcon.getAttribute('data-expanded') === 'true';
            const newExpandedState = !isExpanded;
            
            // Update the data attribute
            expandIcon.setAttribute('data-expanded', newExpandedState);
            
            // Show/hide the submenu
            submenu.style.display = newExpandedState ? 'block' : 'none';
            
            // Note: The rotation is handled by CSS based on the data-expanded attribute
        }, 'submenu toggle');
    });
    
    // Initialize the submenu state based on the initial data-expanded attribute
    const initialExpanded = expandIcon.getAttribute('data-expanded') === 'true';
    submenu.style.display = initialExpanded ? 'block' : 'none';
}

// Modal functions
function openModal() {
    return safeExecute(() => {
        const modalOverlay = safeGetElement('modalOverlay', 'openModal');
        if (modalOverlay) {
            modalOverlay.classList.add('show');
        }
    }, 'openModal');
}

function closeModal(event) {
    return safeExecute(() => {
        const modalOverlay = safeGetElement('modalOverlay', 'closeModal');
        if (!modalOverlay) return;
        
        if (!event || event.target === modalOverlay) {
            modalOverlay.classList.remove('show');
        }
    }, 'closeModal');
}

function performSearch() {
    return safeExecute(() => {
        const searchInput = document.querySelector('.search-input');
        if (!searchInput) {
            console.warn('Search input not found');
            alert('搜尋功能暫時無法使用');
            return;
        }
        
        const searchTerm = searchInput.value;
        if (searchTerm.trim()) {
            alert(`執行搜尋: "${searchTerm}"`);
        } else {
            alert('請輸入搜尋關鍵字');
        }
    }, 'performSearch');
}

function submitAdvancedSearch() {
    return safeExecute(() => {
        const productCode = safeGetElement('productCode', 'submitAdvancedSearch')?.value || '';
        const customerName = safeGetElement('customerName', 'submitAdvancedSearch')?.value || '';
        
        const searchParams = [];
        if (productCode) searchParams.push(`產品編號: ${productCode}`);
        if (customerName) searchParams.push(`客戶名稱: ${customerName}`);
        
        if (searchParams.length > 0) {
            alert(`執行進階搜尋:\n${searchParams.join('\n')}`);
            closeModal();
        } else {
            alert('請至少填寫一個搜尋條件');
        }
    }, 'submitAdvancedSearch');
}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    safeExecute(() => {
        if (event.key === 'Escape') {
            closeModal();
        }
    }, 'escape key handler');
});


// 安全執行任意程式碼
function safeExecute(fn, context = 'operation', fallback = () => {}) {
    try {
        return fn();         // 嘗試執行傳入的函式
    } catch (error) {
        console.error(`Error in ${context}:`, error);    // 有錯就印出來
        return fallback();    // 執行預設的備援動作
    }
}

// 安全取得 DOM 元素，如果不存在就警告但不報錯
function safeGetElement(id, context = '') {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with id '${id}' not found${context ? ` in ${context}` : ''}`);
    }
    return element;
}

// 初始化監聽器(避免同一個元件被重複綁定)
document.addEventListener('DOMContentLoaded', function() {
    safeExecute(() => {
        document.querySelectorAll('.submenu-item').forEach(item => {
            // Only attach if listeners aren't already attached
            if (!item.dataset.listenersAttached) {
                attachActionMenuListeners(item);
                item.dataset.listenersAttached = 'true';
            }
        });
    }, 'DOMContentLoaded initialization');
});


// 全域錯誤攔截器(錯誤顯示在 console，不因單一錯誤導致崩潰)
window.addEventListener('error', function(event) {
    console.error('Global error in search.js:', event.error);
    // Don't break the page, just log the error
    return true;
});

