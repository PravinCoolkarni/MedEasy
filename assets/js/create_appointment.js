$(document).ready(function() {
    // Set the minimum date for the date picker to today to prevent past bookings
    var today = new Date().toISOString().split('T')[0];
    $('#appointment-date').attr('min', today);

    // Reload the page with the selected date in the query string to update available slots
    $('#appointment-date').on('change', function() {
        const selectedDate = $(this).val();
        if (selectedDate) {
            const currentUrl = window.location.pathname;
            window.location.href = currentUrl + '?date=' + selectedDate;
        }
    });
});