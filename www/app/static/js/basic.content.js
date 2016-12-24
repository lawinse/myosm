function query1() {
	var mode = $("#dropdown-selector").val();
	// mode:0  -  by name
	// mode:1  -  by coordinate
	if (mode == 0) {
		var nn = $("#input-Q1-nn").val();
		$.get("/v1/query1", {
			mode: mode,
			name: nn
		},
		function(data, status) {
			if (status == "success" && data.status == "OK") {
				var res = data.main;
				var rst = "<strong>Node Name: </strong>"+res[1]+"<br>" +
						 "<strong>Contained Ways: </strong>"+res[2][0][1]+"<br>" + 
						 "<strong>If intersection? </strong>"+(res[3]?"Yes":"No")+"<br>";
				result_string = rst;
				$("#Q1-result").html(rst);
				data_object = data;
				$("#Q1-pic").attr("src", data.url);
				$("#Q1-pic").css("width", "100%");
				$("#Q1-pic").css("border-radius", "5px");
				$("#Q1-pic").css("box-shadow", "0px 0px 25px #eee");
			} else {
				$("#Q1-result").html(data.status);
			}
		}, 
		"json");
	} else {
		var lat = $("#input-Q1-lat").val();
		var lon = $("#input-Q1-lon").val();
		$.get("/v1/query1", {
			mode: mode,
			lat: lat,
			lon: lon
		},
		function(data, status) {
			if (status == "success" && data.status == "OK") {
				$("#Q1-result").html(data.main);
				data_object = data.main;
				$("#Q1-pic").attr("src", data.url);
				$("#Q1-pic").css("width", "100%");
				$("#Q1-pic").css("border-radius", "5px");
				$("#Q1-pic").css("box-shadow", "0px 0px 25px #eee");
			} else {
				$("#Q1-result").html(data.status);
			}
		}, 
		"json");
	}
}

function query2() {
	var nn = $("#input-Q2-nn").val();
	$.get("/v1/query2", {
		name: nn
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q2-result").html(data.main);
			data_object = data.main;
			$("#Q2-pic").attr("src", data.url);
			$("#Q2-pic").css("width", "100%");
			$("#Q2-pic").css("border-radius", "5px");
			$("#Q2-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q2-result").html(data.status);
		}
	},
	"json");
}

function query5() {
	var lat = $("#input-Q5-lat").val();
	var lon = $("#input-Q5-lon").val();
	$.get("/v1/query5", {
		lat: lat,
		lon: lon
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			$("#Q5-result").html(data.main);
			data_object = data.main;
			$("#Q5-pic").attr("src", data.url);
			$("#Q5-pic").css("width", "100%");
			$("#Q5-pic").css("border-radius", "5px");
			$("#Q5-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q5-result").html(data.status);
		}
	},
	"json");
}