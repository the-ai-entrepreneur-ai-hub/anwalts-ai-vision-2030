/**
 * AnwaltsAI Production Configuration for portal-anwalts.ai
 * Environment-specific settings for the enhanced registration system
 */

// Production configuration for portal-anwalts.ai
const AnwaltsAIConfig = {
    // Environment detection
    environment: window.location.hostname === 'portal-anwalts.ai' ? 'production' : 'development',
    
    // API Configuration
    api: {
        production: {
            baseUrl: 'https://portal-anwalts.ai/api',
            wsUrl: 'wss://portal-anwalts.ai/ws',
            timeout: 10000
        },
        development: {
            baseUrl: 'http://127.0.0.1:8000',
            wsUrl: 'ws://127.0.0.1:8000/ws',
            timeout: 5000
        }
    },
    
    // Enhanced Registration Settings
    registration: {
        // Required fields for enhanced registration
        requiredFields: [
            'email', 
            'password', 
            'first_name', 
            'last_name'
        ],
        
        // Optional enhanced fields
        enhancedFields: [
            'title',
            'law_firm',
            'specializations',
            'bar_number',
            'years_experience',
            'phone',
            'mobile',
            'street_address',
            'city',
            'state',
            'postal_code',
            'country',
            'language',
            'timezone',
            'bio'
        ],
        
        // German legal specializations
        legalSpecializations: [
            'Zivilrecht',
            'Strafrecht', 
            'Arbeitsrecht',
            'Familienrecht',
            'Handelsrecht',
            'Steuerrecht',
            'Immobilienrecht',
            'Versicherungsrecht',
            'IT-Recht',
            'Medizinrecht',
            'Erbrecht',
            'Verkehrsrecht'
        ],
        
        // German federal states
        germanStates: [
            'Baden-Württemberg',
            'Bayern',
            'Berlin',
            'Brandenburg',
            'Bremen',
            'Hamburg',
            'Hessen',
            'Mecklenburg-Vorpommern',
            'Niedersachsen',
            'Nordrhein-Westfalen',
            'Rheinland-Pfalz',
            'Saarland',
            'Sachsen',
            'Sachsen-Anhalt',
            'Schleswig-Holstein',
            'Thüringen'
        ]
    },
    
    // Feature flags for production
    features: {
        enhancedRegistration: true,
        basicRegistrationFallback: true,
        profileManagement: true,
        realTimeSync: true,
        aiSuggestions: true,
        documentGeneration: true
    },
    
    // Security settings for portal-anwalts.ai
    security: {
        enableCSRF: true,
        enableRateLimit: true,
        maxLoginAttempts: 5,
        sessionTimeout: 3600000, // 1 hour
        requirePasswordStrength: true,
        enableTwoFactor: false // Future enhancement
    },
    
    // UI/UX settings
    ui: {
        defaultLanguage: 'de',
        defaultTimezone: 'Europe/Berlin',
        theme: 'professional',
        enableAnimations: true,
        enableNotifications: true
    },
    
    // Analytics and monitoring
    monitoring: {
        enableMetrics: true,
        trackRegistrations: true,
        trackErrors: true,
        enablePerformanceMonitoring: true
    }
};

// Helper functions
AnwaltsAIConfig.getApiUrl = function() {
    const env = this.environment;
    return this.api[env].baseUrl;
};

AnwaltsAIConfig.getWebSocketUrl = function() {
    const env = this.environment;
    return this.api[env].wsUrl;
};

AnwaltsAIConfig.isProduction = function() {
    return this.environment === 'production';
};

AnwaltsAIConfig.isDevelopment = function() {
    return this.environment === 'development';
};

// Initialize API client with correct configuration
AnwaltsAIConfig.createApiClient = function() {
    return new AnwaltsAIApiClient(this.getApiUrl());
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnwaltsAIConfig;
}

// Make available globally
window.AnwaltsAIConfig = AnwaltsAIConfig;

// Log configuration in development
if (AnwaltsAIConfig.isDevelopment()) {
    console.log('🔧 AnwaltsAI Configuration Loaded:', {
        environment: AnwaltsAIConfig.environment,
        apiUrl: AnwaltsAIConfig.getApiUrl(),
        features: AnwaltsAIConfig.features,
        hostname: window.location.hostname
    });
}