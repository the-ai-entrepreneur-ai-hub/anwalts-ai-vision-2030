/**
 * AnwaltsAI Seamless Navigation Manager
 * Smooth transitions between landing page and dashboard
 */
class AnwaltsNavigationManager {
    constructor() {
        this.pages = {
            'landing': 'anwalts-ai-app.html',
            'dashboard': 'anwalts-ai-dashboard.html'
        };
        this.init();
        console.log('🚀 AnwaltsAI Navigation Manager initialized');
    }

    init() {
        // Preload critical resources
        this.preloadCriticalPages();
        
        // Setup smooth transitions
        this.setupTransitionEffects();
        
        // Handle browser back/forward
        this.setupHistoryManagement();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    async navigateToPage(targetPage, userData = null) {
        try {
            console.log(`🔄 Navigating to ${targetPage}...`);
            
            // Show transition loading with AnwaltsAI branding
            this.showTransitionLoader();
            
            // Store navigation context for seamless transition
            if (userData) {
                sessionStorage.setItem('anwalts_navigation_context', JSON.stringify({
                    timestamp: Date.now(),
                    from: window.location.pathname,
                    to: targetPage,
                    userData: userData,
                    themeState: window.anwaltsThemeManager?.getThemeColors()
                }));
            }
            
            // Prepare theme transition
            if (window.anwaltsThemeManager) {
                window.anwaltsThemeManager.prepareTransition(targetPage);
            }
            
            // Smooth page transition
            await this.fadeOutCurrent();
            
            // Navigate to target page
            window.location.href = this.pages[targetPage];
            
        } catch (error) {
            console.error('❌ Navigation failed:', error);
            // Fallback to direct navigation
            window.location.href = this.pages[targetPage];
        }
    }

    preloadCriticalPages() {
        // Preload dashboard styles when on landing page
        if (window.location.pathname.includes('anwalts-ai-app.html')) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = 'anwalts-ai-dashboard.html';
            document.head.appendChild(link);
            console.log('⚡ Preloading dashboard for faster navigation');
        }
        
        // Preload landing page when on dashboard
        if (window.location.pathname.includes('anwalts-ai-dashboard.html')) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = 'anwalts-ai-app.html';
            document.head.appendChild(link);
            console.log('⚡ Preloading landing page for faster navigation');
        }
    }

    showTransitionLoader() {
        const loader = document.createElement('div');
        loader.id = 'anwalts-transition-loader';
        loader.innerHTML = `
            <div style="
                position: fixed; 
                top: 0; left: 0; right: 0; bottom: 0; 
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
                backdrop-filter: blur(20px);
                display: flex; 
                align-items: center; 
                justify-content: center;
                z-index: 9999;
                transition: opacity 0.3s ease;
            ">
                <div style="
                    background: linear-gradient(135deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.9));
                    border: 1px solid rgba(59, 130, 246, 0.2);
                    border-radius: 16px;
                    padding: 32px;
                    box-shadow: 0 20px 40px rgba(59, 130, 246, 0.15);
                    backdrop-filter: blur(20px);
                    text-align: center;
                    max-width: 300px;
                ">
                    <div style="
                        width: 48px; 
                        height: 48px; 
                        border: 3px solid #e2e8f0;
                        border-top: 3px solid #3b82f6;
                        border-radius: 50%;
                        margin: 0 auto 16px;
                        animation: anwalts-spin 1s linear infinite;
                    "></div>
                    <div style="color: #2563eb; font-weight: 600; font-size: 18px; margin-bottom: 8px;">
                        AnwaltsAI
                    </div>
                    <div style="color: #64748b; font-size: 14px;">
                        Loading your workspace...
                    </div>
                </div>
            </div>
        `;
        
        // Add spinner animation
        if (!document.getElementById('anwalts-spinner-styles')) {
            const style = document.createElement('style');
            style.id = 'anwalts-spinner-styles';
            style.textContent = `
                @keyframes anwalts-spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(loader);
    }

    async fadeOutCurrent() {
        return new Promise(resolve => {
            document.body.style.transition = 'opacity 0.2s ease';
            document.body.style.opacity = '0.85';
            setTimeout(resolve, 200);
        });
    }

    setupTransitionEffects() {
        // Add page transition classes
        if (document.body) {
            document.body.classList.add('anwalts-page-transition');
        }
        
        const style = document.createElement('style');
        style.textContent = `
            .anwalts-page-transition {
                transition: opacity 0.3s ease, transform 0.3s ease;
            }
            
            .anwalts-page-entering {
                opacity: 0;
                transform: translateY(20px);
            }
            
            .anwalts-page-entered {
                opacity: 1;
                transform: translateY(0);
            }
        `;
        document.head.appendChild(style);
    }

    setupHistoryManagement() {
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {
            console.log('🔄 Browser navigation detected');
            // Let browser handle navigation naturally
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Alt + D = Dashboard
            if (event.altKey && event.key === 'd') {
                event.preventDefault();
                this.navigateToPage('dashboard');
            }
            
            // Alt + H = Home/Landing
            if (event.altKey && event.key === 'h') {
                event.preventDefault();
                this.navigateToPage('landing');
            }
        });
    }

    // Quick navigation methods
    goToDashboard(userData = null) {
        this.navigateToPage('dashboard', userData);
    }

    goToLanding() {
        this.navigateToPage('landing');
    }

    // Get current page
    getCurrentPage() {
        if (window.location.pathname.includes('dashboard')) return 'dashboard';
        return 'landing';
    }

    // Check if navigation is available
    isNavigationReady() {
        return document.readyState === 'complete';
    }
}

// Initialize navigation manager globally
window.anwaltsNavigationManager = new AnwaltsNavigationManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnwaltsNavigationManager;
}