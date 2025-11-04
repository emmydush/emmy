// Voice Assistant Implementation for Inventory Management System
// Uses Web Speech API for voice input/output functionality (no API keys required)

class VoiceAssistant {
    constructor() {
        this.recognition = null;
        this.synthesis = null;
        this.isListening = false;
        this.floatingButton = null;
        this.statusIndicator = null;
        this.commandHistory = [];
        
        // Check browser support and initialize
        this.init();
    }
    
    init() {
        // Check for Web Speech API support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.synthesis = window.speechSynthesis;
        
        if (!SpeechRecognition) {
            console.warn('Web Speech API Speech Recognition is not supported in this browser.');
            this.showBrowserSupportWarning();
        } else {
            // Initialize speech recognition
            try {
                this.recognition = new SpeechRecognition();
                this.recognition.continuous = false;
                this.recognition.interimResults = true;
                this.recognition.lang = 'en-US';
                console.log('Speech recognition initialized successfully');
            } catch (error) {
                console.error('Error initializing speech recognition:', error);
                this.showInitializationError();
            }
        }
        
        if (!this.synthesis) {
            console.warn('Web Speech API Speech Synthesis is not supported in this browser.');
        }
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Create UI elements
        this.createFloatingButton();
        this.createStatusIndicator();
        
        // Preload voices
        this.preloadVoices();
    }
    
    preloadVoices() {
        if (this.synthesis) {
            // Trigger voice loading
            this.synthesis.getVoices();
        }
    }
    
    showBrowserSupportWarning() {
        console.warn('Web Speech API is not supported. Voice commands will not work.');
        // Don't show alert automatically to avoid annoying users
    }
    
    showInitializationError() {
        console.error('Failed to initialize speech recognition.');
    }
    
    setupEventListeners() {
        if (!this.recognition) return;
        
        // Speech recognition events
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateStatus('Listening...', 'listening');
            this.updateFloatingButton('listening');
            console.log('Speech recognition started');
        };
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            // Get interim and final results
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Update UI with recognized text
            if (finalTranscript) {
                console.log('Final transcript:', finalTranscript);
                this.updateStatus(`Recognized: ${finalTranscript}`, 'success');
                this.commandHistory.push({
                    command: finalTranscript,
                    timestamp: new Date()
                });
                
                // Process the command
                this.processCommand(finalTranscript);
            }
            
            if (interimTranscript) {
                console.log('Interim transcript:', interimTranscript);
                this.updateStatus(`Listening: ${interimTranscript}`, 'listening');
            }
        };
        
        this.recognition.onerror = (event) => {
            this.isListening = false;
            this.updateStatus(`Error: ${event.error}`, 'error');
            this.updateFloatingButton('error');
            console.error('Speech recognition error', event.error);
            
            // Handle specific errors
            if (event.error === 'not-allowed') {
                this.speak('Microphone permission denied. Please check your browser permissions.');
            } else if (event.error === 'no-speech') {
                this.speak('No speech detected. Please try again.');
            } else if (event.error === 'audio-capture') {
                this.speak('No microphone detected. Please connect a microphone and try again.');
            } else {
                this.speak(`Speech recognition error: ${event.error}`);
            }
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            if (!this.statusIndicator.textContent.includes('Recognized')) {
                this.updateStatus('Ready', 'idle');
            }
            this.updateFloatingButton('idle');
            console.log('Speech recognition ended');
        };
    }
    
    createFloatingButton() {
        // Create floating microphone button
        this.floatingButton = document.createElement('button');
        this.floatingButton.id = 'voiceAssistantButton';
        this.floatingButton.innerHTML = '<i class="fas fa-microphone"></i>';
        this.floatingButton.title = 'Voice Assistant';
        this.floatingButton.className = 'voice-assistant-button';
        
        // Add styles
        this.floatingButton.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #0d6efd;
            color: white;
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            cursor: pointer;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            transition: all 0.3s ease;
        `;
        
        // Add hover effect
        this.floatingButton.addEventListener('mouseenter', () => {
            this.floatingButton.style.transform = 'scale(1.1)';
            this.floatingButton.style.boxShadow = '0 6px 12px rgba(0,0,0,0.3)';
        });
        
        this.floatingButton.addEventListener('mouseleave', () => {
            this.floatingButton.style.transform = 'scale(1)';
            this.floatingButton.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        });
        
        // Add click event
        this.floatingButton.addEventListener('click', () => {
            this.toggleVoiceRecognition();
        });
        
        // Add to document
        document.body.appendChild(this.floatingButton);
    }
    
    createStatusIndicator() {
        // Create status indicator
        this.statusIndicator = document.createElement('div');
        this.statusIndicator.id = 'voiceAssistantStatus';
        this.statusIndicator.textContent = 'Ready';
        this.statusIndicator.className = 'voice-assistant-status';
        
        // Add styles
        this.statusIndicator.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 30px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
            color: #6c757d;
            display: none;
            z-index: 9998;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 300px;
        `;
        
        // Add to document
        document.body.appendChild(this.statusIndicator);
    }
    
    updateStatus(message, type) {
        if (!this.statusIndicator) return;
        
        this.statusIndicator.textContent = message;
        this.statusIndicator.style.display = 'block';
        
        // Set status color based on type
        switch (type) {
            case 'listening':
                this.statusIndicator.style.backgroundColor = '#e3f2fd';
                this.statusIndicator.style.color = '#1976d2';
                break;
            case 'success':
                this.statusIndicator.style.backgroundColor = '#e8f5e9';
                this.statusIndicator.style.color = '#388e3c';
                break;
            case 'error':
                this.statusIndicator.style.backgroundColor = '#ffebee';
                this.statusIndicator.style.color = '#d32f2f';
                break;
            default:
                this.statusIndicator.style.backgroundColor = '#f8f9fa';
                this.statusIndicator.style.color = '#6c757d';
        }
        
        // Hide status after 3 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                this.statusIndicator.style.display = 'none';
            }, 3000);
        }
    }
    
    updateFloatingButton(state) {
        if (!this.floatingButton) return;
        
        switch (state) {
            case 'listening':
                this.floatingButton.style.background = '#1976d2';
                this.floatingButton.style.animation = 'pulse 1s infinite';
                break;
            case 'success':
                this.floatingButton.style.background = '#388e3c';
                this.floatingButton.style.animation = 'none';
                setTimeout(() => {
                    this.floatingButton.style.background = '#0d6efd';
                }, 2000);
                break;
            case 'error':
                this.floatingButton.style.background = '#d32f2f';
                this.floatingButton.style.animation = 'shake 0.5s';
                setTimeout(() => {
                    this.floatingButton.style.background = '#0d6efd';
                    this.floatingButton.style.animation = 'none';
                }, 2000);
                break;
            default:
                this.floatingButton.style.background = '#0d6efd';
                this.floatingButton.style.animation = 'none';
        }
    }
    
    toggleVoiceRecognition() {
        if (!this.recognition) {
            this.speak('Voice recognition is not supported in your browser. Please use Chrome or Edge for best results.');
            return;
        }
        
        if (this.isListening) {
            this.stopVoiceRecognition();
        } else {
            this.startVoiceRecognition();
        }
    }
    
    startVoiceRecognition() {
        try {
            console.log('Attempting to start speech recognition...');
            this.recognition.start();
            console.log('Speech recognition start command sent');
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            this.updateStatus('Error starting voice recognition', 'error');
            
            // Handle permission errors specifically
            if (error.name === 'NotAllowedError') {
                this.speak('Microphone permission denied. Please check your browser permissions.');
            } else {
                this.speak('Error starting voice recognition. Please check your browser settings and permissions.');
            }
        }
    }
    
    stopVoiceRecognition() {
        if (this.recognition) {
            console.log('Stopping speech recognition...');
            this.recognition.stop();
            this.isListening = false;
            console.log('Speech recognition stopped');
        }
    }
    
    processCommand(command) {
        command = command.toLowerCase().trim();
        console.log('Processing command:', command);
        
        // Handle different types of commands
        if (this.handleNavigationCommands(command)) return;
        if (this.handleReportCommands(command)) return;
        if (this.handleProductCommands(command)) return;
        if (this.handleInventoryCommands(command)) return;
        if (this.handleSaleCommands(command)) return;
        if (this.handleSystemCommands(command)) return;
        if (this.handleGreetingCommands(command)) return;
        if (this.handleHelpCommands(command)) return;
        if (this.handleCustomerCommands(command)) return;
        if (this.handleSupplierCommands(command)) return;
        if (this.handleExpenseCommands(command)) return;
        if (this.handlePurchaseCommands(command)) return;
        
        // Default response for unrecognized commands
        this.speak("I didn't understand that command. Try saying 'show profit', 'add new product', or 'logout'.");
    }
    
    handleNavigationCommands(command) {
        if (command.includes('go to') || command.includes('navigate to') || 
            command.includes('take me to') || command.includes('open')) {
            const page = command
                .replace('go to', '')
                .replace('navigate to', '')
                .replace('take me to', '')
                .replace('open', '')
                .trim();
            this.navigateToPage(page);
            return true;
        }
        return false;
    }
    
    handleReportCommands(command) {
        // Profit-related commands
        if (command.includes('profit') || command.includes('loss') || command.includes('earnings')) {
            this.speak('Showing profit and loss report.');
            window.location.href = '/reports/profit-loss/';
            return true;
        }
        
        // Sales-related commands
        if (command.includes('sales') || command.includes('revenue')) {
            this.speak('Opening sales dashboard.');
            window.location.href = '/sales/';
            return true;
        }
        
        // Expenses-related commands
        if (command.includes('expenses') || command.includes('costs')) {
            this.speak('Showing expenses report.');
            window.location.href = '/reports/expenses/';
            return true;
        }
        
        // Inventory-related commands
        if (command.includes('inventory') || command.includes('stock report')) {
            this.speak('Showing inventory report.');
            window.location.href = '/reports/inventory/';
            return true;
        }
        
        return false;
    }
    
    handleProductCommands(command) {
        if (command.includes('add product') || command.includes('create product') || command.includes('new product')) {
            this.speak('Opening add product form.');
            window.location.href = '/products/create/';
            return true;
        }
        
        if (command.includes('list products') || command.includes('all products')) {
            this.speak('Showing all products.');
            window.location.href = '/products/';
            return true;
        }
        
        // Product categories
        if (command.includes('product categories') || command.includes('categories')) {
            this.speak('Showing product categories.');
            window.location.href = '/products/categories/';
            return true;
        }
        
        return false;
    }
    
    handleInventoryCommands(command) {
        if (command.includes('check stock') || command.includes('low stock') || command.includes('out of stock')) {
            this.speak('Showing products with low quantity.');
            window.location.href = '/products/?status=low_stock';
            return true;
        }
        
        if (command.includes('expired products') || command.includes('expired items')) {
            const today = new Date().toISOString().split('T')[0];
            this.speak('Showing expired products.');
            window.location.href = `/products/?expiry_date_before=${today}`;
            return true;
        }
        
        return false;
    }
    
    handleSaleCommands(command) {
        // Point of Sale commands
        if (command.includes('point of sale') || command.includes('pos')) {
            this.speak('Opening point of sale system.');
            window.location.href = '/sales/pos/';
            return true;
        }
        
        // Regular sales commands
        if (command.includes('show sales') || command.includes('sales dashboard')) {
            this.speak('Opening sales dashboard.');
            window.location.href = '/sales/';
            return true;
        }
        
        // Add sale
        if (command.includes('add sale') || command.includes('create sale') || command.includes('new sale')) {
            this.speak('Opening point of sale system.');
            window.location.href = '/sales/pos/';
            return true;
        }
        
        // List sales
        if (command.includes('list sales') || command.includes('all sales') || command.includes('sale list')) {
            this.speak('Showing all sales.');
            window.location.href = '/sales/';
            return true;
        }
        
        return false;
    }
    
    handleSystemCommands(command) {
        // Enhanced logout command recognition with correct URL
        if (command.includes('logout') || command.includes('log out') || command.includes('sign out') || command.includes('exit')) {
            this.speak('Logging out. Goodbye!');
            setTimeout(() => {
                // Use the correct logout URL based on the URL patterns shown
                window.location.href = '/accounts/logout/';
            }, 1500);
            return true;
        }
        
        if (command.includes('dashboard') || command.includes('home')) {
            this.speak('Returning to dashboard.');
            // Check if we're in the admin system or superadmin system
            if (window.location.pathname.startsWith('/superadmin/')) {
                window.location.href = '/superadmin/';
            } else if (window.location.pathname.startsWith('/admin_system/')) {
                window.location.href = '/admin_system/';
            } else {
                window.location.href = '/dashboard/';
            }
            return true;
        }
        
        // Settings
        if (command.includes('settings') || command.includes('configuration')) {
            this.speak('Opening settings page.');
            window.location.href = '/settings/';
            return true;
        }
        
        return false;
    }
    
    handleGreetingCommands(command) {
        if (command.includes('hello') || command.includes('hi') || command.includes('hey') || 
            command.includes('good morning') || command.includes('good afternoon') || command.includes('good evening')) {
            const hours = new Date().getHours();
            let greeting = '';
            
            if (hours < 12) {
                greeting = 'Good morning';
            } else if (hours < 18) {
                greeting = 'Good afternoon';
            } else {
                greeting = 'Good evening';
            }
            
            this.speak(`${greeting}! How can I help you today?`);
            return true;
        }
        return false;
    }
    
    handleHelpCommands(command) {
        if (command.includes('help') || command.includes('what can you do')) {
            this.speak('I can help you navigate the system, show reports, manage products, check inventory, handle sales and point of sale, manage customers and suppliers, and more. Try saying commands like: show profit, add new product, check stock, point of sale, or logout.');
            return true;
        }
        return false;
    }
    
    handleCustomerCommands(command) {
        // Add customer
        if (command.includes('add customer') || command.includes('create customer') || command.includes('new customer')) {
            this.speak('Opening add customer form.');
            window.location.href = '/customers/create/';
            return true;
        }
        
        // List customers
        if (command.includes('list customers') || command.includes('all customers') || command.includes('customer list')) {
            this.speak('Showing all customers.');
            window.location.href = '/customers/';
            return true;
        }
        
        return false;
    }
    
    handleSupplierCommands(command) {
        // Add supplier
        if (command.includes('add supplier') || command.includes('create supplier') || command.includes('new supplier')) {
            this.speak('Opening add supplier form.');
            window.location.href = '/suppliers/create/';
            return true;
        }
        
        // List suppliers
        if (command.includes('list suppliers') || command.includes('all suppliers') || command.includes('supplier list')) {
            this.speak('Showing all suppliers.');
            window.location.href = '/suppliers/';
            return true;
        }
        
        return false;
    }
    
    handleExpenseCommands(command) {
        // Add expense
        if (command.includes('add expense') || command.includes('create expense') || command.includes('new expense')) {
            this.speak('Opening add expense form.');
            window.location.href = '/expenses/create/';
            return true;
        }
        
        // List expenses
        if (command.includes('list expenses') || command.includes('all expenses') || command.includes('expense list')) {
            this.speak('Showing all expenses.');
            window.location.href = '/expenses/';
            return true;
        }
        
        return false;
    }
    
    handlePurchaseCommands(command) {
        // Add purchase
        if (command.includes('add purchase') || command.includes('create purchase') || command.includes('new purchase')) {
            this.speak('Opening add purchase form.');
            window.location.href = '/purchases/create/';
            return true;
        }
        
        // List purchases
        if (command.includes('list purchases') || command.includes('all purchases') || command.includes('purchase list')) {
            this.speak('Showing all purchases.');
            window.location.href = '/purchases/';
            return true;
        }
        
        return false;
    }
    
    navigateToPage(page) {
        page = page.toLowerCase();
        
        // Check what system we're currently in to determine the correct dashboard URL
        let dashboardUrl = '/dashboard/';
        if (window.location.pathname.startsWith('/superadmin/')) {
            dashboardUrl = '/superadmin/';
        } else if (window.location.pathname.startsWith('/admin_system/')) {
            dashboardUrl = '/admin_system/';
        }
        
        const pages = {
            'dashboard': dashboardUrl,
            'home': dashboardUrl,
            'products': '/products/',
            'product list': '/products/',
            'customers': '/customers/',
            'customer list': '/customers/',
            'suppliers': '/suppliers/',
            'supplier list': '/suppliers/',
            'sales': '/sales/',
            'sale list': '/sales/',
            'purchases': '/purchases/',
            'purchase list': '/purchases/',
            'reports': '/reports/',
            'report list': '/reports/',
            'settings': '/settings/',
            // Admin system entries
            'admin': '/admin_system/',
            'admin dashboard': '/admin_system/',
            'admin system': '/admin_system/',
            // Super admin entries
            'super admin': '/superadmin/',
            'superadmin': '/superadmin/',
            'platform admin': '/superadmin/',
            // Point of Sale entries
            'point of sale': '/sales/pos/',
            'pos': '/sales/pos/',
            'new sale': '/sales/pos/',
            'create sale': '/sales/pos/',
            // Sales entries
            'sales': '/sales/',
            'sale list': '/sales/',
            // Purchases entries
            'purchases': '/purchases/',
            'purchase list': '/purchases/',
            'new purchase': '/purchases/create/',
            'create purchase': '/purchases/create/',
            // Expenses entries
            'expenses': '/expenses/',
            'expense list': '/expenses/',
            'add expense': '/expenses/create/',
            'new expense': '/expenses/create/',
            // Profit and Loss reports
            'profit': '/reports/profit-loss/',
            'profit loss': '/reports/profit-loss/',
            'profit and loss': '/reports/profit-loss/',
            'loss report': '/reports/profit-loss/',
            // Other reports
            'sales report': '/reports/sales/',
            'inventory report': '/reports/inventory/',
            'inventory': '/reports/inventory/',
            'stock report': '/reports/inventory/',
            'expense report': '/reports/expenses/',
            // Product management
            'add product': '/products/create/',
            'new product': '/products/create/',
            'product categories': '/products/categories/',
            'categories': '/products/categories/',
            // People management
            'add customer': '/customers/create/',
            'new customer': '/customers/create/',
            'add supplier': '/suppliers/create/',
            'new supplier': '/suppliers/create/',
            'customers': '/customers/',
            'customer list': '/customers/',
            'suppliers': '/suppliers/',
            'supplier list': '/suppliers/',
        };
        
        if (pages[page]) {
            this.speak(`Navigating to ${page}`);
            window.location.href = pages[page];
        } else {
            this.speak(`I don't know how to navigate to ${page}. Try saying dashboard, products, or profit.`);
        }
    }
    
    speak(text) {
        // Add a small delay to ensure the speech synthesis is ready
        setTimeout(() => {
            if (!this.synthesis) {
                console.warn('Speech synthesis not supported');
                return;
            }
            
            // Cancel any ongoing speech
            try {
                this.synthesis.cancel();
            } catch (e) {
                console.warn('Could not cancel ongoing speech:', e);
            }
            
            // Create utterance
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            // Add event listeners for debugging
            utterance.onstart = () => {
                console.log('Speech started:', text);
            };
            
            utterance.onend = () => {
                console.log('Speech ended');
            };
            
            utterance.onerror = (event) => {
                console.error('Speech error:', event);
            };
            
            // Speak
            this.synthesis.speak(utterance);
        }, 100);
    }
    
    // Public methods for external control
    start() {
        this.startVoiceRecognition();
    }
    
    stop() {
        this.stopVoiceRecognition();
    }
    
    reset() {
        try {
            // Stop any ongoing recognition
            if (this.recognition && this.isListening) {
                this.recognition.stop();
            }
            
            // Reset flags
            this.isListening = false;
            
            // Reset UI
            if (this.floatingButton) {
                this.floatingButton.innerHTML = '<i class="fas fa-microphone"></i>';
                this.floatingButton.style.background = '#0d6efd';
                this.floatingButton.style.animation = 'none';
            }
            
            if (this.statusIndicator) {
                this.statusIndicator.style.display = 'none';
            }
            
            console.log('Voice assistant reset successfully');
            return true;
        } catch (error) {
            console.error('Error resetting voice assistant:', error);
            return false;
        }
    }
    
    // Method to add new commands (for future expansion)
    addCommand(phrase, action) {
        // This would be implemented in a more sophisticated system
        // For now, we're using the existing command processing structure
        console.log(`Added new command: ${phrase}`);
    }
}

// Initialize voice assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize voice assistant functionality
    window.voiceAssistant = new VoiceAssistant();
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        @keyframes shake {
            0% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            50% { transform: translateX(5px); }
            75% { transform: translateX(-5px); }
            100% { transform: translateX(0); }
        }
    `;
    document.head.appendChild(style);
});

// Export for potential use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceAssistant;
}