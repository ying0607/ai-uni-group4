// login.js - 登入頁面功能
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const usernameError = document.getElementById('usernameError');
    const passwordError = document.getElementById('passwordError');
    const loginErrorMessage = document.getElementById('loginErrorMessage');
    const forgotPasswordLink = document.getElementById('forgotPassword');

    // Initially hide all error elements
    usernameError.style.display = 'none';
    passwordError.style.display = 'none';
    loginErrorMessage.style.display = 'none';

    // Form submission handler
    loginForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Reset error states
        usernameError.style.display = 'none';
        passwordError.style.display = 'none';
        loginErrorMessage.style.display = 'none';
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        
        let hasError = false;
        
        // Validate inputs
        if (!username) {
            usernameError.style.display = 'block';
            hasError = true;
        }
        
        if (!password) {
            passwordError.style.display = 'block';
            hasError = true;
        }
        
        if (hasError) {
            loginErrorMessage.style.display = 'block';
            return;
        }
        
        fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                usernameError.style.display = 'block';
                passwordError.style.display = 'block';
                loginErrorMessage.style.display = 'block';
            }
        });
    });

    // Forgot password handler
    forgotPasswordLink.addEventListener('click', function(event) {
        event.preventDefault();
        alert('請聯繫系統管理員重設密碼。');
    });
});