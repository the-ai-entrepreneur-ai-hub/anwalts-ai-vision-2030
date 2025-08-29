/**
 * Memory Leak Prevention System for AnwaltsAI
 * Manages timers, intervals, event listeners, and other resources to prevent memory leaks
 */

class MemoryLeakPrevention {
    constructor() {
        this.activeTimeouts = new Set();
        this.activeIntervals = new Set();
        this.eventListeners = new Map();
        this.observerInstances = new Set();
        this.chartInstances = new Set();
        this.originalSetTimeout = window.setTimeout;
        this.originalSetInterval = window.setInterval;
        this.originalClearTimeout = window.clearTimeout;
        this.originalClearInterval = window.clearInterval;
        this.isEnabled = true;
        
        this.wrapTimerFunctions();
        this.setupPageUnloadCleanup();
        this.startMemoryMonitoring();
    }

    /**
     * Wrap setTimeout and setInterval to track them
     */
    wrapTimerFunctions() {
        // Wrap setTimeout
        window.setTimeout = (...args) => {
            if (!this.isEnabled) return this.originalSetTimeout(...args);
            
            const id = this.originalSetTimeout(...args);
            this.activeTimeouts.add(id);
            
            // Auto-cleanup after execution
            const originalCallback = args[0];
            if (typeof originalCallback === 'function') {
                args[0] = (...callbackArgs) => {
                    try {
                        originalCallback(...callbackArgs);
                    } finally {
                        this.activeTimeouts.delete(id);
                    }
                };
            }
            
            return id;
        };

        // Wrap setInterval
        window.setInterval = (...args) => {
            if (!this.isEnabled) return this.originalSetInterval(...args);
            
            const id = this.originalSetInterval(...args);
            this.activeIntervals.add(id);
            return id;
        };

        // Wrap clearTimeout
        window.clearTimeout = (id) => {
            this.activeTimeouts.delete(id);
            return this.originalClearTimeout(id);
        };

        // Wrap clearInterval
        window.clearInterval = (id) => {
            this.activeIntervals.delete(id);
            return this.originalClearInterval(id);
        };
    }

    /**
     * Create managed timeout that auto-cleans up
     */
    createManagedTimeout(callback, delay, context = 'general') {
        const timeoutId = setTimeout(() => {
            try {
                callback();
            } catch (error) {
                // Error handling suppressed for production
                console.warn(`Managed timeout error in ${context}:`, error);
            } finally {
                this.activeTimeouts.delete(timeoutId);
            }
        }, delay);
        
        this.activeTimeouts.add(timeoutId);
        return timeoutId;
    }

    /**
     * Create managed interval that auto-tracks and can be bulk cleaned
     */
    createManagedInterval(callback, delay, context = 'general') {
        const intervalId = setInterval(() => {
            try {
                callback();
            } catch (error) {
                // Error handling suppressed for production
                console.warn(`Managed interval error in ${context}:`, error);
                // Optionally clear interval on repeated errors
                this.clearManagedInterval(intervalId);
            }
        }, delay);
        
        this.activeIntervals.add(intervalId);
        return intervalId;
    }

    /**
     * Clear managed interval
     */
    clearManagedInterval(intervalId) {
        this.activeIntervals.delete(intervalId);
        clearInterval(intervalId);
    }

    /**
     * Add event listener with automatic cleanup tracking
     */
    addManagedEventListener(element, event, handler, options = {}) {
        if (!element || typeof handler !== 'function') return;

        const elementKey = this.getElementKey(element);
        
        if (!this.eventListeners.has(elementKey)) {
            this.eventListeners.set(elementKey, []);
        }
        
        const listenerInfo = { event, handler, options };
        this.eventListeners.get(elementKey).push(listenerInfo);
        
        element.addEventListener(event, handler, options);
        
        return () => this.removeManagedEventListener(element, event, handler);
    }

    /**
     * Remove managed event listener
     */
    removeManagedEventListener(element, event, handler) {
        const elementKey = this.getElementKey(element);
        const listeners = this.eventListeners.get(elementKey);
        
        if (listeners) {
            const index = listeners.findIndex(l => l.event === event && l.handler === handler);
            if (index !== -1) {
                listeners.splice(index, 1);
                element.removeEventListener(event, handler);
                
                // Clean up if no more listeners
                if (listeners.length === 0) {
                    this.eventListeners.delete(elementKey);
                }
            }
        }
    }

    /**
     * Register observer instance for cleanup
     */
    registerObserver(observer, name = 'unknown') {
        this.observerInstances.add({ observer, name, created: Date.now() });
        return observer;
    }

    /**
     * Register chart instance for cleanup
     */
    registerChart(chart, id) {
        this.chartInstances.add({ chart, id, created: Date.now() });
        return chart;
    }

    /**
     * Get unique key for DOM elements
     */
    getElementKey(element) {
        if (element.id) return `id:${element.id}`;
        if (element.className) return `class:${element.className}`;
        return `tag:${element.tagName}_${Date.now()}`;
    }

    /**
     * Clear all timeouts
     */
    clearAllTimeouts() {
        this.activeTimeouts.forEach(id => {
            this.originalClearTimeout(id);
        });
        this.activeTimeouts.clear();
    }

    /**
     * Clear all intervals
     */
    clearAllIntervals() {
        this.activeIntervals.forEach(id => {
            this.originalClearInterval(id);
        });
        this.activeIntervals.clear();
    }

    /**
     * Clear all event listeners
     */
    clearAllEventListeners() {
        this.eventListeners.forEach((listeners, elementKey) => {
            // Try to find element and remove listeners
            const element = this.findElementByKey(elementKey);
            if (element) {
                listeners.forEach(({ event, handler }) => {
                    element.removeEventListener(event, handler);
                });
            }
        });
        this.eventListeners.clear();
    }

    /**
     * Find element by key (best effort)
     */
    findElementByKey(elementKey) {
        const [type, value] = elementKey.split(':', 2);
        
        switch (type) {
            case 'id':
                return document.getElementById(value);
            case 'class':
                return document.querySelector(`.${value.split(' ')[0]}`);
            case 'tag':
                const [tagName] = value.split('_', 1);
                return document.querySelector(tagName.toLowerCase());
            default:
                return null;
        }
    }

    /**
     * Clear all observers
     */
    clearAllObservers() {
        this.observerInstances.forEach(({ observer, name }) => {
            try {
                if (observer && typeof observer.disconnect === 'function') {
                    observer.disconnect();
                }
            } catch (error) {
                console.warn(`Error disconnecting observer ${name}:`, error);
            }
        });
        this.observerInstances.clear();
    }

    /**
     * Clear all charts
     */
    clearAllCharts() {
        this.chartInstances.forEach(({ chart, id }) => {
            try {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            } catch (error) {
                console.warn(`Error destroying chart ${id}:`, error);
            }
        });
        this.chartInstances.clear();
    }

    /**
     * Comprehensive cleanup of all resources
     */
    performFullCleanup() {
        this.clearAllTimeouts();
        this.clearAllIntervals();
        this.clearAllEventListeners();
        this.clearAllObservers();
        this.clearAllCharts();
        
        // Cleanup performance utils if available
        if (window.PerformanceUtils) {
            window.PerformanceUtils.cleanup();
        }
        
        // Cleanup chart optimizer if available
        if (window.ChartOptimizer) {
            window.ChartOptimizer.cleanup();
        }
    }

    /**
     * Get memory usage statistics
     */
    getMemoryStats() {
        const performance = window.performance;
        const memory = (performance && performance.memory) ? {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576),
            total: Math.round(performance.memory.totalJSHeapSize / 1048576),
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
        } : null;

        return {
            activeTimeouts: this.activeTimeouts.size,
            activeIntervals: this.activeIntervals.size,
            eventListeners: this.eventListeners.size,
            observers: this.observerInstances.size,
            charts: this.chartInstances.size,
            memory,
            timestamp: Date.now()
        };
    }

    /**
     * Start memory monitoring
     */
    startMemoryMonitoring() {
        // Monitor every 30 seconds
        this.memoryMonitorInterval = this.createManagedInterval(() => {
            const stats = this.getMemoryStats();
            
            // Store in performance utils if available
            if (window.PerformanceUtils) {
                window.PerformanceUtils.performanceMetrics.set('memory_stats', stats);
            }
            
            // Warn if too many resources are active
            const totalResources = stats.activeTimeouts + stats.activeIntervals + 
                                  stats.eventListeners + stats.observers + stats.charts;
            
            if (totalResources > 100) {
                console.warn('High resource usage detected:', stats);
            }
        }, 30000);
    }

    /**
     * Setup page unload cleanup
     */
    setupPageUnloadCleanup() {
        // Clean up on page unload
        this.addManagedEventListener(window, 'beforeunload', () => {
            this.performFullCleanup();
        });

        // Clean up on visibility change (when tab becomes hidden)
        this.addManagedEventListener(document, 'visibilitychange', () => {
            if (document.hidden) {
                // Pause intervals and clear timeouts when tab is hidden
                this.clearAllTimeouts();
            }
        });

        // Clean up on page freeze (mobile browsers)
        this.addManagedEventListener(window, 'freeze', () => {
            this.performFullCleanup();
        });
    }

    /**
     * Disable memory leak prevention (for testing)
     */
    disable() {
        this.isEnabled = false;
        this.performFullCleanup();
    }

    /**
     * Enable memory leak prevention
     */
    enable() {
        this.isEnabled = true;
    }
}

// Global memory leak prevention instance
window.MemoryLeakPrevention = window.MemoryLeakPrevention || new MemoryLeakPrevention();

// Helper functions for easier usage
window.createManagedTimeout = (callback, delay, context) => {
    return window.MemoryLeakPrevention.createManagedTimeout(callback, delay, context);
};

window.createManagedInterval = (callback, delay, context) => {
    return window.MemoryLeakPrevention.createManagedInterval(callback, delay, context);
};

window.addManagedEventListener = (element, event, handler, options) => {
    return window.MemoryLeakPrevention.addManagedEventListener(element, event, handler, options);
};

// Report memory stats to console (development helper)
window.getMemoryReport = () => {
    return window.MemoryLeakPrevention.getMemoryStats();
};