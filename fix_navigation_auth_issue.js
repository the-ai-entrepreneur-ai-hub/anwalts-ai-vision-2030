// Fix navigation authentication issue
// This script prevents unwanted re-authentication on browser back/forward navigation

(function() {
    'use strict';
    
    console.log('🔧 Navigation auth fix loading...');
    
    // Check if user has valid authentication
    function isUserAuthenticated() {
        const token = localStorage.getItem('anwalts_auth_token');
        const user = localStorage.getItem('anwalts_user');
        
        if (!token || !user) {
            console.log('❌ No auth token or user data found');
            return false;
        }
        
        try {
            const userData = JSON.parse(user);
            if (userData && userData.email) {
                console.log('✅ User authenticated:', userData.email);
                return true;
            }
        } catch (e) {
            console.log('❌ Invalid user data in storage');
            return false;
        }
        
        return false;
    }
    
    // Prevent unwanted login redirects on navigation
    function preventNavigationAuthRedirect() {
        // Override any existing popstate handlers that might trigger auth
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;
        
        // Intercept history API calls
        history.pushState = function(state, title, url) {
            console.log('🔄 History pushState intercepted:', url);
            if (isUserAuthenticated() && url && url.includes('/workspace')) {
                // User is authenticated and navigating within workspace - allow it
                return originalPushState.call(this, state, title, url);
            }
            return originalPushState.call(this, state, title, url);
        };
        
        history.replaceState = function(state, title, url) {
            console.log('🔄 History replaceState intercepted:', url);
            return originalReplaceState.call(this, state, title, url);
        };
        
        // Handle popstate events (back/forward navigation)
        window.addEventListener('popstate', function(event) {
            console.log('🔙 Popstate event triggered');
            
            // If user is authenticated, don't trigger re-authentication
            if (isUserAuthenticated()) {
                console.log('✅ User is authenticated - allowing navigation');
                return;
            }
            
            // Only redirect to login if user is not authenticated
            console.log('❌ User not authenticated - considering redirect');
        }, true); // Use capture phase to intercept before other handlers
    }
    
    // Enhanced session validation
    function enhancedSessionCheck() {
        const currentUrl = window.location.href;
        
        // If we're in the workspace and user is authenticated, stay there
        if (currentUrl.includes('/workspace') && isUserAuthenticated()) {
            console.log('✅ In workspace with valid session - no action needed');
            return true;
        }
        
        // If we're in workspace but not authenticated, redirect to login
        if (currentUrl.includes('/workspace') && !isUserAuthenticated()) {
            console.log('❌ In workspace without auth - redirecting to login');
            window.location.href = '/anwalts-ai-app.html';
            return false;
        }
        
        return true;
    }
    
    // Initialize the fix
    function initNavigationAuthFix() {
        console.log('🚀 Initializing navigation auth fix...');
        
        // Prevent unwanted auth redirects
        preventNavigationAuthRedirect();
        
        // Do initial session check
        enhancedSessionCheck();
        
        // Set up periodic session validation (optional)
        setInterval(() => {
            if (window.location.href.includes('/workspace') && !isUserAuthenticated()) {
                console.log('⚠️ Session expired - redirecting to login');
                window.location.href = '/anwalts-ai-app.html';
            }
        }, 60000); // Check every minute
        
        console.log('✅ Navigation auth fix initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavigationAuthFix);
    } else {
        initNavigationAuthFix();
    }
    
})();