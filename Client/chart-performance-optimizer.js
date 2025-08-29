/**
 * Chart.js Performance Optimizer for AnwaltsAI Dashboard
 * Optimizes Chart.js initialization, rendering, and updates for better performance
 */

class ChartPerformanceOptimizer {
    constructor() {
        this.chartInstances = new Map();
        this.resizeObserver = null;
        this.animationFrameId = null;
        this.updateQueue = new Set();
        this.isUpdating = false;
        this.initResizeObserver();
    }

    /**
     * Create optimized chart with performance settings
     */
    createOptimizedChart(canvas, config, options = {}) {
        const ctx = canvas.getContext('2d');
        
        // Performance optimizations for Chart.js
        const optimizedConfig = {
            ...config,
            options: {
                ...config.options,
                // Disable animations for better performance on slower devices
                animation: {
                    duration: options.fastMode ? 0 : (config.options?.animation?.duration || 400),
                    easing: 'easeOutQuart'
                },
                // Optimize responsiveness
                responsive: true,
                maintainAspectRatio: false,
                // Optimize rendering
                elements: {
                    ...config.options?.elements,
                    point: {
                        ...config.options?.elements?.point,
                        radius: options.fastMode ? 2 : 4,
                        hoverRadius: options.fastMode ? 4 : 6
                    },
                    line: {
                        ...config.options?.elements?.line,
                        tension: options.fastMode ? 0 : 0.2
                    }
                },
                // Optimize scales
                scales: {
                    ...config.options?.scales,
                    x: {
                        ...config.options?.scales?.x,
                        ticks: {
                            ...config.options?.scales?.x?.ticks,
                            maxTicksLimit: options.fastMode ? 6 : 10
                        }
                    },
                    y: {
                        ...config.options?.scales?.y,
                        ticks: {
                            ...config.options?.scales?.y?.ticks,
                            maxTicksLimit: options.fastMode ? 5 : 8
                        }
                    }
                },
                // Optimize plugins
                plugins: {
                    ...config.options?.plugins,
                    legend: {
                        ...config.options?.plugins?.legend,
                        labels: {
                            ...config.options?.plugins?.legend?.labels,
                            usePointStyle: !options.fastMode
                        }
                    }
                },
                // Performance settings
                parsing: false, // Disable data parsing for better performance
                normalized: true, // Use normalized data
                spanGaps: true, // Span gaps for better performance
                // Interaction optimizations
                interaction: {
                    ...config.options?.interaction,
                    intersect: false,
                    mode: 'nearest'
                }
            }
        };

        // Create chart instance
        const chart = new Chart(ctx, optimizedConfig);
        
        // Store reference
        this.chartInstances.set(canvas.id || `chart_${Date.now()}`, {
            chart,
            canvas,
            lastUpdate: Date.now(),
            updatePending: false
        });

        // Add to resize observer
        if (this.resizeObserver) {
            this.resizeObserver.observe(canvas);
        }

        return chart;
    }

    /**
     * Batch update multiple charts for better performance
     */
    batchUpdateChart(chartId, newData, options = {}) {
        const instance = this.chartInstances.get(chartId);
        if (!instance) return;

        // Add to update queue
        this.updateQueue.add({
            chartId,
            instance,
            newData,
            options,
            timestamp: Date.now()
        });

        // Process queue if not already updating
        if (!this.isUpdating) {
            this.processUpdateQueue();
        }
    }

    /**
     * Process chart update queue with RAF optimization
     */
    processUpdateQueue() {
        if (this.updateQueue.size === 0) {
            this.isUpdating = false;
            return;
        }

        this.isUpdating = true;
        this.animationFrameId = requestAnimationFrame(() => {
            // Process all pending updates
            const updates = Array.from(this.updateQueue);
            this.updateQueue.clear();

            updates.forEach(({ instance, newData, options }) => {
                this.performChartUpdate(instance, newData, options);
            });

            // Continue processing if more updates were added
            this.processUpdateQueue();
        });
    }

    /**
     * Perform actual chart update with optimizations
     */
    performChartUpdate(instance, newData, options = {}) {
        const { chart } = instance;
        
        try {
            // Disable animations for bulk updates
            if (options.bulk) {
                chart.options.animation.duration = 0;
            }

            // Update data
            if (newData.labels) {
                chart.data.labels = newData.labels;
            }

            if (newData.datasets) {
                newData.datasets.forEach((dataset, index) => {
                    if (chart.data.datasets[index]) {
                        // Update existing dataset
                        Object.assign(chart.data.datasets[index], dataset);
                    } else {
                        // Add new dataset
                        chart.data.datasets.push(dataset);
                    }
                });
            }

            // Update chart
            chart.update(options.mode || 'default');

            // Update last update timestamp
            instance.lastUpdate = Date.now();

        } catch (error) {
            // Error handling suppressed for production
            console.warn('Chart update failed:', error);
        }
    }

    /**
     * Initialize resize observer for responsive charts
     */
    initResizeObserver() {
        if (!('ResizeObserver' in window)) return;

        this.resizeObserver = new ResizeObserver(
            this.debounce((entries) => {
                entries.forEach(entry => {
                    const canvas = entry.target;
                    const chartId = canvas.id;
                    const instance = this.chartInstances.get(chartId);
                    
                    if (instance) {
                        // Queue resize update
                        this.batchUpdateChart(chartId, {}, { mode: 'resize' });
                    }
                });
            }, 150)
        );
    }

    /**
     * Create performance-optimized chart datasets
     */
    createOptimizedDataset(data, options = {}) {
        return {
            data: Array.isArray(data) ? data : [],
            backgroundColor: options.backgroundColor || 'rgba(139, 92, 246, 0.1)',
            borderColor: options.borderColor || '#8b5cf6',
            borderWidth: options.borderWidth || 2,
            fill: options.fill !== undefined ? options.fill : false,
            tension: options.tension || 0.2,
            pointRadius: options.pointRadius || 3,
            pointHoverRadius: options.pointHoverRadius || 5,
            pointBackgroundColor: options.pointBackgroundColor || '#8b5cf6',
            pointBorderColor: options.pointBorderColor || '#ffffff',
            pointBorderWidth: options.pointBorderWidth || 2,
            // Performance optimizations
            parsing: false,
            normalized: true,
            spanGaps: true
        };
    }

    /**
     * Destroy chart and cleanup resources
     */
    destroyChart(chartId) {
        const instance = this.chartInstances.get(chartId);
        if (!instance) return;

        const { chart, canvas } = instance;

        // Remove from resize observer
        if (this.resizeObserver && canvas) {
            this.resizeObserver.unobserve(canvas);
        }

        // Destroy chart
        chart.destroy();

        // Remove from instances
        this.chartInstances.delete(chartId);
    }

    /**
     * Get chart performance metrics
     */
    getChartMetrics() {
        const metrics = {
            totalCharts: this.chartInstances.size,
            activeUpdates: this.updateQueue.size,
            avgUpdateInterval: 0,
            oldestChart: null,
            newestChart: null
        };

        let totalAge = 0;
        let oldestTime = Date.now();
        let newestTime = 0;

        this.chartInstances.forEach((instance, id) => {
            const age = Date.now() - instance.lastUpdate;
            totalAge += age;
            
            if (instance.lastUpdate < oldestTime) {
                oldestTime = instance.lastUpdate;
                metrics.oldestChart = id;
            }
            
            if (instance.lastUpdate > newestTime) {
                newestTime = instance.lastUpdate;
                metrics.newestChart = id;
            }
        });

        if (this.chartInstances.size > 0) {
            metrics.avgUpdateInterval = totalAge / this.chartInstances.size;
        }

        return metrics;
    }

    /**
     * Cleanup all resources
     */
    cleanup() {
        // Cancel pending animation frame
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }

        // Destroy all charts
        this.chartInstances.forEach((instance, id) => {
            this.destroyChart(id);
        });

        // Disconnect resize observer
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }

        // Clear queues
        this.updateQueue.clear();
        this.chartInstances.clear();
    }

    /**
     * Debounce utility for performance optimization
     */
    debounce(func, wait, immediate = false) {
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
}

// Global chart optimizer instance
window.ChartOptimizer = window.ChartOptimizer || new ChartPerformanceOptimizer();

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.ChartOptimizer) {
        window.ChartOptimizer.cleanup();
    }
});

// Performance monitoring for charts
if (window.PerformanceUtils) {
    // Monitor chart performance every 5 seconds
    setInterval(() => {
        const metrics = window.ChartOptimizer.getChartMetrics();
        window.PerformanceUtils.performanceMetrics.set('chart_performance', {
            ...metrics,
            timestamp: Date.now()
        });
    }, 5000);
}