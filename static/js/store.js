/**
 * HIGH TECH MOBILE - Storefront Interactive Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
  initLiveSearch();
  initPincodeChecker();
  initVariantSelector();
  initImageGallery();
  initCartActions();
  initWishlist();
  initMobileMenu();
});

// Toast Notifications
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? '✓' : (type === 'danger' ? '✕' : 'ℹ');
  toast.innerHTML = `<span style="font-weight:700;font-size:1.1rem">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// 1. Live Search
function initLiveSearch() {
  const searchInput = document.getElementById('store-search-input');
  const dropdown = document.getElementById('store-search-dropdown');
  if (!searchInput || !dropdown) return;
  
  let debounceTimeout;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimeout);
    const query = e.target.value.trim();
    if (query.length < 2) {
      dropdown.classList.remove('active');
      dropdown.innerHTML = '';
      return;
    }
    
    debounceTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        if (data && data.length > 0) {
          dropdown.innerHTML = data.map(item => `
            <a href="/product/${item.slug}" class="search-item">
              <img src="${item.image}" alt="${item.name}">
              <div>
                <div style="font-size:0.75rem; color:#38BDF8; font-weight:700;">${item.brand || ''}</div>
                <div style="font-size:0.875rem; font-weight:600;">${item.name}</div>
                <div style="font-size:0.825rem; color:#10B981; font-weight:700;">${item.price}</div>
              </div>
            </a>
          `).join('');
          dropdown.classList.add('active');
        } else {
          dropdown.innerHTML = `<div style="padding:1rem; color:#94A3B8; font-size:0.85rem; text-align:center;">No tech products found for "${query}"</div>`;
          dropdown.classList.add('active');
        }
      } catch (err) {
        console.error('Search error:', err);
      }
    }, 250);
  });
  
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('active');
    }
  });
}

// 2. Add To Cart & Cart Updates
function initCartActions() {
  document.querySelectorAll('.btn-ajax-add-cart').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const productId = btn.dataset.productId;
      const variantId = btn.dataset.variantId || null;
      const quantity = parseInt(btn.dataset.quantity || 1);
      
      const originalText = btn.innerHTML;
      btn.innerHTML = `<span class="spinner"></span> Adding...`;
      btn.disabled = true;
      
      try {
        const res = await fetch('/api/cart/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: productId, variant_id: variantId, quantity: quantity })
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
          showToast(data.message, 'success');
          updateCartBadge(data.total_items);
        } else {
          showToast(data.message || 'Failed to add item', 'danger');
        }
      } catch (err) {
        showToast('Network error while updating cart.', 'danger');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    });
  });
}

function updateCartBadge(count) {
  document.querySelectorAll('.cart-badge-count').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'flex' : 'none';
  });
}

// 3. Pincode Checker
function initPincodeChecker() {
  const checkBtn = document.getElementById('btn-check-pincode');
  const pincodeInput = document.getElementById('input-pincode');
  const resultDiv = document.getElementById('pincode-result');
  if (!checkBtn || !pincodeInput || !resultDiv) return;
  
  checkBtn.addEventListener('click', async () => {
    const pin = pincodeInput.value.trim();
    if (!/^\d{6}$/.test(pin)) {
      resultDiv.innerHTML = `<span style="color:#EF4444;font-size:0.85rem">Please enter a valid 6-digit Indian PIN code.</span>`;
      return;
    }
    
    checkBtn.textContent = 'Checking...';
    try {
      const res = await fetch(`/api/pincode/check?pincode=${pin}`);
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        resultDiv.innerHTML = `
          <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:0.75rem; font-size:0.85rem; color:#166534; margin-top:0.5rem">
            <strong>✓ Delivery to ${data.pincode} (${data.region})</strong>
            <div>Estimated Arrival: <b>${data.estimated_delivery}</b> (${data.estimated_days})</div>
            <div>Express Courier: <b>${data.courier}</b></div>
            <div style="color:#15803D">Cash on Delivery Available</div>
          </div>
        `;
      } else {
        resultDiv.innerHTML = `<span style="color:#EF4444;font-size:0.85rem">${data.message}</span>`;
      }
    } catch (e) {
      resultDiv.innerHTML = `<span style="color:#EF4444;font-size:0.85rem">Could not verify pincode.</span>`;
    } finally {
      checkBtn.textContent = 'Check';
    }
  });
}

// 4. Product Detail Variant Selector
function initVariantSelector() {
  const variantOptions = document.querySelectorAll('.variant-btn');
  const priceDisplay = document.getElementById('product-display-price');
  const stockDisplay = document.getElementById('product-display-stock');
  const addToCartBtn = document.getElementById('btn-detail-add-cart');
  const buyNowBtn = document.getElementById('btn-detail-buy-now');
  if (!variantOptions.length) return;
  
  variantOptions.forEach(opt => {
    opt.addEventListener('click', () => {
      // Toggle active class inside its group
      const group = opt.dataset.group;
      document.querySelectorAll(`.variant-btn[data-group="${group}"]`).forEach(b => b.classList.remove('active'));
      opt.classList.add('active');
      
      // Update variant ID
      const variantId = opt.dataset.variantId;
      const addPrice = parseFloat(opt.dataset.addPrice || 0);
      const stock = parseInt(opt.dataset.stock || 0);
      const basePrice = parseFloat(opt.dataset.basePrice || 0);
      
      if (priceDisplay) {
        const total = basePrice + addPrice;
        priceDisplay.textContent = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(total);
      }
      
      if (stockDisplay) {
        if (stock > 0) {
          stockDisplay.innerHTML = `<span style="color:#10B981;font-weight:600">In Stock (${stock} units left)</span>`;
          if (addToCartBtn) addToCartBtn.disabled = false;
          if (buyNowBtn) buyNowBtn.disabled = false;
        } else {
          stockDisplay.innerHTML = `<span style="color:#EF4444;font-weight:600">Out of Stock</span>`;
          if (addToCartBtn) addToCartBtn.disabled = true;
          if (buyNowBtn) buyNowBtn.disabled = true;
        }
      }
      
      if (addToCartBtn && variantId) {
        addToCartBtn.dataset.variantId = variantId;
      }
    });
  });
}

// 5. Product Image Gallery Switcher
function initImageGallery() {
  const mainImg = document.getElementById('gallery-main-image');
  const thumbs = document.querySelectorAll('.gallery-thumb');
  if (!mainImg || !thumbs.length) return;
  
  thumbs.forEach(t => {
    t.addEventListener('click', () => {
      thumbs.forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      mainImg.src = t.dataset.fullImg;
    });
  });
}

// 6. Wishlist Toggle
function initWishlist() {
  document.querySelectorAll('.btn-wishlist-toggle').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const productId = btn.dataset.productId;
      try {
        const res = await fetch('/api/wishlist/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: productId })
        });
        const data = await res.json();
        if (res.status === 401) {
          showToast('Please log in to save items to your wishlist.', 'info');
          setTimeout(() => window.location.href = '/login', 1200);
          return;
        }
        if (data.status === 'success') {
          btn.classList.toggle('active', data.in_wishlist);
          showToast(data.message, 'success');
          document.querySelectorAll('.wishlist-badge-count').forEach(el => {
            el.textContent = data.wishlist_count;
            el.style.display = data.wishlist_count > 0 ? 'flex' : 'none';
          });
        }
      } catch (err) {
        showToast('Error updating wishlist.', 'danger');
      }
    });
  });
}

// 7. Mobile Drawer Navigation
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-toggle');
  const drawer = document.getElementById('mobile-drawer');
  const closeBtn = document.getElementById('mobile-drawer-close');
  if (!toggleBtn || !drawer) return;
  
  toggleBtn.addEventListener('click', () => drawer.classList.add('active'));
  if (closeBtn) closeBtn.addEventListener('click', () => drawer.classList.remove('active'));
}
