/**
 * AnwaltsAI Session State Manager
 * Maintain user context across page transitions
 */
class AnwaltsSessionManager {
    constructor() {
        this.storageKeys = {
            user: 'anwalts_user',
            token: 'anwalts_auth_token',
            navigation: 'anwalts_navigation_context',
            theme: 'anwalts_theme_preference',
            workspace: 'anwalts_workspace_state',
            lastActivity: 'anwalts_last_activity'
        };
        this.sessionTimeout = 30 * 60 * 1000; // 30 minutes
        this.init();
        console.log('🔐 AnwaltsAI Session Manager initialized');
    }

    init() {
        this.restoreNavigationContext();
        this.setupSessionValidation();
        this.setupAutoRefresh();
        this.setupActivityTracking();
        this.setupBeforeUnloadHandler();
    }

    restoreNavigationContext() {
        const context = sessionStorage.getItem(this.storageKeys.navigation);
        if (context) {
            try {
                const navData = JSON.parse(context);
                console.log('🔄 Restored navigation context from:', navData.from);
                
                // Apply any pending state changes
                if (navData.userData) {
                    this.updateUserState(navData.userData);
                }
                
                // Restore theme state if available
                if (navData.themeState && window.anwaltsThemeManager) {
                    window.anwaltsThemeManager.applyTheme();
                }
                
                // Show transition completion notification
                if (window.anwaltsUIComponents) {
                    window.anwaltsUIComponents.showNotification(
                        'Welcome back! Your session was restored.',
                        'success',
                        2000
                    );
                }
                
                // Clean up after use
                sessionStorage.removeItem(this.storageKeys.navigation);
                
            } catch (error) {
                console.error('❌ Failed to restore navigation context:', error);
                sessionStorage.removeItem(this.storageKeys.navigation);
            }
        }
    }

    updateUserState(userData) {
        try {
            // Store user data with timestamp
            const userStateWithMeta = {
                ...userData,
                lastUpdate: Date.now(),
                sessionId: this.generateSessionId()
            };
            
            localStorage.setItem(this.storageKeys.user, JSON.stringify(userStateWithMeta));
            this.updateLastActivity();
            
            // Trigger user state update events
            window.dispatchEvent(new CustomEvent('anwalts:userStateUpdated', {
                detail: userData
            }));
            
            console.log('✅ User state updated for:', userData.email || userData.username || 'user');
            
        } catch (error) {
            console.error('❌ Failed to update user state:', error);
        }
    }

    validateSession() {
        const token = localStorage.getItem(this.storageKeys.token);
        const user = localStorage.getItem(this.storageKeys.user);
        const lastActivity = localStorage.getItem(this.storageKeys.lastActivity);
        
        if (!token || !user) {
            console.warn('⚠️ Invalid session: missing credentials');
            this.clearSession();
            return false;
        }
        
        // Check session timeout
        if (lastActivity) {
            const timeSinceActivity = Date.now() - parseInt(lastActivity);
            if (timeSinceActivity > this.sessionTimeout) {
                console.warn('⚠️ Session expired due to inactivity');
                this.clearSession();
                if (window.anwaltsUIComponents) {
                    window.anwaltsUIComponents.showNotification(
                        'Session expired. Please log in again.',
                        'warning',
                        4000
                    );
                }
                return false;
            }
        }
        
        // Validate token format (basic check)
        try {
            const tokenData = JSON.parse(atob(token.split('.')[1]));
            if (tokenData.exp && tokenData.exp * 1000 < Date.now()) {
                console.warn('⚠️ Token expired');
                this.clearSession();
                return false;
            }
        } catch (error) {
            console.warn('⚠️ Invalid token format');
            this.clearSession();
            return false;
        }
        
        return true;
    }

    clearSession() {
        Object.values(this.storageKeys).forEach(key => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
        
        // Trigger session cleared event
        window.dispatchEvent(new CustomEvent('anwalts:sessionCleared'));
        
        console.log('🧹 Session cleared');
    }

    setupSessionValidation() {
        // Validate session every 5 minutes
        setInterval(() => {
            if (!this.validateSession()) {
                // Redirect to landing page if on dashboard
                if (window.location.pathname.includes('dashboard')) {
                    if (window.anwaltsNavigationManager) {
                        window.anwaltsNavigationManager.goToLanding();
                    } else {
                        window.location.href = 'anwalts-ai-app.html';
                    }
                }
            }
        }, 5 * 60 * 1000);
    }

    setupAutoRefresh() {
        // Refresh token every 25 minutes if session is valid
        setInterval(async () => {
            if (this.validateSession() && window.apiClient) {
                try {
                    await window.apiClient.refreshToken();
                    console.log('🔄 Token refreshed automatically');
                } catch (error) {
                    console.warn('⚠️ Failed to refresh token:', error);
                }
            }
        }, 25 * 60 * 1000);
    }

    setupActivityTracking() {
        // Track user activity
        const activities = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        let activityThrottled = false;
        
        const updateActivity = () => {
            if (!activityThrottled) {
                this.updateLastActivity();
                activityThrottled = true;
                setTimeout(() => activityThrottled = false, 30000); // Throttle to every 30 seconds
            }
        };
        
        activities.forEach(activity => {
            document.addEventListener(activity, updateActivity, { passive: true });
        });
    }

    setupBeforeUnloadHandler() {
        window.addEventListener('beforeunload', () => {
            // Save workspace state before leaving
            this.saveWorkspaceState();
        });
    }

    updateLastActivity() {
        localStorage.setItem(this.storageKeys.lastActivity, Date.now().toString());
    }

    saveWorkspaceState() {
        try {
            const workspaceState = {
                currentPage: window.location.pathname,
                timestamp: Date.now(),
                scrollPosition: window.scrollY,
                activeSection: document.querySelector('.section-content.active')?.id || null
            };
            
            sessionStorage.setItem(this.storageKeys.workspace, JSON.stringify(workspaceState));
            console.log('💾 Workspace state saved');
            
        } catch (error) {
            console.error('❌ Failed to save workspace state:', error);
        }
    }

    restoreWorkspaceState() {
        try {
            const workspaceState = sessionStorage.getItem(this.storageKeys.workspace);
            if (workspaceState) {
                const state = JSON.parse(workspaceState);
                
                // Restore scroll position
                if (state.scrollPosition) {
                    setTimeout(() => window.scrollTo(0, state.scrollPosition), 100);
                }
                
                // Restore active section if on dashboard
                if (state.activeSection && window.dashboard && window.dashboard.switchSection) {
                    setTimeout(() => window.dashboard.switchSection(state.activeSection.replace('Content', '')), 200);
                }
                
                console.log('🔄 Workspace state restored');
            }
        } catch (error) {
            console.error('❌ Failed to restore workspace state:', error);
        }
    }

    generateSessionId() {
        return 'anwalts_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Public API methods
    getCurrentUser() {
        try {
            const userData = localStorage.getItem(this.storageKeys.user);
            return userData ? JSON.parse(userData) : null;
        } catch (error) {
            console.error('❌ Failed to get current user:', error);
            return null;
        }
    }

    isLoggedIn() {
        return this.validateSession();
    }

    getSessionInfo() {
        const user = this.getCurrentUser();
        const lastActivity = localStorage.getItem(this.storageKeys.lastActivity);
        
        return {
            isLoggedIn: this.isLoggedIn(),
            user: user,
            lastActivity: lastActivity ? new Date(parseInt(lastActivity)) : null,
            sessionTimeout: new Date(Date.now() + this.sessionTimeout)
        };
    }

    extendSession() {
        this.updateLastActivity();
        console.log('⏰ Session extended');
    }

    // Event handling for cross-page communication
    setupCrossPageCommunication() {
        // Listen for storage changes from other tabs
        window.addEventListener('storage', (event) => {
            if (event.key === this.storageKeys.token && !event.newValue) {
                // Token was removed in another tab
                console.log('🔄 Session ended in another tab');
                this.clearSession();
                
                if (window.location.pathname.includes('dashboard')) {
                    window.location.href = 'anwalts-ai-app.html';
                }
            }
        });
    }
}

// Initialize session manager globally
window.anwaltsSessionManager = new AnwaltsSessionManager();

// Restore workspace state when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.anwaltsSessionManager.restoreWorkspaceState();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnwaltsSessionManager;
}