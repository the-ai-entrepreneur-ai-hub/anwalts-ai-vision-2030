/**
 * Performance Utilities for AnwaltsAI
 * Provides optimized loading states, GPU acceleration helpers, and performance monitoring
 */

class PerformanceUtils {
    constructor() {
        this.loadingStates = new Map();
        this.performanceMetrics = new Map();
        this.animationFrameCallbacks = new Set();
        this.intersectionObserver = null;
        this.initLazyLoading();
    }

    /**
     * GPU-Accelerated Loading Spinner Component
     */
    createOptimizedLoadingSpinner(container, context = 'general') {
        const existingSpinner = container.querySelector('.performance-spinner');
        if (existingSpinner) return existingSpinner;

        const spinner = document.createElement('div');
        spinner.className = 'performance-spinner';
        spinner.innerHTML = `
            <div class="spinner-ring">
                <div class="spinner-segment"></div>
                <div class="spinner-segment"></div>
                <div class="spinner-segment"></div>
            </div>
            <div class="spinner-text">${this.getContextualMessage(context)}</div>
        `;

        // GPU-accelerated CSS
        const style = document.createElement('style');
        style.textContent = `
            .performance-spinner {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate3d(-50%, -50%, 0);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
                z-index: 1000;
                pointer-events: none;
                will-change: opacity, transform;
            }
            
            .spinner-ring {
                position: relative;
                width: 40px;
                height: 40px;
                will-change: transform;
            }
            
            .spinner-segment {
                position: absolute;
                width: 100%;
                height: 100%;
                border: 3px solid transparent;
                border-top: 3px solid #8b5cf6;
                border-radius: 50%;
                animation: spin-gpu 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
                will-change: transform;
            }
            
            .spinner-segment:nth-child(2) {
                animation-delay: -0.33s;
                border-top-color: #a855f7;
            }
            
            .spinner-segment:nth-child(3) {
                animation-delay: -0.66s;
                border-top-color: #c084fc;
            }
            
            .spinner-text {
                color: #a1a1aa;
                font-size: 0.875rem;
                font-weight: 500;
                opacity: 0.8;
                text-align: center;
                will-change: opacity;
            }
            
            @keyframes spin-gpu {
                0% { transform: rotate3d(0, 0, 1, 0deg); }
                100% { transform: rotate3d(0, 0, 1, 360deg); }
            }
        `;
        
        if (!document.head.querySelector('style[data-perf-spinner]')) {
            style.setAttribute('data-perf-spinner', 'true');
            document.head.appendChild(style);
        }

        container.style.position = 'relative';
        container.appendChild(spinner);
        
        // Track loading state
        this.loadingStates.set(container, { spinner, context, startTime: performance.now() });
        
        return spinner;
    }

    /**
     * Context-aware loading messages
     */
    getContextualMessage(context) {
        const messages = {
            'document_generation': 'Dokument wird generiert...',
            'api_request': 'Daten werden geladen...',
            'template_load': 'Vorlagen werden geladen...',
            'authentication': 'Anmeldung wird verarbeitet...',
            'file_upload': 'Datei wird hochgeladen...',
            'analysis': 'Analyse läuft...',
            'general': 'Bitte warten...'
        };
        return messages[context] || messages.general;
    }

    /**
     * Remove loading spinner with fade animation
     */
    removeLoadingSpinner(container, showSuccess = false) {
        const loadingState = this.loadingStates.get(container);
        if (!loadingState) return;

        const { spinner, context, startTime } = loadingState;
        const duration = performance.now() - startTime;

        // Track performance metric
        this.performanceMetrics.set(`${context}_load_time`, duration);

        if (showSuccess) {
            spinner.querySelector('.spinner-text').textContent = '✓ Abgeschlossen';
            spinner.style.color = '#10b981';
        }

        // GPU-accelerated fade out
        spinner.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        spinner.style.opacity = '0';
        spinner.style.transform = 'translate3d(-50%, -50%, 0) scale(0.8)';

        setTimeout(() => {
            if (spinner.parentNode) {
                spinner.parentNode.removeChild(spinner);
            }
            this.loadingStates.delete(container);
        }, 300);
    }

    /**
     * Optimized lazy loading with Intersection Observer
     */
    initLazyLoading() {
        if (!('IntersectionObserver' in window)) return;

        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    // Lazy load images
                    if (element.tagName === 'IMG' && element.dataset.src) {
                        element.src = element.dataset.src;
                        element.removeAttribute('data-src');
                        this.intersectionObserver.unobserve(element);
                    }
                    
                    // Lazy load components
                    if (element.dataset.lazyComponent) {
                        this.loadLazyComponent(element);
                        this.intersectionObserver.unobserve(element);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.1
        });
    }

    /**
     * Add element to lazy loading observation
     */
    observeLazyElement(element) {
        if (this.intersectionObserver) {
            this.intersectionObserver.observe(element);
        }
    }

    /**
     * Load lazy component
     */
    loadLazyComponent(element) {
        const componentName = element.dataset.lazyComponent;
        
        // Show loading spinner
        this.createOptimizedLoadingSpinner(element, 'component_load');
        
        // Simulate component loading (replace with actual component loading logic)
        setTimeout(() => {
            this.removeLoadingSpinner(element, true);
            element.innerHTML = `<div>Lazy component "${componentName}" loaded!</div>`;
        }, 500);
    }

    /**
     * GPU-accelerated animation helper
     */
    addGPUAcceleration(element, animations = {}) {
        // Force GPU layer creation
        element.style.willChange = 'transform, opacity';
        element.style.transform = 'translate3d(0, 0, 0)';
        
        // Apply custom animations if provided
        Object.entries(animations).forEach(([property, value]) => {
            element.style[property] = value;
        });

        return element;
    }

    /**
     * Optimized requestAnimationFrame wrapper
     */
    optimizedRAF(callback) {
        const id = requestAnimationFrame((timestamp) => {
            this.animationFrameCallbacks.delete(id);
            callback(timestamp);
        });
        this.animationFrameCallbacks.add(id);
        return id;
    }

    /**
     * Cancel all pending animation frames
     */
    cancelAllAnimations() {
        this.animationFrameCallbacks.forEach(id => {
            cancelAnimationFrame(id);
        });
        this.animationFrameCallbacks.clear();
    }

    /**
     * Memory cleanup
     */
    cleanup() {
        // Clear loading states
        this.loadingStates.forEach(({ spinner }) => {
            if (spinner.parentNode) {
                spinner.parentNode.removeChild(spinner);
            }
        });
        this.loadingStates.clear();

        // Cancel animations
        this.cancelAllAnimations();

        // Disconnect intersection observer
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }

        // Clear performance metrics
        this.performanceMetrics.clear();
    }

    /**
     * Get performance report
     */
    getPerformanceReport() {
        const report = {
            metrics: Object.fromEntries(this.performanceMetrics),
            activeLoadingStates: this.loadingStates.size,
            pendingAnimations: this.animationFrameCallbacks.size,
            timestamp: Date.now()
        };
        
        return report;
    }

    /**
     * Debounce function for performance optimization
     */
    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    /**
     * Throttle function for performance optimization
     */
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Global performance utils instance
window.PerformanceUtils = window.PerformanceUtils || new PerformanceUtils();

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.PerformanceUtils) {
        window.PerformanceUtils.cleanup();
    }
});