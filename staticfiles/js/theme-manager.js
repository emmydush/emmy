/**
 * Theme Manager for Smart Solution Inventory System
 * Handles dynamic theme updates and user preferences
 */

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
        this.init();
    }

    init() {
        // Apply initial theme
        this.applyTheme(this.currentTheme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (!this.getStoredTheme()) {
                this.applyTheme(this.getSystemTheme());
            }
        });
    }

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateThemeToggleIcon(theme);
        this.currentTheme = theme;
    }

    updateThemeToggleIcon(theme) {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = ''; // Clear all classes
                if (theme === 'dark') {
                    icon.classList.add('fas', 'fa-sun');
                } else if (theme === 'custom') {
                    icon.classList.add('fas', 'fa-palette');
                } else {
                    icon.classList.add('fas', 'fa-moon');
                }
            }
        }
    }

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        let next;
        
        if (current === 'light') {
            next = 'dark';
        } else if (current === 'dark') {
            next = 'light';
        } else {
            // For custom theme, toggle between light and dark
            next = 'light';
        }
        
        this.applyTheme(next);
        this.setStoredTheme(next);
    }

    applyCustomTheme(colors) {
        // Apply custom theme colors to CSS variables
        const root = document.documentElement;
        root.style.setProperty('--theme-primary', colors.primary_color);
        root.style.setProperty('--theme-secondary', colors.secondary_color);
        root.style.setProperty('--theme-accent', colors.accent_color);
        root.style.setProperty('--theme-background', colors.background_color);
        root.style.setProperty('--theme-text', colors.text_color);
        root.style.setProperty('--theme-sidebar', colors.sidebar_color);
        root.style.setProperty('--theme-card', colors.card_color);
        
        // Apply custom theme
        this.applyTheme('custom');
        this.setStoredTheme('custom');
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
    
    // Attach event listener to theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            window.themeManager.toggleTheme();
        });
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}