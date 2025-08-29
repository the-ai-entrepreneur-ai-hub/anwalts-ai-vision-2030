/**
 * Client Data Extraction Script for AnwaltsAI
 * Run this script in the browser console to extract data from localStorage/sessionStorage
 * Save the output to a JSON file for migration to PostgreSQL
 */

(function() {
    'use strict';
    
    console.log('🔍 AnwaltsAI Client Data Extraction Script');
    console.log('============================================');
    
    // Data extraction configuration
    const CONFIG = {
        // Keys to look for in localStorage and sessionStorage
        storageKeys: {
            templates: ['anwalts_templates', 'templates', 'law_templates'],
            clauses: ['anwalts_clauses', 'clauses', 'law_clauses', 'clause_library'],
            clipboard: ['anwalts_clipboard', 'clipboard', 'legal_clipboard'],
            user: ['anwalts_user', 'user_profile', 'current_user', 'user_info'],
            settings: ['anwalts_settings', 'app_settings', 'user_settings'],
            documents: ['anwalts_documents', 'documents', 'generated_documents'],
            favorites: ['anwalts_favorites', 'favorites', 'bookmarks']
        },
        // Include debug information
        includeDebug: true,
        // Include metadata
        includeMetadata: true
    };
    
    /**
     * Extract data from storage (localStorage or sessionStorage)
     */
    function extractFromStorage(storage, storageType) {
        console.log(`📦 Extracting from ${storageType}...`);
        
        const data = {};
        const keys = Object.keys(storage);
        
        console.log(`Found ${keys.length} keys in ${storageType}:`, keys);
        
        for (let i = 0; i < keys.length; i++) {
            const key = keys[i];
            try {
                const value = storage.getItem(key);
                
                if (value) {
                    // Try to parse as JSON
                    try {
                        data[key] = JSON.parse(value);
                    } catch (e) {
                        // Store as string if not JSON
                        data[key] = value;
                    }
                }
            } catch (error) {
                console.warn(`⚠️ Could not extract key '${key}':`, error.message);
            }
        }
        
        return data;
    }
    
    /**
     * Find data by key patterns
     */
    function findDataByPatterns(data, patterns) {
        const results = [];
        
        for (const [key, value] of Object.entries(data)) {
            for (const pattern of patterns) {
                if (key.toLowerCase().includes(pattern.toLowerCase())) {
                    results.push({ key, value, pattern });
                    break;
                }
            }
        }
        
        return results;
    }
    
    /**
     * Normalize template data
     */
    function normalizeTemplates(rawTemplates) {
        if (!Array.isArray(rawTemplates)) {
            if (typeof rawTemplates === 'object' && rawTemplates !== null) {
                // Convert object to array
                rawTemplates = Object.values(rawTemplates);
            } else {
                return [];
            }
        }
        
        return rawTemplates.map(template => {
            // Ensure required fields
            const normalized = {
                name: template.name || template.title || 'Unnamed Template',
                content: template.content || template.text || template.body || '',
                category: template.category || template.type || 'general',
                type: template.documentType || template.templateType || 'document'
            };
            
            // Optional fields
            if (template.usage_count || template.usageCount || template.count) {
                normalized.usage_count = parseInt(template.usage_count || template.usageCount || template.count) || 0;
            }
            
            if (template.tags && Array.isArray(template.tags)) {
                normalized.tags = template.tags;
            }
            
            if (template.created_at || template.createdAt || template.dateCreated) {
                normalized.created_at = template.created_at || template.createdAt || template.dateCreated;
            }
            
            return normalized;
        });
    }
    
    /**
     * Normalize clause data
     */
    function normalizeClauses(rawClauses) {
        if (!Array.isArray(rawClauses)) {
            if (typeof rawClauses === 'object' && rawClauses !== null) {
                rawClauses = Object.values(rawClauses);
            } else {
                return [];
            }
        }
        
        return rawClauses.map(clause => {
            const normalized = {
                category: clause.category || clause.type || 'general',
                title: clause.title || clause.name || 'Unnamed Clause',
                content: clause.content || clause.text || clause.body || '',
                tags: clause.tags || [],
                language: clause.language || clause.lang || 'de'
            };
            
            // Optional fields
            if (clause.is_favorite || clause.isFavorite || clause.favorite) {
                normalized.is_favorite = Boolean(clause.is_favorite || clause.isFavorite || clause.favorite);
            }
            
            if (clause.usage_count || clause.usageCount || clause.count) {
                normalized.usage_count = parseInt(clause.usage_count || clause.usageCount || clause.count) || 0;
            }
            
            return normalized;
        });
    }
    
    /**
     * Normalize clipboard data
     */
    function normalizeClipboard(rawClipboard) {
        if (!Array.isArray(rawClipboard)) {
            if (typeof rawClipboard === 'object' && rawClipboard !== null) {
                rawClipboard = Object.values(rawClipboard);
            } else {
                return [];
            }
        }
        
        return rawClipboard.map(entry => {
            const normalized = {
                content: entry.content || entry.text || entry.value || '',
                source_type: entry.source_type || entry.sourceType || entry.source || 'manual',
                metadata: entry.metadata || entry.meta || {}
            };
            
            // Handle expiration
            if (entry.expires_at || entry.expiresAt || entry.expiry) {
                normalized.expires_at = entry.expires_at || entry.expiresAt || entry.expiry;
            }
            
            return normalized;
        });
    }
    
    /**
     * Normalize user data
     */
    function normalizeUser(rawUser) {
        if (!rawUser || typeof rawUser !== 'object') {
            return {
                email: '',
                name: '',
                role: 'assistant'
            };
        }
        
        return {
            email: rawUser.email || rawUser.userEmail || rawUser.mail || '',
            name: rawUser.name || rawUser.fullName || rawUser.displayName || rawUser.username || '',
            role: rawUser.role || rawUser.userRole || rawUser.type || 'assistant'
        };
    }
    
    /**
     * Main extraction function
     */
    function extractAllData() {
        console.log('🚀 Starting data extraction...');
        
        // Extract from localStorage
        const localData = extractFromStorage(localStorage, 'localStorage');
        
        // Extract from sessionStorage
        const sessionData = extractFromStorage(sessionStorage, 'sessionStorage');
        
        // Combine all data
        const allData = { ...localData, ...sessionData };
        
        console.log('📊 Raw data extracted:', Object.keys(allData));
        
        // Find specific data types
        const extractedData = {
            user_info: {},
            templates: [],
            clauses: [],
            clipboard: [],
            debug: {
                total_keys_found: Object.keys(allData).length,
                extraction_timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                url: window.location.href
            }
        };
        
        // Extract templates
        const templateMatches = findDataByPatterns(allData, CONFIG.storageKeys.templates);
        console.log('📄 Template matches:', templateMatches.length);
        
        for (const match of templateMatches) {
            try {
                const normalized = normalizeTemplates(match.value);
                extractedData.templates.push(...normalized);
                console.log(`  ✅ Extracted ${normalized.length} templates from '${match.key}'`);
            } catch (error) {
                console.error(`  ❌ Error processing templates from '${match.key}':`, error);
            }
        }
        
        // Extract clauses
        const clauseMatches = findDataByPatterns(allData, CONFIG.storageKeys.clauses);
        console.log('📜 Clause matches:', clauseMatches.length);
        
        for (const match of clauseMatches) {
            try {
                const normalized = normalizeClauses(match.value);
                extractedData.clauses.push(...normalized);
                console.log(`  ✅ Extracted ${normalized.length} clauses from '${match.key}'`);
            } catch (error) {
                console.error(`  ❌ Error processing clauses from '${match.key}':`, error);
            }
        }
        
        // Extract clipboard
        const clipboardMatches = findDataByPatterns(allData, CONFIG.storageKeys.clipboard);
        console.log('📋 Clipboard matches:', clipboardMatches.length);
        
        for (const match of clipboardMatches) {
            try {
                const normalized = normalizeClipboard(match.value);
                extractedData.clipboard.push(...normalized);
                console.log(`  ✅ Extracted ${normalized.length} clipboard entries from '${match.key}'`);
            } catch (error) {
                console.error(`  ❌ Error processing clipboard from '${match.key}':`, error);
            }
        }
        
        // Extract user info
        const userMatches = findDataByPatterns(allData, CONFIG.storageKeys.user);
        console.log('👤 User matches:', userMatches.length);
        
        for (const match of userMatches) {
            try {
                const normalized = normalizeUser(match.value);
                if (normalized.email || normalized.name) {
                    extractedData.user_info = { ...extractedData.user_info, ...normalized };
                    console.log(`  ✅ Extracted user info from '${match.key}'`);
                }
            } catch (error) {
                console.error(`  ❌ Error processing user info from '${match.key}':`, error);
            }
        }
        
        // Add all raw data for debugging (if enabled)
        if (CONFIG.includeDebug) {
            extractedData.debug.raw_data = allData;
        }
        
        // Remove duplicates
        extractedData.templates = removeDuplicates(extractedData.templates, 'name');
        extractedData.clauses = removeDuplicates(extractedData.clauses, 'title');
        extractedData.clipboard = removeDuplicates(extractedData.clipboard, 'content');
        
        return extractedData;
    }
    
    /**
     * Remove duplicates from array based on key
     */
    function removeDuplicates(array, key) {
        const seen = new Set();
        return array.filter(item => {
            const value = item[key];
            if (seen.has(value)) {
                return false;
            }
            seen.add(value);
            return true;
        });
    }
    
    /**
     * Download data as JSON file
     */
    function downloadJSON(data, filename = 'anwalts_ai_client_data.json') {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log(`💾 Downloaded data as '${filename}'`);
    }
    
    /**
     * Display summary
     */
    function displaySummary(data) {
        console.log('📈 Extraction Summary:');
        console.log('=====================');
        console.log(`👤 User Info: ${data.user_info.email || 'Not found'}`);
        console.log(`📄 Templates: ${data.templates.length}`);
        console.log(`📜 Clauses: ${data.clauses.length}`);
        console.log(`📋 Clipboard Entries: ${data.clipboard.length}`);
        console.log(`🐛 Total Storage Keys: ${data.debug.total_keys_found}`);
        
        if (data.templates.length > 0) {
            console.log('\n📄 Template Categories:');
            const categories = [...new Set(data.templates.map(t => t.category))];
            categories.forEach(cat => {
                const count = data.templates.filter(t => t.category === cat).length;
                console.log(`  - ${cat}: ${count}`);
            });
        }
        
        if (data.clauses.length > 0) {
            console.log('\n📜 Clause Categories:');
            const categories = [...new Set(data.clauses.map(c => c.category))];
            categories.forEach(cat => {
                const count = data.clauses.filter(c => c.category === cat).length;
                console.log(`  - ${cat}: ${count}`);
            });
        }
    }
    
    /**
     * Main execution
     */
    try {
        // Extract all data
        const extractedData = extractAllData();
        
        // Display summary
        displaySummary(extractedData);
        
        // Provide data for inspection
        window.anwaltsAIExtractedData = extractedData;
        
        console.log('\n🎉 Extraction completed successfully!');
        console.log('📦 Data is available in: window.anwaltsAIExtractedData');
        console.log('\n💡 To download the data:');
        console.log('   downloadAnwaltsAIData()');
        console.log('\n💡 To view the data:');
        console.log('   console.log(window.anwaltsAIExtractedData)');
        
        // Create download function
        window.downloadAnwaltsAIData = function(filename) {
            downloadJSON(extractedData, filename);
        };
        
        // Auto-download option (commented out by default)
        // downloadJSON(extractedData);
        
        return extractedData;
        
    } catch (error) {
        console.error('❌ Extraction failed:', error);
        throw error;
    }
    
})();

// Usage instructions
console.log(`
📚 USAGE INSTRUCTIONS:
======================

1. Run this script in your browser console while on the AnwaltsAI website
2. Check the extraction summary in the console
3. Download the data by running: downloadAnwaltsAIData()
4. Save the downloaded JSON file
5. Use the migration script to import data to PostgreSQL:
   
   python migration/migrate_client_data.py migrate --file your_data.json

📝 NOTES:
- The script looks for common storage key patterns
- Data is normalized to match the database schema
- Duplicates are automatically removed
- All extraction is done client-side for privacy

🔍 DEBUGGING:
- Check window.anwaltsAIExtractedData for the extracted data
- Enable CONFIG.includeDebug for raw data access
- Check console logs for detailed extraction info
`);

// Make functions globally available for manual use
window.AnwaltsAIExtractor = {
    extract: function() {
        return window.anwaltsAIExtractedData;
    },
    download: function(filename) {
        if (window.anwaltsAIExtractedData) {
            window.downloadAnwaltsAIData(filename);
        } else {
            console.error('No data extracted. Run the extraction script first.');
        }
    },
    inspect: function() {
        if (window.anwaltsAIExtractedData) {
            console.log('Extracted Data:', window.anwaltsAIExtractedData);
            return window.anwaltsAIExtractedData;
        } else {
            console.error('No data extracted. Run the extraction script first.');
        }
    }
};