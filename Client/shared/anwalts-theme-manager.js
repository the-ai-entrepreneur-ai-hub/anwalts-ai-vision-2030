/**
 * AnwaltsAI Unified Theme Manager
 * Seamless color theme transition between landing page and dashboard
 */
class AnwaltsThemeManager {
    constructor() {
        this.themes = {
            'landing': {
                primary: '#3b82f6',      // blue-500
                primaryDark: '#2563eb',  // blue-600  
                background: '#f8fafc',   // slate-50
                glass: 'rgba(59, 130, 246, 0.1)',
                text: '#1e293b',         // slate-800
                glassPrimary: 'rgba(248, 250, 252, 0.8)',
                glassSecondary: 'rgba(241, 245, 249, 0.6)',
                borderPrimary: '#e2e8f0',
                borderAccent: '#cbd5e1'
            },
            'dashboard': {
                // Apply the SAME colors for consistency
                primary: '#3b82f6',      // blue-500 (was #8b5cf6)
                primaryDark: '#2563eb',  // blue-600 (was #4338ca)
                background: '#f8fafc',   // slate-50 (was #12101c)
                glass: 'rgba(59, 130, 246, 0.1)', // (was rgba(46, 42, 77, 0.25))
                text: '#1e293b',         // slate-800 (was #ffffff)
                glassPrimary: 'rgba(248, 250, 252, 0.8)',
                glassSecondary: 'rgba(241, 245, 249, 0.6)',
                borderPrimary: '#e2e8f0',
                borderAccent: '#cbd5e1'
            }
        };
        this.currentTheme = this.detectPage();
        this.applyTheme();
        console.log('🎨 AnwaltsAI Theme Manager initialized for:', this.currentTheme);
    }

    detectPage() {
        if (window.location.pathname.includes('dashboard')) return 'dashboard';
        if (window.location.pathname.includes('anwalts-ai-app')) return 'landing';
        return 'landing';
    }

    applyTheme() {
        const theme = this.themes[this.currentTheme];
        const root = document.documentElement;
        
        // Apply CSS custom properties for seamless integration
        root.style.setProperty('--theme-primary', theme.primary);
        root.style.setProperty('--theme-primary-dark', theme.primaryDark);
        root.style.setProperty('--theme-background', theme.background);
        root.style.setProperty('--theme-glass', theme.glass);
        root.style.setProperty('--theme-text', theme.text);
        root.style.setProperty('--theme-glass-primary', theme.glassPrimary);
        root.style.setProperty('--theme-glass-secondary', theme.glassSecondary);
        root.style.setProperty('--theme-border-primary', theme.borderPrimary);
        root.style.setProperty('--theme-border-accent', theme.borderAccent);
        
        console.log(`🎨 Applied ${this.currentTheme} theme with unified blue colors`);
    }

    // Smooth transition between pages
    prepareTransition(targetPage) {
        document.body.style.transition = 'all 0.3s ease';
        
        // Add transition overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, 
                rgba(59, 130, 246, 0.1), 
                rgba(37, 99, 235, 0.05));
            backdrop-filter: blur(8px);
            z-index: 9998;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(overlay);
        
        // Fade in overlay
        setTimeout(() => overlay.style.opacity = '1', 10);
        
        // Preload target page styles
        this.preloadPageStyles(targetPage);
    }

    preloadPageStyles(targetPage) {
        const targetFile = targetPage === 'dashboard' ? 
            'anwalts-ai-dashboard.html' : 
            'anwalts-ai-app.html';
            
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = targetFile;
        document.head.appendChild(link);
        
        console.log(`⚡ Preloading ${targetFile} for smooth transition`);
    }

    switchTheme(newTheme) {
        this.currentTheme = newTheme;
        this.applyTheme();
    }

    getThemeColors() {
        return this.themes[this.currentTheme];
    }
}

// Initialize theme manager globally
window.anwaltsThemeManager = new AnwaltsThemeManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnwaltsThemeManager;
}