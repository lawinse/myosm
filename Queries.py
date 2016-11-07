# -*- coding:utf-8 -*- 
from Utils import *
LAZY_START = True


class Queries:
	def __init__(self):
		if not LAZY_START:
			DistanceUtils.Build();
			NodeNameUtils.Build();
			WayNameUtils.Build();
			OtherUtils.Build();
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
			tid = nu.getMostSim(node_name)[0][3];
		else:
			tid = node_id;
		dbh = DBHelper();
		result = dbh.executeAndFetchAll("select distinct id from current_way_nodes where node_id="+str(tid));
		isIntersection = len(result) > 1;
		way_list = [tp[0] for tp in result];
		return (tid, way_list, isIntersection)

	def query2(self,way_id=None):       # assume given by way_id
		if way_id == None:
			return None;
		dbh = DBHelper();
		result = dbh.executeAndFetchAll("select node_id,sequence_id from current_way_nodes where id="+str(way_id)+" order by sequence_id");
		node_list = [tp[0] for tp in result];
		Nid2Coord = OtherUtils.GetNid2Coord();
		node_list = [(nid, Nid2Coord[nid]) for nid in node_list];
		return node_list;

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
				raw = dbh.executeAndFetchAll("select node_id,sequence_id from current_way_nodes where id="+str(way_id)+" order by sequence_id");
				# attention!!
				node_li = [(tp[0],Nid2Coord.get(tp[0],None))for tp in raw]
				theSeg = [way_id,node_li];
				wn_li.append(theSeg);
			all_results.append(wn_li);
		return all_results;

	def query4(self,poitype,coord,radius):
		# coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		poitype = OtherUtils.StdlizePOIType(poitype);
		Nid2Coord = OtherUtils.GetNid2Coord();
		dbh = DBHelper();

		raw = dbh.executeAndFetchAll("select id, latitude, longitude, st_distance(point(longitude/1e7, latitude/1e7),point("+str(coord[1])+","+str(coord[0])+"))*111195 as dis "+\
			"from current_nodes where (id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v='"+poitype+"')) having dis<"+str(radius)+ \
			" order by dis");
		result = [(tp[0], tp[3], [tp[1],tp[2]])for tp in raw]
		# candidates_nids = [tp[0] for tp in raw];
		# result = []
		# for nid in candidates_nids:
		# 	if Nid2Coord.has_keys(nid) and DistanceUtils.spherical_distance(coord_int,Nid2Coord[nid]) <= radius:
		# 		result.append((nid,[Nid2Coord[nid]]))
		return result;

	def query5(self, coord, k1=8, k2=5):
		# k1 means the number of neigh we filter out; 
		# k2 indicates the number of nodes along the way to calc distance
		coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		# print coord_int
		du = DistanceUtils();
		raw = du.queryNN(pointlist = np.array([coord_int]), k_nn=k1);
		dbh = DBHelper();
		wayid_middleSeq = {}
		Nid2Coord = OtherUtils.GetNid2Coord();

		for i in range(k1):
			neigh_nid = raw[0][i][0];
			tmp = dbh.executeAndFetchAll("select id,sequence_id from current_way_nodes where node_id="+str(neigh_nid));
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
					" where id="+str(way_id)+" and sequence_id>="+str(lm)+" and sequence_id<="+str(rm)+" order by sequence_id")
			dbh.PrintLog(1);
			way_nids = [tp[0] for tp in tmp]
			way_line_coord = [Nid2Coord[item] for item in way_nids];
			tmp_dis = du.node2Line(coord_int,way_line_coord);
			if (tmp_dis < minDis):
				minDis = tmp_dis
				minDis_wid = way_id;
		return (minDis_wid,minDis,self.query2(way_id=minDis_wid));

	def query6(self, filename, minLat, maxLat, minLon, maxLon):
		from OsmGenerator import OsmGenerator
		gen = OsmGenerator(filename,minLat, maxLat, minLon, maxLon);
		gen.process();
		gen.commit();
		return filename

	def query_routing(self,routeType,start_coord,end_coord):
		from Routing import Routing
		ro = Routing(routeType);
		return ro.findRoute(start_coord,end_coord)

	def query_pair_poitype(self,coord,poi1,poi2,order_sensitive=False,num=5):
		du = DistanceUtils();
		Nid2Coord = OtherUtils.GetNid2Coord();
		poi1 = OtherUtils.StdlizePOIType(poi1);
		poi2 = OtherUtils.StdlizePOIType(poi2);
		dbh = DBHelper();
		print ">>>>> Searching and Ordering ..."
		# TODO: remains to be refined
		raw = dbh.executeAndFetchAll(\
			"select *, st_distance(point(v1.longitude/1e7,v1.latitude/1e7),point(v2.longitude/1e7,v2.longitude/1e7))+least(st_distance(point(v1.longitude/1e7,v1.latitude/1e7),point("+str(coord[1])+","+str(coord[0])+")),"+\
			" st_distance(point(v2.longitude/1e7,v2.latitude/1e7),point("+str(coord[1])+","+str(coord[0])+"))) as dis from "
			"(select p1.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi1+"') as p1 left join current_nodes on p1.node_id=current_nodes.id) as v1, "+\
			"(select p2.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi2+"') as p2 left join current_nodes on p2.node_id=current_nodes.id) as v2 "+\
			"order by dis "+\
			"limit 0,"+str(num) if order_sensitive == False else \
			"select *,st_distance(point(v1.longitude/1e7,v1.latitude/1e7),point(v2.longitude/1e7,v2.longitude/1e7))+st_distance(point(v1.longitude/1e7,v1.latitude/1e7),point("+str(coord[1])+","+str(coord[0])+"))*111195 as dis from "
			"(select p1.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi1+"') as p1 left join current_nodes on p1.node_id=current_nodes.id) as v1, "+\
			"(select p2.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi2+"') as p2 left join current_nodes on p2.node_id=current_nodes.id) as v2 "+\
			"order by dis "+\
			"limit 0,"+str(num)) 
		data = [((tp[0],[tp[1],tp[2]]), (tp[3],[tp[4],tp[5]]), tp[6])for tp in raw]
		return data
	def query_most_poi_within_radius(self, poitype,radius):
		import ctypes
		poitype = OtherUtils.StdlizePOIType(poitype)

		solve = OtherUtils.GetCirclePointSolver();

		dbh = DBHelper();
		raw = dbh.executeAndFetchAll("select id, latitude, longitude from current_nodes where id in (select distinct node_id from current_node_tags where k='poitype' and v='"+poitype+"') order by latitude,longitude");
		x = [tp[1]/DistanceUtils.coord_scale for tp in raw];
		y = [tp[2]/DistanceUtils.coord_scale for tp in raw];
		num_numbers = len(x)
		array_type = ctypes.c_double * num_numbers
		print ">>>>> Searching ..."
		res = solve(radius,num_numbers,array_type(*x),array_type(*y))
		count = int(res[0])
		return ([res[1]*DistanceUtils.coord_scale,res[2]*DistanceUtils.coord_scale],count)

	def query_middle_poi(self,coord1,coord2,poitype,sum_tolerate=0.2,diff_tolerate=0.1,order_sensitive = False,num=2):
		poitype = OtherUtils.StdlizePOIType(poitype);
		line_dis_max = DistanceUtils.spherical_distance(coord1,coord2)*(1+sum_tolerate);
		# print line_dis_max
		dbh = DBHelper();
		coord1_str = "%f,%f" %(coord1[1],coord1[0])
		coord2_str = "%f,%f" %(coord2[1],coord2[0])
		coordmid_str = "%f,%f" %(0.5*(coord2[1]+coord1[1]),0.5*(coord2[0]+coord1[0]))

		print ">>>>> Searching ..."
		raw = dbh.executeAndFetchAll("select a.id, a.latitude, a.longitude, "+\
			"st_distance(point(a.longitude/1e7,a.latitude/1e7),point("+coord1_str+"))*111195 as dis1, "+\
			"st_distance(point(a.longitude/1e7,a.latitude/1e7),point("+coord2_str+"))*111195 as dis2 "+\
			"from (select id, latitude, longitude from current_nodes where id in "+\
			"(select distinct node_id from current_node_tags where k='poitype' and v='"+poitype+"')) as a "+\
			"having dis1+dis2<"+str(line_dis_max)+" and abs(dis1-dis2)<least(dis1,dis2)*"+str(diff_tolerate)+\
			(" and dis1 > dis2 " if order_sensitive else " ") +\
			"order by st_distance(point(a.longitude/1e7,a.latitude/1e7),point("+coordmid_str+")) limit 0,"+str(num));

		return [(tp[0],[tp[1],tp[2]],tp[3],tp[4]) for tp in raw];

	def query_poi_node_name_nearby(self,coord,poi_name,num=10):
		nu = NodeNameUtils();
		print ">>>>> Searching ..."
		node_list = nu.findIsA(poi_name)
		coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		node_list = [(tp[0],tp[1],tp[2],DistanceUtils.spherical_distance(coord_int,tp[1])) for tp in node_list]
		return sorted(node_list,key=lambda node:node[3])[:num]




if __name__ == '__main__':
	myQuery = Queries();
	# print myQuery.query_poi_node_name_nearby([31.0256896255,121.4364611407],"东北".decode('utf8'))
	# print myQuery.query_middle_poi([31.257391,121.483045],[31.11652,121.391634],"地铁站".decode('utf8'))
	print myQuery.query_most_poi_within_radius("美食".decode('utf8'),2000)
	# print myQuery.query_most_poi_within_radius("金融".decode('utf8'),1000)
	# print myQuery.query_middle_poi([31.1981978,121.4152321],[31.2075866,121.6090868],"住宅区".decode('utf8'))
	# print myQuery.query_pair_poitype([31.1977664,121.4147976],"酒店".decode('utf8'),"加油站".decode('utf8'),order_sensitive=False)
	# print myQuery.query4("加油站".decode('utf8'),[31.1977664,121.4147976],10000)
	# while 1:
	# 	a = raw_input();
	# 	print myQuery.query5(coord=eval(a))
	# while 1:
	# 	id = input();
	# 	print myQuery.query1(node_id=id);









				

