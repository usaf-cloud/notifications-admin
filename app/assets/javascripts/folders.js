(function(Modules) {
  "use strict";

  function hideActions() {
    $('.template-manager-move, .template-manager-new-group').css('max-height', '0');
    $('.template-manager-actions').css({
      'top': '0',
      'margin-bottom': '0',
    });
    $('.template-manager input').prop('checked', false);
  }

  Modules.Folders = function() {

    this.start = function(component) {

      $bar = $(".template-manager");
      $(component).append($bar);

      $bar.addClass('off-bottom');

      $(component).find('.multiple-choice:has(:checkbox)').on('click', function() {

        if (!$(component).has(':checked').length) {
          $bar.addClass('off-bottom');
          hideActions();
        } else {
          $bar.removeClass('off-bottom');
        }

        $bar.toggleClass(
          'off-bottom',
          !$(component).has(':checked').length
        );

      }).trigger('click');

      $(".template-manager-actions .button-secondary").on('click', function() {

        $($(this).data('target-selector')).css('max-height', '100vh');

        $('.template-manager-actions').css({
          'top': '-100vh',
          'margin-bottom': '-30px',
        });

      });

      $('.template-manager-hide-action').on('click', hideActions);

    };

  };

})(window.GOVUK.Modules);
