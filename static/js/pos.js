// POS System JavaScript functionality
class POSSystem {
    constructor() {
        this.cart = [];
        this.scannerActive = false;
        this.scannerStopping = false;
        this.scanProcessing = false;
        this.lastScannedBarcode = null;
        this.lastScanTime = 0;
        this.scanDebounceTime = 2000; // Increased from 1000ms to 2000ms to prevent duplicate scans
        this.autoStopScanner = false; // Whether to auto-stop scanner after each scan
        this.pendingRequests = new Map(); // Track pending requests to prevent duplicates
        this.loadCartFromStorage();
        this.initializeEventListeners();
        this.initializeKeyboardShortcuts();
    }

    initializeEventListeners() {
        // Add product to cart when product card is clicked
        document.addEventListener('click', (e) => {
            // Handle product card clicks
            if (e.target.closest('.product-card')) {
                const productCard = e.target.closest('.product-card');
                
                // Check if this event is already being handled by another system
                // to prevent duplicate processing - IMPROVED COORDINATION
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by POS system
                e.cartSystemHandled = true;
                
                this.addProductToCart(productCard);
                // Add animation effect
                this.animateButton(productCard);
            }
            
            // Handle clear cart button
            if (e.target.id === 'clearCart') {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by POS system
                e.cartSystemHandled = true;
                
                this.clearCart();
                // Add animation effect
                this.animateButton(e.target);
            }
            
            // Handle quantity buttons in cart
            if (e.target.classList.contains('qty-btn')) {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by POS system
                e.cartSystemHandled = true;
                
                const productId = e.target.closest('.cart-item').dataset.productId;
                if (e.target.classList.contains('qty-increase')) {
                    this.updateQuantity(productId, 1);
                } else if (e.target.classList.contains('qty-decrease')) {
                    this.updateQuantity(productId, -1);
                }
                // Add animation effect
                this.animateButton(e.target);
            }
            
            // Handle remove item from cart
            if (e.target.classList.contains('remove-item')) {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by POS system
                e.cartSystemHandled = true;
                
                const productId = e.target.closest('.cart-item').dataset.productId;
                this.removeFromCart(productId);
                // Add animation effect
                this.animateButton(e.target);
            }
            
            // Handle checkout button - ONLY process if not already handled
            if ((e.target.id === 'checkoutButton' || e.target.id === 'processSale') && !e.saleProcessed) {
                // Mark this sale as processed to prevent duplicate processing
                e.saleProcessed = true;
                this.processSale();
                // Add animation effect
                this.animateButton(e.target);
            }
            
            // Handle scan button
            if (e.target.id === 'scanButton') {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by POS system
                e.cartSystemHandled = true;
                
                this.openScanner();
                // Add animation effect
                this.animateButton(e.target);
            }
        });

        // Handle discount input changes
        const discountInput = document.getElementById('discountInput');
        if (discountInput) {
            discountInput.addEventListener('input', () => {
                this.updateCartDisplay();
            });
        }

        // Handle payment method selection
        const paymentOptions = document.querySelectorAll('.payment-option');
        paymentOptions.forEach(option => {
            option.addEventListener('click', () => {
                paymentOptions.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                // Add animation effect
                this.animateButton(option);
            });
        });

        // Handle customer selection
        const customerSelect = document.getElementById('customerSelect');
        if (customerSelect) {
            customerSelect.addEventListener('change', () => {
                this.updateCustomerInfo();
            });
        }

        // Handle search input
        const productSearch = document.getElementById('productSearch');
        if (productSearch) {
            productSearch.addEventListener('input', (e) => {
                this.filterProducts(e.target.value);
            });
            
            // Handle Enter key for manual barcode entry
            productSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const barcode = productSearch.value.trim();
                    if (barcode) {
                        this.searchProductByBarcode(barcode);
                        productSearch.value = ''; // Clear the input
                    }
                }
            });
        }

        // Handle tab changes to update summary
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', (e) => {
                if (e.target.getAttribute('data-bs-target') === '#confirm') {
                    this.updateOrderSummary();
                }
                // Add animation effect
                this.animateButton(e.target);
            });
        });
    }

    initializeKeyboardShortcuts() {
        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+S to process sale - ONLY process if not already handled
            if (e.ctrlKey && e.key === 's' && !e.saleProcessed) {
                e.preventDefault();
                const processButton = document.getElementById('processSale');
                if (processButton) {
                    // Mark this sale as processed to prevent duplicate processing
                    e.saleProcessed = true;
                    this.animateButton(processButton);
                    this.processSale();
                }
            }
            
            // Enter to checkout - ONLY process if not already handled
            if (e.key === 'Enter' && !e.target.matches('input, textarea') && !e.saleProcessed) {
                const checkoutButton = document.getElementById('checkoutButton');
                if (checkoutButton && !checkoutButton.disabled) {
                    // Mark this sale as processed to prevent duplicate processing
                    e.saleProcessed = true;
                    this.animateButton(checkoutButton);
                    checkoutButton.click();
                }
            }
            
            // Ctrl+B to open barcode scanner
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                const scanButton = document.getElementById('scanButton');
                if (scanButton) {
                    // Check if this event is already being handled by another system
                    if (e.cartSystemHandled) {
                        return;
                    }
                    
                    // Mark this event as handled by POS system
                    e.cartSystemHandled = true;
                    
                    this.animateButton(scanButton);
                    this.openScanner();
                }
            }
        });

    }

    // Add animation effect to buttons
    animateButton(element) {
        if (!element) return;
        
        // Add visual feedback
        element.classList.add('btn-animating');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            element.classList.remove('btn-animating');
        }, 300);
    }

    // Open the barcode scanner modal
    openScanner() {
        // Create and show scanner in a completely self-contained way
        this.createAndShowScanner();
    }

    // Create and show scanner modal completely dynamically
    createAndShowScanner() {
        // Remove any existing scanner modal
        const existingModal = document.getElementById('dynamicScannerModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create scanner modal HTML
        const scannerModalHtml = `
            <div class="modal fade" id="dynamicScannerModal" tabindex="-1" aria-labelledby="dynamicScannerModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="dynamicScannerModalLabel">Scan Barcode</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center">
                            <div id="dynamicScannerContainer" style="position: relative; width: 100%; height: 300px; border: 2px solid #007bff; border-radius: 8px; overflow: hidden;">
                                <video id="dynamicScannerVideo" style="width: 100%; height: 100%; object-fit: cover;"></video>
                                <div id="dynamicScannerOverlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; height: 20%; border: 3px solid rgba(0, 255, 0, 0.8); box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.5); animation: scannerPulse 2s infinite;"></div>
                                </div>
                            </div>
                            <div id="dynamicScannerStatus" class="mt-2 alert alert-info">Scanner not started. Make sure to allow camera access when prompted.</div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', scannerModalHtml);
        
        // Get the newly created modal
        const scannerModal = document.getElementById('dynamicScannerModal');
        
        // Show the modal
        const modal = new bootstrap.Modal(scannerModal);
        modal.show();
        
        // Initialize scanner when modal is shown
        scannerModal.addEventListener('shown.bs.modal', () => {
            setTimeout(() => {
                this.initDynamicScanner();
            }, 100);
        });
        
        // Clean up when modal is hidden
        scannerModal.addEventListener('hidden.bs.modal', () => {
            this.stopScanner();
            // Remove modal from DOM after a short delay to ensure animations complete
            setTimeout(() => {
                if (scannerModal.parentNode) {
                    scannerModal.parentNode.removeChild(scannerModal);
                }
            }, 300);
        });
    }

    // Initialize the dynamic barcode scanner
    initDynamicScanner() {
        // Check if QuaggaJS is loaded
        if (typeof Quagga === 'undefined') {
            this.showNotification('Barcode scanner library not loaded', 'error');
            return;
        }

        // Check if we're in a secure context
        if (!window.isSecureContext) {
            this.showNotification('Camera requires HTTPS or localhost', 'warning');
            return;
        }

        // Get scanner elements (these should now exist since we just created them)
        const scannerVideo = document.getElementById('dynamicScannerVideo');
        const scannerStatus = document.getElementById('dynamicScannerStatus');
        const scannerContainer = document.getElementById('dynamicScannerContainer');
        
        // Check if elements exist
        if (!scannerVideo || !scannerStatus || !scannerContainer) {
            console.error('Dynamic scanner elements not found:', {
                video: !!scannerVideo,
                status: !!scannerStatus,
                container: !!scannerContainer
            });
            this.showNotification('Scanner failed to initialize. Please try again.', 'error');
            return;
        }

        // Update status
        scannerStatus.textContent = 'Initializing camera...';
        scannerStatus.className = 'mt-2 alert alert-warning';

        // Configure QuaggaJS with IMPROVED settings for better accuracy
        const config = {
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: scannerVideo,
                constraints: {
                    facingMode: "environment", // Use rear camera
                    width: { min: 800, ideal: 1280, max: 1920 },
                    height: { min: 600, ideal: 720, max: 1080 },
                    aspectRatio: { min: 1.333, ideal: 1.777, max: 2 }
                }
            },
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader",
                    "upc_reader",
                    "upc_e_reader",
                    "codabar_reader"
                ]
            },
            locator: {
                halfSample: false,
                patchSize: "medium", // medium is better for accuracy than small
                area: {
                    top: "10%",
                    right: "10%",
                    left: "10%",
                    bottom: "10%"
                }
            },
            frequency: 10, // Reduce frequency to prevent overload
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader",
                    "upc_reader",
                    "upc_e_reader",
                    "codabar_reader"
                ]
            }
        };

        Quagga.init(config, (err) => {
            if (err) {
                console.error('Error initializing scanner:', err);
                let errorMessage = 'Error initializing camera';
                if (err.message) {
                    errorMessage += ': ' + err.message;
                } else if (typeof err === 'string') {
                    errorMessage += ': ' + err;
                }
                scannerStatus.textContent = errorMessage;
                scannerStatus.className = 'mt-2 alert alert-danger';
                
                // Handle specific error types with more detailed messages
                if (err.name === 'NotAllowedError' || err.message.includes('Permission') || err.message.includes('permission')) {
                    scannerStatus.innerHTML = 'Camera permission denied. Please allow camera access.<br><br>' +
                        '<button class="btn btn-sm btn-primary" onclick="location.reload()">Retry Camera Access</button>';
                } else if (err.name === 'NotFoundError' || err.message.includes('NotFoundError')) {
                    scannerStatus.textContent = 'No camera found. Please connect a camera and try again.';
                } else if (err.name === 'NotReadableError') {
                    scannerStatus.textContent = 'Camera is already in use. Close other applications using the camera.';
                } else if (err.name === 'OverconstrainedError') {
                    scannerStatus.textContent = 'Camera constraints cannot be satisfied. Trying with default constraints...';
                    // Try with default constraints
                    this.initScannerWithDefaultConstraints(scannerVideo, scannerStatus);
                    return;
                }
                return;
            }

            // Start scanning
            Quagga.start();
            this.scannerActive = true;
            scannerStatus.textContent = 'Scanner started. Position barcode in the frame';
            scannerStatus.className = 'mt-2 alert alert-success';

            // Add drawing canvas for debug visualization
            Quagga.onProcessed((result) => {
                var drawingCtx = Quagga.canvas.ctx.overlay;
                var drawingCanvas = Quagga.canvas.dom.overlay;

                if (result) {
                    if (result.boxes) {
                        drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                        result.boxes.filter(function (box) {
                            return box !== result.box;
                        }).forEach(function (box) {
                            Quagga.ImageDebug.drawPath(box, {x: 0, y: 1}, drawingCtx, {color: "green", lineWidth: 2});
                        });
                    }

                    if (result.box) {
                        Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: "#00F", lineWidth: 2});
                    }

                    if (result.codeResult && result.codeResult.code) {
                        Quagga.ImageDebug.drawPath(result.line, {x: 'x', y: 'y'}, drawingCtx, {color: 'red', lineWidth: 3});
                    }
                }
            });
        });

        // Register callback for detected barcodes - ENHANCED FOR BETTER ACCURACY
        Quagga.onDetected((result) => {
            // Immediate check to prevent any processing if scanner is not active or already processing
            if (!this.scannerActive || this.scannerStopping) {
                return;
            }

            const code = result.codeResult.code;
            const format = result.codeResult.format;
            const confidence = result.codeResult.decodedCodes ? 
                result.codeResult.decodedCodes.reduce((sum, code) => sum + (code.quality || 0), 0) / result.codeResult.decodedCodes.length : 0;
            
            console.log('Barcode detected:', {code, format, confidence});
            
            // Only process barcodes with high confidence (above 0.5)
            if (confidence < 0.5) {
                console.log('Ignoring low confidence barcode:', code, 'Confidence:', confidence);
                return;
            }
            
            // Check if this is the same barcode detected recently (debounce)
            const currentTime = Date.now();
            if (this.lastScannedBarcode === code && (currentTime - this.lastScanTime) < this.scanDebounceTime) {
                // Ignore this detection as it's too soon after the last one
                console.log('Ignoring duplicate barcode detection:', code);
                return;
            }
            
            // If we're already processing a scan, ignore this one
            if (this.scanProcessing) {
                console.log('Scanner busy, ignoring new scan:', code);
                return;
            }
            
            // Set processing flag to prevent multiple concurrent scans
            this.scanProcessing = true;
            
            // Update last scanned barcode and time
            this.lastScannedBarcode = code;
            this.lastScanTime = currentTime;
            
            const scannerStatus = document.getElementById('dynamicScannerStatus');
            if (scannerStatus) {
                scannerStatus.textContent = `Barcode detected: ${code} (${format})`;
                scannerStatus.className = 'mt-2 alert alert-success';
            }
            
            // Search for product and add to cart
            this.searchProductByBarcode(code)
                .finally(() => {
                    // Always reset the processing flag after the request completes
                    this.scanProcessing = false;
                    
                    // If auto-stop is enabled, stop the scanner after each scan
                    if (this.autoStopScanner) {
                        this.scannerStopping = true;
                        setTimeout(() => {
                            this.stopScanner();
                            const scannerModal = document.getElementById('dynamicScannerModal');
                            if (scannerModal) {
                                const modal = bootstrap.Modal.getInstance(scannerModal);
                                if (modal) {
                                    modal.hide();
                                }
                            }
                        }, 1500); // Close after 1.5 seconds
                    }
                });
        });
    }

    // Initialize scanner with default constraints as fallback
    initScannerWithDefaultConstraints(scannerVideo, scannerStatus) {
        const defaultConfig = {
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: scannerVideo,
                constraints: {
                    facingMode: "environment", // Use rear camera
                    width: { min: 640, ideal: 1280 },
                    height: { min: 480, ideal: 720 }
                }
            },
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader",
                    "upc_reader",
                    "upc_e_reader",
                    "codabar_reader"
                ]
            },
            locator: {
                halfSample: false,
                patchSize: "medium",
                area: {
                    top: "10%",
                    right: "10%",
                    left: "10%",
                    bottom: "10%"
                }
            },
            frequency: 10
        };

        Quagga.init(defaultConfig, (err) => {
            if (err) {
                console.error('Error initializing scanner with default constraints:', err);
                scannerStatus.textContent = 'Failed to initialize camera with any settings. Please check your camera and try again.';
                scannerStatus.className = 'mt-2 alert alert-danger';
                return;
            }

            // Start scanning
            Quagga.start();
            this.scannerActive = true;
            scannerStatus.textContent = 'Scanner started with default settings. Position barcode in the frame';
            scannerStatus.className = 'mt-2 alert alert-success';
        });
    }

    // Stop the barcode scanner
    stopScanner() {
        this.scannerActive = false;
        this.scannerStopping = true; // Set stopping flag
        this.scanProcessing = false; // Reset processing flag
        this.lastScannedBarcode = null; // Clear last scanned barcode
        if (typeof Quagga !== 'undefined' && Quagga) {
            try {
                Quagga.stop();
                console.log('Quagga scanner stopped');
            } catch (e) {
                console.error('Error stopping Quagga:', e);
            }
        }
        // Reset stopping flag after a short delay
        setTimeout(() => {
            this.scannerStopping = false;
        }, 1000); // Increased delay to ensure scanner is fully stopped
    }

    // New method to reset scanner state for continuous scanning
    resetScannerState() {
        this.scanProcessing = false;
        this.scannerStopping = false;
        // Don't reset scannerActive as the scanner might still be running
        console.log('Scanner state reset for continuous scanning');
    }

    // Search for product by barcode and add to cart - NOW RETURNS PROMISE
    searchProductByBarcode(barcode) {
        // Show loading indicator
        this.showLoading(true);
        
        // Check if there's already a pending request for this barcode
        if (this.pendingRequests.has(barcode)) {
            console.log('Ignoring duplicate request for barcode:', barcode);
            this.showLoading(false);
            return Promise.resolve(); // Return resolved promise
        }
        
        // Mark this barcode as having a pending request
        this.pendingRequests.set(barcode, true);
        
        // Fetch product by barcode
        return fetch(`/sales/product/barcode/${barcode}/`)
            .then(response => response.json())
            .then(data => {
                // Remove from pending requests
                this.pendingRequests.delete(barcode);
                
                if (data.error) {
                    this.showNotification(`Product not found: ${data.error}`, 'warning');
                } else {
                    // Add product to cart
                    this.addProductToCartFromData(data);
                    this.showNotification(`Added ${data.name} to cart`, 'success');
                }
            })
            .catch(error => {
                // Remove from pending requests on error
                this.pendingRequests.delete(barcode);
                
                console.error('Error searching product:', error);
                this.showNotification(`Error searching product: ${error.message}`, 'error');
            })
            .finally(() => {
                this.showLoading(false);
            });
    }

    // Add product to cart from API data
    addProductToCartFromData(productData) {
        // Check if product is already in cart
        const existingItem = this.cart.find(item => item.id == productData.id);
        
        if (existingItem) {
            // Check if we can add more (stock limit)
            if (existingItem.quantity < productData.stock) {
                existingItem.quantity += 1;
            } else {
                this.showNotification('Cannot add more of this item. Insufficient stock.', 'warning');
                return;
            }
        } else {
            // Check stock before adding
            if (productData.stock <= 0) {
                this.showNotification('This product is out of stock.', 'warning');
                return;
            }
            
            // Add new item to cart
            this.cart.push({
                id: productData.id,
                name: productData.name,
                price: productData.price,
                quantity: 1,
                stock: productData.stock
            });
        }
        
        // Save cart and update display
        this.saveCartToStorage();
        this.updateCartDisplay();
    }

    addProductToCart(productCard) {
        const productId = productCard.dataset.productId;
        const productName = productCard.querySelector('h6').textContent;
        const productPriceText = productCard.querySelector('.product-price').textContent;
        const productPrice = parseFloat(productPriceText.replace(/[^\d.-]/g, ''));
        const productStockText = productCard.querySelector('.product-stock').textContent;
        const productStock = parseFloat(productStockText);
        
        // Check if product is already in cart
        const existingItem = this.cart.find(item => item.id == productId);
        
        if (existingItem) {
            // Check if we can add more (stock limit)
            if (existingItem.quantity < productStock) {
                existingItem.quantity += 1;
            } else {
                this.showNotification('Cannot add more of this item. Insufficient stock.', 'warning');
                return;
            }
        } else {
            // Check stock before adding
            if (productStock <= 0) {
                this.showNotification('This product is out of stock.', 'warning');
                return;
            }
            
            // Add new item to cart
            this.cart.push({
                id: productId,
                name: productName,
                price: productPrice,
                quantity: 1,
                stock: productStock
            });
        }
        
        // Save cart and update display
        this.saveCartToStorage();
        this.updateCartDisplay();
        this.showNotification(`${productName} added to cart`, 'success');
    }

    updateQuantity(productId, change) {
        const item = this.cart.find(item => item.id == productId);
        if (!item) return;
        
        const newQuantity = item.quantity + change;
        
        // Check stock limits
        if (newQuantity <= 0) {
            this.removeFromCart(productId);
            return;
        }
        
        if (newQuantity > item.stock) {
            this.showNotification('Cannot add more of this item. Insufficient stock.', 'warning');
            return;
        }
        
        item.quantity = newQuantity;
        this.saveCartToStorage();
        this.updateCartDisplay();
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id != productId);
        this.saveCartToStorage();
        this.updateCartDisplay();
        this.showNotification('Item removed from cart', 'info');
    }

    clearCart() {
        if (this.cart.length === 0) return;
        
        if (confirm('Are you sure you want to clear the cart?')) {
            this.cart = [];
            this.saveCartToStorage();
            this.updateCartDisplay();
            this.showNotification('Cart cleared', 'info');
        }
    }

    updateCartDisplay() {
        const cartItemsContainer = document.getElementById('cartItems');
        const cartItemCount = document.getElementById('cartItemCount');
        const cartSubtotal = document.getElementById('cartSubtotal');
        const cartTax = document.getElementById('cartTax');
        const cartDiscount = document.getElementById('cartDiscount');
        const cartTotal = document.getElementById('cartTotal');
        const checkoutButton = document.getElementById('checkoutButton');
        
        if (!cartItemsContainer) return;
        
        // Update cart items count
        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        if (cartItemCount) {
            cartItemCount.textContent = `${totalItems} ${totalItems === 1 ? 'item' : 'items'}`;
        }
        
        // Update cart items display
        if (this.cart.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="empty-cart">
                    <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                    <p>Your cart is empty</p>
                </div>
            `;
            if (checkoutButton) checkoutButton.disabled = true;
        } else {
            let cartHTML = '';
            this.cart.forEach(item => {
                const itemTotal = item.price * item.quantity;
                cartHTML += `
                    <div class="cart-item" data-product-id="${item.id}">
                        <div class="item-info">
                            <h6>${item.name}</h6>
                            <p class="item-price">${this.getCurrencySymbol()}${item.price.toFixed(2)}</p>
                        </div>
                        <div class="item-controls">
                            <button class="btn btn-sm btn-outline-secondary qty-btn qty-decrease">
                                <i class="fas fa-minus"></i>
                            </button>
                            <span class="item-quantity">${item.quantity}</span>
                            <button class="btn btn-sm btn-outline-secondary qty-btn qty-increase">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                        <div class="item-total">${this.getCurrencySymbol()}${itemTotal.toFixed(2)}</div>
                        <button class="btn btn-sm btn-outline-danger remove-item">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
            });
            cartItemsContainer.innerHTML = cartHTML;
            if (checkoutButton) checkoutButton.disabled = false;
        }
        
        // Update totals
        const totals = this.calculateTotals();
        if (cartSubtotal) cartSubtotal.textContent = `${this.getCurrencySymbol()}${totals.subtotal.toFixed(2)}`;
        if (cartTax) cartTax.textContent = `${this.getCurrencySymbol()}${totals.tax.toFixed(2)}`;
        if (cartDiscount) cartDiscount.textContent = `${this.getCurrencySymbol()}${totals.discount.toFixed(2)}`;
        if (cartTotal) cartTotal.textContent = `${this.getCurrencySymbol()}${totals.total.toFixed(2)}`;
    }

    updateOrderSummary() {
        const summaryItems = document.getElementById('summaryItems');
        const summarySubtotal = document.getElementById('summarySubtotal');
        const summaryTax = document.getElementById('summaryTax');
        const summaryDiscount = document.getElementById('summaryDiscount');
        const summaryTotal = document.getElementById('summaryTotal');
        
        if (!summaryItems) return;
        
        // Update order summary items
        if (this.cart.length === 0) {
            summaryItems.innerHTML = '<p class="text-center text-muted">No items in cart</p>';
        } else {
            let summaryHTML = '';
            this.cart.forEach(item => {
                const itemTotal = item.price * item.quantity;
                summaryHTML += `
                    <div class="summary-item">
                        <div class="summary-item-info">
                            <h6>${item.name}</h6>
                            <p class="item-details">${item.quantity} × ${this.getCurrencySymbol()}${item.price.toFixed(2)}</p>
                        </div>
                        <div class="summary-item-total">${this.getCurrencySymbol()}${itemTotal.toFixed(2)}</div>
                    </div>
                `;
            });
            summaryItems.innerHTML = summaryHTML;
        }
        
        // Update summary totals
        const totals = this.calculateTotals();
        if (summarySubtotal) summarySubtotal.textContent = `${this.getCurrencySymbol()}${totals.subtotal.toFixed(2)}`;
        if (summaryTax) summaryTax.textContent = `${this.getCurrencySymbol()}${totals.tax.toFixed(2)}`;
        if (summaryDiscount) summaryDiscount.textContent = `${this.getCurrencySymbol()}${totals.discount.toFixed(2)}`;
        if (summaryTotal) summaryTotal.textContent = `${this.getCurrencySymbol()}${totals.total.toFixed(2)}`;
    }

    calculateTotals() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const taxRate = window.business_settings ? window.business_settings.tax_rate : 0;
        const tax = subtotal * (taxRate / 100);
        const discountInput = document.getElementById('discountInput');
        const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
        const total = subtotal + tax - discount;
        
        return {
            subtotal: subtotal,
            tax: tax,
            discount: discount,
            total: Math.max(0, total) // Ensure total is not negative
        };
    }

    updateCustomerInfo() {
        const customerSelect = document.getElementById('customerSelect');
        const customerInfo = document.getElementById('customerInfo');
        
        if (!customerSelect || !customerInfo) return;
        
        const customerId = customerSelect.value;
        if (!customerId) {
            customerInfo.innerHTML = '';
            return;
        }
        
        // In a real implementation, you would fetch customer details from the server
        // For now, we'll just show a placeholder
        customerInfo.innerHTML = `
            <div class="customer-details">
                <p><strong>Customer:</strong> Walk-in Customer</p>
                <p><strong>Phone:</strong> +1 (555) 123-4567</p>
                <p><strong>Email:</strong> customer@example.com</p>
            </div>
        `;
    }

    filterProducts(searchTerm) {
        const productCards = document.querySelectorAll('.product-card');
        const suggestionsContainer = document.getElementById('productSuggestions');
        
        if (!searchTerm) {
            // Show all products
            productCards.forEach(card => {
                card.style.display = 'block';
            });
            
            if (suggestionsContainer) {
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
            }
            return;
        }
        
        // Filter products by name
        const filteredProducts = [];
        productCards.forEach(card => {
            const productName = card.querySelector('h6').textContent.toLowerCase();
            if (productName.includes(searchTerm.toLowerCase())) {
                card.style.display = 'block';
                filteredProducts.push({
                    id: card.dataset.productId,
                    name: card.querySelector('h6').textContent,
                    element: card
                });
            } else {
                card.style.display = 'none';
            }
        });
        
        // Show suggestions
        if (suggestionsContainer && filteredProducts.length > 0) {
            let suggestionsHTML = '';
            filteredProducts.slice(0, 5).forEach(product => {
                suggestionsHTML += `
                    <div class="suggestion-item" data-product-id="${product.id}">
                        ${product.name}
                    </div>
                `;
            });
            
            suggestionsContainer.innerHTML = suggestionsHTML;
            suggestionsContainer.style.display = 'block';
        } else if (suggestionsContainer) {
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.style.display = 'none';
        }
    }

    processSale() {
        if (this.cart.length === 0) {
            this.showNotification('Cannot process sale. Cart is empty.', 'warning');
            return;
        }
        
        // Get form data
        const customerSelect = document.getElementById('customerSelect');
        const paymentOptions = document.querySelectorAll('.payment-option.active');
        const discountInput = document.getElementById('discountInput');
        
        const saleData = {
            customer_id: customerSelect ? customerSelect.value : null,
            payment_method: paymentOptions.length > 0 ? paymentOptions[0].dataset.method : 'cash',
            discount: discountInput ? parseFloat(discountInput.value) || 0 : 0,
            cart_items: this.cart.map(item => ({
                id: item.id,
                name: item.name,
                price: item.price,
                quantity: item.quantity
            }))
        };
        
        console.log('Processing sale with data:', saleData);
        
        // Show loading spinner
        this.showLoading(true);
        
        // Send data to server
        const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfTokenElement) {
            console.error('CSRF token not found');
            this.showNotification('Security token not found. Please refresh the page and try again.', 'error');
            this.showLoading(false);
            return;
        }
        
        const csrfToken = csrfTokenElement.value;
        console.log('CSRF Token:', csrfToken);
        
        // Use the correct URL endpoint - FIXED: was '/sales/process/' but should be '/sales/pos/process/'
        fetch('/sales/pos/process/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(saleData)
        })
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                this.showNotification('Sale processed successfully!', 'success');
                // Clear cart
                this.cart = [];
                this.saveCartToStorage();
                this.updateCartDisplay();
                this.updateOrderSummary();
                
                // Redirect to sale detail page or show receipt
                if (data.sale_id) {
                    setTimeout(() => {
                        window.location.href = `/sales/${data.sale_id}/`;
                    }, 2000);
                }
            } else {
                this.showNotification(data.error || 'Error processing sale', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showNotification('Error processing sale. Please try again.', 'error');
        })
        .finally(() => {
            this.showLoading(false);
        });
    }

    showNotification(message, type = 'info') {
        // Remove any existing notifications of the same type
        const existingNotifications = document.querySelectorAll(`.notification-${type}`);
        existingNotifications.forEach(notification => {
            notification.style.animation = 'fadeOutUp 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
        
        // Create modern notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} position-fixed shadow-lg`;
        notification.style.cssText = `
            top: 20px; 
            right: 20px; 
            z-index: 9999; 
            min-width: 300px;
            max-width: 400px;
            border-radius: 8px;
            padding: 15px 20px;
            margin: 10px;
            backdrop-filter: blur(10px);
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        `;
        
        // Set background and text colors based on type
        const typeStyles = {
            'success': {
                'background': 'linear-gradient(135deg, rgba(40, 167, 69, 0.9) 0%, rgba(40, 167, 69, 0.95) 100%)',
                'color': 'white',
                'border': '1px solid rgba(255, 255, 255, 0.2)'
            },
            'error': {
                'background': 'linear-gradient(135deg, rgba(220, 53, 69, 0.9) 0%, rgba(220, 53, 69, 0.95) 100%)',
                'color': 'white',
                'border': '1px solid rgba(255, 255, 255, 0.2)'
            },
            'warning': {
                'background': 'linear-gradient(135deg, rgba(255, 193, 7, 0.9) 0%, rgba(255, 193, 7, 0.95) 100%)',
                'color': 'black',
                'border': '1px solid rgba(0, 0, 0, 0.1)'
            },
            'info': {
                'background': 'linear-gradient(135deg, rgba(23, 162, 184, 0.9) 0%, rgba(23, 162, 184, 0.95) 100%)',
                'color': 'white',
                'border': '1px solid rgba(255, 255, 255, 0.2)'
            }
        };
        
        const styles = typeStyles[type] || typeStyles['info'];
        Object.assign(notification.style, styles);
        
        // Add icon based on type
        const icons = {
            'success': '<i class="fas fa-check-circle me-2"></i>',
            'error': '<i class="fas fa-exclamation-circle me-2"></i>',
            'warning': '<i class="fas fa-exclamation-triangle me-2"></i>',
            'info': '<i class="fas fa-info-circle me-2"></i>'
        };
        
        const icon = icons[type] || icons['info'];
        
        // Create notification content
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    ${icon}
                    <div class="notification-message">${message}</div>
                </div>
                <button type="button" class="btn-close btn-close-white" aria-label="Close" style="font-size: 0.6rem;"></button>
            </div>
        `;
        
        // Add close button functionality
        const closeBtn = notification.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'fadeOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
        
        // Add to document
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 10);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'fadeOutRight 0.3s ease';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }

    showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            if (show) {
                loadingOverlay.style.display = 'flex';
                loadingOverlay.style.animation = 'fadeIn 0.3s ease';
            } else {
                loadingOverlay.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                }, 300);
            }
        }
    }

    getCurrencySymbol() {
        return window.business_settings ? window.business_settings.currency_symbol : '$';
    }

    saveCartToStorage() {
        try {
            localStorage.setItem('posCart', JSON.stringify(this.cart));
        } catch (e) {
            console.error('Error saving cart to localStorage:', e);
        }
    }

    loadCartFromStorage() {
        try {
            const savedCart = localStorage.getItem('posCart');
            if (savedCart) {
                this.cart = JSON.parse(savedCart);
            }
        } catch (e) {
            console.error('Error loading cart from localStorage:', e);
            this.cart = [];
        }
    }

    // New method to manually stop the scanner
    manuallyStopScanner() {
        this.scannerStopping = true;
        this.scanProcessing = false; // Reset processing flag
        this.lastScannedBarcode = null; // Clear last scanned barcode
        this.stopScanner();
        
        const scannerModal = document.getElementById('dynamicScannerModal');
        if (scannerModal) {
            const modal = bootstrap.Modal.getInstance(scannerModal);
            if (modal) {
                modal.hide();
            }
        }
        
        // Show notification that scanner has been manually stopped
        this.showNotification('Barcode scanner stopped manually', 'info');
    }

    // New method to toggle auto-stop behavior
    toggleAutoStop() {
        this.autoStopScanner = !this.autoStopScanner;
        const status = this.autoStopScanner ? 'enabled' : 'disabled';
        this.showNotification(`Auto-stop scanner ${status}`, 'info');
        
        // Update UI button if it exists
        const toggleButton = document.getElementById('toggleAutoStop');
        if (toggleButton) {
            toggleButton.innerHTML = this.autoStopScanner ? 
                '<i class="fas fa-stop"></i> Auto-Stop: ON' : 
                '<i class="fas fa-play"></i> Auto-Stop: OFF';
            toggleButton.className = this.autoStopScanner ? 
                'btn btn-sm btn-success' : 
                'btn btn-sm btn-warning';
        }
        
        // If enabling auto-stop and scanner is active, make sure we can process scans
        if (this.autoStopScanner && this.scannerActive) {
            this.scanProcessing = false;
        }
    }
}

// Initialize POS system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.posSystem = new POSSystem();
});