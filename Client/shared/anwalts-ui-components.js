/**
 * AnwaltsAI Shared UI Component Library
 * Consistent UI elements across landing page and dashboard
 */
class AnwaltsUIComponents {
    constructor() {
        this.components = {
            button: this.createButton,
            input: this.createInput,
            modal: this.createModal,
            card: this.createCard,
            loader: this.createLoader,
            notification: this.createNotification
        };
        console.log('🎨 AnwaltsAI UI Components initialized');
    }

    // Consistent button styling with blue theme
    createButton(text, type = 'primary', onClick = null, options = {}) {
        const button = document.createElement('button');
        button.textContent = text;
        button.className = `anwalts-btn anwalts-btn-${type}`;
        
        const baseStyles = `
            background: ${this.getButtonBackground(type)};
            border: ${this.getButtonBorder(type)};
            border-radius: 8px;
            color: ${this.getButtonColor(type)};
            font-weight: 600;
            padding: ${options.size === 'sm' ? '8px 16px' : '12px 24px'};
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            font-size: ${options.size === 'sm' ? '14px' : '16px'};
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            min-height: ${options.size === 'sm' ? '36px' : '44px'};
            outline: none;
        `;
        
        button.style.cssText = baseStyles;
        
        // Hover effects
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-1px)';
            button.style.boxShadow = this.getButtonShadow(type);
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = 'none';
        });
        
        // Focus effects
        button.addEventListener('focus', () => {
            button.style.boxShadow = `0 0 0 3px rgba(59, 130, 246, 0.2)`;
        });
        
        button.addEventListener('blur', () => {
            button.style.boxShadow = 'none';
        });
        
        if (onClick) button.addEventListener('click', onClick);
        return button;
    }

    getButtonBackground(type) {
        switch (type) {
            case 'primary':
                return 'linear-gradient(135deg, #3b82f6, #2563eb)';
            case 'secondary':
                return 'rgba(241, 245, 249, 0.8)';
            case 'danger':
                return 'linear-gradient(135deg, #ef4444, #dc2626)';
            default:
                return 'linear-gradient(135deg, #3b82f6, #2563eb)';
        }
    }

    getButtonBorder(type) {
        switch (type) {
            case 'primary':
                return '1px solid rgba(59, 130, 246, 0.3)';
            case 'secondary':
                return '1px solid #cbd5e1';
            case 'danger':
                return '1px solid rgba(239, 68, 68, 0.3)';
            default:
                return '1px solid rgba(59, 130, 246, 0.3)';
        }
    }

    getButtonColor(type) {
        switch (type) {
            case 'primary':
                return 'white';
            case 'secondary':
                return '#1e293b';
            case 'danger':
                return 'white';
            default:
                return 'white';
        }
    }

    getButtonShadow(type) {
        switch (type) {
            case 'primary':
                return '0 8px 25px rgba(59, 130, 246, 0.3)';
            case 'secondary':
                return '0 4px 15px rgba(0, 0, 0, 0.1)';
            case 'danger':
                return '0 8px 25px rgba(239, 68, 68, 0.3)';
            default:
                return '0 8px 25px rgba(59, 130, 246, 0.3)';
        }
    }

    // Consistent input styling with blue theme
    createInput(placeholder, type = 'text', options = {}) {
        const input = document.createElement('input');
        input.type = type;
        input.placeholder = placeholder;
        input.className = 'anwalts-input';
        
        input.style.cssText = `
            background: rgba(248, 250, 252, 0.9);
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            color: #1e293b;
            padding: 12px 16px;
            width: ${options.fullWidth ? '100%' : 'auto'};
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            font-size: 16px;
            outline: none;
        `;
        
        input.addEventListener('focus', () => {
            input.style.borderColor = '#3b82f6';
            input.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            input.style.background = 'rgba(248, 250, 252, 1)';
        });
        
        input.addEventListener('blur', () => {
            input.style.borderColor = '#e2e8f0';
            input.style.boxShadow = 'none';
            input.style.background = 'rgba(248, 250, 252, 0.9)';
        });
        
        return input;
    }

    // Consistent modal styling with blue glassmorphism
    createModal(content, title = '', options = {}) {
        const modal = document.createElement('div');
        modal.className = 'anwalts-modal';
        modal.innerHTML = `
            <div class="anwalts-modal-backdrop" style="
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(59, 130, 246, 0.1) 50%, rgba(15, 23, 42, 0.6) 100%);
                backdrop-filter: blur(12px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.3s ease;
            ">
                <div class="anwalts-modal-content" style="
                    background: linear-gradient(135deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.9));
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(59, 130, 246, 0.2);
                    border-radius: 16px;
                    max-width: ${options.maxWidth || '500px'};
                    width: 90%;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 40px rgba(59, 130, 246, 0.15);
                    transform: scale(0.9) translateY(20px);
                    transition: all 0.3s ease;
                ">
                    ${title ? `
                        <div class="modal-header" style="
                            padding: 24px; 
                            border-bottom: 1px solid #e2e8f0;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        ">
                            <h3 style="color: #1e293b; margin: 0; font-size: 20px; font-weight: 600;">${title}</h3>
                            <button class="modal-close" style="
                                background: none;
                                border: none;
                                font-size: 24px;
                                color: #64748b;
                                cursor: pointer;
                                padding: 4px;
                                border-radius: 4px;
                                transition: all 0.2s ease;
                            ">×</button>
                        </div>
                    ` : ''}
                    <div class="modal-body" style="padding: 24px; color: #1e293b;">
                        ${content}
                    </div>
                </div>
            </div>
        `;
        
        // Show modal with animation
        document.body.appendChild(modal);
        const backdrop = modal.querySelector('.anwalts-modal-backdrop');
        const modalContent = modal.querySelector('.anwalts-modal-content');
        
        setTimeout(() => {
            backdrop.style.opacity = '1';
            modalContent.style.transform = 'scale(1) translateY(0)';
        }, 10);
        
        // Close functionality
        const closeBtn = modal.querySelector('.modal-close');
        const closeModal = () => {
            backdrop.style.opacity = '0';
            content.style.transform = 'scale(0.9) translateY(20px)';
            setTimeout(() => modal.remove(), 300);
        };
        
        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) closeModal();
        });
        
        return modal;
    }

    // Consistent card styling
    createCard(content, options = {}) {
        const card = document.createElement('div');
        card.className = 'anwalts-card';
        card.innerHTML = content;
        
        card.style.cssText = `
            background: linear-gradient(135deg, rgba(248, 250, 252, 0.8), rgba(241, 245, 249, 0.6));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.1);
            border-radius: 12px;
            padding: ${options.padding || '24px'};
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.08);
            transition: all 0.3s ease;
        `;
        
        if (options.hover !== false) {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px)';
                card.style.boxShadow = '0 12px 25px rgba(59, 130, 246, 0.15)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 4px 15px rgba(59, 130, 246, 0.08)';
            });
        }
        
        return card;
    }

    // Consistent loader component
    createLoader(text = 'Loading...') {
        const loader = document.createElement('div');
        loader.className = 'anwalts-loader';
        loader.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 32px;
                text-align: center;
            ">
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 3px solid #e2e8f0;
                    border-top: 3px solid #3b82f6;
                    border-radius: 50%;
                    animation: anwalts-spin 1s linear infinite;
                    margin-bottom: 16px;
                "></div>
                <div style="color: #64748b; font-size: 16px;">${text}</div>
            </div>
        `;
        
        return loader;
    }

    // Notification system
    createNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = 'anwalts-notification';
        
        const colors = {
            info: { bg: 'rgba(59, 130, 246, 0.1)', border: '#3b82f6', text: '#1e40af' },
            success: { bg: 'rgba(16, 185, 129, 0.1)', border: '#10b981', text: '#065f46' },
            warning: { bg: 'rgba(245, 158, 11, 0.1)', border: '#f59e0b', text: '#92400e' },
            error: { bg: 'rgba(239, 68, 68, 0.1)', border: '#ef4444', text: '#991b1b' }
        };
        
        const color = colors[type] || colors.info;
        
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${color.bg};
                backdrop-filter: blur(12px);
                border: 1px solid ${color.border};
                border-radius: 8px;
                padding: 16px 20px;
                color: ${color.text};
                font-weight: 500;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                z-index: 10000;
                transform: translateX(400px);
                transition: transform 0.3s ease;
                max-width: 300px;
            ">
                ${message}
            </div>
        `;
        
        document.body.appendChild(notification);
        const notifEl = notification.firstElementChild;
        
        // Animate in
        setTimeout(() => notifEl.style.transform = 'translateX(0)', 10);
        
        // Auto remove
        setTimeout(() => {
            notifEl.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, duration);
        
        return notification;
    }

    // Utility methods
    showNotification(message, type = 'info', duration = 3000) {
        return this.createNotification(message, type, duration);
    }

    showModal(content, title = '', options = {}) {
        return this.createModal(content, title, options);
    }
}

// Initialize UI components globally
window.anwaltsUIComponents = new AnwaltsUIComponents();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnwaltsUIComponents;
}