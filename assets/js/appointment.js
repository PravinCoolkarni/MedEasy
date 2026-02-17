$(document).ready(function() {
    const setupSelect2Ajax = (elementId, placeholder, minInputLength, delay) => {
        const element = $(`#${elementId}`);
        if (element.length) {
            element.select2({
                theme: "bootstrap-5",
                placeholder: placeholder,
                allowClear: true,
                minimumInputLength: minInputLength,
                ajax: {
                    url: element.data('ajax-url'),
                    dataType: 'json',
                    delay: delay,
                    data: function (params) {
                        return {
                            term: params.term, // search term
                        };
                    },
                    processResults: function (data) {
                        // Transforms the API response into the format Select2 expects
                        return {
                            results: data.results
                        };
                    },
                }
            });
        }
    };

    setupSelect2Ajax(
        'disease',
        'Type to search for a disease or symptom...',
        1,
        500
    );
    setupSelect2Ajax(
        'location',
        'Choose or search for a location...',
        1,
        250
    );

    const populateUserDetails = () => {
        const form = $('#appointment-form');
        const userName = form.data('userName');

        // Check if the data attributes exist (i.e., user is logged in)
        if (typeof userName !== 'undefined') {
            // Trim the name to remove any leading/trailing whitespace
            $('#patient_name').val(userName.trim());
            $('#age').val(form.data('userAge'));
            $('#mobile').val(form.data('userMobile'));
        }
    };

    const clearUserDetails = () => {
        $('#patient_name').val('');
        $('#age').val('');
        $('#mobile').val('');
    };

    // Handle radio button changes for booking for self or other
    $('input[name="booking_for"]').on('change', function() {
        if ($(this).val() === 'self') {
            populateUserDetails();
        } else {
            clearUserDetails();
            $('#patient_name').focus();
        }
    });

    // Initial population if "Yourself" is checked by default and user is logged in
    if ($('#booking_for_self').is(':checked')) {
        populateUserDetails();
    }
});