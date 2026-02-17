document.addEventListener('DOMContentLoaded', () => {
    // Function to get the CSRF token from cookies
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
    const csrftoken = getCookie('csrftoken');

    const setupAsyncValidation = ({ inputId, feedbackId, urlDataAttribute, fieldName, validationFn, takenMsg, availableMsg }) => {
        const inputElement = document.getElementById(inputId);

        if (inputElement) {
            const feedbackElement = document.getElementById(feedbackId);
            const checkUrl = inputElement.dataset[urlDataAttribute];
            let debounceTimeout;

            inputElement.addEventListener('keyup', () => {
                const value = inputElement.value;
                clearTimeout(debounceTimeout);

                if (validationFn(value)) {
                    debounceTimeout = setTimeout(() => {
                        fetch(checkUrl, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrftoken
                            },
                            body: JSON.stringify({ [fieldName]: value })
                        })
                        .then(response => response.json())
                        .then(data => {
                            feedbackElement.textContent = data.is_taken ? takenMsg : availableMsg;
                            feedbackElement.style.color = data.is_taken ? 'red' : 'green';
                        })
                        .catch(error => console.error(`Error checking ${fieldName}:`, error));
                    }, 500);
                } else {
                    feedbackElement.textContent = '';
                }
            });
        }
    };

    // Setup username validation
    setupAsyncValidation({
        inputId: 'username',
        feedbackId: 'username-feedback',
        urlDataAttribute: 'checkUsernameUrl',
        fieldName: 'username',
        validationFn: (value) => value.length >= 3,
        takenMsg: 'This username is already taken.',
        availableMsg: 'This username is available!'
    });

    // Setup email validation
    setupAsyncValidation({
        inputId: 'email',
        feedbackId: 'email-feedback',
        urlDataAttribute: 'checkEmailUrl',
        fieldName: 'email',
        validationFn: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        takenMsg: 'This email is already in use.',
        availableMsg: 'This email is available.'
    });
});