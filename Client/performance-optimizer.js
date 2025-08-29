/**
 * AnwaltsAI Landing Page Performance Optimizer
 * Optimizes loading performance and user experience
 */

class LandingPageOptimizer {
    constructor() {
        this.loadStartTime = performance.now();
        this.criticalResourcesLoaded = false;
        this.deferredScripts = [];
        this.lazyImages = [];
        
        this.init();
    }
    
    init() {
        // Initialize performance monitoring
        this.setupPerformanceMonitoring();
        
        // Optimize critical resource loading
        this.optimizeCriticalPath();
        
        // Setup lazy loading
        this.setupLazyLoading();
        
        // Optimize animations
        this.optimizeAnimations();
        
        // Setup service worker (if available)
        this.setupServiceWorker();
        
        // Monitor and log performance
        this.logPerformanceMetrics();
    }
    
    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        if ('web-vital' in window) {
            // Largest Contentful Paint (LCP)
            this.observeLCP();
            
            // First Input Delay (FID)
            this.observeFID();
            
            // Cumulative Layout Shift (CLS)
            this.observeCLS();
        }
        
        // Monitor page load performance
        window.addEventListener('load', () => {
            const loadTime = performance.now() - this.loadStartTime;
            console.log(`🚀 Page fully loaded in ${loadTime.toFixed(2)}ms`);
            
            // Log navigation timing
            this.logNavigationTiming();
        });
    }
    
    optimizeCriticalPath() {
        // Preload critical assets
        this.preloadCriticalAssets();
        
        // Inline critical CSS (if not already done)
        this.inlineCriticalCSS();
        
        // Defer non-critical scripts
        this.deferNonCriticalScripts();
    }
    
    preloadCriticalAssets() {
        const criticalAssets = [
            { href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap', as: 'style' },
            { href: 'https://cdn.tailwindcss.com', as: 'script' },
            { href: 'favicon.ico', as: 'image' }
        ];
        
        criticalAssets.forEach(asset => {
            if (!document.querySelector(`link[href="${asset.href}"]`)) {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.href = asset.href;
                link.as = asset.as;
                if (asset.as === 'style') link.onload = () => link.rel = 'stylesheet';
                document.head.appendChild(link);
            }
        });
    }
    
    inlineCriticalCSS() {
        // Critical CSS for above-the-fold content
        const criticalCSS = `
            body { 
                font-family: 'Inter', sans-serif; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #334155 100%);
                margin: 0;
                padding: 0;
            }
            .legal-gradient { 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #334155 100%); 
            }
            .hero-loading { 
                min-height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
            }
        `;
        
        if (!document.getElementById('critical-css')) {
            const style = document.createElement('style');
            style.id = 'critical-css';
            style.textContent = criticalCSS;
            document.head.insertBefore(style, document.head.firstChild);
        }
    }
    
    deferNonCriticalScripts() {
        // Scripts that can be loaded after initial render
        const nonCriticalScripts = [
            'https://unpkg.com/lucide@latest/dist/umd/lucide.js'
        ];
        
        nonCriticalScripts.forEach(src => {
            this.deferredScripts.push(src);
        });
        
        // Load deferred scripts after page load
        window.addEventListener('load', () => {
            setTimeout(() => this.loadDeferredScripts(), 100);
        });
    }
    
    loadDeferredScripts() {
        this.deferredScripts.forEach(src => {
            if (!document.querySelector(`script[src="${src}"]`)) {
                const script = document.createElement('script');
                script.src = src;
                script.async = true;
                document.body.appendChild(script);
            }
        });
    }
    
    setupLazyLoading() {
        // Create intersection observer for lazy loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });
            
            // Observe all lazy images
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
    
    optimizeAnimations() {
        // Use requestAnimationFrame for smooth animations
        const animatedElements = document.querySelectorAll('.animate-fade-in-up');
        
        if ('IntersectionObserver' in window) {
            const animationObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        requestAnimationFrame(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        });
                        animationObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });
            
            animatedElements.forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
                animationObserver.observe(el);
            });
        }
    }
    
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('🔧 Service Worker registered:', registration.scope);
                    })
                    .catch(error => {
                        console.log('Service Worker registration failed:', error);
                    });
            });
        }
    }
    
    observeLCP() {
        try {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                console.log('📊 LCP:', lastEntry.startTime);
            });
            observer.observe({entryTypes: ['largest-contentful-paint']});
        } catch (e) {
            console.log('LCP observation not supported');
        }
    }
    
    observeFID() {
        try {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    console.log('⚡ FID:', entry.processingStart - entry.startTime);
                });
            });
            observer.observe({entryTypes: ['first-input']});
        } catch (e) {
            console.log('FID observation not supported');
        }
    }
    
    observeCLS() {
        try {
            let clsValue = 0;
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                console.log('📐 CLS:', clsValue);
            });
            observer.observe({entryTypes: ['layout-shift']});
        } catch (e) {
            console.log('CLS observation not supported');
        }
    }
    
    logNavigationTiming() {
        const timing = performance.getEntriesByType('navigation')[0];
        if (timing) {
            console.log('📈 Navigation Timing:');
            console.log(`  DNS: ${timing.domainLookupEnd - timing.domainLookupStart}ms`);
            console.log(`  Connect: ${timing.connectEnd - timing.connectStart}ms`);
            console.log(`  TTFB: ${timing.responseStart - timing.requestStart}ms`);
            console.log(`  DOM Content Loaded: ${timing.domContentLoadedEventEnd - timing.navigationStart}ms`);
            console.log(`  Load Complete: ${timing.loadEventEnd - timing.navigationStart}ms`);
        }
    }
    
    logPerformanceMetrics() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const resources = performance.getEntriesByType('resource');
                const totalSize = resources.reduce((size, resource) => {
                    return size + (resource.transferSize || 0);
                }, 0);
                
                console.log('📊 Performance Metrics:');
                console.log(`  Total Resources: ${resources.length}`);
                console.log(`  Total Transfer Size: ${(totalSize / 1024).toFixed(2)}KB`);
                console.log(`  Memory Usage: ${this.getMemoryUsage()}`);
                
                // Check for performance issues
                this.checkPerformanceIssues();
            }, 2000);
        });
    }
    
    getMemoryUsage() {
        if ('memory' in performance) {
            const memory = performance.memory;
            return `${(memory.usedJSHeapSize / 1048576).toFixed(2)}MB / ${(memory.jsHeapSizeLimit / 1048576).toFixed(2)}MB`;
        }
        return 'Not available';
    }
    
    checkPerformanceIssues() {
        const issues = [];
        
        // Check for large images
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.naturalWidth > 1920 || img.naturalHeight > 1080) {
                issues.push(`Large image detected: ${img.src}`);
            }
        });
        
        // Check for unused CSS
        const styleSheets = document.styleSheets;
        if (styleSheets.length > 5) {
            issues.push(`Many stylesheets detected: ${styleSheets.length}`);
        }
        
        // Check for memory leaks
        if ('memory' in performance && performance.memory.usedJSHeapSize > 50 * 1048576) {
            issues.push('High memory usage detected');
        }
        
        if (issues.length > 0) {
            console.warn('⚠️ Performance Issues Found:');
            issues.forEach(issue => console.warn(`  - ${issue}`));
        } else {
            console.log('✅ No performance issues detected');
        }
    }
    
    // Utility method to optimize images
    optimizeImages() {
        const images = document.querySelectorAll('img:not([data-optimized])');
        images.forEach(img => {
            // Add loading="lazy" if not present
            if (!img.hasAttribute('loading')) {
                img.loading = 'lazy';
            }
            
            // Add data-optimized flag
            img.setAttribute('data-optimized', 'true');
        });
    }
    
    // Method to preload next page
    preloadNextPage(url) {
        if (!document.querySelector(`link[href="${url}"]`)) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        }
    }
}

// Initialize performance optimizer when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.landingPageOptimizer = new LandingPageOptimizer();
    });
} else {
    window.landingPageOptimizer = new LandingPageOptimizer();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LandingPageOptimizer;
}