// IAE Tutorials - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeSidebar();
    initializeFlashMessages();
    initializeDropdowns();
    initializeFormValidation();
    initializeTooltips();
}

// ========================================
// SIDEBAR FUNCTIONALITY
// ========================================

function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (!sidebar) return;
    
    function openSidebar() {
        sidebar.classList.add('open');
        if (overlay) overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
    
    function closeSidebar() {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('open');
        document.body.style.overflow = '';
    }
    
    function toggleSidebar() {
        if (sidebar.classList.contains('open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }
    
    // Mobile menu button
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleSidebar);
    }
    
    // Sidebar toggle button (inside sidebar)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', closeSidebar);
    }
    
    // Overlay click
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
    
    // Close sidebar on window resize if width > 768px
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });
    
    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });
    
    // Active link highlighting
    highlightActiveNavLink();
}

function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

// ========================================
// FLASH MESSAGES
// ========================================

function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(flash => {
        // Auto-dismiss after 5 seconds for success and info messages
        if (flash.classList.contains('flash-success') || flash.classList.contains('flash-info')) {
            setTimeout(() => {
                fadeOutAndRemove(flash);
            }, 5000);
        }
        
        // Close button functionality
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                fadeOutAndRemove(flash);
            });
        }
    });
}

function fadeOutAndRemove(element) {
    element.style.transition = 'opacity 0.3s ease';
    element.style.opacity = '0';
    setTimeout(() => {
        if (element.parentNode) {
            element.remove();
        }
    }, 300);
}

function showFlashMessage(message, type = 'info') {
    const container = document.querySelector('.flash-container');
    if (!container) return;
    
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.setAttribute('role', 'alert');
    
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    flash.innerHTML = `
        <span class="flash-icon">${icons[type] || icons.info}</span>
        <span class="flash-message">${escapeHtml(message)}</span>
        <button class="flash-close" onclick="this.parentElement.remove()" aria-label="Close">×</button>
    `;
    
    container.appendChild(flash);
    
    // Auto-dismiss for success and info
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            fadeOutAndRemove(flash);
        }, 5000);
    }
    
    // Close button
    flash.querySelector('.flash-close').addEventListener('click', function() {
        fadeOutAndRemove(flash);
    });
}

// ========================================
// DROPDOWNS
// ========================================

function initializeDropdowns() {
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        const dropdowns = document.querySelectorAll('.user-dropdown');
        const userMenus = document.querySelectorAll('.user-menu');
        
        let clickedInside = false;
        userMenus.forEach(menu => {
            if (menu.contains(e.target)) {
                clickedInside = true;
            }
        });
        
        if (!clickedInside) {
            dropdowns.forEach(dropdown => {
                dropdown.style.opacity = '0';
                dropdown.style.visibility = 'hidden';
            });
        }
    });
}

// ========================================
// FORM VALIDATION
// ========================================

function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
    
    // Real-time validation on input
    const inputs = document.querySelectorAll('input[data-validate], select[data-validate], textarea[data-validate]');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            validateField(this);
        });
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

function validateForm(form) {
    const fields = form.querySelectorAll('[data-validate]');
    let isValid = true;
    
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const rules = field.dataset.validate.split(' ');
    let isValid = true;
    let errorMessage = '';
    
    for (const rule of rules) {
        switch (rule) {
            case 'required':
                if (!value) {
                    isValid = false;
                    errorMessage = 'This field is required';
                }
                break;
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (value && !emailRegex.test(value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
                break;
            case 'min:6':
                if (value.length < 6) {
                    isValid = false;
                    errorMessage = 'Must be at least 6 characters';
                }
                break;
            case 'password':
                if (value && value.length < 8) {
                    isValid = false;
                    errorMessage = 'Password must be at least 8 characters';
                }
                break;
        }
        
        if (!isValid) break;
    }
    
    showFieldError(field, isValid, errorMessage);
    return isValid;
}

function showFieldError(field, isValid, message) {
    const formGroup = field.closest('.form-group');
    if (!formGroup) return;
    
    let errorElement = formGroup.querySelector('.field-error');
    
    if (!isValid) {
        field.classList.add('is-invalid');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            formGroup.appendChild(errorElement);
        }
        errorElement.textContent = message;
    } else {
        field.classList.remove('is-invalid');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

// ========================================
// EXAM FUNCTIONALITY
// ========================================

class ExamSession {
    constructor(options) {
        this.duration = options.duration || 3600; // seconds
        this.totalQuestions = options.totalQuestions || 0;
        this.onTimeUp = options.onTimeUp || (() => {});
        this.onTimerUpdate = options.onTimerUpdate || (() => {});
        
        this.timeRemaining = this.duration;
        this.timerInterval = null;
        this.isRunning = false;
        
        this.answers = {};
        this.markedQuestions = new Set();
        this.currentQuestion = 1;
    }
    
    startTimer() {
        if (this.isRunning) return;
        this.isRunning = true;
        
        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            if (this.onTimerUpdate) {
                this.onTimerUpdate(this.timeRemaining);
            }
            
            if (this.timeRemaining <= 0) {
                this.stopTimer();
                if (this.onTimeUp) {
                    this.onTimeUp();
                }
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        this.isRunning = false;
    }
    
    updateTimerDisplay() {
        const display = document.querySelector('.timer-display');
        if (!display) return;
        
        const hours = Math.floor(this.timeRemaining / 3600);
        const minutes = Math.floor((this.timeRemaining % 3600) / 60);
        const seconds = this.timeRemaining % 60;
        
        let timeString = '';
        if (hours > 0) {
            timeString = `${String(hours).padStart(2, '0')}:`;
        }
        timeString += `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        display.textContent = timeString;
        
        // Add warning classes
        display.classList.remove('warning', 'danger');
        if (this.timeRemaining <= 300) { // 5 minutes
            display.classList.add('danger');
        } else if (this.timeRemaining <= 600) { // 10 minutes
            display.classList.add('warning');
        }
    }
    
    saveAnswer(questionId, answer) {
        this.answers[questionId] = answer;
        this.updatePaletteItem(questionId, 'answered');
    }
    
    markQuestion(questionId) {
        if (this.markedQuestions.has(questionId)) {
            this.markedQuestions.delete(questionId);
            this.updatePaletteItem(questionId, this.answers[questionId] ? 'answered' : 'visited');
        } else {
            this.markedQuestions.add(questionId);
            this.updatePaletteItem(questionId, 'marked');
        }
    }
    
    updatePaletteItem(questionId, status) {
        const item = document.querySelector(`.palette-item[data-question="${questionId}"]`);
        if (!item) return;
        
        item.classList.remove('answered', 'marked', 'visited', 'current');
        item.classList.add(status);
    }
    
    navigateToQuestion(questionId) {
        this.currentQuestion = questionId;
        this.updatePaletteItem(questionId, 'current');
    }
    
    getSummary() {
        return {
            total: this.totalQuestions,
            answered: Object.keys(this.answers).length,
            marked: this.markedQuestions.size,
            unattempted: this.totalQuestions - Object.keys(this.answers).length,
            timeRemaining: this.timeRemaining
        };
    }
}

// ========================================
// TOOLTIPS
// ========================================

function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            showTooltip(this);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = element.dataset.tooltip;
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    setTimeout(() => tooltip.classList.add('show'), 10);
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
        setTimeout(() => tooltip.remove(), 200);
    }
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ========================================
// AJAX HELPERS
// ========================================

async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    if (mergedOptions.body && typeof mergedOptions.body === 'object') {
        mergedOptions.body = JSON.stringify(mergedOptions.body);
    }
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'An error occurred');
        }
        
        return data;
    } catch (error) {
        showFlashMessage(error.message, 'error');
        throw error;
    }
}

// ========================================
// EXPORT FOR GLOBAL USE
// ========================================

window.IAE = {
    showFlashMessage,
    ExamSession,
    apiRequest,
    debounce,
    throttle
};

// Add CSS for dynamic elements
const style = document.createElement('style');
style.textContent = `
    .field-error {
        color: var(--danger);
        font-size: 0.875rem;
        margin-top: 0.375rem;
    }
    
    .is-invalid {
        border-color: var(--danger) !important;
    }
    
    .is-invalid:focus {
        box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1) !important;
    }
    
    .tooltip {
        position: fixed;
        background: var(--bg-card);
        color: var(--text-primary);
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-md);
        font-size: 0.875rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-lg);
        z-index: 9999;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
        white-space: nowrap;
    }
    
    .tooltip.show {
        opacity: 1;
    }
    
    .tooltip::after {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 50%;
        transform: translateX(-50%);
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid var(--border-color);
    }
`;
document.head.appendChild(style);
