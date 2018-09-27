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

  let toggleHiddenCheckboxes = ($component, forceVisible) => event => {

    if (event) {
      event.preventDefault();
    }

    $('.group-select-hide').toggle(!!forceVisible);
    $('.group-select-change').toggle(!forceVisible);

    $component.find('.multiple-choice').each(function() {

      $(this).toggle(forceVisible || !!$(this).has(':checked').length);

    });

  };

  Modules.Folders = function() {

    this.start = function(component) {

      $bar = $(".template-manager");
      $(component).append($bar);

      $bar.addClass('off-bottom');

      $(component).find('.multiple-choice:has(:checkbox)').on('click', function() {

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

      $('.template-manager-clear')
        .on('click', function() {
          $(component).find('input').prop('checked', false);
          $bar.addClass('off-bottom');
        });

    };

  };

  Modules.GroupSelect = function() {

    this.start = function(component) {

      let $component = $(component);

      $component.on('click', '.group-select-change', toggleHiddenCheckboxes($component, true));

      $component.on('click', '.group-select-hide', toggleHiddenCheckboxes($component));

      toggleHiddenCheckboxes($component, false)();

    };
  };

})(window.GOVUK.Modules);
