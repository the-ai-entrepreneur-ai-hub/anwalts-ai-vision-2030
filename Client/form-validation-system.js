/**
 * AnwaltsAI Enhanced Form Validation & UX System
 * Provides real-time validation, accessibility features, and consistent UX patterns
 */

class FormValidationSystem {
    constructor(options = {}) {
        this.options = {
            realTimeValidation: true,
            showSuccessStates: true,
            accessibilityEnabled: true,
            animateTransitions: true,
            debounceDelay: 300,
            ...options
        };
        
        this.validators = new Map();
        this.formStates = new Map();
        this.init();
    }

    init() {
        this.setupGlobalValidators();
        this.setupEventListeners();
        this.enhanceExistingForms();
        this.injectStyles();
    }

    /**
     * Setup global validation rules
     */
    setupGlobalValidators() {
        this.validators.set('required', {
            validate: (value) => value !== null && value !== undefined && String(value).trim() !== '',
            message: 'Dieses Feld ist erforderlich'
        });

        this.validators.set('email', {
            validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            message: 'Bitte geben Sie eine gültige E-Mail-Adresse ein'
        });

        this.validators.set('minLength', {
            validate: (value, params) => String(value).length >= params.min,
            message: (params) => `Mindestens ${params.min} Zeichen erforderlich`
        });

        this.validators.set('maxLength', {
            validate: (value, params) => String(value).length <= params.max,
            message: (params) => `Maximal ${params.max} Zeichen erlaubt`
        });

        this.validators.set('pattern', {
            validate: (value, params) => new RegExp(params.regex).test(value),
            message: (params) => params.message || 'Ungültiges Format'
        });

        this.validators.set('numeric', {
            validate: (value) => /^\d+$/.test(String(value)),
            message: 'Nur Zahlen sind erlaubt'
        });

        this.validators.set('phone', {
            validate: (value) => /^[\+]?[1-9][\d]{0,15}$/.test(String(value).replace(/[\s\-\(\)]/g, '')),
            message: 'Bitte geben Sie eine gültige Telefonnummer ein'
        });
    }

    /**
     * Setup event listeners for form interactions
     */
    setupEventListeners() {
        // Use event delegation for dynamic forms
        document.addEventListener('input', this.handleInput.bind(this));
        document.addEventListener('blur', this.handleBlur.bind(this));
        document.addEventListener('focus', this.handleFocus.bind(this));
        document.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Form field state change listeners
        document.addEventListener('change', this.handleChange.bind(this));
    }

    /**
     * Handle real-time input validation
     */
    handleInput(event) {
        const field = event.target;
        if (!this.isValidatedField(field)) return;

        // Debounce validation for better UX
        clearTimeout(field._validationTimeout);
        field._validationTimeout = setTimeout(() => {
            if (this.options.realTimeValidation) {
                this.validateField(field);
            }
        }, this.options.debounceDelay);
    }

    /**
     * Handle field blur events
     */
    handleBlur(event) {
        const field = event.target;
        if (!this.isValidatedField(field)) return;

        this.validateField(field);
        this.updateFieldState(field, 'blurred');
    }

    /**
     * Handle field focus events
     */
    handleFocus(event) {
        const field = event.target;
        if (!this.isValidatedField(field)) return;

        this.clearFieldErrors(field);
        this.updateFieldState(field, 'focused');
    }

    /**
     * Handle form submission
     */
    handleSubmit(event) {
        const form = event.target;
        if (!form.classList.contains('enhanced-form')) return;

        event.preventDefault();
        
        const isValid = this.validateForm(form);
        
        if (isValid) {
            this.handleSuccessfulSubmission(form);
        } else {
            this.handleFailedSubmission(form);
        }
    }

    /**
     * Handle field changes (for selects, checkboxes, etc.)
     */
    handleChange(event) {
        const field = event.target;
        if (!this.isValidatedField(field)) return;

        this.validateField(field);
    }

    /**
     * Check if field should be validated
     */
    isValidatedField(field) {
        return field.hasAttribute('data-validation') || 
               field.closest('.enhanced-form');
    }

    /**
     * Validate individual field
     */
    validateField(field, showSuccess = true) {
        const validationRules = this.getFieldValidationRules(field);
        const value = this.getFieldValue(field);
        const errors = [];

        // Run each validation rule
        for (const rule of validationRules) {
            const validator = this.validators.get(rule.type);
            if (!validator) continue;

            const isValid = validator.validate(value, rule.params);
            if (!isValid) {
                const message = typeof validator.message === 'function' 
                    ? validator.message(rule.params)
                    : validator.message;
                errors.push(message);
            }
        }

        // Update field UI
        if (errors.length > 0) {
            this.showFieldErrors(field, errors);
            return false;
        } else {
            this.clearFieldErrors(field);
            if (showSuccess && this.options.showSuccessStates) {
                this.showFieldSuccess(field);
            }
            return true;
        }
    }

    /**
     * Validate entire form
     */
    validateForm(form) {
        const fields = form.querySelectorAll('[data-validation], input, select, textarea');
        let isValid = true;
        let firstInvalidField = null;

        fields.forEach(field => {
            if (!this.isValidatedField(field)) return;
            
            const fieldValid = this.validateField(field, false);
            if (!fieldValid && isValid) {
                isValid = false;
                firstInvalidField = field;
            }
        });

        // Focus first invalid field
        if (!isValid && firstInvalidField) {
            firstInvalidField.focus();
        }

        return isValid;
    }

    /**
     * Get validation rules for a field
     */
    getFieldValidationRules(field) {
        const rules = [];
        const validationAttr = field.getAttribute('data-validation');
        
        if (validationAttr) {
            const ruleStrings = validationAttr.split('|');
            ruleStrings.forEach(ruleString => {
                const [type, paramsString] = ruleString.split(':');
                const params = paramsString ? JSON.parse(paramsString) : {};
                rules.push({ type, params });
            });
        }

        // HTML5 validation attributes
        if (field.hasAttribute('required')) {
            rules.push({ type: 'required', params: {} });
        }
        
        if (field.type === 'email') {
            rules.push({ type: 'email', params: {} });
        }
        
        if (field.hasAttribute('minlength')) {
            rules.push({ 
                type: 'minLength', 
                params: { min: parseInt(field.getAttribute('minlength')) }
            });
        }
        
        if (field.hasAttribute('maxlength')) {
            rules.push({ 
                type: 'maxLength', 
                params: { max: parseInt(field.getAttribute('maxlength')) }
            });
        }

        return rules;
    }

    /**
     * Get field value
     */
    getFieldValue(field) {
        if (field.type === 'checkbox') {
            return field.checked;
        } else if (field.type === 'radio') {
            const form = field.closest('form');
            const checked = form.querySelector(`input[name="${field.name}"]:checked`);
            return checked ? checked.value : null;
        } else {
            return field.value;
        }
    }

    /**
     * Show field errors
     */
    showFieldErrors(field, errors) {
        const container = this.getOrCreateFieldContainer(field);
        
        // Remove existing error states
        this.clearFieldErrors(field);
        
        // Add error class
        container.classList.add('field-error');
        container.classList.remove('field-success', 'field-focused');
        
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error-message';
        errorElement.setAttribute('role', 'alert');
        errorElement.setAttribute('aria-live', 'polite');
        
        if (errors.length === 1) {
            errorElement.textContent = errors[0];
        } else {
            const ul = document.createElement('ul');
            errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                ul.appendChild(li);
            });
            errorElement.appendChild(ul);
        }
        
        // Add error to container
        container.appendChild(errorElement);
        
        // Update ARIA attributes
        if (this.options.accessibilityEnabled) {
            field.setAttribute('aria-invalid', 'true');
            field.setAttribute('aria-describedby', 
                (field.getAttribute('aria-describedby') || '') + ' ' + this.getFieldId(field) + '-error'
            );
            errorElement.id = this.getFieldId(field) + '-error';
        }
    }

    /**
     * Clear field errors
     */
    clearFieldErrors(field) {
        const container = this.getOrCreateFieldContainer(field);
        
        // Remove error classes
        container.classList.remove('field-error');
        
        // Remove error messages
        const errorMessages = container.querySelectorAll('.field-error-message');
        errorMessages.forEach(msg => msg.remove());
        
        // Clear ARIA attributes
        if (this.options.accessibilityEnabled) {
            field.setAttribute('aria-invalid', 'false');
            const describedBy = field.getAttribute('aria-describedby');
            if (describedBy) {
                field.setAttribute('aria-describedby', 
                    describedBy.replace(this.getFieldId(field) + '-error', '').trim()
                );
            }
        }
    }

    /**
     * Show field success state
     */
    showFieldSuccess(field) {
        const container = this.getOrCreateFieldContainer(field);
        
        container.classList.add('field-success');
        container.classList.remove('field-error');
        
        // Add success indicator if not exists
        if (!container.querySelector('.field-success-icon')) {
            const successIcon = document.createElement('div');
            successIcon.className = 'field-success-icon';
            successIcon.innerHTML = '✓';
            successIcon.setAttribute('aria-label', 'Eingabe gültig');
            container.appendChild(successIcon);
        }
    }

    /**
     * Update field state
     */
    updateFieldState(field, state) {
        const container = this.getOrCreateFieldContainer(field);
        
        // Remove all state classes
        container.classList.remove('field-focused', 'field-blurred');
        
        // Add current state
        container.classList.add(`field-${state}`);
        
        // Store state
        this.formStates.set(this.getFieldId(field), state);
    }

    /**
     * Get or create field container
     */
    getOrCreateFieldContainer(field) {
        let container = field.closest('.form-field');
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'form-field';
            field.parentNode.insertBefore(container, field);
            container.appendChild(field);
        }
        
        return container;
    }

    /**
     * Get unique field ID
     */
    getFieldId(field) {
        if (!field.id) {
            field.id = 'field-' + Math.random().toString(36).substr(2, 9);
        }
        return field.id;
    }

    /**
     * Handle successful form submission
     */
    handleSuccessfulSubmission(form) {
        // Show success state
        form.classList.add('form-success');
        
        // Create success message
        const successMessage = document.createElement('div');
        successMessage.className = 'form-success-message';
        successMessage.textContent = 'Formular erfolgreich übermittelt!';
        successMessage.setAttribute('role', 'alert');
        successMessage.setAttribute('aria-live', 'polite');
        
        form.insertBefore(successMessage, form.firstChild);
        
        // Scroll to success message
        successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Hide success message after delay
        setTimeout(() => {
            successMessage.remove();
            form.classList.remove('form-success');
        }, 5000);
    }

    /**
     * Handle failed form submission
     */
    handleFailedSubmission(form) {
        // Show error state
        form.classList.add('form-has-errors');
        
        // Create error summary
        const errorSummary = document.createElement('div');
        errorSummary.className = 'form-error-summary';
        errorSummary.setAttribute('role', 'alert');
        errorSummary.setAttribute('aria-live', 'polite');
        
        const errorTitle = document.createElement('h3');
        errorTitle.textContent = 'Bitte korrigieren Sie die folgenden Fehler:';
        errorSummary.appendChild(errorTitle);
        
        const errorList = document.createElement('ul');
        const errorFields = form.querySelectorAll('.field-error');
        
        errorFields.forEach(fieldContainer => {
            const field = fieldContainer.querySelector('input, select, textarea');
            const label = this.getFieldLabel(field);
            const errorMessage = fieldContainer.querySelector('.field-error-message');
            
            if (errorMessage) {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.href = '#' + this.getFieldId(field);
                link.textContent = `${label}: ${errorMessage.textContent}`;
                link.onclick = (e) => {
                    e.preventDefault();
                    field.focus();
                };
                li.appendChild(link);
                errorList.appendChild(li);
            }
        });
        
        errorSummary.appendChild(errorList);
        form.insertBefore(errorSummary, form.firstChild);
        
        // Scroll to error summary
        errorSummary.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Remove error summary when form becomes valid
        setTimeout(() => {
            if (!form.querySelector('.field-error')) {
                errorSummary.remove();
                form.classList.remove('form-has-errors');
            }
        }, 1000);
    }

    /**
     * Get field label text
     */
    getFieldLabel(field) {
        const label = document.querySelector(`label[for="${field.id}"]`) || 
                     field.closest('.form-field')?.querySelector('label');
        return label ? label.textContent.trim() : field.name || 'Feld';
    }

    /**
     * Enhance existing forms
     */
    enhanceExistingForms() {
        const forms = document.querySelectorAll('form:not(.enhanced-form)');
        forms.forEach(form => this.enhanceForm(form));
        
        // Enhanced existing filter selects
        const filterSelects = document.querySelectorAll('.filter-select, .filter-input');
        filterSelects.forEach(field => this.enhanceField(field));
    }

    /**
     * Enhance a specific form
     */
    enhanceForm(form) {
        form.classList.add('enhanced-form');
        
        // Add form-level attributes
        form.setAttribute('novalidate', 'true'); // Use our custom validation
        
        // Enhance all fields in form
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => this.enhanceField(field));
    }

    /**
     * Enhance a specific field
     */
    enhanceField(field) {
        const container = this.getOrCreateFieldContainer(field);
        
        // Add enhanced field class
        field.classList.add('enhanced-field');
        
        // Ensure proper labeling for accessibility
        if (this.options.accessibilityEnabled) {
            this.ensureFieldLabeling(field);
        }
        
        // Add loading state capability
        this.addLoadingState(field);
        
        // Add clear button for text inputs
        if (field.type === 'text' || field.type === 'email' || field.type === 'search') {
            this.addClearButton(field);
        }
    }

    /**
     * Ensure proper field labeling for accessibility
     */
    ensureFieldLabeling(field) {
        let label = document.querySelector(`label[for="${field.id}"]`);
        
        if (!label) {
            label = field.closest('.form-field')?.querySelector('label');
        }
        
        if (!label && field.placeholder) {
            // Create label from placeholder
            label = document.createElement('label');
            label.textContent = field.placeholder;
            label.htmlFor = this.getFieldId(field);
            label.className = 'sr-only'; // Screen reader only
            field.parentNode.insertBefore(label, field);
        }
        
        // Add ARIA attributes
        if (label) {
            field.setAttribute('aria-labelledby', label.id || this.getFieldId(field) + '-label');
        }
    }

    /**
     * Add loading state functionality
     */
    addLoadingState(field) {
        field._setLoading = (isLoading) => {
            const container = this.getOrCreateFieldContainer(field);
            
            if (isLoading) {
                container.classList.add('field-loading');
                field.disabled = true;
            } else {
                container.classList.remove('field-loading');
                field.disabled = false;
            }
        };
    }

    /**
     * Add clear button to text fields
     */
    addClearButton(field) {
        const container = this.getOrCreateFieldContainer(field);
        
        if (container.querySelector('.field-clear-btn')) return;
        
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'field-clear-btn';
        clearBtn.innerHTML = '×';
        clearBtn.setAttribute('aria-label', 'Feld leeren');
        clearBtn.style.display = field.value ? 'block' : 'none';
        
        clearBtn.onclick = () => {
            field.value = '';
            field.focus();
            this.clearFieldErrors(field);
            clearBtn.style.display = 'none';
            field.dispatchEvent(new Event('input'));
        };
        
        // Show/hide clear button based on content
        field.addEventListener('input', () => {
            clearBtn.style.display = field.value ? 'block' : 'none';
        });
        
        container.appendChild(clearBtn);
    }

    /**
     * Inject enhanced form styles
     */
    injectStyles() {
        const styleId = 'enhanced-form-styles';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* Enhanced Form Field Container */
            .form-field {
                position: relative;
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
            }
            
            /* Enhanced Form Fields */
            .enhanced-field {
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 0.95rem;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }
            
            .enhanced-field:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
                background: rgba(255, 255, 255, 0.15);
            }
            
            .enhanced-field::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
            
            /* Field States */
            .field-focused {
                transform: translateY(-2px);
            }
            
            .field-success .enhanced-field {
                border-color: #4ade80;
                background: rgba(74, 222, 128, 0.1);
            }
            
            .field-error .enhanced-field {
                border-color: #f87171;
                background: rgba(248, 113, 113, 0.1);
                animation: fieldShake 0.4s ease-in-out;
            }
            
            @keyframes fieldShake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-4px); }
                75% { transform: translateX(4px); }
            }
            
            /* Field Loading State */
            .field-loading .enhanced-field {
                background: rgba(255, 255, 255, 0.05);
                cursor: wait;
            }
            
            .field-loading::after {
                content: '';
                position: absolute;
                right: 1rem;
                top: 50%;
                transform: translateY(-50%);
                width: 16px;
                height: 16px;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-left: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: translateY(-50%) rotate(0deg); }
                100% { transform: translateY(-50%) rotate(360deg); }
            }
            
            /* Success Icon */
            .field-success-icon {
                position: absolute;
                right: 1rem;
                top: 50%;
                transform: translateY(-50%);
                color: #4ade80;
                font-weight: bold;
                font-size: 1.1rem;
                pointer-events: none;
                animation: successPop 0.3s ease-out;
            }
            
            @keyframes successPop {
                0% { transform: translateY(-50%) scale(0); opacity: 0; }
                50% { transform: translateY(-50%) scale(1.2); opacity: 1; }
                100% { transform: translateY(-50%) scale(1); opacity: 1; }
            }
            
            /* Clear Button */
            .field-clear-btn {
                position: absolute;
                right: 0.5rem;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                color: rgba(255, 255, 255, 0.7);
                cursor: pointer;
                display: none;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                transition: all 0.2s ease;
            }
            
            .field-clear-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                color: #ffffff;
            }
            
            /* Error Messages */
            .field-error-message {
                margin-top: 0.5rem;
                color: #f87171;
                font-size: 0.85rem;
                animation: errorSlideDown 0.3s ease-out;
            }
            
            @keyframes errorSlideDown {
                0% { opacity: 0; transform: translateY(-10px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            
            .field-error-message ul {
                margin: 0;
                padding-left: 1rem;
            }
            
            .field-error-message li {
                margin-bottom: 0.25rem;
            }
            
            /* Form Success/Error States */
            .form-success-message {
                background: linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(34, 197, 94, 0.1) 100%);
                border: 1px solid #4ade80;
                border-radius: 8px;
                padding: 1rem;
                color: #4ade80;
                margin-bottom: 1.5rem;
                animation: successSlideDown 0.4s ease-out;
            }
            
            @keyframes successSlideDown {
                0% { opacity: 0; transform: translateY(-20px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            
            .form-error-summary {
                background: linear-gradient(135deg, rgba(248, 113, 113, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%);
                border: 1px solid #f87171;
                border-radius: 8px;
                padding: 1.5rem;
                color: #f87171;
                margin-bottom: 1.5rem;
                animation: errorSlideDown 0.4s ease-out;
            }
            
            .form-error-summary h3 {
                margin: 0 0 1rem 0;
                font-size: 1rem;
                font-weight: 600;
            }
            
            .form-error-summary ul {
                margin: 0;
                padding-left: 1rem;
            }
            
            .form-error-summary li {
                margin-bottom: 0.5rem;
            }
            
            .form-error-summary a {
                color: #f87171;
                text-decoration: underline;
                cursor: pointer;
            }
            
            .form-error-summary a:hover {
                color: #ffffff;
            }
            
            /* Enhanced Button Styles */
            .enhanced-form .btn {
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            
            .enhanced-form .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .enhanced-form .btn:active {
                transform: translateY(-1px);
            }
            
            /* Screen Reader Only */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            
            /* Mobile Responsive Enhancements */
            @media (max-width: 768px) {
                .form-field {
                    margin-bottom: 1rem;
                }
                
                .enhanced-field {
                    padding: 0.875rem 1rem;
                    font-size: 16px; /* Prevents zoom on iOS */
                }
                
                .field-clear-btn {
                    width: 32px;
                    height: 32px;
                    right: 0.25rem;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    /**
     * Add custom validator
     */
    addValidator(name, validator) {
        this.validators.set(name, validator);
    }

    /**
     * Get form validation state
     */
    getFormState(form) {
        const fields = form.querySelectorAll('.enhanced-field');
        const state = {
            isValid: true,
            fields: {},
            errors: []
        };

        fields.forEach(field => {
            const fieldState = {
                isValid: this.validateField(field, false),
                value: this.getFieldValue(field)
            };
            
            if (!fieldState.isValid) {
                state.isValid = false;
                const errors = field.closest('.form-field').querySelectorAll('.field-error-message');
                fieldState.errors = Array.from(errors).map(err => err.textContent);
                state.errors.push(...fieldState.errors);
            }
            
            state.fields[field.name || this.getFieldId(field)] = fieldState;
        });

        return state;
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.formValidationSystem = new FormValidationSystem();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormValidationSystem;
}