/**
 * Crypto Polyfill for older browsers
 * Provides crypto.randomUUID() functionality
 */
(function() {
    'use strict';
    
    // Check if crypto.randomUUID is already available
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        console.log('✅ Native crypto.randomUUID available');
        return;
    }
    
    console.log('⚠️  Adding crypto.randomUUID polyfill');
    
    // Ensure crypto object exists
    if (typeof crypto === 'undefined') {
        window.crypto = {};
    }
    
    // Polyfill for crypto.randomUUID()
    crypto.randomUUID = function() {
        // Use crypto.getRandomValues if available
        if (typeof crypto.getRandomValues === 'function') {
            const arr = new Uint8Array(16);
            crypto.getRandomValues(arr);
            
            // Set version (4) and variant bits
            arr[6] = (arr[6] & 0x0f) | 0x40; // Version 4
            arr[8] = (arr[8] & 0x3f) | 0x80; // Variant 10
            
            const hex = Array.from(arr, byte => 
                byte.toString(16).padStart(2, '0')
            ).join('');
            
            return [
                hex.substring(0, 8),
                hex.substring(8, 12),
                hex.substring(12, 16),
                hex.substring(16, 20),
                hex.substring(20, 32)
            ].join('-');
        }
        
        // Fallback for very old browsers
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    };
    
    console.log('✅ crypto.randomUUID polyfill loaded');
})();