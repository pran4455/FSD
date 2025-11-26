/**
 * Financial Services Dashboard - Main JavaScript
 * Handles common functionality and comprehensive validation
 */

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Update date and time display
 */
function updateDateTime() {
    const now = new Date();
    const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    const dateString = now.toLocaleDateString('en-US', options);
    const timeString = now.toLocaleTimeString('en-US');
    
    const dateTimeElement = document.getElementById('current-date-time');
    if (dateTimeElement) {
        dateTimeElement.textContent = `${dateString} | ${timeString}`;
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================================
// VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate password strength
 */
function validatePassword(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    return {
        isValid: password.length >= minLength && hasUpperCase && hasLowerCase && hasNumbers,
        length: password.length >= minLength,
        hasUpperCase,
        hasLowerCase,
        hasNumbers,
        hasSpecialChar
    };
}

/**
 * Validate username
 */
function validateUsername(username) {
    const minLength = 3;
    const maxLength = 50;
    const validPattern = /^[a-zA-Z0-9_@.-]+$/;
    
    return {
        isValid: username.length >= minLength && username.length <= maxLength && validPattern.test(username),
        minLength: username.length >= minLength,
        maxLength: username.length <= maxLength,
        validChars: validPattern.test(username)
    };
}

/**
 * Validate TOTP code
 */
function validateTOTP(code) {
    const validPattern = /^\d{6}$/;
    return validPattern.test(code);
}

/**
 * Validate stock symbol
 */
function validateStockSymbol(symbol) {
    const validPattern = /^[A-Z]{1,5}$/;
    return validPattern.test(symbol.toUpperCase());
}

/**
 * Validate number (positive)
 */
function validatePositiveNumber(value) {
    const num = parseFloat(value);
    return !isNaN(num) && num > 0;
}

/**
 * Validate required field
 */
function validateRequired(value) {
    return value !== null && value !== undefined && value.toString().trim() !== '';
}

/**
 * Sanitize input
 */
function sanitizeInput(input) {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

/**
 * Add real-time form validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // Validate on blur
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            // Re-validate on input if previously invalid
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateInput(this);
                }
            });
        });
        
        // Validate on submit
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(input => {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showAlert('Please fix the errors in the form', 'danger');
            }
        });
    });
}

/**
 * Validate individual input
 */
function validateInput(input) {
    const value = input.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Skip validation for hidden or disabled inputs
    if (input.type === 'hidden' || input.disabled) {
        return true;
    }
    
    // Check if required
    if (input.hasAttribute('required') && !validateRequired(value)) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    else if (input.type === 'email' && value) {
        if (!isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Password validation
    else if (input.type === 'password' && value && input.name === 'password') {
        const validation = validatePassword(value);
        if (!validation.isValid) {
            isValid = false;
            const errors = [];
            if (!validation.length) errors.push('at least 8 characters');
            if (!validation.hasUpperCase) errors.push('one uppercase letter');
            if (!validation.hasLowerCase) errors.push('one lowercase letter');
            if (!validation.hasNumbers) errors.push('one number');
            errorMessage = `Password must contain ${errors.join(', ')}`;
        }
    }
    
    // Username validation
    else if (input.name === 'username' && value) {
        const validation = validateUsername(value);
        if (!validation.isValid) {
            isValid = false;
            if (!validation.minLength) {
                errorMessage = 'Username must be at least 3 characters';
            } else if (!validation.maxLength) {
                errorMessage = 'Username must be less than 50 characters';
            } else if (!validation.validChars) {
                errorMessage = 'Username can only contain letters, numbers, and @.-_';
            }
        }
    }
    
    // TOTP validation
    else if (input.name === 'totp' && value) {
        if (!validateTOTP(value)) {
            isValid = false;
            errorMessage = 'TOTP code must be 6 digits';
        }
    }
    
    // Stock symbol validation
    else if (input.name === 'symbol' && value) {
        if (!validateStockSymbol(value)) {
            isValid = false;
            errorMessage = 'Stock symbol must be 1-5 uppercase letters';
        }
    }
    
    // Number validation
    else if ((input.name === 'quantity' || input.name === 'avg_cost') && value) {
        if (!validatePositiveNumber(value)) {
            isValid = false;
            errorMessage = 'Must be a positive number';
        }
    }
    
    // Min length validation
    else if (input.hasAttribute('minlength') && value) {
        const minLength = parseInt(input.getAttribute('minlength'));
        if (value.length < minLength) {
            isValid = false;
            errorMessage = `Must be at least ${minLength} characters`;
        }
    }
    
    // Max length validation
    else if (input.hasAttribute('maxlength') && value) {
        const maxLength = parseInt(input.getAttribute('maxlength'));
        if (value.length > maxLength) {
            isValid = false;
            errorMessage = `Must be less than ${maxLength} characters`;
        }
    }
    
    // Pattern validation
    else if (input.hasAttribute('pattern') && value) {
        const pattern = new RegExp(input.getAttribute('pattern'));
        if (!pattern.test(value)) {
            isValid = false;
            errorMessage = input.getAttribute('title') || 'Invalid format';
        }
    }
    
    // Update UI
    if (isValid) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        removeErrorMessage(input);
    } else {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        showErrorMessage(input, errorMessage);
    }
    
    return isValid;
}

/**
 * Show error message for input
 */
function showErrorMessage(input, message) {
    removeErrorMessage(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

/**
 * Remove error message for input
 */
function removeErrorMessage(input) {
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

// ============================================================================
// LOADING STATES
// ============================================================================

/**
 * Show loading spinner
 */
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.id = 'loading-spinner';
    
    if (element) {
        element.appendChild(spinner);
    } else {
        document.body.appendChild(spinner);
    }
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
}

// ============================================================================
// SMOOTH SCROLLING
// ============================================================================

/**
 * Initialize smooth scrolling for anchor links
 */
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// ============================================================================
// FLASH MESSAGES
// ============================================================================

/**
 * Auto-dismiss flash messages
 */
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

// ============================================================================
// FEATURE BOX INTERACTIONS
// ============================================================================

/**
 * Add click handlers to feature boxes
 */
function initFeatureBoxes() {
    const featureBoxes = document.querySelectorAll('.feature-box[data-href]');
    featureBoxes.forEach(box => {
        box.style.cursor = 'pointer';
        box.addEventListener('click', function() {
            const href = this.getAttribute('data-href');
            if (href) {
                window.location.href = href;
            }
        });
    });
}

// ============================================================================
// ROLE SELECTOR
// ============================================================================

/**
 * Initialize role selector
 */
function initRoleSelector() {
    const roleOptions = document.querySelectorAll('.role-option');
    roleOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove selected class from all options
            roleOptions.forEach(opt => opt.classList.remove('selected'));
            
            // Add selected class to clicked option
            this.classList.add('selected');
            
            // Check the radio button
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });
}

// ============================================================================
// LOCAL STORAGE UTILITIES
// ============================================================================

/**
 * Save to local storage
 */
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (e) {
        console.error('Error saving to localStorage:', e);
        return false;
    }
}

/**
 * Load from local storage
 */
function loadFromLocalStorage(key) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (e) {
        console.error('Error loading from localStorage:', e);
        return null;
    }
}

/**
 * Remove from local storage
 */
function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (e) {
        console.error('Error removing from localStorage:', e);
        return false;
    }
}

// ============================================================================
// AJAX UTILITIES
// ============================================================================

/**
 * Make AJAX request
 */
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// ============================================================================
// INPUT SANITIZATION
// ============================================================================

/**
 * Sanitize all form inputs on submit
 */
function initInputSanitization() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[type="text"], input[type="email"], textarea');
            inputs.forEach(input => {
                input.value = sanitizeInput(input.value);
            });
        });
    });
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize all functionality when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Update date/time every second
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Initialize features
    initFormValidation();
    initSmoothScrolling();
    initFlashMessages();
    initFeatureBoxes();
    initRoleSelector();
    initInputSanitization();
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.container, .page-wrapper');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    console.log('Financial Services Dashboard initialized');
});

// ============================================================================
// EXPORT FOR USE IN OTHER SCRIPTS
// ============================================================================

window.FinancialApp = {
    updateDateTime,
    showAlert,
    formatCurrency,
    formatNumber,
    debounce,
    isValidEmail,
    validatePassword,
    validateUsername,
    validateTOTP,
    validateStockSymbol,
    validatePositiveNumber,
    validateRequired,
    sanitizeInput,
    showLoading,
    hideLoading,
    saveToLocalStorage,
    loadFromLocalStorage,
    removeFromLocalStorage,
    makeRequest
};
