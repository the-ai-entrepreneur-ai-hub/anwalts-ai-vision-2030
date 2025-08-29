/**
 * AnwaltsAI Responsive Consistency Manager
 * Unified responsive behavior across landing page and dashboard
 */
class AnwaltsResponsiveManager {
    constructor() {
        this.breakpoints = {
            mobile: '(max-width: 767px)',
            tablet: '(min-width: 768px) and (max-width: 1023px)', 
            desktop: '(min-width: 1024px)',
            largeDesktop: '(min-width: 1440px)'
        };
        this.currentDevice = this.detectDevice();
        this.init();
        console.log(`📱 AnwaltsAI Responsive Manager initialized for: ${this.currentDevice}`);
    }

    init() {
        this.setupBreakpointListeners();
        this.applyConsistentStyles();
        this.optimizeForDevice();
        this.setupOrientationHandling();
        this.setupViewportMetaTag();
    }

    detectDevice() {
        if (window.matchMedia(this.breakpoints.mobile).matches) return 'mobile';
        if (window.matchMedia(this.breakpoints.tablet).matches) return 'tablet';
        if (window.matchMedia(this.breakpoints.largeDesktop).matches) return 'largeDesktop';
        return 'desktop';
    }

    setupBreakpointListeners() {
        Object.entries(this.breakpoints).forEach(([device, query]) => {
            const mediaQuery = window.matchMedia(query);
            
            // Initial check
            if (mediaQuery.matches) {
                this.handleDeviceChange(device);
            }
            
            // Listen for changes
            mediaQuery.addEventListener('change', (e) => {
                if (e.matches) {
                    this.handleDeviceChange(device);
                }
            });
        });
    }

    handleDeviceChange(device) {
        if (this.currentDevice !== device) {
            console.log(`📱 Device changed from ${this.currentDevice} to ${device}`);
            this.currentDevice = device;
            
            // Update body attribute for CSS targeting
            if (document.body) {
                document.body.setAttribute('data-device', device);
            }
            
            // Apply device-specific optimizations
            this.optimizeForDevice();
            
            // Trigger custom event for other components
            window.dispatchEvent(new CustomEvent('anwalts:deviceChanged', {
                detail: { device, previousDevice: this.currentDevice }
            }));
        }
    }

    optimizeForDevice() {
        const root = document.documentElement;
        
        switch (this.currentDevice) {
            case 'mobile':
                this.optimizeForMobile();
                break;
            case 'tablet':
                this.optimizeForTablet();
                break;
            case 'desktop':
                this.optimizeForDesktop();
                break;
            case 'largeDesktop':
                this.optimizeForLargeDesktop();
                break;
        }
    }

    optimizeForMobile() {
        const root = document.documentElement;
        
        // Enhanced touch interactions
        root.style.setProperty('--touch-target-size', '44px');
        root.style.setProperty('--mobile-padding', '16px');
        root.style.setProperty('--mobile-gap', '12px');
        
        // Optimize glassmorphism for mobile performance
        root.style.setProperty('--mobile-backdrop-blur', '8px');
        root.style.setProperty('--mobile-opacity', '0.95');
        
        // Adjust modal sizes
        root.style.setProperty('--modal-width', '95vw');
        root.style.setProperty('--modal-margin', '8px');
        
        // Mobile-specific navigation adjustments
        if (document.querySelector('.nav-sidebar')) {
            document.querySelector('.nav-sidebar').style.width = '280px';
        }
        
        console.log('📱 Mobile optimizations applied');
    }

    optimizeForTablet() {
        const root = document.documentElement;
        
        root.style.setProperty('--touch-target-size', '40px');
        root.style.setProperty('--mobile-padding', '20px');
        root.style.setProperty('--mobile-gap', '16px');
        root.style.setProperty('--mobile-backdrop-blur', '12px');
        root.style.setProperty('--modal-width', '80vw');
        root.style.setProperty('--modal-margin', '16px');
        
        console.log('📱 Tablet optimizations applied');
    }

    optimizeForDesktop() {
        const root = document.documentElement;
        
        root.style.setProperty('--touch-target-size', '36px');
        root.style.setProperty('--mobile-padding', '24px');
        root.style.setProperty('--mobile-gap', '20px');
        root.style.setProperty('--mobile-backdrop-blur', '20px');
        root.style.setProperty('--modal-width', '600px');
        root.style.setProperty('--modal-margin', '24px');
        
        console.log('🖥️ Desktop optimizations applied');
    }

    optimizeForLargeDesktop() {
        const root = document.documentElement;
        
        root.style.setProperty('--touch-target-size', '36px');
        root.style.setProperty('--mobile-padding', '32px');
        root.style.setProperty('--mobile-gap', '24px');
        root.style.setProperty('--mobile-backdrop-blur', '24px');
        root.style.setProperty('--modal-width', '700px');
        root.style.setProperty('--modal-margin', '32px');
        
        console.log('🖥️ Large desktop optimizations applied');
    }

    applyConsistentStyles() {
        const style = document.createElement('style');
        style.id = 'anwalts-responsive-styles';
        style.textContent = `
            /* Consistent responsive utilities across both pages */
            .anwalts-hide-mobile { display: block !important; }
            .anwalts-hide-tablet { display: block !important; }
            .anwalts-hide-desktop { display: block !important; }
            .anwalts-show-mobile { display: none !important; }
            .anwalts-show-tablet { display: none !important; }
            .anwalts-show-desktop { display: none !important; }
            
            /* Mobile first approach */
            @media (max-width: 767px) {
                .anwalts-hide-mobile { display: none !important; }
                .anwalts-show-mobile { display: block !important; }
                
                /* Mobile-specific glassmorphism optimization */
                .glass-card, .anwalts-card {
                    backdrop-filter: blur(var(--mobile-backdrop-blur, 8px)) !important;
                }
                
                /* Touch-friendly interactions */
                button, .btn, .nav-item {
                    min-height: var(--touch-target-size, 44px) !important;
                    min-width: var(--touch-target-size, 44px) !important;
                }
                
                /* Mobile navigation */
                .nav-sidebar {
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    height: 100vh !important;
                    z-index: 1000 !important;
                    transform: translateX(-100%) !important;
                    transition: transform 0.3s ease !important;
                }
                
                .nav-sidebar.mobile-open {
                    transform: translateX(0) !important;
                }
                
                /* Mobile modal adjustments */
                .anwalts-modal .anwalts-modal-content,
                .modal-content {
                    margin: var(--mobile-gap, 12px) !important;
                    max-width: calc(100vw - 24px) !important;
                    max-height: calc(100vh - 24px) !important;
                }
            }
            
            /* Tablet styles */
            @media (min-width: 768px) and (max-width: 1023px) {
                .anwalts-hide-tablet { display: none !important; }
                .anwalts-show-tablet { display: block !important; }
                
                /* Tablet-specific optimizations */
                .dashboard-grid {
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
                }
            }
            
            /* Desktop and above */
            @media (min-width: 1024px) {
                .anwalts-hide-desktop { display: none !important; }
                .anwalts-show-desktop { display: block !important; }
                
                /* Desktop-specific optimizations */
                .dashboard-grid {
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)) !important;
                }
            }
            
            /* Large desktop */
            @media (min-width: 1440px) {
                .main-content {
                    max-width: 1400px !important;
                    margin: 0 auto !important;
                }
            }
            
            /* Consistent form handling */
            @media (max-width: 767px) {
                .form-input, .anwalts-input {
                    font-size: 16px !important; /* Prevent zoom on iOS */
                }
            }
            
            /* Print styles */
            @media print {
                .nav-sidebar,
                .anwalts-modal,
                button,
                .btn,
                .fab-container {
                    display: none !important;
                }
                
                .main-content {
                    margin: 0 !important;
                    width: 100% !important;
                }
            }
        `;
        
        // Remove existing styles if present
        const existing = document.getElementById('anwalts-responsive-styles');
        if (existing) existing.remove();
        
        document.head.appendChild(style);
        console.log('🎨 Consistent responsive styles applied');
    }

    setupOrientationHandling() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100); // Small delay to ensure viewport has updated
        });
        
        // Also handle resize events
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleOrientationChange();
            }, 250);
        });
    }

    handleOrientationChange() {
        const newDevice = this.detectDevice();
        if (newDevice !== this.currentDevice) {
            this.handleDeviceChange(newDevice);
        }
        
        // Refresh viewport height for mobile browsers
        if (this.currentDevice === 'mobile') {
            document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
        }
        
        console.log('📱 Orientation change handled');
    }

    setupViewportMetaTag() {
        // Ensure proper viewport meta tag
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        viewport.content = 'width=device-width, initial-scale=1, shrink-to-fit=no, viewport-fit=cover';
    }

    // Public API
    getCurrentDevice() {
        return this.currentDevice;
    }

    isMobile() {
        return this.currentDevice === 'mobile';
    }

    isTablet() {
        return this.currentDevice === 'tablet';
    }

    isDesktop() {
        return this.currentDevice === 'desktop' || this.currentDevice === 'largeDesktop';
    }

    getTouchTargetSize() {
        return getComputedStyle(document.documentElement).getPropertyValue('--touch-target-size') || '44px';
    }

    // Utility methods for responsive behavior
    adaptModalForDevice(modal) {
        if (!modal) return;
        
        const content = modal.querySelector('.anwalts-modal-content, .modal-content');
        if (!content) return;
        
        if (this.isMobile()) {
            content.style.margin = '8px';
            content.style.maxWidth = 'calc(100vw - 16px)';
            content.style.maxHeight = 'calc(100vh - 16px)';
        } else if (this.isTablet()) {
            content.style.margin = '16px';
            content.style.maxWidth = '80vw';
        } else {
            content.style.margin = '24px';
            content.style.maxWidth = '600px';
        }
    }

    // Performance monitoring
    getResponsiveMetrics() {
        return {
            device: this.currentDevice,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            devicePixelRatio: window.devicePixelRatio,
            orientation: screen.orientation?.type || 'unknown'
        };
    }
}

// Initialize responsive manager globally
window.anwaltsResponsiveManager = new AnwaltsResponsiveManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnwaltsResponsiveManager;
}