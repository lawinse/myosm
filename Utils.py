# -*- coding:utf-8 -*- 
import pickle
import numpy as np
from sklearn.externals import joblib
from scipy import spatial
from DBHelper import *
from BKTree_EditDistance import BKTree
import sys
import math
import re
from BM_25 import *;
sys.setrecursionlimit(10000)
eps = 1e-7
coord_scale_default = 1e7

if not os.path.exists("./data"):
	os.mkdir("./data")

class DistanceUtils:
	kd_tuple = None;
	coord_scale = coord_scale_default;

	def __init__(self):
		if DistanceUtils.kd_tuple == None:
			DistanceUtils.Build();

	def queryNN(self,pointlist, k_nn=1): # query for nearest neighbors
		# print DistanceUtils.kd_tuple[1].data;
		(dis,idx) = DistanceUtils.kd_tuple[1].query(pointlist,k=k_nn);
		if k_nn==1:
			dis = dis.reshape(-1,1);
			idx = idx.reshape(-1,1);
		mapping = DistanceUtils.kd_tuple[0];
		node_data = DistanceUtils.kd_tuple[1].data;
		result = [[] for i in range(pointlist.shape[0])];
		for i in range(len(result)):
			for k in range(k_nn):
				retid = mapping[idx[i][k]];
				result[i].append((retid, node_data[idx[i][k]][0], node_data[idx[i][k]][1], dis[i][k]))
		return result

	@classmethod
	def Build(cls):
		print ">>>>> Initalize DistanceUtils ..."
		dbh = DBHelper();
		all_nodes = dbh.executeAndFetchAll("select id,latitude,longitude from current_nodes where visible = 1")
		# build idx->node_id map
		idx_map = {};
		for i in xrange(len(all_nodes)):
			idx_map[i] = all_nodes[i][0];
		# build kdtree
		x = [item[1] for item in all_nodes];
		y = [item[2] for item in all_nodes];
		tree = spatial.KDTree(zip(x,y));
		DistanceUtils.kd_tuple = (idx_map,tree);
		print ">>>>> Done Initalization"

	@classmethod
	def spherical_distance(cls, f, t):
		def lw(a, b, c):
		    a = max(a,b)
		    a = min(a,c)
		    return a
		def ew(a, b, c):
		    while a > c:
		        a -= c - b
		    while a < b:
		        a += c - b
		    return a
		def oi(a):
		    return math.pi * a / 180
		def Td(a, b, c, d):
		    return 6370996.81 * math.acos(math.sin(c) * math.sin(d) + math.cos(c) * math.cos(d) * math.cos(b - a))
		def getD(a, b):
		    if not a or not b:
		        return 0;
		    a[1] = ew(a[1], -180, 180);
		    a[0] = lw(a[0], -74, 74);
		    b[1] = ew(b[1], -180, 180);
		    b[0] = lw(b[0], -74, 74);
		    return Td(oi(a[1]), oi(b[1]), oi(a[0]), oi(b[0]))
		return getD([f[0]/DistanceUtils.coord_scale,f[1]/DistanceUtils.coord_scale],[t[0]/DistanceUtils.coord_scale,t[1]/DistanceUtils.coord_scale])\
			 if abs(f[0]) > DistanceUtils.coord_scale else getD([f[0],f[1]],[t[0],t[1]])

	def getHeight(self,top,left,right):
		l1 = DistanceUtils.spherical_distance(top,left);
		l2 = DistanceUtils.spherical_distance(top,right);
		bottom = DistanceUtils.spherical_distance(left,right);
		p = 0.5*(l1+l2+bottom);
		return math.sqrt(max(p*(p-l1)*(p-l2)*(p-bottom),0))/bottom

	def node2Line(self, node_coord, line_coords): #line_coords must be sequatially
		def isAcute(vtr1,vtr2):
			return vtr1[0]*vtr2[0]+vtr1[1]*vtr2[1] >= -eps;
		def isMiddle(s_node, t_node1, t_node2):
			v1 = (s_node[0]-t_node1[0],s_node[1]-t_node1[1]);
			v2 = (t_node2[0]-t_node1[0],t_node2[1]-t_node1[1]);
			if isAcute(v1,v2):
				v1 = (s_node[0]-t_node2[0],s_node[1]-t_node2[1]);
				v2 = (t_node1[0]-t_node2[0],t_node1[1]-t_node2[1]);
				return isAcute(v1,v2);
			else:
				return False;
		for i in range(len(line_coords)-1):
			if (isMiddle(node_coord,line_coords[i],line_coords[i+1])):
				return self.getHeight(node_coord,line_coords[i],line_coords[i+1]);
		return min(DistanceUtils.spherical_distance(node_coord,line_coords[0]), \
				DistanceUtils.spherical_distance(node_coord, line_coords[-1]));



class NodeNameUtils:  # align to utf8
	Name2id = {};
	BKT = None;

	def __init__(self):
		if len(NodeNameUtils.Name2id) == 0 or NodeNameUtils.BKT == None:
			NodeNameUtils.Build();

	@classmethod
	def cleanName(cls, name):    # remove brackets and whitespaces
		name = "".join(re.split("[()（） ]",name));
		return name

	@classmethod
	def Build(cls):
		print ">>>>> Initalize NodeNameUtils ..."

		if (os.path.exists("./data/Name2id.dat")):
			print ">>>>> Loading ..."
			NodeNameUtils.Name2id = joblib.load("./data/Name2id.dat")
		else:
			print ">>>>> Generating ..."
			dbh = DBHelper();
			data = dbh.executeAndFetchAll("select node_id,v from current_node_tags where k='name'");
			for pair in data:
				cname = NodeNameUtils.cleanName(pair[1]);
				if NodeNameUtils.Name2id.has_key(cname):
					NodeNameUtils.Name2id[cname].append(pair[0])
				else:
					NodeNameUtils.Name2id[cname] = [pair[0]];
			joblib.dump(NodeNameUtils.Name2id,"./data/Name2id.dat",compress=3)
		
		if (os.path.exists("./data/BKT.dat")):
			print ">>>>> Load BKTree ..."
			NodeNameUtils.BKT = joblib.load("./data/BKT.dat")
		else:
			print ">>>>> Build BKTree ..."
			NodeNameUtils.BKT = BKTree(words=NodeNameUtils.Name2id.keys())
			joblib.dump(NodeNameUtils.BKT,"./data/BKT.dat",compress=3)
		print ">>>>> Done Initalization"


	def findSim(self,s1):   # return none indicates nothing ever matches
		s1 = NodeNameUtils.cleanName(s1)
		if (NodeNameUtils.Name2id.has_key(s1)):
			return [(s1,0,NodeNameUtils.Name2id[s1])];
		else:
			data = NodeNameUtils.BKT.query(s1,3);
			if len(data) > 0:
				return [(data[i][1],data[i][0],NodeNameUtils.Name2id[data[i][1]]) for i in range(min(5,len(data)))]
			else: 
				data = NodeNameUtils.BKT.query(s1,5);
				if len(data) > 0:
					return [(data[i][1],data[i][0],NodeNameUtils.Name2id[data[i][1]]) for i in range(min(5,len(data)))]
		return None
	def getMostSim(self,s1,num=1):
		ret = self.findSim(s1);
		if ret == None: return None;
		nodeBm = BM_25(typ='Node');
		scores = nodeBm.score(s1,[item[0] for item in ret]);
		ret = [ (ret[i][0], scores[i], ret[i][1], ret[i][2])for i in range(len(scores))]
		def cmp(x,y):
			return x[2]-y[2] if y[1] == x[1] else (-1 if y[1]<x[1] else 1);
		return sorted(ret,cmp)[:num];

class WayNameUtils:  # align to utf8
	Name2id_way = {};
	BKTree_way = None;

	def __init__(self):
		if len(WayNameUtils.Name2id_way) == 0 or WayNameUtils.BKTree_way == None:
			WayNameUtils.Build();

	@classmethod
	def cleanName(cls, name):    # remove brackets and whitespaces
		name = "".join(re.split("[()（） ]",name));
		return name

	@classmethod
	def Build(cls):
		print ">>>>> Initalize WayNameUtils ..."

		if (os.path.exists("./data/Name2id_way.dat")):
			print ">>>>> Loading ..."
			WayNameUtils.Name2id_way = joblib.load("./data/Name2id_way.dat")
		else:
			print ">>>>> Generating ..."
			dbh = DBHelper();
			data = dbh.executeAndFetchAll("select way_id,v from current_way_tags where k='name'");
			for pair in data:
				cname = WayNameUtils.cleanName(pair[1]);
				if WayNameUtils.Name2id_way.has_key(cname):
					WayNameUtils.Name2id_way[cname].append(pair[0])
				else:
					WayNameUtils.Name2id_way[cname] = [pair[0]];
			joblib.dump(WayNameUtils.Name2id_way,"./data/Name2id_way.dat",compress=3)
		
		if (os.path.exists("./data/BKTree_way.dat")):
			print ">>>>> Load BKTree ..."
			WayNameUtils.BKTree_way = joblib.load("./data/BKTree_way.dat")
		else:
			print ">>>>> Build BKTree ..."
			WayNameUtils.BKTree_way = BKTree(words=WayNameUtils.Name2id_way.keys())
			joblib.dump(WayNameUtils.BKTree_way,"./data/BKTree_way.dat",compress=3)
		print ">>>>> Done Initalization"


	def findSim(self,s1):   # return none indicates nothing ever matches
		s1 = WayNameUtils.cleanName(s1)
		if (WayNameUtils.Name2id_way.has_key(s1)):
			return [(s1,0,WayNameUtils.Name2id_way[s1])];
		else:
			data = WayNameUtils.BKTree_way.query(s1,3);
			if len(data) > 0:
				return [(data[i][1],data[i][0],WayNameUtils.Name2id_way[data[i][1]]) for i in range(min(5,len(data)))]
			else: 
				data = WayNameUtils.BKTree_way.query(s1,5);
				if len(data) > 0:
					return [(data[i][1],data[i][0],WayNameUtils.Name2id_way[data[i][1]]) for i in range(min(5,len(data)))]
		return None
	def getMostSim(self,s1,num=1):
		ret = self.findSim(s1);
		if ret == None: return None;
		wBm = BM_25(typ='Way');
		scores = wBm.score(s1,[item[0] for item in ret]);
		ret = [ (ret[i][0], scores[i], ret[i][1], ret[i][2])for i in range(len(scores))]
		def cmp(x,y):
			return x[2]-y[2] if y[1] == x[1] else (-1 if y[1]<x[1] else 1);
		return sorted(ret,cmp)[:num];



class OtherUtils:
	Nid_Coord = None
	Relation_Father = None
	Poi_Mapping = None
	@staticmethod
	def Build():
		print ">>>>> Initalize OtherUtils ..."
		OtherUtils.GetRelationFather();
		OtherUtils.GetNid2Coord();
		print ">>>>> Done Initalization"
	@staticmethod
	def GetNid2Coord():
		if OtherUtils.Nid_Coord == None:
			ret = {}
			if os.path.exists("./data/Nid_Coord.dat"):
				print ">>>>> Loading Nid_Coord ..."
				ret = joblib.load("./data/Nid_Coord.dat");
			else:
				dbh = DBHelper();
				raw = dbh.executeAndFetchAll("select id, latitude, longitude from current_nodes where visible=1")
				x = [tp[0] for tp in raw];
				y = [[tp[1],tp[2]] for tp in raw];
				ret = dict(zip(x,y))
				joblib.dump(ret,"./data/Nid_Coord.dat",compress=3)
			OtherUtils.Nid_Coord = ret;
		return OtherUtils.Nid_Coord;
	@staticmethod
	def StdlizePOIType(poitype):
		if OtherUtils.Poi_Mapping == None:
			OtherUtils.Poi_Mapping = {}
			with open('./poitype.map','r+') as f1:
				for lines in f1.readlines():
					li = lines.decode('utf8').split();
					for item in li: OtherUtils.Poi_Mapping[item] = li[0]
		if OtherUtils.Poi_Mapping.has_key(poitype):
			return OtherUtils.Poi_Mapping[poitype];
		return None
	@staticmethod
	def GetRelationFather():
		if OtherUtils.Relation_Father == None:
			ret = {}
			if os.path.exists("./data/Relation_Father.dat"):
				print ">>>>> Loading Relation_Father ..."
				ret = joblib.load("./data/Relation_Father.dat");
			else:
				dbh = DBHelper();
				raw = dbh.executeAndFetchAll("select relation_id, member_id from current_relation_members where member_type='Relation'")
				for tp in raw:
					if ret.has_key(tp[1]):
						ret[tp[1]].append(tp[0]);
					else:
						ret[tp[1]] = [tp[0]];
				joblib.dump(ret,"./data/Relation_Father.dat",compress=3)
			OtherUtils.Relation_Father = ret;
		return OtherUtils.Relation_Father;
def test_node2Line():
	ds = DistanceUtils();
	ds.node2Line()


if __name__ == '__main__':
	# print OtherUtils.StdlizePOIType("高校".decode('utf8'))
	# DistanceUtils.Build()
	frompoint = [31.1977664,121.4147976]
	topoint = [31.2086403, 121.6091085]
	print DistanceUtils.spherical_distance(frompoint,topoint)
	# nu = NodeNameUtils();
	# print NodeNameUtils.Name2id["中国浦发".decode("utf8")]
	# retli = nu.getMostSim("中国民生银行".decode('utf8'))
	# for ret in retli:
	# 	print ret[0],ret[1],ret[2]
	# while(True):
	# 	target = raw_input();
	# 	retli = nu.getMostSim(target.decode('utf8'))
	# 	for ret in retli:
	# 		print ret[0],ret[1],ret[2]
	# WayNameUtils.Build();
	# wnu = WayNameUtils();
	# retli = wnu.findSim("杨高中路".decode('utf8'))
	# for ret in retli:
	# 	print ret[0],ret[1],ret[2]
	# while(True):
	# 	target = raw_input();
	# 	retli = wnu.findSim(target.decode('utf8'))
	# 	for ret in retli:
	# 		print ret[0],ret[1],ret[2]
	# ds = DistanceUtils();
	# print ds.queryNN(pointlist = np.array([[312268644,1215310826]]), k_nn=8);
	# ds2 = DistanceUtils();
	# print ds2.queryNN(pointlist = np.array([[312268644,1215310826],[0,1]]), k_nn=3);