console.log('found');

(function(Modules) {
  "use strict";

  Modules.UserType = function() {

    console.log('init');

    this.start = function(component) {

      const $radios = $('[type=radio]', $(component)),
            showHidePanels = function() {
              $radios.each(function() {
                $('#panel-' + $(this).attr('id'))
                  .toggleClass(
                    'js-hidden',
                    !$(this).is(":checked")
                  );
              });
            },
            clearSelectedItemsInPanels = function() {
              $radios.each(function() {
                $('#panel-' + $(this).attr('id'))
                  .find('[type=checkbox]')
                  .attr('checked', false);

              });
            };

      $radios.on('click', showHidePanels);
      // Don’t think this is very user-friendly
      // $radios.on('click', clearSelectedItemsInPanels);
      showHidePanels();

    };
  };

})(window.GOVUK.Modules);
