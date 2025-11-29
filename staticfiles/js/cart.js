// Modern Cart System JavaScript functionality
class ModernCartSystem {
    constructor() {
        this.cart = [];
        this.init();
    }

    init() {
        // Initialize the cart system
        this.bindEvents();
        this.loadCart();
    }

    bindEvents() {
        // Handle add to cart buttons
        document.addEventListener('click', (e) => {
            // Handle product card clicks
            if (e.target.closest('.product-card')) {
                const productCard = e.target.closest('.product-card');
                
                // Check if this event is already being handled by another system
                // to prevent duplicate processing - IMPROVED COORDINATION
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by cart system
                e.cartSystemHandled = true;
                
                // Check if the click was on the "Add to Cart" button or the card itself
                if (e.target.closest('.add-to-cart-btn')) {
                    // Clicked on the button, let the button handler deal with it
                    const button = e.target.closest('.add-to-cart-btn');
                    const productId = productCard.dataset.productId;
                    const quantity = 1; // Default quantity
                    this.addToCart(productId, quantity);
                    this.animateButton(button);
                } else {
                    // Clicked on the card itself, add to cart
                    const productId = productCard.dataset.productId;
                    const quantity = 1; // Default quantity
                    this.addToCart(productId, quantity);
                    this.animateButton(productCard);
                }
            }
            
            // Handle clear cart button
            if (e.target.id === 'clearCart') {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by cart system
                e.cartSystemHandled = true;
                
                this.clearCart();
                this.animateButton(e.target);
            }
            
            // Handle quantity buttons in cart
            if (e.target.classList.contains('qty-btn')) {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by cart system
                e.cartSystemHandled = true;
                
                const itemId = e.target.closest('.cart-item').dataset.itemId;
                const change = e.target.classList.contains('qty-increase') ? 1 : -1;
                this.updateQuantity(itemId, change);
                this.animateButton(e.target);
            }
            
            // Handle remove item from cart
            if (e.target.classList.contains('remove-item')) {
                // Check if this event is already being handled by another system
                if (e.cartSystemHandled) {
                    return;
                }
                
                // Mark this event as handled by cart system
                e.cartSystemHandled = true;
                
                const itemId = e.target.closest('.cart-item').dataset.itemId;
                this.removeFromCart(itemId);
                this.animateButton(e.target);
            }
            
            // Handle checkout button - ONLY process if not already handled
            if ((e.target.id === 'checkoutButton' || e.target.id === 'processSale') && !e.saleProcessed) {
                // Mark this sale as processed to prevent duplicate processing
                e.saleProcessed = true;
                this.processSale();
                this.animateButton(e.target);
            }
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
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
            
            // Ctrl+S to process sale - ONLY process if not already handled
            if (e.ctrlKey && e.key === 's' && !e.saleProcessed) {
                e.preventDefault();
                const processButton = document.getElementById('processSale');
                if (processButton) {
                    // Mark this sale as processed to prevent duplicate processing
                    e.saleProcessed = true;
                    this.animateButton(processButton);
                    processButton.click();
                }
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
                this.animateButton(option);
            });
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

    // Add product to cart
    async addToCart(productId, quantity) {
        try {
            console.log('Adding to cart:', { productId, quantity });
            
            const csrfToken = this.getCSRFToken();
            if (!csrfToken) {
                this.showNotification('Security token not found. Please refresh the page and try again.', 'error');
                return;
            }
            
            console.log('Sending request to add item to cart...');
            const response = await fetch('/sales/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            });
            
            console.log('Response status:', response.status);
            
            // Check if response is OK
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error response:', errorText);
                this.showNotification(`Server error (${response.status}): ${errorText}`, 'error');
                return;
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                console.log('Loading cart after adding item...');
                this.loadCart();
            } else {
                this.showNotification(data.error || 'Error adding to cart', 'error');
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            this.showNotification(`Error adding to cart: ${error.message || 'Please try again.'}`, 'error');
        }
    }

    // Update cart item quantity
    async updateQuantity(itemId, change) {
        try {
            // Get current item to determine new quantity
            const currentItem = this.cart.find(item => item.id == itemId);
            if (!currentItem) return;
            
            const newQuantity = parseFloat(currentItem.quantity) + change;
            
            // If quantity is 0 or less, remove the item
            if (newQuantity <= 0) {
                this.removeFromCart(itemId);
                return;
            }
            
            const csrfToken = this.getCSRFToken();
            const response = await fetch('/sales/cart/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    item_id: itemId,
                    quantity: newQuantity
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadCart();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error updating cart item:', error);
            this.showNotification('Error updating cart item. Please try again.', 'error');
        }
    }

    // Remove item from cart
    async removeFromCart(itemId) {
        try {
            const csrfToken = this.getCSRFToken();
            const response = await fetch('/sales/cart/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    item_id: itemId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.loadCart();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error removing from cart:', error);
            this.showNotification('Error removing from cart. Please try again.', 'error');
        }
    }

    // Load cart contents
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
                this.cart = data.items;
                console.log('Cart items loaded:', this.cart);
                this.updateCartDisplay();
            } else {
                // Show a more user-friendly error message
                const errorMessage = data.error || 'Error loading cart. Please try again.';
                this.showNotification(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error loading cart:', error);
            // Show a more user-friendly error message
            const errorMessage = 'Error loading cart. Please refresh the page and try again.';
            this.showNotification(errorMessage, 'error');
        }
    }

    // Clear cart
    async clearCart() {
        try {
            const csrfToken = this.getCSRFToken();
            const response = await fetch('/sales/cart/clear/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.cart = [];
                this.updateCartDisplay();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error clearing cart:', error);
            this.showNotification('Error clearing cart. Please try again.', 'error');
        }
    }

    // Process sale
    async processSale() {
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
            discount: discountInput ? parseFloat(discountInput.value) || 0 : 0
        };
        
        console.log('Processing sale with data:', saleData);
        
        // Show loading spinner
        this.showLoading(true);
        
        try {
            const csrfToken = this.getCSRFToken();
            if (!csrfToken) {
                throw new Error('CSRF token not found');
            }
            
            console.log('CSRF Token:', csrfToken); // Debug log
            
            // Use the correct URL endpoint for cart-based sale processing
            const response = await fetch('/sales/cart/process/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(saleData)
            });
            
            console.log('Sale processing response status:', response.status);
            
            // Check if response is OK
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error response:', errorText);
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Sale processing response data:', data);
            
            if (data.success) {
                this.showNotification('Sale processed successfully!', 'success');
                // Clear cart
                this.cart = [];
                this.updateCartDisplay();
                
                // Redirect to sale detail page or show receipt
                if (data.sale_id) {
                    setTimeout(() => {
                        window.location.href = `/sales/${data.sale_id}/`;
                    }, 2000);
                }
            } else {
                this.showNotification(data.error || 'Error processing sale', 'error');
            }
        } catch (error) {
            console.error('Error processing sale:', error);
            // ADDITIONAL DEBUGGING: Show more detailed error message
            const errorMessage = error.message || 'Please try again.';
            this.showNotification(`Error processing sale: ${errorMessage}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Update cart display in UI
    updateCartDisplay() {
        const cartItemsContainer = document.getElementById('cartItems');
        const cartItemCount = document.getElementById('cartItemCount');
        const cartSubtotal = document.getElementById('cartSubtotal');
        const cartTax = document.getElementById('cartTax');
        const cartDiscount = document.getElementById('cartDiscount');
        const cartTotal = document.getElementById('cartTotal');
        const checkoutButton = document.getElementById('checkoutButton');
        
        console.log('Updating cart display with items:', this.cart);
        
        if (!cartItemsContainer) {
            console.error('Cart items container not found');
            return;
        }
        
        if (this.cart.length === 0) {
            console.log('Cart is empty, showing empty cart message');
            cartItemsContainer.innerHTML = `
                <div class="empty-cart">
                    <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                    <p>Your cart is empty</p>
                </div>
            `;
            if (cartItemCount) cartItemCount.textContent = '0 items';
            if (cartSubtotal) cartSubtotal.textContent = this.formatCurrency(0);
            if (cartTax) cartTax.textContent = this.formatCurrency(0);
            if (cartDiscount) cartDiscount.textContent = this.formatCurrency(0);
            if (cartTotal) cartTotal.textContent = this.formatCurrency(0);
            if (checkoutButton) checkoutButton.disabled = true;
            return;
        }
        
        // Update item count
        if (cartItemCount) {
            const totalItems = this.cart.reduce((sum, item) => sum + parseFloat(item.quantity), 0);
            cartItemCount.textContent = `${totalItems} item${totalItems !== 1 ? 's' : ''}`;
            console.log('Updated item count:', totalItems);
        }
        
        // Generate cart items HTML
        let cartItemsHTML = '';
        this.cart.forEach(item => {
            console.log('Processing cart item:', item);
            cartItemsHTML += `
                <div class="cart-item" data-item-id="${item.id}">
                    <div class="item-info">
                        <h6>${item.product_name}</h6>
                        <p class="item-price">${this.formatCurrency(item.unit_price)} × ${item.quantity}</p>
                    </div>
                    <div class="item-controls">
                        <button class="btn btn-outline-secondary btn-sm qty-btn qty-decrease">
                            <i class="fas fa-minus"></i>
                        </button>
                        <span class="item-quantity">${item.quantity}</span>
                        <button class="btn btn-outline-secondary btn-sm qty-btn qty-increase">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <div class="item-total">${this.formatCurrency(item.total_price)}</div>
                    <button class="btn btn-outline-danger btn-sm remove-item">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        });
        
        cartItemsContainer.innerHTML = cartItemsHTML;
        console.log('Updated cart items HTML');
        
        // Calculate and display totals
        const subtotal = this.cart.reduce((sum, item) => sum + parseFloat(item.total_price), 0);
        const tax = 0; // For now, no tax
        const discountInput = document.getElementById('discountInput');
        const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
        const total = subtotal + tax - discount;
        
        console.log('Calculated totals:', { subtotal, tax, discount, total });
        
        if (cartSubtotal) cartSubtotal.textContent = this.formatCurrency(subtotal);
        if (cartTax) cartTax.textContent = this.formatCurrency(tax);
        if (cartDiscount) cartDiscount.textContent = this.formatCurrency(discount);
        if (cartTotal) cartTotal.textContent = this.formatCurrency(total);
        if (checkoutButton) checkoutButton.disabled = false;
    }

    // Format currency
    formatCurrency(amount) {
        // Try to get currency symbol from global settings
        if (typeof window.business_settings !== 'undefined' && window.business_settings.currency_symbol) {
            return `${window.business_settings.currency_symbol}${parseFloat(amount).toFixed(2)}`;
        }
        // Fallback to $
        return `$${parseFloat(amount).toFixed(2)}`;
    }

    // Get CSRF token
    getCSRFToken() {
        // First try to get from hidden input (more reliable)
        const csrfTokenElement = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (csrfTokenElement) {
            console.log('CSRF token found in hidden input');
            return csrfTokenElement.value;
        }
        
        // Fallback to meta tag
        const csrfMetaTag = document.querySelector('meta[name=csrf-token]');
        if (csrfMetaTag) {
            console.log('CSRF token found in meta tag');
            return csrfMetaTag.getAttribute('content');
        }
        
        console.log('CSRF token not found');
        // ADDITIONAL DEBUGGING: Log all input elements to see what's available
        console.log('All input elements:', document.querySelectorAll('input'));
        return '';
    }

    // Show notification
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
        
        // Add to document
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 10);
        
        // Add close event
        const closeBtn = notification.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'fadeOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
        
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

    // Show loading spinner
    showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
}

// Initialize the cart system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing ModernCartSystem');
    window.modernCartSystem = new ModernCartSystem();
    console.log('ModernCartSystem initialized');
    
    // Load cart contents when page loads
    if (window.modernCartSystem) {
        console.log('Loading cart contents');
        window.modernCartSystem.loadCart();
    }
});