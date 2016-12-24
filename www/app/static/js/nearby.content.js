function query4() {
	var pty = $("#input-Q4-pty").val();
	var lat = $("#input-Q4-lat").val();
	var lon = $("#input-Q4-lon").val();
	var rd = $("#input-Q4-rd").val();
	$.get("/v1/query4", {
		poitype: pty,
		lat: lat,
		lon: lon,
		radius: rd
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q4-result").html(data.main);
			data_object = data;
			$("#Q4-pic").attr("src", data.url);
			$("#Q4-pic").css("width", "100%");
			$("#Q4-pic").css("border-radius", "5px");
			$("#Q4-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q4-result").html(data.status);
		}
	},
	"json");
}

function query11() {
	var pn = $("#input-Q11-pn").val();
	var lat = $("#input-Q11-lat").val();
	var lon = $("#input-Q11-lon").val();
	var mnum = $("#input-Q11-mn").val();
	$.get("/v1/query11", {
		poiname: pn,
		lat: lat,
		lon: lon,
		max_num: mnum
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q11-result").html(data.main);
			data_object = data;
			$("#Q11-pic").attr("src", data.url);
			$("#Q11-pic").css("width", "100%");
			$("#Q11-pic").css("border-radius", "5px");
			$("#Q11-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q11-result").html(data.status);
		}
	},
	"json");
}

function query9() {
	var pty = $("#input-Q9-pty").val();
	var rd = $("#input-Q9-rd").val();
	$.get("/v1/query9", {
		poitype: pty,
		radius: rd
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			var res = data.main;
			var rst = "<strong>Center Point Coordinate: </strong>("+res[0][0]/10000000+", "+res[0][1]/10000000+")<br>" +
						"<strong>Total Number: </strong>"+res[1]+"<br>";
			result_string = rst;
			$("#Q9-result").html(rst);
			data_object = data;

			// $("#Q9-pic").attr("src", data.url);
			var map_url = "/static/maps/query_most_poi_within_radius@452713510624766690.png";
			$("#Q9-pic").attr("src", map_url);
			$("#Q9-pic").css("width", "100%");
			$("#Q9-pic").css("border-radius", "5px");
			$("#Q9-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q9-result").html(data.status);
		}
	},
	"json");
}

function query8() {
	var lat = $("#input-Q8-lat").val();
	var lon = $("#input-Q8-lon").val();
	var pty1 = $("#input-Q8-pty1").val();
	var pty2 = $("#input-Q8-pty2").val();
	$.get("/v1/query8", {
		lat: lat,
		lon: lon,
		poitype1: pty1,
		poitype2: pty2
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q8-result").html(data.main);
			data_object = data;
			$("#Q8-pic").attr("src", data.url);
			$("#Q8-pic").css("width", "100%");
			$("#Q8-pic").css("border-radius", "5px");
			$("#Q8-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q8-result").html(data.status);
		}
	},
	"json");
}