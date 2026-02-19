(() => {
    // Do not run session timeout logic on public-facing pages like login or register
    if (window.location.pathname.includes('/login') || window.location.pathname.includes('/new-account')) {
        return;
    }

    // --- Configuration ---
    const IDLE_TIMEOUT_MINUTES = 15; // Total idle time in minutes before logout
    const WARNING_SECONDS = 60;      // Seconds to show warning before logout
    const LOGOUT_URL = '/accounts/logout/';   // The URL to redirect to for logging out

    // Convert times to milliseconds for setTimeout
    const IDLE_TIMEOUT_MS = IDLE_TIMEOUT_MINUTES * 60 * 1000;
    const WARNING_MS = WARNING_SECONDS * 1000;

    let idleTimer;
    let warningTimer;
    let countdownTimer;
    let sessionTimeoutModal;
    let countdownSpan;
    let isWarningShown = false; // Flag to prevent modal from showing repeatedly

    function showWarningModal() {
        if (isWarningShown) return; // Don't show modal if it's already up

        const modalEl = document.getElementById('sessionTimeoutModal');
        if (!modalEl) return; // Exit if modal isn't on the page

        if (!sessionTimeoutModal) {
            sessionTimeoutModal = new bootstrap.Modal(modalEl);
        }
        sessionTimeoutModal.show();
        isWarningShown = true;

        let countdown = WARNING_SECONDS;
        if (!countdownSpan) {
            countdownSpan = document.getElementById('sessionTimeoutCountdown');
        }
        countdownSpan.textContent = countdown;

        // Start the visual countdown
        countdownTimer = setInterval(() => {
            countdown--;
            if (countdown >= 0) {
                countdownSpan.textContent = countdown;
            } else {
                clearInterval(countdownTimer);
            }
        }, 1000);
    }

    function resetTimers() {
        // Clear all existing timers
        clearTimeout(idleTimer);
        clearTimeout(warningTimer);
        clearInterval(countdownTimer);
        isWarningShown = false; // Reset warning flag on activity

        // Hide modal if it's currently showing
        if (sessionTimeoutModal && document.getElementById('sessionTimeoutModal')?.classList.contains('show')) {
            sessionTimeoutModal.hide();
        }

        // Set a new timer to show the warning modal before the session expires
        warningTimer = setTimeout(showWarningModal, IDLE_TIMEOUT_MS - WARNING_MS);

        // Set a new timer to automatically log out when the session expires
        idleTimer = setTimeout(logout, IDLE_TIMEOUT_MS);
    }

    function logout() {
        // Clear all timers and redirect to the logout page to invalidate the session
        clearTimeout(idleTimer);
        clearTimeout(warningTimer);
        clearInterval(countdownTimer);
        // Use replace to prevent the back button from going to the logged-in page
        window.location.replace(LOGOUT_URL);
    }

    // --- Event Listeners ---
    document.addEventListener('DOMContentLoaded', () => {
        let isThrottled = false;
        const throttleDelay = 500; // Only reset timers at most once every 500ms

        const throttledReset = () => {
            if (isThrottled) return;
            resetTimers();
            isThrottled = true;
            setTimeout(() => { isThrottled = false; }, throttleDelay);
        };

        // Listen for user activity to reset the timers
        const activityEvents = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
        activityEvents.forEach(event => document.addEventListener(event, throttledReset, true));

        document.getElementById('stayLoggedInBtn')?.addEventListener('click', resetTimers);
        document.getElementById('logoutBtn')?.addEventListener('click', logout);
        
        resetTimers(); // Start the timers when the page loads
    });
})();
