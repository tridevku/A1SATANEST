const page = document.body.dataset.page;

const money = (num) => Number(num || 0).toLocaleString("en-IN");

const cart = {
    key: "a1_cart",
    all() {
        try {
            return JSON.parse(localStorage.getItem(this.key) || "[]");
        } catch {
            return [];
        }
    },
    save(items) {
        localStorage.setItem(this.key, JSON.stringify(items));
        updateCartCounter();
    },
};

const el = (id) => document.getElementById(id);

function setupMobileMenu() {
    const btn = el("mobileMenuBtn");
    const nav = document.querySelector(".nav-links");
    if (!btn || !nav) return;
    btn.addEventListener("click", () => nav.classList.toggle("open"));
}

function updateCartCounter() {
    const countEl = el("cartCount");
    if (!countEl) return;
    const count = cart.all().reduce((sum, item) => sum + item.quantity, 0);
    countEl.textContent = String(count);
}

async function initHome() {
    const reviewList = el("reviewList");
    if (!reviewList) return;

    const [reviewRes, statsRes] = await Promise.all([fetch("/api/reviews"), fetch("/api/stats")]);
    const reviews = await reviewRes.json();
    const stats = await statsRes.json();

    reviewList.innerHTML = reviews
        .map(
            (r) => `
                <article class="review-card">
                    <p>"${r.message}"</p>
                    <div class="review-meta">${r.customer_name} | ${"★".repeat(Number(r.rating || 4))}</div>
                </article>
            `
        )
        .join("");

    const statsWrap = el("heroStats");
    if (statsWrap) {
        statsWrap.innerHTML = `
            <article><h3>${stats.service_requests}</h3><p>Repairs Requested</p></article>
            <article><h3>${stats.completed_repairs}</h3><p>Repairs Completed</p></article>
            <article><h3>${stats.completion_rate}%</h3><p>On-Time Delivery</p></article>
            <article><h3>${stats.orders}</h3><p>Parts Orders</p></article>
        `;
    }
}

async function initProducts() {
    const grid = el("productGrid");
    const search = el("productSearch");
    const category = el("categoryFilter");
    const clear = el("clearFilters");

    if (!grid || !search || !category) return;

    async function loadProducts() {
        const params = new URLSearchParams({
            category: category.value,
            search: search.value.trim(),
        });

        const res = await fetch(`/api/products?${params.toString()}`);
        const products = await res.json();

        if (!products.length) {
            grid.innerHTML = "<p>No products found for this filter.</p>";
            return;
        }

        grid.innerHTML = products
            .map(
                (p) => `
                    <article class="product-card">
                        <img src="${p.image}" alt="${p.name}" />
                        <div class="product-body">
                            <h3>${p.name}</h3>
                            <p>${p.description}</p>
                            <div class="stock-badge">${p.stock} in stock | ${p.category}</div>
                            <div class="price-row">
                                <strong>Rs ${money(p.price)}</strong>
                                <s>Rs ${money(p.mrp)}</s>
                            </div>
                            <button class="btn btn-primary full" data-add-cart="${p.id}">Add to Cart</button>
                        </div>
                    </article>
                `
            )
            .join("");
    }

    async function addToCart(productId) {
        const res = await fetch(`/api/products?category=all`);
        const products = await res.json();
        const target = products.find((p) => Number(p.id) === Number(productId));
        if (!target) return;

        const items = cart.all();
        const existing = items.find((i) => i.product_id === target.id);
        if (existing) {
            existing.quantity += 1;
        } else {
            items.push({
                product_id: target.id,
                name: target.name,
                unit_price: target.price,
                quantity: 1,
            });
        }

        cart.save(items);
        renderCart();
    }

    function renderCart() {
        const items = cart.all();
        const cartItems = el("cartItems");
        const cartTotal = el("cartTotal");
        if (!cartItems || !cartTotal) return;

        if (!items.length) {
            cartItems.innerHTML = "<p>Your cart is empty.</p>";
            cartTotal.textContent = "0";
            return;
        }

        cartItems.innerHTML = items
            .map(
                (item) => `
                    <article class="cart-item">
                        <h4>${item.name}</h4>
                        <p>Qty: ${item.quantity} | Rs ${money(item.unit_price)} each</p>
                        <button class="btn btn-ghost full" data-remove-item="${item.product_id}">Remove</button>
                    </article>
                `
            )
            .join("");

        const total = items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0);
        cartTotal.textContent = money(total);
    }

    grid.addEventListener("click", (event) => {
        const button = event.target.closest("[data-add-cart]");
        if (!button) return;
        addToCart(Number(button.dataset.addCart));
    });

    el("cartItems")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-remove-item]");
        if (!button) return;
        const id = Number(button.dataset.removeItem);
        const updated = cart.all().filter((item) => item.product_id !== id);
        cart.save(updated);
        renderCart();
    });

    search.addEventListener("input", loadProducts);
    category.addEventListener("change", loadProducts);
    clear?.addEventListener("click", () => {
        search.value = "";
        category.value = "all";
        loadProducts();
    });

    el("openCartBtn")?.addEventListener("click", () => el("cartDrawer")?.classList.add("open"));
    el("closeCartBtn")?.addEventListener("click", () => el("cartDrawer")?.classList.remove("open"));

    const checkoutModal = el("checkoutModal");
    el("checkoutBtn")?.addEventListener("click", () => {
        if (!cart.all().length) return;
        checkoutModal?.classList.remove("hidden");
    });
    el("closeCheckout")?.addEventListener("click", () => checkoutModal?.classList.add("hidden"));

    el("checkoutForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const customer = Object.fromEntries(formData.entries());

        const res = await fetch("/api/place-order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ customer, items: cart.all() }),
        });

        const data = await res.json();
        const msg = el("checkoutMessage");
        if (!res.ok || !data.ok) {
            msg.textContent = data.message || "Order failed. Please try again.";
            msg.style.color = "#b73030";
            return;
        }

        msg.textContent = `Order #${data.order_id} confirmed. Total Rs ${money(data.total)}.`;
        msg.style.color = "#0c7f6f";
        cart.save([]);
        renderCart();
        form.reset();
    });

    updateCartCounter();
    renderCart();
    await loadProducts();
}

function initBooking() {
    const form = el("bookingForm");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());

        const res = await fetch("/api/book-service", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        const msg = el("bookingMessage");
        if (!res.ok || !data.ok) {
            msg.textContent = data.message || "Booking failed. Please retry.";
            msg.style.color = "#b73030";
            return;
        }

        msg.textContent = `Ticket #${data.ticket_id} created. Estimated repair charge Rs ${money(data.estimated_price)}.`;
        msg.style.color = "#0c7f6f";
        form.reset();
    });
}

function initSupport() {
    const form = el("supportForm");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());

        const res = await fetch("/api/support-request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        const msg = el("supportMessage");
        if (!res.ok || !data.ok) {
            msg.textContent = data.message || "Unable to submit support ticket. Please try again.";
            msg.style.color = "#b73030";
            return;
        }

        msg.textContent = `Support ticket #${data.ticket_id} created. Our team will contact you shortly.`;
        msg.style.color = "#0c7f6f";
        form.reset();
    });
}

function initContact() {
    const form = el("contactForm");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());

        const res = await fetch("/api/contact-message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        const msg = el("contactMessage");
        if (!res.ok || !data.ok) {
            msg.textContent = data.message || "Unable to send your message right now.";
            msg.style.color = "#b73030";
            return;
        }

        msg.textContent = `Message #${data.message_id} received. We will get back to you soon.`;
        msg.style.color = "#0c7f6f";
        form.reset();
    });
}

function initCustomerLogin() {
    const form = el("customerOtpForm");
    const sendBtn = el("sendOtpBtn");
    const messageEl = el("customerOtpMessage");
    const hintEl = el("customerOtpHint");
    const phoneInput = el("customerPhone");

    if (!form || !sendBtn || !messageEl || !hintEl || !phoneInput) return;

    sendBtn.addEventListener("click", async () => {
        const phone = phoneInput.value.trim();
        if (phone.length < 10) {
            messageEl.textContent = "Please enter a valid phone number.";
            messageEl.style.color = "#b73030";
            return;
        }

        const res = await fetch("/api/customer/send-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone }),
        });
        const data = await res.json();

        if (!res.ok || !data.ok) {
            messageEl.textContent = data.message || "Unable to send OTP.";
            messageEl.style.color = "#b73030";
            hintEl.textContent = "";
            return;
        }

        messageEl.textContent = "OTP sent successfully.";
        messageEl.style.color = "#0c7f6f";
        hintEl.textContent = `Demo OTP: ${data.demo_otp} (valid for 5 minutes)`;
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());

        const res = await fetch("/api/customer/verify-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (!res.ok || !data.ok) {
            messageEl.textContent = data.message || "OTP verification failed.";
            messageEl.style.color = "#b73030";
            return;
        }

        messageEl.textContent = "Login successful. Redirecting...";
        messageEl.style.color = "#0c7f6f";
        window.location.href = "/customer/dashboard";
    });
}

async function initCustomerDashboard() {
    const serviceRows = el("customerServiceRows");
    const orderRows = el("customerOrderRows");
    const phoneLabel = el("customerPhoneLabel");
    if (!serviceRows || !orderRows || !phoneLabel) return;

    const res = await fetch("/api/customer/overview");
    if (res.status === 401) {
        window.location.href = "/customer/login";
        return;
    }

    const data = await res.json();
    if (!data.ok) {
        phoneLabel.textContent = "Unable to load dashboard data.";
        return;
    }

    phoneLabel.textContent = `Logged in phone: ${data.phone}`;

    serviceRows.innerHTML = (data.services || [])
        .map(
            (s) => `
                <tr>
                    <td>#${s.id}</td>
                    <td>${s.laptop_brand}</td>
                    <td>${s.issue_type}</td>
                    <td>${s.urgency}</td>
                    <td>Rs ${money(s.estimated_price)}</td>
                    <td>${s.status}</td>
                </tr>
            `
        )
        .join("");

    if (!serviceRows.innerHTML) {
        serviceRows.innerHTML = `<tr><td colspan="6">No repair tickets found for this phone number.</td></tr>`;
    }

    orderRows.innerHTML = (data.orders || [])
        .map(
            (o) => `
                <tr>
                    <td>#${o.id}</td>
                    <td>${o.city}</td>
                    <td>Rs ${money(o.total_amount)}</td>
                    <td>${o.payment_mode}</td>
                    <td>${o.status}</td>
                </tr>
            `
        )
        .join("");

    if (!orderRows.innerHTML) {
        orderRows.innerHTML = `<tr><td colspan="5">No orders found for this phone number.</td></tr>`;
    }
}

async function initAdmin() {
    const statsEl = el("adminStats");
    const serviceRows = el("serviceRows");
    const orderRows = el("orderRows");
    if (!statsEl || !serviceRows || !orderRows) return;

    const res = await fetch("/api/admin/overview");
    if (res.status === 401) {
        window.location.href = "/admin/login?next=/admin";
        return;
    }
    const data = await res.json();

    statsEl.innerHTML = `
        <article><h3>${data.stats.service_requests}</h3><p>Service Tickets</p></article>
        <article><h3>${data.stats.completed_repairs}</h3><p>Completed Repairs</p></article>
        <article><h3>${data.stats.orders}</h3><p>Total Orders</p></article>
        <article><h3>Rs ${money(data.stats.revenue)}</h3><p>Total Revenue</p></article>
    `;

    serviceRows.innerHTML = data.recent_services
        .map(
            (s) => `
                <tr>
                    <td>#${s.id}</td>
                    <td>${s.customer_name}</td>
                    <td>${s.city}</td>
                    <td>${s.issue_type}</td>
                    <td>${s.urgency}</td>
                    <td>Rs ${money(s.estimated_price)}</td>
                    <td>${s.status}</td>
                </tr>
            `
        )
        .join("");

    orderRows.innerHTML = data.recent_orders
        .map(
            (o) => `
                <tr>
                    <td>#${o.id}</td>
                    <td>${o.customer_name}</td>
                    <td>${o.city}</td>
                    <td>Rs ${money(o.total_amount)}</td>
                    <td>${o.payment_mode}</td>
                    <td>${o.status}</td>
                </tr>
            `
        )
        .join("");
}

setupMobileMenu();

if (page === "home") initHome();
if (page === "products") initProducts();
if (page === "booking") initBooking();
if (page === "support") initSupport();
if (page === "contact") initContact();
if (page === "customer-login") initCustomerLogin();
if (page === "customer-dashboard") initCustomerDashboard();
if (page === "admin") initAdmin();
