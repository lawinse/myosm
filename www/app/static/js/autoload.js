var version = 1.0;
var data_object = null;
var result_string = "";

function get_current_position() {
	if (navigator.geolocation) {
	    navigator.geolocation.getCurrentPosition(
	        function(position) {
	            var coords = position.coords;
	            var latlng = new google.maps.LatLng(coords.latitude, coords.longitude);
	            var options = {zoom:12, center:latlng, mapTypeId:google.maps.MapTypeId.ROADMAP};
	            var wrapper = document.getElementById('map-wrapper');
	            var mp = new google.maps.Map(wrapper, options);
	            var marker = new google.maps.Marker({position:latlng, map:mp});
	            var info_window = new google.maps.InfoWindow({content:"<div style='margin-top:5px;'><strong>I'm here!!</strong><br> Latitude: " + 
	            	coords.latitude.toFixed(6) + 
	            	",&nbsp;<br> Longitude: " + coords.longitude.toFixed(6) + "</div>"});
	            info_window.open(mp, marker);
	        }, function(error) {
	            switch (error.code) {
	                case error.TIMEOUT:
	                    alert("[geolocation.error]\nTIMEOUT! Please try again!"); break;
	                case error.POSITION_UNAVAILABLE:
	                    alert("[geolocation.error]\nWe can\'t detect your location. Sorry!"); break;
	                case error.PERMISSION_DENIED:
	                    alert("[geolocation.error]\nPlease allow geolocation access for this device!"); break;
	                case error.UNKNOWN_ERROR:
	                    alert("[geolocation.error]\nUnknown error occured!"); break;
	            }
	        }, {enableHighAcuracy: true, timeout: 30000, maximumAge: 3000});
	    console.log("navigator.geolocation.getCurrentPosition finished...");
	} else {
	    alert("Your browser doesn\'t support Geolocation!");
	}
}

var available_poi = [
	"金融", "财经",
	"其他旅游景点", "旅游景点", "景点", "其他景点",
	"体育场馆", "体育场", "体育馆", "运动场", "运动场馆",
	"极限运动场所", "极限运动",
	"高等院校", "高校", "大学",
	"收费站",
	"酒店", "宾馆", "旅店",
	"游乐园", "游乐场", "游乐中心", "游乐",
	"写字楼",
	"加油加气站", "加油站", "加油",
	"公交车站", "公交站", "车站",
	"港口", 
	"飞机场", "机场",
	"海滨浴场",
	"政府机构", "政府", "政府机关",
	"风景区", "景区",
	"健身中心", "健身馆", "健身", "健身场所",
	"大型购物", "大型商场", "大商场",
	"桥", "桥梁",
	"公司", 
	"住宅区", 
	"农林园艺", "园艺",
	"厂矿", "矿",
	"停车场", "停车",
	"其他", 
	"文化传媒", "传媒",
	"地铁站", "轨道交通", "地铁",
	"休闲娱乐", "娱乐", "休闲",
	"其他教育", 
	"火车站", "动车站",
	"服务区", "服务中心",
	"长途汽车站", "长途汽车",
	"医疗", "医院", "诊所",
	"小型购物", 
	"美食", 
	"园区", 
	"宿舍", "寝室"];