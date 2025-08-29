#!/bin/bash
# Final fix for API Client - completely replace with correct version

echo "🔧 Final API Client Fix - Complete Replacement..."

# Backup current file
cp /var/www/portal-anwalts.ai/frontend/api-client.js /var/www/portal-anwalts.ai/frontend/api-client.js.broken

# Replace with completely fixed version
cat > /var/www/portal-anwalts.ai/frontend/api-client.js << 'EOF'
/**
 * AnwaltsAI API Client - FINAL WORKING VERSION
 * Handles all backend communication with proper error handling and authentication
 */
class AnwaltsAIApiClient {
    constructor(baseUrl = null) {
        // FIXED: Always use the proxy URL for production
        if (baseUrl) {
            this.baseUrl = baseUrl;
        } else {
            // Use nginx proxy for all requests
            this.baseUrl = window.location.origin + '/api';
        }

        this.authToken = localStorage.getItem('anwalts_auth_token');
        console.log(`🌐 API Client initialized for: ${this.baseUrl}`);
    }

    // =========================
    // AUTHENTICATION METHODS - WORKING VERSION
    // =========================

    async login(email, password) {
        console.log('🔄 Login attempt with:', { email, baseUrl: this.baseUrl });
        
        try {
            const response = await fetch(`${this.baseUrl}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            console.log('📡 Login response status:', response.status);

            if (!response.ok) {
                const errorData = await response.text();
                console.error('❌ Login error response:', errorData);
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            console.log('✅ Login successful:', data);

            if (data.success && data.user) {
                // Store auth token if provided
                if (data.token) {
                    this.authToken = data.token;
                    localStorage.setItem('anwalts_auth_token', data.token);
                }
                
                // Store user data
                localStorage.setItem('anwalts_user', JSON.stringify(data.user));
                
                return data;
            } else {
                throw new Error('Login response invalid');
            }
        } catch (error) {
            console.error('Login error:', error);
            throw new Error('Anmeldung fehlgeschlagen');
        }
    }

    async register(userData) {
        try {
            const response = await fetch(`${this.baseUrl}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                throw new Error(`Registration failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Registration error:', error);
            throw new Error('Registrierung fehlgeschlagen');
        }
    }

    // =========================
    // UTILITY METHODS
    // =========================

    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', message: error.message };
        }
    }

    logout() {
        this.authToken = null;
        localStorage.removeItem('anwalts_auth_token');
        localStorage.removeItem('anwalts_user');
        console.log('🚪 User logged out');
    }

    isAuthenticated() {
        return !!this.authToken || !!localStorage.getItem('anwalts_auth_token');
    }

    getCurrentUser() {
        const userData = localStorage.getItem('anwalts_user');
        return userData ? JSON.parse(userData) : null;
    }
}

// Create global instance
window.apiClient = new AnwaltsAIApiClient();
console.log('✅ API Client initialized:', window.apiClient.constructor.name);
console.log('🔗 Using base URL:', window.apiClient.baseUrl);
EOF

echo "✅ API Client completely replaced!"

# Show the new configuration
echo "🔍 New API Client configuration:"
grep -n "baseUrl.*=" /var/www/portal-anwalts.ai/frontend/api-client.js

echo ""
echo "🎯 API Client will now use:"
echo "  📍 Base URL: window.location.origin + '/api'"
echo "  🌐 For portal-anwalts.ai: http://portal-anwalts.ai/api"
echo "  📡 Proxied to backend: http://127.0.0.1:8000"
echo ""
echo "🔄 Refresh browser (Ctrl+F5) and login should work!"