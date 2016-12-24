function query7() {
	var moff = ["car", "walk", "bike"];
	var mode = moff[$("#dropdown-selector").val()];
	var lat1 = $("#input-Q7-lat1").val();
	var lon1 = $("#input-Q7-lon1").val();
	var lat2 = $("#input-Q7-lat2").val();
	var lon2 = $("#input-Q7-lon2").val();
	$.get("/v1/query7", {
		mode: mode,
		lat1: lat1,
		lon1: lon1,
		lat2: lat2,
		lon2: lon2
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q7-result").html(data.main);
			data_object = data;
			$("#Q7-pic").attr("src", data.url);
			$("#Q7-pic").css("width", "100%");
			$("#Q7-pic").css("border-radius", "5px");
			$("#Q7-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q7-result").html(data.status);
		}
	},
	"json");
}

function query10() {
	var lat1 = $("#input-Q10-lat1").val();
	var lon1 = $("#input-Q10-lon1").val();
	var lat2 = $("#input-Q10-lat2").val();
	var lon2 = $("#input-Q10-lon2").val();
	var pty = $("#input-Q10-pty").val();
	$.get("/v1/query10", {
		lat1: lat1,
		lon1: lon1,
		lat2: lat2,
		lon2: lon2,
		poitype: pty
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q10-result").html(data.main);
			data_object = data;
			$("#Q10-pic").attr("src", data.url);
			$("#Q10-pic").css("width", "100%");
			$("#Q10-pic").css("border-radius", "5px");
			$("#Q10-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q10-result").html(data.status);
		}
	},
	"json");
}

