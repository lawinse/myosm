function query6() {
	var filename = Date.parse(new Date())+'.osm';
	var minlat = $("#input-Q6-minlat").val();
	var maxlat = $("#input-Q6-maxlat").val();
	var minlon = $("#input-Q6-minlon").val();
	var maxlon = $("#input-Q6-maxlon").val();
	$.get("/v1/query6", {
		filename: filename,
		minlat: minlat,
		maxlat: maxlat,
		minlon: minlon,
		maxlon: maxlon
	},
	function(data, status) {
		if (status == "success" && data.status == "OK") {
			var link = data.main;
			$("#Q6-result").html("<a href="+link+" download='export"+Date.parse(new Date())+".osm'>Click to Download...</a>");
			data_object = data;
			$("#Q6-pic").attr("src", data.url);
			$("#Q6-pic").css("width", "100%");
			$("#Q6-pic").css("border-radius", "5px");
			$("#Q6-pic").css("box-shadow", "0px 0px 25px #eee");
		} else {
			$("#Q6-result").html(data.status);
		}
	},
	"json");
}

function file_upload() {
	$("#input-Q12-file").fileinput({'showUpload':false, 'previewFileType':'any', 'uploadUrl':'/v1/query12'});
	$('#input-Q12-file').on('fileuploaded', function(event, data, previewId, index) {
    	var form = data.form, files = data.files, extra = data.extra,
        response = data.response, reader = data.reader;
    	console.log('File uploaded triggered');
    	$("#Q12-result").html(response.main);
		data_object = response;
		$("#Q12-pic").attr("src", data.url);
		$("#Q12-pic").css("width", "100%");
		$("#Q12-pic").css("border-radius", "5px");
		$("#Q12-pic").css("box-shadow", "0px 0px 25px #eee");
	});
}