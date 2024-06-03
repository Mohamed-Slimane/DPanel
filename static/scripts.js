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
jQuery(document).ready(function() {
    jQuery('[data-bs-toggle="tooltip"]').tooltip();

    jQuery('.database-action-btn').click(function(){
        if(!jQuery(this).hasClass('import')){
            jQuery('tr .blur-group').slideUp()
            jQuery('tr .import-from').slideDown()
            jQuery(this).addClass('import')
        }else{
            jQuery('tr .blur-group').slideDown()
            jQuery('tr .import-from').slideUp()
            jQuery(this).removeClass('import')
        }
    });
});