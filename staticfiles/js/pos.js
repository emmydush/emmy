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
        this.loadCart(); // Load cart from server instead of localStorage
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
            
            // Handle variant selection
            if (e.target.classList.contains('variant-option')) {
                const variantId = e.target.dataset.variantId;
                const productId = e.target.closest('.product-card').dataset.productId;
                this.selectProductVariant(productId, variantId);
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
        
        // Handle credit sale checkbox
        const creditSaleCheckbox = document.getElementById('creditSaleCheckbox');
        const creditSaleOptions = document.getElementById('creditSaleOptions');
        const dueDateInput = document.getElementById('dueDateInput');
        
        if (creditSaleCheckbox && creditSaleOptions) {
            creditSaleCheckbox.addEventListener('change', () => {
                if (creditSaleCheckbox.checked) {
                    creditSaleOptions.style.display = 'block';
                    // Set default due date to 30 days from now
                    const today = new Date();
                    const dueDate = new Date();
                    dueDate.setDate(today.getDate() + 30);
                    dueDateInput.valueAsDate = dueDate;
                } else {
                    creditSaleOptions.style.display = 'none';
                    dueDateInput.value = '';
                }
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
        console.log('Creating and showing scanner modal');
        
        // Remove any existing scanner modal
        const existingModal = document.getElementById('dynamicScannerModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create scanner modal HTML - SIMPLIFIED VERSION WITHOUT ANIMATION
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
                                <canvas class="drawingBuffer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
                                <div id="dynamicScannerOverlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; height: 20%; border: 3px solid rgba(0, 255, 0, 0.8); box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.5);"></div>
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
            console.log('Scanner modal shown, initializing scanner...');
            setTimeout(() => {
                this.initDynamicScanner();
            }, 100);
        });
        
        // Clean up when modal is hidden
        scannerModal.addEventListener('hidden.bs.modal', () => {
            console.log('Scanner modal hidden, stopping scanner...');
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
        console.log('Initializing dynamic scanner...');
        
        // Check if QuaggaJS is loaded
        if (typeof Quagga === 'undefined') {
            console.error('QuaggaJS library not loaded');
            this.showNotification('Barcode scanner library not loaded', 'error');
            return;
        }

        // Check if we're in a secure context
        if (!window.isSecureContext) {
            console.warn('Not in secure context - this may affect camera access');
            this.showNotification('Camera requires HTTPS or localhost', 'warning');
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

        // Configure QuaggaJS with settings similar to the working product form scanner
        const config = {
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: scannerVideo,
                constraints: {
                    facingMode: "environment", // Use rear camera
                    width: { min: 640 },
                    height: { min: 480 }
                }
            },
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader",
                    "upc_reader",
                    "upc_e_reader"
                ]
            },
            locator: {
                halfSample: false,
                patchSize: "medium"
            }
        };

        console.log('Quagga config:', config);

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
                }
                return;
            }

            console.log('Quagga initialized successfully');
            
            // Update status
            scannerStatus.textContent = 'Scanner started. Position barcode in the frame';
            scannerStatus.className = 'mt-2 alert alert-success';

            // Start scanning
            Quagga.start();
            console.log('Quagga started');

            // Handle processed frames for visualization (similar to product form)
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

            // Handle detected barcodes
            Quagga.onDetected((data) => {
                console.log('Barcode detected:', data);
                
                // Reduce debounce time for better responsiveness
                const now = Date.now();
                if (this.lastScannedBarcode === data.codeResult.code && 
                    (now - this.lastScanTime) < 1000) { // Reduced from 2000ms to 1000ms
                    console.log('Ignoring duplicate scan');
                    return;
                }
                
                this.lastScannedBarcode = data.codeResult.code;
                this.lastScanTime = now;
                
                // Process the scanned barcode
                console.log('Processing scanned barcode:', data.codeResult.code);
                this.processScannedBarcode(data.codeResult.code);
                
                // Auto-stop scanner if enabled
                if (this.autoStopScanner) {
                    this.manuallyStopScanner();
                }
            });

            this.scannerActive = true;
        });
    }

    // Stop the scanner
    stopScanner() {
        console.log('Stopping scanner, currently active:', this.scannerActive);
        if (this.scannerActive) {
            try {
                Quagga.stop();
                console.log('Quagga stopped successfully');
            } catch (e) {
                console.error('Error stopping Quagga:', e);
            }
            this.scannerActive = false;
        }
    }

    // Process scanned barcode
    processScannedBarcode(barcode) {
        console.log('Processing barcode:', barcode);
        
        // Show loading indicator
        const scannerStatus = document.getElementById('dynamicScannerStatus');
        if (scannerStatus) {
            scannerStatus.textContent = `Scanned: ${barcode}. Processing...`;
            scannerStatus.className = 'mt-2 alert alert-info';
        }

        // Search for product by barcode
        this.searchProductByBarcode(barcode);
    }

    // Search for product by barcode
    searchProductByBarcode(barcode) {
        console.log('Searching for product with barcode:', barcode);
        
        // Show loading indicator
        this.showLoading(true);
        
        // Make AJAX request to search for product
        fetch(`/sales/product/barcode/${barcode}/`)
            .then(response => {
                console.log('Received response from server:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data from server:', data);
                if (data.error) {
                    this.showNotification(`Product not found: ${data.error}`, 'error');
                } else {
                    // Add product to cart
                    this.addProductToCartFromData(data);
                    this.showNotification(`Added ${data.name} to cart`, 'success');
                }
            })
            .catch(error => {
                console.error('Error searching for product:', error);
                this.showNotification('Error searching for product. Please try again.', 'error');
            })
            .finally(() => {
                // Hide loading indicator
                this.showLoading(false);
            });
    }

    // Add product to cart from data
    addProductToCartFromData(productData) {
        console.log('Adding product to cart:', productData);
        
        // Check if product already exists in cart
        const existingItemIndex = this.cart.findIndex(item => 
            item.id == productData.id && !item.is_variant);
        
        if (existingItemIndex !== -1) {
            // Update quantity of existing item
            this.cart[existingItemIndex].quantity += 1;
            console.log('Updated existing item quantity');
        } else {
            // Add new item to cart
            this.cart.push({
                id: productData.id,
                name: productData.name,
                price: productData.selling_price,
                quantity: 1,
                stock: productData.stock,
                unit: productData.unit,
                is_variant: false
            });
            console.log('Added new item to cart');
        }
        
        // Save cart and update display
        this.saveCart();
        this.updateCartDisplay();
        this.updateCheckoutButtonState();
        
        // Show notification
        this.showNotification(`${productData.name} added to cart`, 'success');
    }

    // Add product to cart
    addProductToCart(productCard) {
        // Check if product has variants
        const hasVariants = productCard.dataset.hasVariants === 'true';
        
        if (hasVariants) {
            // Show variant selection modal
            this.showVariantSelectionModal(productCard);
            return;
        }
        
        // Get product data from card
        const productId = productCard.dataset.productId;
        const productName = productCard.dataset.productName;
        const productPrice = parseFloat(productCard.dataset.productPrice);
        const productStock = parseFloat(productCard.dataset.productStock);
        const productUnit = productCard.dataset.productUnit || '';
        
        // Check if product already exists in cart
        const existingItemIndex = this.cart.findIndex(item => 
            item.id == productId && !item.is_variant);
        
        if (existingItemIndex !== -1) {
            // Check stock availability
            if (this.cart[existingItemIndex].quantity >= productStock) {
                this.showNotification('Cannot add more items. Insufficient stock available.', 'warning');
                return;
            }
            
            // Update quantity of existing item
            this.cart[existingItemIndex].quantity += 1;
        } else {
            // Check stock availability
            if (productStock <= 0) {
                this.showNotification('Cannot add item. Product is out of stock.', 'warning');
                return;
            }
            
            // Add new item to cart
            this.cart.push({
                id: productId,
                name: productName,
                price: productPrice,
                quantity: 1,
                stock: productStock,
                unit: productUnit,
                is_variant: false
            });
        }
        
        // Save cart and update display
        this.saveCart();
        this.updateCartDisplay();
        this.updateCheckoutButtonState();
        
        // Show notification
        this.showNotification(`${productName} added to cart`, 'success');
    }

    // Show variant selection modal
    showVariantSelectionModal(productCard) {
        const productId = productCard.dataset.productId;
        const productName = productCard.dataset.productName;
        
        // Fetch variants via AJAX
        fetch(`/sales/product/${productId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.showNotification(`Error loading variants: ${data.error}`, 'error');
                    return;
                }
                
                if (!data.has_variants || !data.variants || data.variants.length === 0) {
                    this.showNotification('No variants available for this product', 'warning');
                    return;
                }
                
                // Generate variant options
                let variantOptionsHtml = '';
                data.variants.forEach(variant => {
                    variantOptionsHtml += `
                        <div class="variant-option" data-variant-id="${variant.id}">
                            <div class="variant-info">
                                <h6>${variant.name}</h6>
                                <p class="variant-price">${this.getCurrencySymbol()}${variant.price}</p>
                                <p class="variant-stock">${variant.stock} ${data.unit} left</p>
                            </div>
                        </div>
                    `;
                });
                
                // Create modal HTML
                const modalHtml = `
                    <div class="modal fade" id="variantSelectionModal" tabindex="-1" aria-labelledby="variantSelectionModalLabel" aria-hidden="true">
                        <div class="modal-dialog modal-dialog-centered">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title" id="variantSelectionModalLabel">Select Variant for ${productName}</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="variant-options">
                                        ${variantOptionsHtml}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Remove existing modal if present
                const existingModal = document.getElementById('variantSelectionModal');
                if (existingModal) {
                    existingModal.remove();
                }
                
                // Add modal to body
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('variantSelectionModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Error fetching variants:', error);
                this.showNotification('Error loading variants. Please try again.', 'error');
            });
    }

    // Select product variant
    selectProductVariant(productId, variantId) {
        // Fetch variant details via AJAX
        fetch(`/sales/product/variant/${variantId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.showNotification(`Error loading variant: ${data.error}`, 'error');
                    return;
                }
                
                // Check if variant already exists in cart
                const existingItemIndex = this.cart.findIndex(item => 
                    item.id == data.id && item.is_variant);
                
                if (existingItemIndex !== -1) {
                    // Check stock availability
                    if (this.cart[existingItemIndex].quantity >= data.stock) {
                        this.showNotification('Cannot add more items. Insufficient stock available.', 'warning');
                        return;
                    }
                    
                    // Update quantity of existing variant
                    this.cart[existingItemIndex].quantity += 1;
                } else {
                    // Check stock availability
                    if (data.stock <= 0) {
                        this.showNotification('Cannot add variant. Variant is out of stock.', 'warning');
                        return;
                    }
                    
                    // Add new variant to cart
                    this.cart.push({
                        id: data.id,
                        name: data.name,
                        price: data.price,
                        quantity: 1,
                        stock: data.stock,
                        unit: data.unit,
                        is_variant: true,
                        parent_product_id: data.parent_product_id,
                        parent_product_name: data.parent_product_name
                    });
                }
                
                // Save cart and update display
                this.saveCart();
                this.updateCartDisplay();
                this.updateCheckoutButtonState();
                
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('variantSelectionModal'));
                if (modal) {
                    modal.hide();
                }
                
                // Show notification
                this.showNotification(`${data.name} added to cart`, 'success');
            })
            .catch(error => {
                console.error('Error fetching variant details:', error);
                this.showNotification('Error adding variant to cart. Please try again.', 'error');
            });
    }

    // Update quantity of item in cart
    updateQuantity(productId, change) {
        const itemIndex = this.cart.findIndex(item => item.id == productId);
        if (itemIndex !== -1) {
            const newItemQuantity = this.cart[itemIndex].quantity + change;
            
            // Ensure quantity doesn't go below 1
            if (newItemQuantity < 1) {
                return;
            }
            
            // Check stock availability when increasing quantity
            if (change > 0 && newItemQuantity > this.cart[itemIndex].stock) {
                this.showNotification('Cannot add more items. Insufficient stock available.', 'warning');
                return;
            }
            
            this.cart[itemIndex].quantity = newItemQuantity;
            
            // Save cart and update display
            this.saveCart();
            this.updateCartDisplay();
            this.updateCheckoutButtonState();
        }
    }

    // Remove item from cart
    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id != productId);
        
        // Save cart and update display
        this.saveCart();
        this.updateCartDisplay();
        this.updateCheckoutButtonState();
        
        // Show notification
        this.showNotification('Item removed from cart', 'info');
    }

    // Clear cart
    clearCart() {
        this.cart = [];
        
        // Save cart and update display
        this.saveCart();
        this.updateCartDisplay();
        this.updateCheckoutButtonState();
        
        // Show notification
        this.showNotification('Cart cleared', 'info');
    }

    // Update cart display
    updateCartDisplay() {
        const cartItemsContainer = document.getElementById('cartItems');
        const cartItemCount = document.getElementById('cartItemCount');
        const cartSubtotal = document.getElementById('cartSubtotal');
        const cartTax = document.getElementById('cartTax');
        const cartDiscount = document.getElementById('cartDiscount');
        const cartTotal = document.getElementById('cartTotal');
        const checkoutButton = document.getElementById('checkoutButton');
        
        if (!cartItemsContainer) return;
        
        if (this.cart.length === 0) {
            // Show empty cart message
            cartItemsContainer.innerHTML = `
                <div class="empty-cart">
                    <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                    <p>Your cart is empty</p>
                </div>
            `;
            
            // Update item count
            if (cartItemCount) {
                cartItemCount.textContent = '0 items';
                cartItemCount.className = 'badge bg-primary';
            }
            
            // Update totals
            if (cartSubtotal) cartSubtotal.textContent = `${this.getCurrencySymbol()}0.00`;
            if (cartTax) cartTax.textContent = `${this.getCurrencySymbol()}0.00`;
            if (cartDiscount) cartDiscount.textContent = `${this.getCurrencySymbol()}0.00`;
            if (cartTotal) cartTotal.textContent = `${this.getCurrencySymbol()}0.00`;
            
            // Disable checkout button
            if (checkoutButton) {
                checkoutButton.disabled = true;
            }
            
            return;
        }
        
        // Update item count
        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        if (cartItemCount) {
            cartItemCount.textContent = `${totalItems} ${totalItems === 1 ? 'item' : 'items'}`;
            cartItemCount.className = 'badge bg-primary';
        }
        
        // Generate cart items HTML
        let cartHTML = '';
        this.cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            cartHTML += `
                <div class="cart-item" data-product-id="${item.id}">
                    <div class="cart-item-info">
                        <h6>${item.name}</h6>
                        <p class="item-details">${item.quantity} × ${this.getCurrencySymbol()}${item.price.toFixed(2)}</p>
                    </div>
                    <div class="cart-item-actions">
                        <div class="quantity-controls">
                            <button class="btn btn-sm btn-outline-secondary qty-btn qty-decrease" type="button">
                                <i class="fas fa-minus"></i>
                            </button>
                            <span class="quantity-display">${item.quantity}</span>
                            <button class="btn btn-sm btn-outline-secondary qty-btn qty-increase" type="button">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                        <div class="item-total">${this.getCurrencySymbol()}${itemTotal.toFixed(2)}</div>
                        <button class="btn btn-sm btn-outline-danger remove-item" type="button">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        cartItemsContainer.innerHTML = cartHTML;
        
        // Update totals
        const totals = this.calculateTotals();
        if (cartSubtotal) cartSubtotal.textContent = `${this.getCurrencySymbol()}${totals.subtotal.toFixed(2)}`;
        if (cartTax) cartTax.textContent = `${this.getCurrencySymbol()}${totals.tax.toFixed(2)}`;
        if (cartDiscount) cartDiscount.textContent = `${this.getCurrencySymbol()}${totals.discount.toFixed(2)}`;
        if (cartTotal) cartTotal.textContent = `${this.getCurrencySymbol()}${totals.total.toFixed(2)}`;
        
        // Enable checkout button
        if (checkoutButton) {
            checkoutButton.disabled = false;
        }
    }

    // Update checkout button state
    updateCheckoutButtonState() {
        const checkoutButton = document.getElementById('checkoutButton');
        if (checkoutButton) {
            checkoutButton.disabled = this.cart.length === 0;
        }
    }

    // Update order summary
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
        const creditSaleCheckbox = document.getElementById('creditSaleCheckbox');
        const dueDateInput = document.getElementById('dueDateInput');
        
        const saleData = {
            customer_id: customerSelect ? customerSelect.value : null,
            payment_method: paymentOptions.length > 0 ? paymentOptions[0].dataset.method : 'cash',
            discount: discountInput ? parseFloat(discountInput.value) || 0 : 0,
            is_credit_sale: creditSaleCheckbox ? creditSaleCheckbox.checked : false,
            due_date: dueDateInput ? dueDateInput.value : null,
            cart_items: this.cart.map(item => ({
                id: item.id,
                name: item.name,
                price: item.price,
                quantity: item.quantity,
                is_variant: item.is_variant || false
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
                
                // Reset credit sale form
                if (creditSaleCheckbox) {
                    creditSaleCheckbox.checked = false;
                    creditSaleOptions.style.display = 'none';
                    dueDateInput.value = '';
                }
                
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

    // Show/hide loading indicator
    showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    // Show notification message
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.style.maxWidth = '300px';
        notification.textContent = message;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    getCurrencySymbol() {
        return window.business_settings ? window.business_settings.currency_symbol : '$';
    }

    // Load cart from server instead of localStorage
    async loadCart() {
        try {
            console.log('Fetching cart data from server...');
            const response = await fetch('/sales/cart/get/');
            console.log('Cart fetch response status:', response.status);
            
            // Check if response is OK
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error response:', errorText);
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Cart data received:', data);
            
            if (data.success) {
                this.cart = data.items.map(item => ({
                    id: item.product_id,
                    name: item.product_name,
                    price: item.unit_price,
                    quantity: item.quantity,
                    stock: item.product_stock || 0, // Add stock if available
                    unit: item.product_unit || '', // Add unit if available
                    is_variant: item.is_variant || false // Add variant flag
                }));
                console.log('Cart items loaded:', this.cart);
                this.updateCartDisplay();
            } else {
                console.error('Error loading cart:', data.error);
            }
        } catch (error) {
            console.error('Error loading cart:', error);
        }
    }

    // Save cart to server instead of localStorage
    async saveCart() {
        // In this implementation, we're directly working with server-side cart
        // So we don't need to save to localStorage, but we do need to update the display
        this.updateCartDisplay();
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
    }
}