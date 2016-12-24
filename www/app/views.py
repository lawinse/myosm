# -*- coding:utf-8 -*- 
from flask import render_template, flash, redirect, session, url_for, request, json, jsonify, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app import app, db, lm, oid, agent
from .forms import LoginForm
from .models import User

@app.route('/')
@app.route('/index')
def index():
	# user = g.user
	user = { 'nickname' : 'MyOSM User' } # fake user
	posts = [ # fake array
		{
			'author' : { 'nickname' : 'Steve' },
			'body' : 'Beautiful day in Shanghai!'
		},
		{
			'author' : { 'nickname' : 'Elisa' },
			'body' : 'The MyOSM system is awesome!'
		}
	]
	return render_template("index.html",
		title = "MyOSM",
		user = user,
		posts = posts)

@app.route('/basic')
def basic_view():
	return render_template("basic.html", title = "Basic Functions")

@app.route('/nearby')
def nearby_view():
	return render_template("nearby.html", title = "Nearby POIs")

@app.route('/plan')
def plan_view():
	return render_template("plan.html", title = "Plan Your Time")

@app.route('/advanced')
def advanced_view():
	return render_template("advanced.html", title = "Advanced Functions")



@app.route('/v1/query1', methods=['GET', 'POST'])
def query1():
	if request.method == 'GET':
		mode = request.args.get('mode')
		if mode == '0':
			name = request.args.get('name')
			print "[Query1] name:", name
			try:
				res = agent.query1(node_name=name)
				url = agent.getMapConverter().get_url()
				assert url != "", "Unavailable Url.."
				# print "[Query1] final res, url:", res, url
				return jsonify(status="OK", main=res, url=url[5:])
			except Exception as e:
				raise e
				return jsonify(status="INTERNAL ERROR")
		else:
			lat = request.args.get('lat')
			lon = request.args.get('lon')
			coord = [float(lat), float(lon)]
			print "[Query1] coord:", coord
			try:
				res = agent.query1(coord=coord)
				url = agent.getMapConverter().get_url()
				assert url != "", "Unavailable Url.."
				# print "[Query1] final res, url:", res, url
				return jsonify(status="OK", main=res, url=url[5:])
			except Exception as e:
				raise e
				return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query2', methods=['GET', 'POST'])
def query2():
	if request.method == 'GET':
		name = request.args.get('name')
		print "[Query2] name:", name
		try:
			res = agent.query2(way_name=name)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			print "[Query2] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			# raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query4', methods=['GET', 'POST'])
def query4():
	if request.method == 'GET':
		poitype = request.args.get('poitype')
		lat = request.args.get('lat')
		lon = request.args.get('lon')
		coord = [float(lat), float(lon)]
		radius = float(request.args.get('radius'))*1000
		print "[Query4] poitype, coord, radius:", poitype, coord, radius
		try:
			res = agent.query4(poitype, coord, radius)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query4] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query5', methods=['GET', 'POST'])
def query5():
	if request.method == 'GET':
		lat = request.args.get('lat')
		lon = request.args.get('lon')
		coord = [float(lat), float(lon)]
		print "[Query5] coord:", coord
		try:
			res = agent.query5(coord=coord)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query5] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query6', methods=['GET', 'POST'])
def query6():
	if request.method == 'GET':
		filename = request.args.get("filename")
		minlat = float(request.args.get("minlat"))
		maxlat = float(request.args.get("maxlat"))
		minlon = float(request.args.get("minlon"))
		maxlon = float(request.args.get("maxlon"))
		print "[Query6] minlat, maxlat, minlon, maxlon:", minlat, maxlat, minlon, maxlon
		try:
			res = agent.query6("./app/static/userfile/export/"+filename, minlat, maxlat, minlon, maxlon)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query6] final res, url:", res, url
			return jsonify(status="OK", main=res[5:], url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query7', methods=['GET', 'POST'])
def query7():
	if request.method == 'GET':
		lat1 = request.args.get('lat1')
		lon1 = request.args.get('lon1')
		coord1 = [float(lat1), float(lon1)]
		lat2 = request.args.get('lat2')
		lon2 = request.args.get('lon2')
		coord2 = [float(lat2), float(lon2)]
		rtype = request.args.get('mode')
		print "[Query7] coord1, coord2, rtype:", coord1, coord2, rtype
		try:
			res = agent.query_routing(rtype, coord1, coord2)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query7] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query8', methods=['GET', 'POST'])
def query8():
	if request.method == 'GET':
		lat = request.args.get('lat')
		lon = request.args.get('lon')
		coord = [float(lat), float(lon)]
		poitype1 = request.args.get('poitype1')
		poitype2 = request.args.get('poitype2')
		print "[Query8] coord, poitype1, poitype2:", coord, poitype1, poitype2
		try:
			res = agent.query_pair_poitype(coord, poitype1, poitype2)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query8] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query9', methods=['GET', 'POST'])
def query9():
	if request.method == 'GET':
		poitype = request.args.get('poitype')
		radius = float(request.args.get('radius'))*1000
		print "[Query9] poitype, radius:", poitype, radius
		try:
			res = agent.query_most_poi_within_radius(poitype, radius)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query9] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query10', methods=['GET', 'POST'])
def query10():
	if request.method == 'GET':
		lat1 = request.args.get('lat1')
		lon1 = request.args.get('lon1')
		coord1 = [float(lat1), float(lon1)]
		lat2 = request.args.get('lat2')
		lon2 = request.args.get('lon2')
		coord2 = [float(lat2), float(lon2)]
		poitype = request.args.get('poitype')
		print "[Query10] coord1, coord2, poitype:", coord1, coord2, poitype
		try:
			res = agent.query_middle_poi(coord1, coord2, poitype)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query10] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query11', methods=['GET', 'POST'])
def query11():
	if request.method == 'GET':
		poiname = request.args.get('poiname')
		lat = request.args.get('lat')
		lon = request.args.get('lon')
		coord = [float(lat), float(lon)]
		max_num = int(request.args.get('max_num'))
		print "[Query11] poiname, coord, max_num:", poiname, coord, max_num
		try:
			res = agent.query_poi_node_name_nearby(coord, poiname, num=max_num)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query11] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


@app.route('/v1/query12', methods=['GET', 'POST'])
def query12():
	if request.method == 'POST':
		f = request.files['input-Q12-file']
		full_path = './app/static/uploads/'+secure_filename(f.filename)
		f.save(full_path)
		filenames = [full_path]
		print "[Query12] filenames:", filenames
		try:
			res = agent.query_changesets(filenames=filenames)
			url = agent.getMapConverter().get_url()
			assert url != "", "Unavailable Url.."
			# print "[Query12] final res, url:", res, url
			return jsonify(status="OK", main=res, url=url[5:])
		except Exception as e:
			raise e
			return jsonify(status="INTERNAL ERROR")
	else:
		return jsonify(status="BAD METHOD")


