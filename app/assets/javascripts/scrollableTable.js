(function(Modules) {
  "use strict";

  Modules.ScrollableTable = function() {

    this.start = function(component) {

      $('caption', component).on('click', () => {
          $(component).toggleClass('expanded').focus();
          $("html").toggleClass('noscroll');
      });

    };
  };

})(window.GOVUK.Modules);
