$(document).ready(function() {
    // Handle the modal display and data population when it's about to be shown
    $('#confirmationModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget); // Button that triggered the modal
        var actionUrl = button.data('action-url'); // Extract URL from data-action-url attribute
        var modalBodyText = button.data('modal-body'); // Extract text from data-modal-body attribute
        
        var modal = $(this);
        modal.find('#confirmationModalBody').text(modalBodyText);
        modal.find('#confirmActionButton').attr('href', actionUrl);
    });
});