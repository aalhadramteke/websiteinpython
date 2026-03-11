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

// Initialize DOM elements when document is ready
function initializeDOMElements() {
    all_seats = document.querySelectorAll('.row .seat');
    cta_btn = document.querySelector('button.purchase_btn');
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
    
    console.log('DOM elements initialized:', {
        all_seats: all_seats?.length,
        cta_btn: !!cta_btn,
        customerModal: !!customerModal,
        movieSelect: !!movieSelect
    });
}

// Fetch current user data on page load
async function loadCurrentUser() {
    try {
        const response = await fetch('/user-info/');
        const data = await response.json();
        if (data.authenticated) {
            currentUserData = data;
            // Pre-fill form if user is logged in
            const firstNameInput = document.getElementById('modalFirstName');
            const lastNameInput = document.getElementById('modalLastName');
            const emailInput = document.getElementById('modalEmail');
            const phoneInput = document.getElementById('modalPhone');
            
            if (firstNameInput) firstNameInput.value = data.first_name || '';
            if (lastNameInput) lastNameInput.value = data.last_name || '';
            if (emailInput) emailInput.value = data.email || '';
            if (phoneInput) phoneInput.value = data.phone || '';
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

async function contactAPI(url,body){
    const response=await fetch(url,{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify(body)
    })

    return response.json()
}

function refreshSeat(){
    // First try to get movie from localStorage (set by movie card click)
    let movie_title = localStorage.getItem('selectedMovieTitle');
    
    // If not in localStorage, try the dropdown
    if (!movie_title && movieSelect && movieSelect.options[movieSelect.selectedIndex]) {
        movie_title = movieSelect.options[movieSelect.selectedIndex].id;
    }
    
    selectedMovieTitle = movie_title;

    if (!movie_title) {
        all_seats.forEach(seat=>{
            seat.classList.remove("occupied")
        })
        return;
    }

    contactAPI("/occupied/",{movie_title}).then(data=>{
        const occupied_seat=data['occupied_seats']
        const movie_title_response=data["movie"]

        const seat_LocalStorage=localStorage.getItem('selectedSeats')?JSON.parse(localStorage.getItem('selectedSeats')):null

        all_seats.forEach(seat=>{
            seat.classList.remove("occupied")
        })

        const LS_movie = localStorage.getItem("selectedMovieTitle");

        if (LS_movie === movie_title_response || LS_movie === movie_title){
            if (occupied_seat !== null && occupied_seat.length > 0){
                all_seats.forEach((seat,index)=>{
                    if(occupied_seat.indexOf(index) > -1){
                        seat.classList.add('occupied')
                        seat.classList.remove('selected')
                    }
                })
            }

            if(seat_LocalStorage !== null && seat_LocalStorage.length > 0){
                const updated_seats = seat_LocalStorage.filter(seat => !occupied_seat.includes(seat));
                localStorage.setItem("selectedSeats", JSON.stringify(updated_seats));
            }
        }
        updateDisplayPrice()
    }).catch(e=>{
        console.log("Error refreshing seats:", e)
    })
}

// Update the price display based on selected seats
function updateDisplayPrice() {
    const selectedSeats = document.querySelectorAll('.row .seat.selected');
    const countDisplay = document.getElementById('count');
    const totalDisplay = document.getElementById('total');
    
    // Get the price from localStorage (set by movie card click or dropdown)
    // This ensures we always have the current movie price
    const ticketPrice = +localStorage.getItem('selectedMoviePrice') || selectedMoviePrice || 0;
    
    // Update the global ticketPrice to match
    window.ticketPrice = ticketPrice;
    
    if (countDisplay) countDisplay.innerText = selectedSeats.length;
    if (totalDisplay) totalDisplay.innerText = selectedSeats.length * ticketPrice;
    
    console.log('Price updated:', { seatCount: selectedSeats.length, ticketPrice: ticketPrice, total: selectedSeats.length * ticketPrice });
}

// Initialize seat selection in script.js style
function initializeSeatSelection() {
    const container = document.querySelector('.container');
    if (!container) return;

    // Re-populate selected seats from localStorage
    populateSelectedSeats();

    // Add click listener for seat selection
    container.addEventListener('click', (e) => {
        if (e.target.classList.contains('seat') && !e.target.classList.contains('occupied')) {
            e.target.classList.toggle('selected');
            
            // Update localStorage with selected seat indices
            updateSelectedSeatsInStorage();
            
            // Update the price display
            updateDisplayPrice();
        }
    });
    
    console.log('Seat selection initialized');
}

// Populate previously selected seats from localStorage
function populateSelectedSeats() {
    const selectedSeats = JSON.parse(localStorage.getItem('selectedSeats'));
    const allSeats = document.querySelectorAll('.row .seat');
    
    if (selectedSeats !== null && selectedSeats.length > 0) {
        allSeats.forEach((seat, index) => {
            if (selectedSeats.indexOf(index) > -1 && !seat.classList.contains('occupied')) {
                seat.classList.add('selected');
            }
        });
    }
    
    // Ensure price is displayed correctly
    updateDisplayPrice();
}

// Update selected seats in localStorage based on current DOM state
function updateSelectedSeatsInStorage() {
    const allSeats = document.querySelectorAll('.row .seat');
    const selectedSeats = document.querySelectorAll('.row .seat.selected');
    
    const seatsIndex = [...selectedSeats].map(seat => [...allSeats].indexOf(seat));
    localStorage.setItem('selectedSeats', JSON.stringify(seatsIndex));
}

// Update behavior when dropdown changes - will be setup after DOM ready
function setupMovieSelectListener() {
    if (!movieSelect) return;
    
    movieSelect.addEventListener('change', e => {
        selectedMoviePrice = +e.target.value;
        selectedMovieTitle = e.target.options[e.target.selectedIndex].id;
        localStorage.setItem('selectedMoviePrice', selectedMoviePrice);
        localStorage.setItem('selectedMovieTitle', selectedMovieTitle);
        ticketPrice = selectedMoviePrice;
        updateDisplayPrice();
        refreshSeat();
    });
}

// Load previously saved movie price (and update dropdown selection)
function setupWindowLoad() {
    const previousPrice = localStorage.getItem('selectedMoviePrice');
    const previousTitle = localStorage.getItem('selectedMovieTitle');
    if (previousPrice) {
        selectedMoviePrice = +previousPrice;
        ticketPrice = selectedMoviePrice;
        updateDisplayPrice();
    }
    if (previousTitle && movieSelect) {
        for (let i=0;i<movieSelect.options.length;i++){
            if (movieSelect.options[i].id === previousTitle){
                movieSelect.selectedIndex = i;
                break;
            }
        }
        selectedMovieTitle = previousTitle;
        refreshSeat();
    }
}

function showPaymentStatus(message, isError = false) {
    const statusDiv = document.getElementById('paymentStatus');
    statusDiv.textContent = message;
    statusDiv.className = 'payment-status';
    if (isError) {
        statusDiv.classList.add('error');
    }
    statusDiv.style.display = 'block';
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

// Payment method selection handlers
function setupPaymentOptionListeners() {
    const paymentOptions = document.querySelectorAll('.payment-option');
    paymentOptions.forEach(option => {
        // Remove existing listeners to avoid duplicates
        option.removeEventListener('click', handlePaymentOptionClick);
        option.addEventListener('click', handlePaymentOptionClick);
    });
}

async function handlePaymentOptionClick(e) {
    const option = e.currentTarget;
    selectedPaymentMethod = option.dataset.method;
    
    // Remove previous selection
    document.querySelectorAll('.payment-option').forEach(o => o.classList.remove('selected'));
    option.classList.add('selected');
    
    // Process payment based on selected method
    await processPayment();
}

// This function will be called inside DOMContentLoaded
function setupModalListeners() {
    // Cancel button for customer modal
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            if (customerModal) customerModal.style.display = 'none';
            selectedPaymentMethod = null;
        });
    }
    
    // Payment method cancel button
    const paymentMethodBtn = document.getElementById('cancelPaymentMethodBtn');
    if (paymentMethodBtn) {
        paymentMethodBtn.addEventListener('click', () => {
            if (paymentMethodModal) paymentMethodModal.style.display = 'none';
            selectedPaymentMethod = null;
        });
    }
    
    // Setup payment option listeners
    setupPaymentOptionListeners();
    
    // Proceed button for customer info
    if (proceedBtn) {
        proceedBtn.addEventListener('click', setupProceedButtonHandler);
    }
}

async function setupProceedButtonHandler() {
    const first_name = document.getElementById('modalFirstName').value.trim();
    const last_name = document.getElementById('modalLastName').value.trim();
    const email = document.getElementById('modalEmail').value.trim();
    const phone = document.getElementById('modalPhone').value.trim();
    
    if (!first_name || !last_name || !email || !phone) {
        showPaymentStatus('Please fill in all required fields', true);
        return;
    }
    
    if (!selectedMovieTitle) {
        showPaymentStatus('Please select a movie', true);
        return;
    }
    
    const seat_list=JSON.parse(localStorage.getItem("selectedSeats"))

    if(seat_list === null || seat_list.length === 0) {
        showPaymentStatus('Please select at least one seat', true);
        return;
    }
    
    // Store customer info
    customerInfo = {
        first_name,
        last_name,
        email,
        phone
    };
    
    // Show payment method selection
    if (customerModal) customerModal.style.display = 'none';
    if (paymentMethodModal) paymentMethodModal.style.display = 'block';
    selectedPaymentMethod = null;
}

// Process payment based on method selected
async function processPayment() {
    const first_name = customerInfo.first_name;
    const last_name = customerInfo.last_name;
    const email = customerInfo.email;
    const phone = customerInfo.phone;
    const movie_title = selectedMovieTitle;
    const seat_list=JSON.parse(localStorage.getItem("selectedSeats"))

    const data={
        movie_title,
        seat_list,
        first_name,
        last_name,
        email,
        phone,
        payment_method: selectedPaymentMethod
    };

    try {
        const res = await contactAPI("/payment/", data);
        
        if (selectedPaymentMethod === 'card') {
            // Card payment via Paystack
            if (res["payment_url"]){
                if (paymentMethodModal) paymentMethodModal.style.display = 'none';
                showPaymentStatus('Redirecting to payment...');
                setTimeout(() => {
                    window.location.href=res["payment_url"]
                }, 1000);
            }else if (res["test_mode"]){
                if (paymentMethodModal) paymentMethodModal.style.display = 'none';
                showPaymentStatus('Processing payment (test mode)...');
                setTimeout(() => {
                    window.location.href=res["confirm_url"]
                }, 1000);
            }else{
                showPaymentStatus('Error: ' + (res["error"] || 'Failed to process payment'), true)
                console.log('error', res)
            }
        } else if (selectedPaymentMethod === 'upi') {
            // UPI QR Code payment
            if (res.booking_reference && res.total_amount) {
                if (paymentMethodModal) paymentMethodModal.style.display = 'none';
                
                // Generate QR code
                const qrRes = await contactAPI("/generate-upi-qr/", {
                    booking_reference: res.booking_reference,
                    total_amount: res.total_amount,
                    phone: phone
                });
                
                const qrCodeImg = document.getElementById('qrCodeImage');
                const upiRef = document.getElementById('upiReference');
                const upiAmt = document.getElementById('upiAmount');
                
                if (qrRes.qr_code && qrCodeImg && upiRef && upiAmt) {
                    qrCodeImg.src = qrRes.qr_code;
                    upiRef.textContent = res.booking_reference;
                    upiAmt.textContent = '₹' + res.total_amount;
                    if (upiModal) upiModal.style.display = 'block';
                } else {
                    showPaymentStatus('Failed to generate QR code', true);
                }
            } else {
                showPaymentStatus('Error: ' + (res["error"] || 'Failed to process UPI payment'), true)
            }
        } else if (selectedPaymentMethod === 'cash') {
            // Cash payment at counter
            if (res.booking_reference && res.total_amount) {
                if (paymentMethodModal) paymentMethodModal.style.display = 'none';
                
                const cashRef = document.getElementById('cashReference');
                const cashAmt = document.getElementById('cashAmount');
                const cashSeats = document.getElementById('cashSeats');
                
                if (cashRef && cashAmt && cashSeats) {
                    cashRef.textContent = res.booking_reference;
                    cashAmt.textContent = '₹' + res.total_amount;
                    cashSeats.textContent = seat_list.length;
                }
                
                // Clear selected seats
                all_seats.forEach(seat => seat.classList.remove('selected'));
                localStorage.setItem('selectedSeats', JSON.stringify([]));
                localStorage.setItem('selectedMoviePrice', '');
                localStorage.setItem('selectedMovieTitle', '');
                
                if (cashModal) cashModal.style.display = 'block';
            } else {
                showPaymentStatus('Error: ' + (res["error"] || 'Failed to create booking'), true)
            }
        }
    } catch (e){
        showPaymentStatus('Error: ' + e.message, true)
        console.log('error', e)
    }
}

// ============================================
// ALL EVENT LISTENERS AND INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM elements
    initializeDOMElements();
    
    // Load current user
    loadCurrentUser();
    
    // Setup movie select listener
    setupMovieSelectListener();
    
    // Setup window load functionality
    setupWindowLoad();
    
    // Initialize seat selection (click handlers, etc.)
    initializeSeatSelection();
    
    // Initial seat refresh
    refreshSeat();
    
    // Setup all modal and other listeners
    setupModalListeners();
    
    // ===== PURCHASE BUTTON =====
    if (cta_btn) {
        cta_btn.addEventListener("click", e => {
            const seat_list=JSON.parse(localStorage.getItem("selectedSeats"))

            if(seat_list !== null && seat_list.length > 0){
                // Show modal for customer info
                if (customerModal) customerModal.style.display = 'block';
            }else{
                showPaymentStatus('Please select at least one seat', true)
            }
        });
    }
    
    // ===== UPI MODAL HANDLERS =====
    const cancelUpiBtn = document.getElementById('cancelUpiBtn');
    const confirmUpiBtn = document.getElementById('confirmUpiBtn');
    
    if (cancelUpiBtn) {
        cancelUpiBtn.addEventListener('click', () => {
            if (upiModal) upiModal.style.display = 'none';
        });
    }

    if (confirmUpiBtn) {
        confirmUpiBtn.addEventListener('click', () => {
            if (upiModal) upiModal.style.display = 'none';
            showPaymentStatus('Booking confirmed! You can proceed to the counter.');
            
            // Clear selected seats
            all_seats.forEach(seat => seat.classList.remove('selected'));
            localStorage.setItem('selectedSeats', JSON.stringify([]));
            localStorage.setItem('selectedMoviePrice', '');
            localStorage.setItem('selectedMovieTitle', '');
            
            setTimeout(() => {
                window.location.href = '/payment-history/';
            }, 2000);
        });
    }

    // ===== CASH MODAL HANDLERS =====
    const completeCashBtn = document.getElementById('completeCashBtn');
    if (completeCashBtn) {
        completeCashBtn.addEventListener('click', () => {
            if (cashModal) cashModal.style.display = 'none';
            window.location.href = '/';
        });
    }
    
    // ===== CLOSE MODAL ON OUTSIDE CLICK =====
    window.addEventListener('click', (event) => {
        if (event.target === customerModal) {
            customerModal.style.display = 'none';
        }
        if (event.target === paymentMethodModal) {
            paymentMethodModal.style.display = 'none';
            selectedPaymentMethod = null;
        }
        if (event.target === upiModal) {
            upiModal.style.display = 'none';
        }
        if (event.target === cashModal) {
            cashModal.style.display = 'none';
        }
    });
});