// script.js - Simplified to work with backend.js
// The main seat selection logic is now in backend.js

// Make sure the ticketPrice is available globally
let ticketPrice = +localStorage.getItem('selectedMoviePrice') || 0;

// Function to get ticket price (used by other parts of the app)
function getTicketPrice() {
    return +localStorage.getItem('selectedMoviePrice') || ticketPrice;
}

// Export to global scope
window.getTicketPrice = getTicketPrice;

