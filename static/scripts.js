const Toast = Swal.mixin({
      toast: true,
      position: 'top',
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
      }
});
function dPanelPopup(url) {
    window.open(
        url,
        '_blank',
        'width=1000,height=800,scrollbars=yes,resizable=yes'
    );
}

jQuery(document).ready(function() {
    jQuery('[data-bs-toggle="tooltip"]').tooltip();
});