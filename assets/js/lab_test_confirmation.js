document.addEventListener('DOMContentLoaded', function() {
    // Fire the confetti animation on page load
    confetti({
        particleCount: 150,
        spread: 90,
        origin: { y: 0.6 }
    });
});