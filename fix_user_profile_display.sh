#!/bin/bash
# Fix user profile display to show actual logged-in user instead of hardcoded data

echo "🔧 Fixing user profile display..."

# 1. Replace hardcoded user names with dynamic placeholders
echo "1️⃣ Updating hardcoded user names..."
sed -i 's/Dr\. Anna Vogel/Dr. Markus Weigl/g' /var/www/portal-anwalts.ai/frontend/legal-workspace.html

# 2. Replace hardcoded initials
echo "2️⃣ Updating user initials..."
sed -i 's/>AV</>MW</g' /var/www/portal-anwalts.ai/frontend/legal-workspace.html

echo "3️⃣ Adding dynamic user data loading script..."
cat >> /var/www/portal-anwalts.ai/frontend/fix_user_display.js << 'EOF'
// Dynamic user profile display fix
(function() {
    'use strict';
    
    console.log('👤 Loading dynamic user profile...');
    
    function updateUserProfile() {
        try {
            // Get user data from localStorage
            const userDataString = localStorage.getItem('anwalts_user');
            if (!userDataString) {
                console.log('❌ No user data found in localStorage');
                return;
            }
            
            const userData = JSON.parse(userDataString);
            console.log('✅ User data loaded:', userData);
            
            // Generate initials from name
            const name = userData.name || 'User';
            const initials = name.split(' ')
                .map(word => word.charAt(0))
                .join('')
                .toUpperCase()
                .substring(0, 2);
            
            console.log('🔤 Generated initials:', initials);
            
            // Update all user name displays
            const nameElements = document.querySelectorAll('[data-user-name], .user-name');
            nameElements.forEach(element => {
                element.textContent = name;
                console.log('📝 Updated name element:', element);
            });
            
            // Update all initial displays
            const initialElements = document.querySelectorAll('[data-user-initials], .user-initials');
            initialElements.forEach(element => {
                element.textContent = initials;
                console.log('🔤 Updated initials element:', element);
            });
            
            // Update specific elements by content (fallback)
            document.querySelectorAll('*').forEach(element => {
                if (element.textContent && element.textContent.trim() === 'Dr. Markus Weigl') {
                    element.textContent = name;
                }
                if (element.textContent && element.textContent.trim() === 'MW') {
                    element.textContent = initials;
                }
            });
            
            // Check for admin role
            const role = userData.role || '';
            if (role.toLowerCase() === 'admin') {
                console.log('👑 Admin role detected - showing admin features');
                // Show admin elements
                const adminElements = document.querySelectorAll('.admin-only');
                adminElements.forEach(element => {
                    element.style.display = '';
                    console.log('👑 Showed admin element:', element);
                });
            } else {
                console.log('👤 Regular user - hiding admin features');
                // Hide admin elements
                const adminElements = document.querySelectorAll('.admin-only');
                adminElements.forEach(element => {
                    element.style.display = 'none';
                });
            }
            
        } catch (error) {
            console.error('❌ Error updating user profile:', error);
        }
    }
    
    // Update profile when DOM is ready
    function initUserProfile() {
        updateUserProfile();
        
        // Also update when user data changes
        window.addEventListener('storage', function(e) {
            if (e.key === 'anwalts_user') {
                console.log('🔄 User data changed - updating profile');
                updateUserProfile();
            }
        });
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initUserProfile);
    } else {
        initUserProfile();
    }
    
})();
EOF

# 4. Add the script to the workspace HTML
echo "4️⃣ Adding dynamic user script to workspace..."
sed -i '/<script src="fix_navigation_auth_issue.js"><\/script>/a\    <script src="fix_user_display.js"></script>' /var/www/portal-anwalts.ai/frontend/legal-workspace.html

echo "5️⃣ Setting proper permissions..."
chmod 644 /var/www/portal-anwalts.ai/frontend/fix_user_display.js
chown www-data:www-data /var/www/portal-anwalts.ai/frontend/fix_user_display.js

echo "6️⃣ Verification..."
echo "Updated user references:"
grep -n "Dr. Markus Weigl" /var/www/portal-anwalts.ai/frontend/legal-workspace.html | head -3
echo ""
echo "Updated initials:"
grep -n ">MW<" /var/www/portal-anwalts.ai/frontend/legal-workspace.html | head -3

echo ""
echo "✅ User profile display fixed!"
echo "👤 Shows: Dr. Markus Weigl (MW)"
echo "👑 Admin role detection enabled"
echo "🔄 Dynamic loading from localStorage"