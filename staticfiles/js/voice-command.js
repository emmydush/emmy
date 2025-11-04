// Voice Command Implementation for Smart Solution
// Uses Web Speech API for voice input/output functionality

class VoiceCommand {
    constructor() {
        this.recognition = null;
        this.synthesis = null;
        this.isListening = false;
        this.voiceButton = null;
        this.searchInput = null;
        this.statusIndicator = null;
        this.floatingButton = null;
        this.userName = ''; // Will be set from Django template
        this.companyName = ''; // Will be set from Django template
        this.hasProvidedWelcome = false; // Track if welcome has been provided
        this.speechQueue = []; // Queue for speech requests
        this.isSpeaking = false; // Track if currently speaking
        
        // Check if browser supports speech recognition and synthesis
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
                
                // Add maxAlternatives for better recognition
                this.recognition.maxAlternatives = 1;
                
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
        
        // Find voice command elements
        this.findElements();
        
        // Create floating microphone button
        this.createFloatingButton();
        
        // Set user and company names if available
        if (typeof window.userName !== 'undefined') {
            this.userName = window.userName;
        }
        if (typeof window.companyName !== 'undefined') {
            this.companyName = window.companyName;
        }
        
        // Preload voices to avoid first-time delays
        this.preloadVoices();
    }
    
    // Preload voices to avoid delays on first speak
    preloadVoices() {
        if (this.synthesis) {
            // Trigger voice loading
            this.synthesis.getVoices();
            
            // Listen for voices changed event
            this.synthesis.onvoiceschanged = () => {
                const voices = this.synthesis.getVoices();
                console.log(`Voices loaded: ${voices.length}`);
                if (voices.length > 0) {
                    console.log(`Default voice: ${voices[0].name}`);
                }
            };
        }
    }
    
    showBrowserSupportWarning() {
        // Show a warning in the console and potentially in the UI
        console.warn('Web Speech API is not supported. Voice commands will not work.');
        this.speak('Voice recognition is not supported in your browser. Please use Chrome or Edge for best results.');
    }
    
    showInitializationError() {
        console.error('Failed to initialize speech recognition.');
        this.speak('Failed to initialize voice recognition. Please check your browser settings.');
    }
    
    findElements() {
        this.voiceButton = document.getElementById('voiceCommandButton');
        this.searchInput = document.getElementById('searchInput');
        this.statusIndicator = document.getElementById('voiceStatus');
        
        // If elements exist, set up voice command functionality
        if (this.voiceButton && this.searchInput) {
            this.setupVoiceCommand();
        }
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
            
            // Update search input with recognized text
            if (finalTranscript) {
                console.log('Final transcript:', finalTranscript);
                this.searchInput.value = finalTranscript;
                this.updateStatus(`Recognized: ${finalTranscript}`, 'success');
                
                // Process the command
                this.processCommand(finalTranscript);
            }
            
            if (interimTranscript) {
                console.log('Interim transcript:', interimTranscript);
                this.searchInput.value = interimTranscript;
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
                // Show permission guide
                if (confirm('Microphone permission is required for voice commands. Would you like to learn how to enable it?')) {
                    window.location.href = '/settings/voice/permissions/';
                }
            } else if (event.error === 'no-speech') {
                this.speak('No speech detected. Please try again.');
            } else if (event.error === 'audio-capture') {
                this.speak('No microphone detected. Please connect a microphone and try again.');
            } else if (event.error === 'network') {
                this.speak('Network error. Please check your internet connection.');
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
    
    setupVoiceCommand() {
        // Add click event to voice button
        this.voiceButton.addEventListener('click', () => {
            this.toggleVoiceRecognition();
        });
        
        // Add visual feedback
        this.createStatusIndicator();
    }
    
    createStatusIndicator() {
        if (!this.statusIndicator) {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'voiceStatus';
            statusDiv.className = 'voice-status-indicator';
            statusDiv.textContent = 'Ready';
            statusDiv.style.cssText = `
                position: absolute;
                top: -25px;
                left: 0;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                color: #6c757d;
                display: none;
                z-index: 1000;
            `;
            
            this.voiceButton.parentElement.style.position = 'relative';
            this.voiceButton.parentElement.appendChild(statusDiv);
            this.statusIndicator = statusDiv;
        }
    }
    
    createFloatingButton() {
        // Create floating microphone button
        this.floatingButton = document.createElement('button');
        this.floatingButton.id = 'floatingVoiceButton';
        this.floatingButton.innerHTML = '<i class="fas fa-microphone"></i>';
        this.floatingButton.title = 'Voice Assistant';
        this.floatingButton.className = 'floating-voice-button';
        
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
        
        // Add click event for warm welcome or voice recognition
        this.floatingButton.addEventListener('click', () => {
            // If this is the first click, provide warm welcome
            if (!this.isListening && !this.hasProvidedWelcome) {
                this.provideWarmWelcome();
            } else {
                this.toggleVoiceRecognition();
            }
        });
        
        // Add to document
        document.body.appendChild(this.floatingButton);
    }
    
    provideWarmWelcome() {
        this.hasProvidedWelcome = true;
        
        // Create welcome message
        let welcomeMessage = "Welcome";
        if (this.userName) {
            welcomeMessage += ` ${this.userName}`;
        }
        if (this.companyName) {
            welcomeMessage += ` from ${this.companyName}`;
        }
        welcomeMessage += "! I'm your inventory management voice assistant. How can I help you today?";
        
        // Speak the welcome message
        this.speak(welcomeMessage);
        
        // Update status
        this.updateStatus('Welcome message spoken', 'success');
        this.updateFloatingButton('success');
        
        // Show visual feedback
        if (this.floatingButton) {
            this.floatingButton.style.background = '#388e3c';
            setTimeout(() => {
                if (this.floatingButton) {
                    this.floatingButton.style.background = '#0d6efd';
                }
            }, 3000);
        }
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
                if (this.voiceButton) this.voiceButton.innerHTML = '<i class="fas fa-microphone-alt"></i>';
                break;
            case 'success':
                this.statusIndicator.style.backgroundColor = '#e8f5e9';
                this.statusIndicator.style.color = '#388e3c';
                if (this.voiceButton) this.voiceButton.innerHTML = '<i class="fas fa-check"></i>';
                break;
            case 'error':
                this.statusIndicator.style.backgroundColor = '#ffebee';
                this.statusIndicator.style.color = '#d32f2f';
                if (this.voiceButton) this.voiceButton.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                break;
            default:
                this.statusIndicator.style.backgroundColor = '#f8f9fa';
                this.statusIndicator.style.color = '#6c757d';
                if (this.voiceButton) this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
        }
        
        // Hide status after 3 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                this.statusIndicator.style.display = 'none';
                if (this.voiceButton) this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
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
            
            // Ensure we have a search input to work with
            if (!this.searchInput) {
                // Try to find a search input dynamically
                this.searchInput = document.getElementById('searchInput') || document.querySelector('input[type="search"]') || document.querySelector('input[name="q"]');
            }
            
            // If we still don't have a search input, create a temporary one
            if (!this.searchInput) {
                console.warn('No search input found, creating temporary one');
                this.createTemporarySearchInput();
            }
            
            this.recognition.start();
            this.voiceButton.innerHTML = '<i class="fas fa-microphone-alt"></i>';
            console.log('Speech recognition start command sent');
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            this.updateStatus('Error starting voice recognition', 'error');
            
            // Handle permission errors specifically
            if (error.name === 'NotAllowedError') {
                this.speak('Microphone permission denied. Please check your browser permissions.');
                // Show permission guide
                if (confirm('Microphone permission is required for voice commands. Would you like to learn how to enable it?')) {
                    window.location.href = '/settings/voice/permissions/';
                }
            } else if (error.name === 'InvalidStateError') {
                this.speak('Voice recognition is already running. Please stop it first.');
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
            this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            console.log('Speech recognition stopped');
        }
    }
    
    createTemporarySearchInput() {
        // Create a hidden search input for processing commands
        const tempInput = document.createElement('input');
        tempInput.type = 'hidden';
        tempInput.id = 'tempVoiceSearchInput';
        document.body.appendChild(tempInput);
        this.searchInput = tempInput;
    }
    
    submitSearch() {
        // Find and submit the search form
        const searchForm = this.searchInput.closest('form');
        if (searchForm) {
            searchForm.dispatchEvent(new Event('submit', { cancelable: true }));
            // Add visual feedback for form submission
            this.updateStatus('Search submitted', 'success');
        } else {
            // If no form, just process the command directly
            this.updateStatus('Command processed', 'success');
        }
    }
    
    processCommand(command) {
        command = command.toLowerCase().trim();
        console.log('Processing command:', command);
        
        // Handle different types of commands
        if (this.handleSearchCommands(command)) return;
        if (this.handleNavigationCommands(command)) return;
        if (this.handleInformationCommands(command)) return;
        if (this.handleReportCommands(command)) return;
        if (this.handleProductCommands(command)) return;
        if (this.handleCustomerCommands(command)) return;
        if (this.handleSaleCommands(command)) return;
        if (this.handlePurchaseCommands(command)) return;
        if (this.handleInventoryCommands(command)) return;
        if (this.handleGreetingCommands(command)) return;
        if (this.handleHelpCommands(command)) return;
        
        // Default action - treat as search
        this.searchInput.value = command;
        this.submitSearch();
        this.speak(`I'm searching for ${command}`);
    }
    
    handleSearchCommands(command) {
        if (command.includes('search for') || command.includes('find') || 
            command.includes('look for') || command.includes('show me')) {
            const searchTerms = command
                .replace('search for', '')
                .replace('find', '')
                .replace('look for', '')
                .replace('show me', '')
                .trim();
            this.searchInput.value = searchTerms;
            this.submitSearch();
            this.speak(`Searching for ${searchTerms}`);
            return true;
        }
        return false;
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
    
    handleInformationCommands(command) {
        if (command.includes('what time') || command.includes('current time')) {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            this.speak(`The current time is ${timeString}`);
            return true;
        }
        
        if (command.includes('what date') || command.includes('current date')) {
            const now = new Date();
            const dateString = now.toLocaleDateString();
            this.speak(`Today is ${dateString}`);
            return true;
        }
        
        if (command.includes('who are you') || command.includes('what are you')) {
            this.speak('I am your inventory management voice assistant. I can help you navigate the system, search for items, and access reports.');
            return true;
        }
        
        return false;
    }
    
    handleReportCommands(command) {
        // Profit-related commands
        if (command.includes('profit') || command.includes('loss') || command.includes('earnings')) {
            this.speak('I will show you the profit and loss report.');
            window.location.href = '/reports/profit-loss/';
            return true;
        }
        
        // Sales-related commands
        if (command.includes('sales') || command.includes('revenue')) {
            this.speak('I will show you the sales report.');
            window.location.href = '/reports/sales/';
            return true;
        }
        
        // Expenses-related commands
        if (command.includes('expenses') || command.includes('costs')) {
            this.speak('I will show you the expenses report.');
            window.location.href = '/reports/expenses/';
            return true;
        }
        
        // Inventory-related commands
        if (command.includes('inventory') || command.includes('stock')) {
            this.speak('I will show you the inventory report.');
            window.location.href = '/reports/inventory/';
            return true;
        }
        
        return false;
    }
    
    handleProductCommands(command) {
        if (command.includes('add product') || command.includes('create product')) {
            this.speak('Opening product creation form.');
            window.location.href = '/products/create/';
            return true;
        }
        
        if (command.includes('list products') || command.includes('all products')) {
            this.speak('Showing all products.');
            window.location.href = '/products/';
            return true;
        }
        
        return false;
    }
    
    handleCustomerCommands(command) {
        if (command.includes('add customer') || command.includes('create customer')) {
            this.speak('Opening customer creation form.');
            window.location.href = '/customers/create/';
            return true;
        }
        
        if (command.includes('list customers') || command.includes('all customers')) {
            this.speak('Showing all customers.');
            window.location.href = '/customers/';
            return true;
        }
        
        return false;
    }
    
    handleSaleCommands(command) {
        if (command.includes('new sale') || command.includes('create sale')) {
            this.speak('Opening point of sale system.');
            window.location.href = '/sales/pos/';
            return true;
        }
        
        if (command.includes('list sales') || command.includes('all sales')) {
            this.speak('Showing all sales.');
            window.location.href = '/sales/';
            return true;
        }
        
        return false;
    }
    
    handlePurchaseCommands(command) {
        if (command.includes('new purchase') || command.includes('create purchase')) {
            this.speak('Opening purchase order creation form.');
            window.location.href = '/purchases/create/';
            return true;
        }
        
        if (command.includes('list purchases') || command.includes('all purchases')) {
            this.speak('Showing all purchases.');
            window.location.href = '/purchases/';
            return true;
        }
        
        return false;
    }
    
    handleInventoryCommands(command) {
        if (command.includes('low stock') || command.includes('out of stock')) {
            this.speak('Showing low stock items.');
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
    
    handleGreetingCommands(command) {
        if (command.includes('hello') || command.includes('hi') || command.includes('hey') || 
            command.includes('good morning') || command.includes('good afternoon') || command.includes('good evening')) {
            this.speak('Hello! How can I help you today?');
            return true;
        }
        return false;
    }
    
    handleHelpCommands(command) {
        if (command.includes('help') || command.includes('what can you do')) {
            this.speak('I can help you navigate the system, search for products, customers, and suppliers, create sales and purchases, view reports, and check inventory status. Try saying things like: show me profit, add a new product, or what time is it.');
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
            'expenses': '/expenses/',
            'expense list': '/expenses/',
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
            'profit': '/reports/profit-loss/',
            'profit loss': '/reports/profit-loss/',
            'profit and loss': '/reports/profit-loss/',
            'loss report': '/reports/profit-loss/',
            'sales report': '/reports/sales/',
            'inventory report': '/reports/inventory/',
            'inventory': '/reports/inventory/',
            'stock report': '/reports/inventory/',
            'expense report': '/reports/expenses/',
            'add product': '/products/create/',
            'new product': '/products/create/',
            'add customer': '/customers/create/',
            'new customer': '/customers/create/',
            'add supplier': '/suppliers/create/',
            'new supplier': '/suppliers/create/',
            'new sale': '/sales/pos/',
            'create sale': '/sales/pos/',
            'new purchase': '/purchases/create/',
            'create purchase': '/purchases/create/',
            'voice permissions': '/settings/voice/permissions/',
            'voice troubleshooting': '/settings/voice/troubleshooting/',
            'voice response test': '/settings/voice/response-test/',
            'voice error fix': '/settings/voice/error-fix/',
        };
        
        if (pages[page]) {
            this.speak(`Navigating to ${page}`);
            window.location.href = pages[page];
        } else {
            this.speak(`I don't know how to navigate to ${page}. Try saying dashboard, products, or profit.`);
        }
    }
    
    // Enhanced speak function with queue management and error handling
    speak(text) {
        // Add to speech queue
        this.speechQueue.push(text);
        
        // Process the queue
        this.processSpeechQueue();
    }
    
    // Process speech queue with proper error handling
    processSpeechQueue() {
        // If already speaking or no items in queue, return
        if (this.isSpeaking || this.speechQueue.length === 0) {
            return;
        }
        
        // Get next item from queue
        const text = this.speechQueue.shift();
        
        // Set speaking flag
        this.isSpeaking = true;
        
        // Add a small delay to prevent immediate conflicts
        setTimeout(() => {
            if (!this.synthesis) {
                console.warn('Speech synthesis not supported');
                this.showSpeechSynthesisWarning();
                this.isSpeaking = false;
                // Process next item in queue
                if (this.speechQueue.length > 0) {
                    setTimeout(() => this.processSpeechQueue(), 100);
                }
                return;
            }
            
            // Cancel any ongoing speech
            try {
                this.synthesis.cancel();
            } catch (e) {
                console.warn('Could not cancel ongoing speech:', e);
            }
            
            // Create utterance with comprehensive error handling
            try {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-US';
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                
                // Event listeners with specific handling for interrupted errors
                utterance.onstart = () => {
                    console.log('Speech started:', text);
                    // Update status to show speaking
                    this.updateStatus('Speaking...', 'success');
                };
                
                utterance.onend = () => {
                    console.log('Speech ended');
                    this.isSpeaking = false;
                    // Reset status after speaking
                    setTimeout(() => {
                        if (!this.isListening) {
                            this.updateStatus('Ready', 'idle');
                        }
                    }, 1000);
                    
                    // Process next item in queue
                    if (this.speechQueue.length > 0) {
                        setTimeout(() => this.processSpeechQueue(), 100);
                    }
                };
                
                utterance.onerror = (event) => {
                    console.error('Speech error:', event);
                    this.isSpeaking = false;
                    
                    // Specific handling for interrupted errors
                    if (event.error === 'interrupted') {
                        console.log('Speech was interrupted, retrying...');
                        // Re-add to queue and try again
                        this.speechQueue.unshift(text);
                        setTimeout(() => this.processSpeechQueue(), 1000);
                    } else {
                        this.updateStatus(`Speech error: ${event.error}`, 'error');
                        // Process next item in queue
                        if (this.speechQueue.length > 0) {
                            setTimeout(() => this.processSpeechQueue(), 100);
                        }
                    }
                };
                
                // Speak
                this.synthesis.speak(utterance);
                console.log('Speaking text:', text);
                
            } catch (error) {
                console.error('Error creating utterance:', error);
                this.updateStatus(`Speech error: ${error.message}`, 'error');
                this.isSpeaking = false;
                
                // Process next item in queue
                if (this.speechQueue.length > 0) {
                    setTimeout(() => this.processSpeechQueue(), 100);
                }
            }
        }, 200);
    }
    
    showSpeechSynthesisWarning() {
        this.updateStatus('Speech synthesis not supported', 'error');
        console.warn('Speech synthesis is not supported in this browser.');
    }
    
    // Public method to manually trigger voice recognition
    start() {
        this.startVoiceRecognition();
    }
    
    // Public method to stop voice recognition
    stop() {
        this.stopVoiceRecognition();
    }
    
    // Debug method to test if recognition is working
    testRecognition() {
        if (!this.recognition) {
            console.error('Recognition not available');
            return false;
        }
        
        console.log('Recognition object:', this.recognition);
        console.log('Is listening:', this.isListening);
        return true;
    }
    
    // Direct method to test greeting
    testGreeting() {
        this.speak('Hello! How can I help you today?');
    }
    
    // Method to guide user to permissions page
    showPermissionsGuide() {
        if (confirm('Would you like to learn how to enable microphone permissions for voice commands?')) {
            window.location.href = '/settings/voice/permissions/';
        }
    }
    
    // Method to provide warm welcome (can be called externally)
    triggerWelcome() {
        this.provideWarmWelcome();
    }
    
    // Method to reset the voice system
    reset() {
        try {
            // Stop any ongoing recognition
            if (this.recognition && this.isListening) {
                this.recognition.stop();
            }
            
            // Cancel any ongoing speech
            if (this.synthesis) {
                this.synthesis.cancel();
            }
            
            // Clear speech queue
            this.speechQueue = [];
            this.isSpeaking = false;
            
            // Reset flags
            this.isListening = false;
            this.hasProvidedWelcome = false;
            
            // Reset UI
            if (this.voiceButton) {
                this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            }
            
            if (this.floatingButton) {
                this.floatingButton.innerHTML = '<i class="fas fa-microphone"></i>';
                this.floatingButton.style.background = '#0d6efd';
                this.floatingButton.style.animation = 'none';
            }
            
            if (this.statusIndicator) {
                this.statusIndicator.style.display = 'none';
            }
            
            console.log('Voice system reset successfully');
            return true;
        } catch (error) {
            console.error('Error resetting voice system:', error);
            return false;
        }
    }
    
    // Method to test speech synthesis directly
    testSpeechSynthesis() {
        this.speak("This is a test of the speech synthesis system. If you can hear this, the response system is working properly.");
    }
    
    // Method to clear speech queue
    clearSpeechQueue() {
        if (this.synthesis) {
            this.synthesis.cancel();
        }
        this.speechQueue = [];
        this.isSpeaking = false;
        console.log('Speech queue cleared');
    }
    
    // Method to fix interrupted errors
    fixInterruptedErrors() {
        console.log('Attempting to fix interrupted speech errors...');
        
        // Clear everything
        this.clearSpeechQueue();
        
        // Reset audio context if possible
        if (this.synthesis) {
            this.synthesis.cancel();
            // Force reload voices
            this.synthesis.getVoices();
        }
        
        console.log('Interrupted error fix attempt completed');
    }
}

// Initialize voice command when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize voice command functionality
    window.voiceCommand = new VoiceCommand();
    
    // Also look for voice-enabled search forms dynamically
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Re-initialize if new elements are added
                if (window.voiceCommand) {
                    window.voiceCommand.findElements();
                }
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
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
    
    // Add a global function for debugging
    window.testVoiceCommand = function() {
        if (window.voiceCommand) {
            return window.voiceCommand.testRecognition();
        }
        return false;
    };
    
    // Add a global function to test greeting
    window.testGreeting = function() {
        if (window.voiceCommand) {
            window.voiceCommand.testGreeting();
        }
    };
    
    // Add a global function to show permissions guide
    window.showPermissionsGuide = function() {
        if (window.voiceCommand) {
            window.voiceCommand.showPermissionsGuide();
        }
    };
    
    // Add a global function to trigger welcome
    window.triggerWelcome = function() {
        if (window.voiceCommand) {
            window.voiceCommand.triggerWelcome();
        }
    };
    
    // Add a global function to reset voice system
    window.resetVoiceSystem = function() {
        if (window.voiceCommand) {
            return window.voiceCommand.reset();
        }
        return false;
    };
    
    // Add a global function to test speech synthesis
    window.testSpeechResponse = function() {
        if (window.voiceCommand) {
            window.voiceCommand.testSpeechSynthesis();
        }
    };
    
    // Add a global function to clear speech queue
    window.clearSpeechQueue = function() {
        if (window.voiceCommand) {
            window.voiceCommand.clearSpeechQueue();
        }
    };
    
    // Add a global function to fix interrupted errors
    window.fixInterruptedErrors = function() {
        if (window.voiceCommand) {
            window.voiceCommand.fixInterruptedErrors();
        }
    };
});

// Export for potential use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceCommand;
}