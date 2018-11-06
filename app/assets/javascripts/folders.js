(function(Modules) {
  "use strict";

  function hideActions() {
    $('.template-manager-move, .template-manager-new-group, .template-manager-new-folder, .template-manager-new-template').css('max-height', '0');
    $('.template-manager-actions').css({
      'top': '0',
      'margin-bottom': '0',
    });
    $('.template-manager input').prop('checked', false);
  }

  let toggleHiddenCheckboxes = ($component, forceVisible, allowDefault) => event => {

    if (event && !allowDefault) {
      event.preventDefault();
    }

    $('.group-select-hide').toggle(!!forceVisible);
    $('.group-select-change').toggle(!forceVisible);
    $('.group-select').toggleClass('closed', !forceVisible);

    $component.find('.multiple-choice').each(function() {

      $(this).toggle(forceVisible || !!$(this).has(':checked').length);

    });

    $component.focus();

  };

  let toggleAllChecked = $component => function(event) {

    if ($(this).find('input').attr('id') == 't-all' || $component.find('.multiple-choice').has(':checked').length === 0) {
      $component.find('.multiple-choice input').prop('checked', false);
      $component.find('.multiple-choice input').eq(0).prop('checked', true)
      $component.find('.group-select-subfolder .multiple-choice').addClass('selection-inferred');
    } else {
      if ($component.find('.multiple-choice').has(':checked').length > 1) {
        $component.find('.multiple-choice input').eq(0).prop('checked', false)
      }
      $component.find('.group-select-subfolder .multiple-choice').removeClass('selection-inferred');
    }

  }

  Modules.Folders = function() {

    this.start = function(component) {

      $bar = $(".template-manager");
      $(component).append($bar);

      let determineActions = function() {

        let selectedCount = $(component).find(':checked').length;

        if (selectedCount) {

          $('.template-manager-actions-specific').show();
          $('.template-manager-actions-general').hide();

          $('.template-manager-selected-count', component).html(
            selectedCount + ' selected&emsp;' + '<div class="template-manager-clear">Clear</div>'
          )

        } else {

          $('.template-manager-actions-specific').hide();
          $('.template-manager-actions-general').show();

          if ($(component).find('[type=checkbox]').length) {
            $('.template-manager-selected-count', component).html(
              'Nothing selected'
            )
          } else {
            $('.template-manager-selected-count', component).html(
              ''
            )
          }

        }

      };

      $(component).find('.multiple-choice:has(:checkbox)').on('click', determineActions);

      determineActions();

      $(".template-manager-actions-specific .button-secondary, .template-manager-actions-general .button-secondary").on('click', function() {

        $($(this).data('target-selector')).css('max-height', '100vh');

        $('.template-manager-actions').css({
          'top': '-100vh',
          'margin-bottom': '-30px',
        });

      });

      $('.template-manager-hide-action').on('click', hideActions);

      $(component)
        .on(
          'click',
          '.template-manager-clear',
          () => {
            $(component).find('input').prop('checked', false);
            $(component).find('.multiple-choice:has(:checkbox)').trigger('click');
          }
        );

    };

  };

  Modules.GroupSelect = function() {

    this.start = function(component) {

      let $component = $(component);

      $component.on('click', '.group-select-change', toggleHiddenCheckboxes($component, true));

      $component.on('click', '.group-select-hide', toggleHiddenCheckboxes($component));

      $(component).find('.multiple-choice:has(:checkbox)').on('click', toggleAllChecked($component));

      toggleHiddenCheckboxes($component, false)();

      toggleAllChecked($component).bind($('#t-all').parent()[0])();

      $('#t-all').parent('.multiple-choice').on('click', toggleHiddenCheckboxes($component, true, true));

    };
  };

})(window.GOVUK.Modules);
