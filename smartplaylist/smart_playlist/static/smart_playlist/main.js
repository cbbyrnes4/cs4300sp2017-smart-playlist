$(function () {
  	$("#song").autocomplete({
	    source: '/find_song',
	    minLength: 3,
	    select: function (event, ui) {
	    	$("#artist").val(ui.item.id);
	    }
  	});

  	$("#artist").autocomplete({
	    source: '/find_artist',
	    minLength: 3
  	});

});

function showValue(id, newValue) {
    document.getElementById(id).innerHTML = String(newValue)
}

  