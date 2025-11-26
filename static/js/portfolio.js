function refreshPage() {
    // Refresh the page every 10 seconds to get updated prices
    setTimeout(function() {
        window.location.reload();
    }, 10000);
}

// Start the refresh cycle when the page loads
document.addEventListener('DOMContentLoaded', function() {
    refreshPage();
});