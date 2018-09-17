(function(Modules) {
  "use strict";

  let normalize = (string) => string.toLowerCase().replace(/ /g,'');

  let filter = ($searchBox, $targets) => () => {

    let query = normalize($searchBox.val());

    $targets.each(function() {

      let content = $(this).text();

      $(this).toggle(
        normalize(content).indexOf(normalize(query)) > -1
      );

    });

  };

  let toggleLists = ($searchBox) => () => {

    let searching = (normalize($searchBox.val()) != '');
    console.log(normalize($searchBox.val()), searching);

    $("#template-list").toggle(!searching);
    $("#template-list-flat").toggle(searching);

  };


  Modules.LiveSearchFolders = function() {

    this.start = function(component) {

      let $component = $(component);

      let $searchBox = $('input', $component);

      let filterFunc = filter(
        $searchBox,
        $($component.data('targets'))
      );

      let toggleFunc = toggleLists($searchBox);

      $searchBox
        .on('keyup input', filterFunc)
        .on('keyup input', toggleFunc);

      filterFunc();
      toggleFunc();

    };

  };

})(window.GOVUK.Modules);
