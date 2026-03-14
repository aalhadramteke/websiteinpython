let all_seats = null;
let cta_btn = null;
let customerModal = null;
let paymentMethodModal = null;
let upiModal = null;
let cashModal = null;
let cancelBtn = null;
let proceedBtn = null;
let movieSelect = null;

let currentUserData = null;
let selectedMoviePrice = 0;
let selectedMovieTitle = '';
let selectedPaymentMethod = null;
let customerInfo = {};
let ticketPrice = 0;
let bookingReference = '';

window.selectSeat = function(seatElement) {
    if (seatElement.classList.contains('occupied')) return;
    seatElement.classList.toggle('selected');
    const allSeats = document.querySelectorAll('.row .seat');
    const selectedSeats = document.querySelectorAll('.row .seat.selected');
    const seatsIndex = Array.from(selectedSeats).map(s => Array.from(allSeats).indexOf(s));
    localStorage.setItem('selectedSeats', JSON.stringify(seatsIndex));
    updateDisplayPrice();
    console.log(`Seats: ${seatsIndex.length}`, seatsIndex);
};

function initializeDOMElements() {
    all_seats = document.querySelectorAll('.row .seat');
    cta_btn = document.getElementById('purchaseBtn') || document.querySelector('.purchase_btn');
    customerModal = document.getElementById('customerModal');
    paymentMethodModal = document.getElementById('paymentMethodModal');
    upiModal = document.getElementById('upiModal');
    cashModal = document.getElementById('cashModal');
    cancelBtn = document.getElementById('cancelBtn');
    proceedBtn = document.getElementById('proceedBtn');
    movieSelect = document.getElementById('movie');
    if (movieSelect) {
        selectedMoviePrice = +movieSelect.value;
        selectedMovieTitle = movieSelect.options[movieSelect.selectedIndex]?.id || '';
        ticketPrice = selectedMoviePrice;
    }
}

async function loadCurrentUser() {
    try {
        const response = await fetch('/user-info/');
        currentUserData = await response.json();
        if (currentUserData.authenticated) {
            ['modalFirstName', 'modalLastName', 'modalEmail', 'modalPhone'].forEach(id => {
                const input = document.getElementById(id);
                if (input) input.value = currentUserData[id.replace('modal', '').toLowerCase()] || '';
            });
        }
    } catch (e) {
        console.warn('User load failed:', e);
    }
}

async function contactAPI(url, body) {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });
        return await response.json();
    } catch (e) {
        console.error('API error:', e);
        throw e;
    }
}

async function refreshSeat() {
    const movie_title = localStorage.getItem('selectedMovieTitle') || selectedMovieTitle;
    if (!movie_title) return;
    try {
        const data = await contactAPI("/occupied/", { movie_title });
        const occupied_seat = data['occupied_seats'] || [];
        all_seats.forEach(seat => seat.classList.remove("occupied"));
        if (localStorage.getItem("selectedMovieTitle") === data["movie"]) {
            occupied_seat.forEach(idx => {
                const seat = all_seats[idx];
                if (seat) {
                    seat.classList.add('occupied');
                    seat.classList.remove('selected');
                }
            });
            let stored = [];
    try {
      const storedStr = localStorage.getItem('selectedSeats');
      stored = storedStr ? JSON.parse(storedStr) : [];
    } catch (e) {
      console.error('refreshSeat stored parse error:', e);
      localStorage.removeItem('selectedSeats');
    }
            const updated = stored.filter(idx => !occupied_seat.includes(idx));
            if (updated.length !== stored.length) localStorage.setItem("selectedSeats", JSON.stringify(updated));
        }
        updateDisplayPrice();
    } catch (e) {
        console.error("Refresh seats error:", e);
    }
}

function updateDisplayPrice() {
    const selectedSeats = document.querySelectorAll('.row .seat.selected');
    const countDisplay = document.getElementById('count');
    const totalDisplay = document.getElementById('total');
    ticketPrice = +localStorage.getItem('selectedMoviePrice') || selectedMoviePrice || 0;
    if (countDisplay) countDisplay.innerText = selectedSeats.length;
    if (totalDisplay) totalDisplay.innerText = selectedSeats.length * ticketPrice;
}

function populateSelectedSeats() {
    let selectedSeats = [];
    try {
      const stored = localStorage.getItem('selectedSeats');
      selectedSeats = stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('populateSelectedSeats parse error:', e);
      localStorage.removeItem('selectedSeats');
    }
    if (selectedSeats.length === 0) return;
    all_seats.forEach((seat, index) => {
        if (selectedSeats.includes(index) && !seat.classList.contains('occupied')) seat.classList.add('selected');
    });
    updateDisplayPrice();
}

function setupMovieSelectListener() {
    if (!movieSelect) return;
    movieSelect.addEventListener('change', e => {
        selectedMoviePrice = +e.target.value;
        selectedMovieTitle = e.target.options[e.target.selectedIndex].id;
        localStorage.setItem('selectedMoviePrice', selectedMoviePrice);
        localStorage.setItem('selectedMovieTitle', selectedMovieTitle);
        refreshSeat();
    });
}

async function handlePurchaseClick() {
    console.log('Purchase button clicked!');
    let seat_list = [];
    try {
      const stored = localStorage.getItem("selectedSeats");
      seat_list = stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('handlePurchaseClick seats parse error:', e);
      localStorage.removeItem("selectedSeats");
    }
    const movie_title = localStorage.getItem('selectedMovieTitle') || '';
    
    console.log('Seats:', seat_list.length, 'Movie:', movie_title);
    
    if (seat_list.length === 0) {
        showPaymentStatus('Please select at least one seat', true);
        console.log('Blocked: no seats');
        return;
    }
    if (!movie_title) {
        showPaymentStatus('No movie selected. Go to home page first!', true);
        console.log('Blocked: no movie');
        return;
    }
    if (!customerModal) {
        console.error('Customer modal not found!');
        showPaymentStatus('UI error - refresh page', true);
        return;
    }
    customerModal.style.display = 'block';
    console.log('Opened customer modal');
}

function showPaymentStatus(message, isError = false) {
    const statusDiv = document.getElementById('paymentStatus');
    if (!statusDiv) return;
    statusDiv.textContent = message;
    statusDiv.className = 'payment-status' + (isError ? ' error' : '');
    statusDiv.style.display = 'block';
    setTimeout(() => statusDiv.style.display = 'none', 5000);
}

function closeCustomerModal() {
    customerModal.style.display = 'none';
}

function handleProceedToPayment() {
    customerInfo = {
        first_name: document.getElementById('modalFirstName').value,
        last_name: document.getElementById('modalLastName').value,
        email: document.getElementById('modalEmail').value,
        phone: document.getElementById('modalPhone').value
    };
    if (!customerInfo.first_name || !customerInfo.email || !customerInfo.phone) {
        showPaymentStatus('Please fill all required fields', true);
        return;
    }
    customerModal.style.display = 'none';
    paymentMethodModal.style.display = 'block';
}

function closePaymentMethodModal() {
    paymentMethodModal.style.display = 'none';
}

window.selectPaymentMethod = function(method) {
    selectedPaymentMethod = method;
    paymentMethodModal.style.display = 'none';
    if (method === 'card') {
        proceedToPayment();
    } else if (method === 'upi') {
        generateUPI();
    } else if (method === 'cash') {
        handleCashPayment();
    }
};

async function generateUPI() {
    const seat_list = JSON.parse(localStorage.getItem('selectedSeats') || '[]');
    const total = seat_list.length * ticketPrice;
    try {
        const data = await contactAPI('/generate-upi-qr/', { booking_reference: '', total_amount: total, phone: customerInfo.phone });
        bookingReference = data.booking_reference;
        document.getElementById('upiReference').textContent = data.booking_reference;
        document.getElementById('upiAmount').textContent = `₹${total}`;
        if (data.qr_code) {
            document.getElementById('qrCodeImage').src = data.qr_code;
            document.getElementById('qrCodeImage').style.display = 'block';
        }
        upiModal.style.display = 'block';
    } catch (e) {
        showPaymentStatus('UPI generation failed', true);
    }
}

async function confirmUPI() {
    await proceedToPayment('upi');
    upiModal.style.display = 'none';
}

async function handleCashPayment() {
    const seat_list = JSON.parse(localStorage.getItem('selectedSeats') || '[]');
    const total = seat_list.length * ticketPrice;
    bookingReference = `CASH${Date.now()}`;
    document.getElementById('cashReference').textContent = bookingReference;
    document.getElementById('cashAmount').textContent = `₹${total}`;
    document.getElementById('cashSeats').textContent = seat_list.length;
    cashModal.style.display = 'block';
}

async function proceedToPayment(method = 'card') {
    const seat_list = JSON.parse(localStorage.getItem('selectedSeats') || '[]');
    // Fallback movie_title from localStorage if not available
    const movie_title = selectedMovieTitle || localStorage.getItem('selectedMovieTitle') || '';
    
    if (!movie_title) {
        showPaymentStatus('No movie selected. Please go back and select a movie.', true);
        return;
    }
    
    const data = {
        seat_list,
        movie_title,
        payment_method: method,
        ...customerInfo
    };
    try {
        const response = await contactAPI('/payment/', data);
        console.log('Payment initiation response:', response); // Debug log
        
        if (response.success && response.payment_url) {
            console.log('Redirecting to Paystack:', response.payment_url);
            window.location.href = response.payment_url;
        } else if (response.test_mode) {
            console.log('Test mode - redirecting to confirm');
            window.location.href = '/payment-confirm/';
        } else if (response.booking_reference) {
            console.log('Non-card payment reference:', response.booking_reference);
            showPaymentStatus(`Payment initiated. Reference: ${response.booking_reference}`);
        } else if (response.error) {
            console.error('Payment error:', response.error);
            showPaymentStatus(`Payment failed: ${response.error}`, true);
        } else {
            console.error('Unexpected payment response:', response);
            showPaymentStatus('Payment initiation failed. Check console.', true);
        }
    } catch (e) {
        console.error('Payment error:', e);
        showPaymentStatus('Payment initiation failed: ' + (e.message || 'Unknown error'), true);
    }
}

function setupModalListeners() {
    if (cta_btn) {
        cta_btn.addEventListener('click', handlePurchaseClick);
        console.log('Purchase button click handler attached');
    } else {
        console.error('purchaseBtn not found!');
    }
    if (cancelBtn) cancelBtn.onclick = closeCustomerModal;
    if (document.getElementById('cancelPaymentMethodBtn')) document.getElementById('cancelPaymentMethodBtn').onclick = closePaymentMethodModal;
    if (document.getElementById('cancelUpiBtn')) document.getElementById('cancelUpiBtn').onclick = () => upiModal.style.display = 'none';
    if (document.getElementById('completeCashBtn')) document.getElementById('completeCashBtn').onclick = () => { cashModal.style.display = 'none'; window.location.href = '/'; };
    document.onclick = (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    };
    window.handleProceedToPayment = handleProceedToPayment;
    window.closeCustomerModal = closeCustomerModal;
    window.selectPaymentMethod = selectPaymentMethod;
    window.confirmUpiBtn = confirmUPI;
}

document.addEventListener('DOMContentLoaded', async () => {
    initializeDOMElements();
    await loadCurrentUser();
    populateSelectedSeats();
    refreshSeat();
    setupMovieSelectListener();
    setupModalListeners();
    setInterval(refreshSeat, 5000);
    console.log('Backend.js fully initialized with modals');
});
