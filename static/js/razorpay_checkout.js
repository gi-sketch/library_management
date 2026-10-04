/**
 * Library Management System - Seamless Payment Checkout
 * Supports both Razorpay live/test credentials AND an interactive built-in gateway simulator
 * (No PAN Card or third-party merchant account required).
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function initiatePayment(fineId) {
    const csrftoken = getCookie('csrftoken');
    const payBtn = document.getElementById(`pay-btn-${fineId}`);
    
    if (payBtn) {
        payBtn.disabled = true;
        payBtn.innerHTML = '<span>⏳ Preparing Checkout...</span>';
    }

    fetch(`/transactions/create-payment/${fineId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Payment Error: ' + (data.error || 'Could not initiate payment.'));
            if (payBtn) {
                payBtn.disabled = false;
                payBtn.innerHTML = '💳 Pay Now';
            }
            return;
        }

        // If user has real Razorpay credentials loaded
        if (typeof Razorpay !== 'undefined' && data.key && data.key.startsWith('rzp_live') && !data.is_simulated) {
            const options = {
                "key": data.key,
                "amount": data.amount,
                "currency": data.currency,
                "name": "Library Management System",
                "description": `Overdue Fine: ${data.book_title}`,
                "order_id": data.order_id,
                "handler": function (response) {
                    verifyBackendPayment({
                        fine_id: data.fine_id,
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_order_id: response.razorpay_order_id,
                        razorpay_signature: response.razorpay_signature
                    });
                },
                "prefill": {
                    "name": data.student_name,
                    "email": data.student_email,
                    "contact": data.student_phone
                },
                "theme": {
                    "color": "#059669"
                },
                "modal": {
                    "ondismiss": function() {
                        if (payBtn) {
                            payBtn.disabled = false;
                            payBtn.innerHTML = '💳 Pay Now';
                        }
                    }
                }
            };
            const rzp = new Razorpay(options);
            rzp.on('payment.failed', function (response){
                window.location.href = `/transactions/payment-failed/${data.fine_id}/?reason=${encodeURIComponent(response.error.description)}`;
            });
            rzp.open();
        } else {
            // Interactive Built-in Payment Gateway Simulator (No PAN / KYC required)
            renderSimulationModal(data);
        }
    })
    .catch(error => {
        console.error('Payment order creation error:', error);
        alert('Network error while initiating payment.');
        if (payBtn) {
            payBtn.disabled = false;
            payBtn.innerHTML = '💳 Pay Now';
        }
    });
}

function verifyBackendPayment(payload) {
    const csrftoken = getCookie('csrftoken');
    
    fetch('/transactions/verify-payment/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.redirect_url) {
            window.location.href = result.redirect_url;
        } else {
            alert('Verification Error: ' + (result.error || 'Payment verification failed.'));
            window.location.reload();
        }
    })
    .catch(err => {
        console.error('Verification error:', err);
        alert('Network error verifying payment.');
        window.location.reload();
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.style.background = 'rgba(255,255,255,0.06)');
    document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');
    
    const activeBtn = document.getElementById(`tab-btn-${tabName}`);
    const activeContent = document.getElementById(`tab-content-${tabName}`);
    
    if (activeBtn) activeBtn.style.background = '#69818d';
    if (activeContent) activeContent.style.display = 'block';
}

function renderSimulationModal(data) {
    const existing = document.getElementById('sim-payment-modal');
    if (existing) existing.remove();

    const amountInRupees = (data.amount / 100).toFixed(2);
    const modalHtml = `
        <div id="sim-payment-modal" style="
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.8); backdrop-filter: blur(10px);
            display: flex; align-items: center; justify-content: center; z-index: 99999;
            padding: 20px;
        ">
            <div style="
                background: #132e35; border: 1px solid rgba(255,255,255,0.15);
                border-radius: 24px; padding: 35px; max-width: 520px; width: 100%;
                color: #ffffff; box-shadow: 0 30px 70px rgba(0,0,0,0.6);
                animation: modalFadeIn 0.3s ease-out;
            ">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div>
                        <h3 style="margin: 0 0 4px 0; color: #ffffff; font-size: 20px; font-weight: 700;">💳 Library Payment Gateway</h3>
                        <p style="margin: 0; color: #afb3b7; font-size: 13px;">Secure Checkout Simulator</p>
                    </div>
                    <button onclick="cancelSimulatedPayment(${data.fine_id})" style="
                        background: rgba(255,255,255,0.1); border: none; color: #ffffff;
                        width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 16px;
                    ">✕</button>
                </div>

                <!-- Bill Summary -->
                <div style="
                    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 14px; padding: 14px 18px; margin-bottom: 20px;
                    display: flex; justify-content: space-between; align-items: center;
                ">
                    <div>
                        <div style="color: #afb3b7; font-size: 12px; text-transform: uppercase;">Book Title</div>
                        <div style="color: #ffffff; font-weight: 600; font-size: 14px;">${data.book_title}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #afb3b7; font-size: 12px; text-transform: uppercase;">Payable Fine</div>
                        <div style="color: #34d399; font-weight: 700; font-size: 22px;">₹${amountInRupees}</div>
                    </div>
                </div>

                <!-- Payment Method Tabs -->
                <div style="display: flex; gap: 8px; margin-bottom: 20px;">
                    <button id="tab-btn-upi" class="tab-btn" onclick="switchTab('upi')" style="
                        flex: 1; padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
                        background: #69818d; color: white; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
                    ">
                        📱 UPI / QR
                    </button>
                    <button id="tab-btn-card" class="tab-btn" onclick="switchTab('card')" style="
                        flex: 1; padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
                        background: rgba(255,255,255,0.06); color: white; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
                    ">
                        💳 Card
                    </button>
                    <button id="tab-btn-net" class="tab-btn" onclick="switchTab('net')" style="
                        flex: 1; padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
                        background: rgba(255,255,255,0.06); color: white; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
                    ">
                        🏦 Net Banking
                    </button>
                </div>

                <!-- Tab 1: UPI -->
                <div id="tab-content-upi" class="tab-content" style="text-align: center; margin-bottom: 20px;">
                    <div style="background: white; width: 140px; height: 140px; margin: 0 auto 12px auto; border-radius: 12px; padding: 8px; display: flex; align-items: center; justify-content: center;">
                        <svg viewBox="0 0 100 100" width="100%" height="100%">
                            <rect width="100" height="100" fill="white"/>
                            <path d="M10 10h30v30h-30z M60 10h30v30h-30z M10 60h30v30h-30z M20 20h10v10h-10z M70 20h10v10h-10z M20 70h10v10h-10z M50 20h5v10h-5z M50 50h10v10h-10z M70 50h20v5h-20z M50 70h15v20h-15z M70 70h20v20h-20z" fill="#0d1f23"/>
                        </svg>
                    </div>
                    <p style="font-size: 13px; color: #afb3b7; margin: 0 0 8px 0;">Scan with GPay / PhonePe / Paytm / BHIM</p>
                    <div style="font-size: 13px; color: #6ee7b7; background: rgba(16,185,129,0.1); border-radius: 8px; padding: 6px 12px; display: inline-block;">
                        UPI ID: <strong>library@upi</strong>
                    </div>
                </div>

                <!-- Tab 2: Card -->
                <div id="tab-content-card" class="tab-content" style="display: none; margin-bottom: 20px;">
                    <div style="margin-bottom: 12px;">
                        <label style="display: block; font-size: 12px; color: #afb3b7; margin-bottom: 4px;">Card Number</label>
                        <input type="text" value="4111 •••• •••• 1111" readonly style="
                            width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
                            border-radius: 8px; color: white; font-family: monospace; font-size: 14px;
                        ">
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <div style="flex: 1;">
                            <label style="display: block; font-size: 12px; color: #afb3b7; margin-bottom: 4px;">Expiry Date</label>
                            <input type="text" value="12/28" readonly style="
                                width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
                                border-radius: 8px; color: white; font-size: 14px;
                            ">
                        </div>
                        <div style="flex: 1;">
                            <label style="display: block; font-size: 12px; color: #afb3b7; margin-bottom: 4px;">CVV</label>
                            <input type="password" value="888" readonly style="
                                width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
                                border-radius: 8px; color: white; font-size: 14px;
                            ">
                        </div>
                    </div>
                </div>

                <!-- Tab 3: Net Banking -->
                <div id="tab-content-net" class="tab-content" style="display: none; margin-bottom: 20px;">
                    <label style="display: block; font-size: 12px; color: #afb3b7; margin-bottom: 6px;">Select Your Bank</label>
                    <select style="
                        width: 100%; padding: 12px; background: #0d1f23; border: 1px solid rgba(255,255,255,0.15);
                        border-radius: 8px; color: white; font-size: 14px; outline: none;
                    ">
                        <option>State Bank of India (SBI)</option>
                        <option>HDFC Bank</option>
                        <option>ICICI Bank</option>
                        <option>Axis Bank</option>
                        <option>Punjab National Bank</option>
                    </select>
                </div>

                <!-- Action Button -->
                <button id="sim-submit-btn" onclick="executeMockPayment(${data.fine_id}, '${data.order_id}', '${amountInRupees}')" style="
                    width: 100%; background: #059669; color: white; border: none; padding: 14px;
                    border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.3s;
                    box-shadow: 0 4px 15px rgba(5, 150, 105, 0.4);
                ">
                    ✓ Pay ₹${amountInRupees} & Clear Fine
                </button>

                <p style="text-align: center; margin: 15px 0 0 0; font-size: 12px; color: #69818d;">
                    🔒 256-bit SSL Encrypted Simulation • Instant Receipt Generation
                </p>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function executeMockPayment(fineId, orderId, amount) {
    const btn = document.getElementById('sim-submit-btn');
    if (btn) {
        btn.disabled = true;
        btn.style.background = '#047857';
        btn.innerHTML = '<span>⏳ Processing with Bank...</span>';
    }

    setTimeout(() => {
        const simPaymentId = 'pay_' + Date.now().toString(36) + Math.random().toString(36).substring(2, 6).toUpperCase();
        verifyBackendPayment({
            fine_id: fineId,
            razorpay_payment_id: simPaymentId,
            razorpay_order_id: orderId,
            razorpay_signature: 'simulated_signature'
        });
    }, 900);
}

function cancelSimulatedPayment(fineId) {
    const modal = document.getElementById('sim-payment-modal');
    if (modal) modal.remove();
    const payBtn = document.getElementById(`pay-btn-${fineId}`);
    if (payBtn) {
        payBtn.disabled = false;
        payBtn.innerHTML = '💳 Pay Now';
    }
}
