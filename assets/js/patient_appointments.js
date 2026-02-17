$(document).ready(function() {
    $('#confirmationModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget), actionUrl = button.data('action-url'), modalBodyText = button.data('modal-body'), modal = $(this);
        modal.find('#confirmationModalBody').text(modalBodyText);
        modal.find('#confirmActionButton').attr('href', actionUrl);
    });
});