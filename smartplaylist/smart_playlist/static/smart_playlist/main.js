$(function () {
  	$("#song").autocomplete({
	    source: '/find_song',
	    minLength: 3,
	    select: function (event, ui) {
	    	if (!$("#artist").val()) {
	    		$("#artist").val(ui.item.id);
	    	}
	    }
  	});

});

  