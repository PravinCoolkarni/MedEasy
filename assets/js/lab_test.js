$(document).ready(function() {
    function initializeSelect2(selector, placeholder) {
        $(selector).select2({
            theme: "bootstrap-5",
            placeholder: placeholder,
            minimumInputLength: 1, // Only trigger search after 1 character is typed
            ajax: {
                url: $(selector).data('ajax-url'),
                dataType: 'json',
                delay: 250, // Debounce API calls by 250ms
                data: function (params) {
                    // `params.term` is the search term from Select2
                    return {
                        term: params.term || ''
                    };
                },
                processResults: function (data) {
                    return { results: data.results };
                },
                cache: true
            }
        });
    }

    initializeSelect2('#location', 'Select Your Location');
    initializeSelect2('#type_test', 'Choose Your Lab Test');
});