(function(Modules) {
  "use strict";

  Modules.Folders = function() {

    this.start = function(component) {

      $bar = $("<div class='template-manager'><div class='button-secondary'>Move…</div></div>");
      $(component).append($bar);
      $bar.hide();
      $(component).find('.multiple-choice').on('click', function() {
        console.log('click');
        $bar.toggle();
      });

    };

  };

  console.log('load', Modules);

})(window.GOVUK.Modules);
