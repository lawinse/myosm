# -*- coding:utf-8 -*- 
from Utils import *
from MapConverter import MapConverter



class Queries:
	def __init__(self):
		if not LAZY_START:
			DistanceUtils.Build();
			NodeNameUtils.Build();
			WayNameUtils.Build();
			Routing.Build();
			OtherUtils.Build();

	#########################################################################################################
	#* Desc: Given a node and find all the ways containing it and whether it is a intersection
	#* Input: [int]node_id (useless) or [list(float,2)]coord or [string]node_name (the name of target_node)
	#* Return: node_id, all the way_id, whether it is a intersection
	#* Return format: tuple ( [int]node_id, [list]list of way_id, [bool]whether it is ai intersection
	#########################################################################################################
	def query1(self, node_id=None,coord=None,node_name=None):  # type(coord)=list 
		tid = -1;
		if node_id==None and coord==None and node_name == None:
			return None;
		if coord != None:  #by coord
			du = DistanceUtils();
			coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
			raw = du.queryNN(pointlist = np.array([coord_int]), k_nn=1);
			tid = raw[0][0][0];
		elif node_name != None:
			nu = NodeNameUtils();
			tid_list = nu.getMostSim(node_name)[0][3];	# try to get random one along way if there are mutiple choices
			dbh = DBHelper();
			for tid in tid_list:
				result = dbh.executeAndFetchAll("select distinct id from current_way_nodes where node_id=%s",params=(tid,));
				isIntersection = len(result) > 1;
				way_list = [tp[0] for tp in result];
				if len(way_list)>0: return (tid, way_list, isIntersection)
		else:
			tid = node_id;
		dbh = DBHelper();
		result = dbh.executeAndFetchAll("select distinct id from current_way_nodes where node_id=%s",params=(tid,));
		isIntersection = len(result) > 1;
		way_list = [tp[0] for tp in result];

		mc = MapConverter();
		mc.add_root_point_byid(tid);
		if len(way_list) > 0: mc.set_target_lines_byid(way_list);
		mc.convert();

		return (tid, way_list, isIntersection)

	#########################################################################################################
	#* Desc: Given a way and find all the nodes along it
	#* Input: [int]way_id (useless) or [string]way_name (the name of target_way)
	#* Return: a list consisting of all the way segments
	#* Return format: list[seg1,seg2,seg3...] 
	#*   seg := list [node1,node2,node3...] node := tuple(node_id, coord_int)
	#########################################################################################################
	def query2(self,way_id=None, way_name=None, no_graph=False):       # assume given by way_id
		if way_id != None:
			wid_list = [way_id];
		elif way_name != None:
			wnu = WayNameUtils();
			wid_list = wnu.getMostSim(way_name)[0][3];
		else:
			return None;
		dbh = DBHelper();
		ret = [];
		mc = MapConverter();
		for wid in wid_list:
			result = dbh.executeAndFetchAll("select node_id,sequence_id from current_way_nodes where id=%s order by sequence_id",params=(wid,));
			node_list = [tp[0] for tp in result];
			Nid2Coord = OtherUtils.GetNid2Coord();
			node_list = [(nid, Nid2Coord[nid]) for nid in node_list];
			mc.add_target_point_byid(nid);
			mc.add_target_line([(nd[1][0]/DistanceUtils.coord_scale,nd[1][1]/DistanceUtils.coord_scale) for nd in node_list]);
			ret.append(node_list);
		if not no_graph: 
			mc.convert();

		return ret;

	#########################################################################################################
	#* Desc: Similar usage as query2, perhaps deprecated
	#########################################################################################################
	def query3(self,way_name):
		wnu = WayNameUtils();
		raw = wnu.getMostSim(way_name);
		all_results = [];
		dbh = DBHelper();

		Nid2Coord = OtherUtils.GetNid2Coord();

		# for every way_name result should be like
		# [way_name, numOfSegs,...[way_id, ...[(node_id,[node_lat,node_lon])]]];
		# since a way_name may consist of numbers of segments and every segments consists of numbers of nodes;
		for item in raw:
			wn = item[0];
			prior = item[1];
			wid_li = item[2];
			wn_li = [wn, len(wid_li)];
			for way_id in wid_li:
				raw = dbh.executeAndFetchAll("select node_id,sequence_id from current_way_nodes where id=%s order by sequence_id",params=(way_id,));
				# attention!!
				node_li = [(tp[0],Nid2Coord.get(tp[0],None))for tp in raw]
				theSeg = [way_id,node_li];
				wn_li.append(theSeg);
			all_results.append(wn_li);
		return all_results;

	#########################################################################################################
	#* Desc: Find all the poi in the area given center coord and radius
	#* Input: [string]poitype, [list(float,2)] coord, [float] radius
	#* Return: a list of target poi nodes
	#* Return format: list[node1,node2,node3...] 
	#*   node := tuple(node_id, [float]distance, coord_int)
	#########################################################################################################
	def query4(self,poitype,coord,radius):
		# coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		poitype = OtherUtils.StdlizePOIType(poitype);
		Nid2Coord = OtherUtils.GetNid2Coord();
		dbh = DBHelper();
		mc = MapConverter();
		mc.add_root_point(tuple(coord));
		mc.set_target_range(coord,DistanceUtils.degree_distance(radius));

		raw = dbh.executeAndFetchAll("select id, latitude, longitude, st_distance(point(longitude/1e7, latitude/1e7),point(%s,%s))*111195 as dis "+\
			"from current_nodes where (id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v=%s)) having dis<%s"+ \
			" order by dis", params=(coord[1],coord[0],poitype,radius,));
		result = [(tp[0], tp[3], [tp[1],tp[2]])for tp in raw]
		mc.set_target_points([tuple([item/DistanceUtils.coord_scale for item in tp[2]]) for tp in result])
		mc.downsampling_target_points(num=5000);
		mc.convert();
		# candidates_nids = [tp[0] for tp in raw];
		# result = []
		# for nid in candidates_nids:
		# 	if Nid2Coord.has_keys(nid) and DistanceUtils.spherical_distance(coord_int,Nid2Coord[nid]) <= radius:
		# 		result.append((nid,[Nid2Coord[nid]]))
		return result;

	#########################################################################################################
	#* Desc: Find the nearest way of given coord
	#* Input: [list(float,2)] coord
	#* Return: the way with least distance and its inforamtion
	#* Return format: tuple(way_id, [float] min_dis, query2(way_id))
	#########################################################################################################
	def query5(self, coord, k1=8, k2=5):
		# k1 means the number of neigh we filter out; 
		# k2 indicates the number of nodes along the way to calc distance
		coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		# print coord_int
		du = DistanceUtils();
		raw = du.queryNN(pointlist = np.array([coord_int]), k_nn=k1);
		dbh = DBHelper();
		mc = MapConverter();
		mc.add_target_point(tuple(coord));
		wayid_middleSeq = {}
		Nid2Coord = OtherUtils.GetNid2Coord();

		for i in range(k1):
			neigh_nid = raw[0][i][0];
			tmp = dbh.executeAndFetchAll("select id,sequence_id from current_way_nodes where node_id=%s",params=(neigh_nid,));
			for tp in tmp:
				if not wayid_middleSeq.has_key(tp[0]):
					wayid_middleSeq[tp[0]] = tp[1];

		minDis = sys.maxint
		minDis_wid = -1;
		for way_id in wayid_middleSeq.keys():
			mid_seq = wayid_middleSeq[way_id];
			lm = max(mid_seq-k2,1);
			rm = lm+2*k2
			tmp = dbh.executeAndFetchAll("select node_id, sequence_id from current_way_nodes"+ \
					" where id=%s and sequence_id>=%s and sequence_id<=%s order by sequence_id",\
					params=(way_id,lm,rm,))
			way_nids = [tp[0] for tp in tmp]
			way_line_coord = [Nid2Coord[item] for item in way_nids];
			tmp_dis = du.node2Line(coord_int,way_line_coord);
			if (tmp_dis < minDis):
				minDis = tmp_dis
				minDis_wid = way_id;
		mc.add_target_line_byid(minDis_wid);
		li = wayid_middleSeq.keys()[:];
		li.remove(minDis_wid)
		mc.set_background_lines_byid(li);
		mc.convert();
		return (minDis_wid,minDis,self.query2(way_id=minDis_wid,no_graph=True));

	#########################################################################################################
	#* Desc: Generate new osm with given range of lat and lon
	#* Input: [string] filename, [float]minLat, maxLat, minLon, maxLon
	#* Return: filename of osm file
	#* Return format: [string] filename
	#########################################################################################################
	def query6(self, filename, minLat, maxLat, minLon, maxLon):
		from OsmGenerator import OsmGenerator
		gen = OsmGenerator(filename,minLat, maxLat, minLon, maxLon);
		gen.process();
		gen.commit();
		return filename

	#########################################################################################################
	#* Desc: Find a routing path from A to B with certain routeType
	#* Input: [string in ("car","walk","bike")] routeType, [list(float,2)] start_coord,end_coord
	#* Return: The routing path
	#* Return format: tuple([string] status, totalDistance, path)
	#*  path:=[node1,node2...] node:=(node_id,coord_int)
	#########################################################################################################
	def query_routing(self,routeType,start_coord,end_coord):
		from Routing import Routing
		ro = Routing(routeType);
		ret = ro.findRoute(start_coord,end_coord)
		mc = MapConverter();
		if ret[0] == 'success':
			mc.add_root_point(tuple(start_coord));
			mc.add_root_point(tuple(end_coord));
			mc.add_target_line([(nd[1][0]/DistanceUtils.coord_scale,nd[1][1]/DistanceUtils.coord_scale) for nd in ret[2]])

		mc.convert();
		return ret;

	#########################################################################################################
	#* Desc: Find poi pairs and ttl_distance from given coord, order by ttl_distance
	#* Input: [list(float,2)]coord, [string]poi1,poi2, 
	#*   [bool]order_senstive (whether considering order), [int]candidate number
	#* Return: poi pair order by distance
	#* Return format: list[(poi1,poi2,[float]ttl_line_distance)]
	#*  poi:=(node_id,name,coord_int)
	#########################################################################################################
	def query_pair_poitype(self,coord,poi1,poi2,order_sensitive=False,num=5):
		Nid2Coord = OtherUtils.GetNid2Coord();
		poi1 = OtherUtils.StdlizePOIType(poi1);
		poi2 = OtherUtils.StdlizePOIType(poi2);
		mc = MapConverter();
		mc.add_root_point(tuple(coord));
		dbh = DBHelper();
		import ctypes;
		solve = OtherUtils.GetPOIPairSolver();
		print ">>>>> Searching ..."

		nodelist1 = dbh.executeAndFetchAll("select id,latitude/1e7,longitude/1e7 from current_nodes where id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v=%s) order by st_distance(point(longitude/1e7,latitude/1e7),point(%s,%s))",\
			params = (poi1,coord[1],coord[0]))
		nodelist2 = dbh.executeAndFetchAll("select id,latitude/1e7,longitude/1e7 from current_nodes where id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v=%s) order by st_distance(point(longitude/1e7,latitude/1e7),point(%s,%s))",\
			params = (poi2,coord[1],coord[0]))


		print ">>>>> Ordering ..."
		n1 = len(nodelist1);
		atype1_int = ctypes.c_int*n1;
		atype1_double = ctypes.c_double*n1;
		id1 = [tp[0] for tp in nodelist1];
		x1 = [tp[1] for tp in nodelist1];
		y1 = [tp[2] for tp in nodelist1];

		n2 = len(nodelist2);
		atype2_int = ctypes.c_int*n2;
		atype2_double = ctypes.c_double*n2;
		id2 = [tp[0] for tp in nodelist2];
		x2 = [tp[1] for tp in nodelist2];
		y2 = [tp[2] for tp in nodelist2];

		k = num;
		atypeRet_int = ctypes.c_int*k;
		atypeRet_double = ctypes.c_double*k;
		id1ret = atypeRet_int(*[]);
		x1ret = atypeRet_double(*[]);
		y1ret = atypeRet_double(*[]);
		id2ret = atypeRet_int(*[]);
		x2ret = atypeRet_double(*[]);
		y2ret = atypeRet_double(*[]);
		disret = atypeRet_double(*[]);


		solve(n1,atype1_int(*id1),atype1_double(*x1),atype1_double(*y1),\
				n2,atype2_int(*id2),atype2_double(*x2),atype2_double(*y2),\
				coord[0],coord[1],num,order_sensitive,\
				id1ret,x1ret,y1ret,\
				id2ret,x2ret,y2ret,\
				disret);

		ret = [((id1ret[i],NodeNameUtils.GetNameById(id1ret[i]),[int(x1ret[i]*DistanceUtils.coord_scale),int(y1ret[i]*DistanceUtils.coord_scale)]),\
			(id2ret[i],NodeNameUtils.GetNameById(id2ret[i]),[int(x2ret[i]*DistanceUtils.coord_scale),int(y2ret[i]*DistanceUtils.coord_scale)]),disret[i])for i in range(k)]



		for tp in ret:
			mc.add_target_pair_points_byid(tp[0][0],tp[1][0]);
		mc.convert();
		return ret

	#########################################################################################################
	#* Desc: Find the area with given radius which contains most poi (roughly)
	#* Input: [[string] poitype, [float] radius, [bool] whether needs precisely calc
	#* Return: the area
	#* Return format: (coord_int, num of poi)
	#########################################################################################################	
	def query_most_poi_within_radius(self, poitype,radius,need_precise = False):
		import ctypes
		poitype = OtherUtils.StdlizePOIType(poitype)
		mc = MapConverter();

		solve = OtherUtils.GetCirclePointSolver();

		dbh = DBHelper();
		raw = dbh.executeAndFetchAll("select id, latitude, longitude from current_nodes where id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v=%s)",params=(poitype,));
		x = [tp[1]/DistanceUtils.coord_scale for tp in raw];
		y = [tp[2]/DistanceUtils.coord_scale for tp in raw];
		num_numbers = len(x)
		array_type = ctypes.c_double * num_numbers
		print ">>>>> Searching ..."
		res = solve(radius,num_numbers,array_type(*x),array_type(*y),need_precise)
		count = int(res[0])
		mc.add_root_point((res[1],res[2]));
		mc.set_target_range((res[1],res[2]),DistanceUtils.degree_distance(radius));
		mc.convert();
		return ([int(res[1]*DistanceUtils.coord_scale),int(res[2]*DistanceUtils.coord_scale)],count)

	#########################################################################################################
	#* Desc: Find a poi lying in middle of two point with some tolerance
	#* Input: [list(float,2)]coord1，coord2, [stirng] poitype, [float] sum_tolerate,diff_tolerate,
	#*   [bool] is order sensitive, [int] candidate num
	#* Return: the candidates ordered by ttl_distance
	#* Return format: list(tuple(node_id,coord_int,[float]distance1,[float]distance2))
	#########################################################################################################
	def query_middle_poi(self,coord1,coord2,poitype,sum_tolerate=0.2,diff_tolerate=0.1,order_sensitive = False,num=2):
		poitype = OtherUtils.StdlizePOIType(poitype);
		line_dis_max = DistanceUtils.spherical_distance(coord1,coord2)*(1+sum_tolerate);
		mc = MapConverter();
		mc.add_root_point(tuple(coord1));
		mc.add_root_point(tuple(coord2));
		dbh = DBHelper();

		print ">>>>> Searching ..."
		raw = dbh.executeAndFetchAll("select a.id, a.latitude, a.longitude, "+\
			"st_distance(point(a.longitude/1e7,a.latitude/1e7),point(%s,%s))*111195 as dis1, "+\
			"st_distance(point(a.longitude/1e7,a.latitude/1e7),point(%s,%s))*111195 as dis2 "+\
			"from (select id, latitude, longitude from current_nodes where id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v=%s)) as a "+\
			"having dis1+dis2<%s and abs(dis1-dis2)<least(dis1,dis2)*%s"+\
			(" and dis1 > dis2 " if order_sensitive else " ") +\
			"order by st_distance(point(a.longitude/1e7,a.latitude/1e7),point(%s,%s)) limit 0,%s",\
			params=(coord1[1],coord1[0],coord2[1],coord2[0],poitype,line_dis_max,diff_tolerate,\
				0.5*(coord2[1]+coord1[1]),0.5*(coord2[0]+coord1[0]),num,));
		ret = [(tp[0],[tp[1],tp[2]],tp[3],tp[4]) for tp in raw];
		mc.set_target_points_byid([tp[0] for tp in ret])
		mc.convert();
		return ret;

	#########################################################################################################
	#* Desc: Find a poi by NAME (e.g. 电信营业厅) around a given location
	#* Input: [list(float,2)]coord, [stirng] poi_name, [int] candidate num
	#* Return: the candidates ordered by distance
	#* Return format: list(tuple(node_id, coord_int, node_name, distance))
	#########################################################################################################
	def query_poi_node_name_nearby(self,coord,poi_name,num=10):
		nu = NodeNameUtils();
		mc = MapConverter();
		mc.add_root_point(tuple(coord));
		print ">>>>> Searching ..."
		node_list = nu.findIsA(poi_name)
		coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		node_list = [(tp[0],tp[1],tp[2],DistanceUtils.spherical_distance(coord_int,tp[1])) for tp in node_list]
		ret = sorted(node_list,key=lambda node:node[3])[:num];
		mc.set_target_points_byid([tp[0] for tp in ret]);
		mc.convert();
		return ret

	#########################################################################################################
	#* Desc: Commit/rollback a changeset by XML
	#* Input: [list(string)] XML filename list
	#* Return: the changeset id list, -1 denotes a rollback
	#* Return format: list(int)
	#########################################################################################################
	def query_changesets(self, fiilenames=None):
		from ChangeSetUtils import ChangeSetTask
		task = ChangeSetTask();
		for f in filenames:
			task.push(f);
		ret = task.execute();
		return ret;

	#########################################################################################################
	#* Desc: Simply create a graph (just nodes) for given bounder for main page
	#* Input: [list(float,2)]coord, [float]minLat, maxLat, minLon, maxLon
	#* Return: None
	#########################################################################################################
	def query_region_graph(self,coord,minLat,maxLat,minLon,maxLon):
		mc = MapConverter();
		mc.add_root_point(tuple(coord));
		mc.set_target_bounder((minLat, minLon, maxLat, maxLon));
		mc.convert();
		return;




if __name__ == '__main__':
	myQuery = Queries();
	# print myQuery.query1(node_name="人民广场".decode('utf8'))
	# print myQuery.query5(coord=[31,121])
	# print myQuery.query_routing("car",[31.1981978,121.4152321],[31.2075866,121.6090868]);
	# print myQuery.query_poi_node_name_nearby([31.0256896255,121.4364611407],"电信营业厅".decode('utf8'))
	# print myQuery.query_middle_poi([31.257391,121.483045],[31.11652,121.391634],"大型购物".decode('utf8'))
	# print myQuery.query_most_poi_within_radius("美食".decode('utf8'),2000)
	# print myQuery.query2(way_name="杨高中路".decode('utf8'));
	# print myQuery.query_most_poi_within_radius("地铁站".decode('utf8'),1000)
	# print myQuery.query_middle_poi([31.1981978,121.4152321],[31.2075866,121.6090868],"住宅区".decode('utf8'))
	print myQuery.query_pair_poitype([31.025403,121.431028],"住宅区".decode('utf8'),"美食".decode('utf8'),order_sensitive=False)
	# print myQuery.query4("加油站".decode('utf8'),[31.1977664,121.4147976],10000)
	# while 1:
	# 	a = raw_input();
	# 	print myQuery.query5(coord=eval(a))
	# while 1:
	# 	id = input();
	# 	print myQuery.query1(node_id=id);









				

