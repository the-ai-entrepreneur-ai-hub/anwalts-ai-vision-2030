/**
 * AnwaltsAI Client Configuration
 */
window.API_BASE = 'http://localhost:8009';

// Alternative configurations for different environments
const CONFIG = {
  development: 'http://localhost:8009',
  production: 'https://your-production-domain.com',
  local: 'http://127.0.0.1:8009'
};

// Auto-detect environment and set API_BASE
if (!window.API_BASE) {
  window.API_BASE = CONFIG.development;
}

console.log('🔧 AnwaltsAI Config loaded - API Base:', window.API_BASE);