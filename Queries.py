# -*- coding:utf-8 -*- 
from Utils import *


class Queries:
	def __init__(self):
		DistanceUtils.Build();
		NodeNameUtils.Build();
		WayNameUtils.Build();
		OtherUtils.Build();
	def query1(self, node_id=None,coord=None):  # type(coord)=list 
		tid = -1;
		if node_id==None and coord==None:
			return None;
		if node_id==None:  #by coord
			du = DistanceUtils();
			coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
			raw = du.queryNN(pointlist = np.array([coord_int]), k_nn=1);
			tid = raw[0][0][0];
		else:
			tid = node_id;
		dbh = DBHelper();
		result = dbh.executeAndFetchAll("select distinct id from current_way_nodes where node_id="+str(tid));
		isIntersection = len(result) > 1;
		way_list = [tp[0] for tp in result];
		return (way_list, isIntersection)

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
		coord_int = [int(item*DistanceUtils.coord_scale) for item in coord];
		poitype = OtherUtils.StdlizePOIType(poitype);
		Nid2Coord = OtherUtils.GetNid2Coord();
		dbh = DBHelper();
		raw = dbh.executeAndFetchAll("select distinct node_id from current_node_tags where k='poitype' and v='"+poitype+"'");
		candidates_nids = [tp[0] for tp in raw];
		result = []
		for nid in candidates_nids:
			if Nid2Coord.has_keys(nid) and DistanceUtils.spherical_distance(coord_int,Nid2Coord[nid]) <= radius:
				result.append((nid,[Nid2Coord[nid]]))
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



if __name__ == '__main__':
	myQuery = Queries();
	while 1:
		a = raw_input();
		print myQuery.query5(coord=eval(a))
	# while 1:
	# 	id = input();
	# 	print myQuery.query1(node_id=id);









				
