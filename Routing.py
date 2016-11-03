# -*- coding:utf-8 -*- 
from OsmGenerator import Point,Way
from sklearn.externals import joblib
from scipy import spatial
import gc
import os,sys
from DBHelper import *
from Utils import OtherUtils;
import numpy as np


def getWeight(transport, wayType):
	Weightings = { \
	'motorway': {'car':10},
	'trunk':    {'car':10, 'bike':0.05},
	'primary':  {'bike': 0.3, 'car':2, 'walk':1},
	'secondary': {'bike': 1, 'car':1.5, 'walk':1},
	'tertiary': {'bike': 1, 'car':1, 'walk':1},
	'unclassified': {'bike': 1, 'car':1, 'walk':1},
	'minor': {'bike': 1, 'car':1, 'walk':1},
	'bikeway': {'bike': 3, 'walk':0.2},
	'residential': {'bike': 3, 'car':0.7, 'walk':1},
	'track': {'bike': 1, 'car':1, 'walk':1},
	'service': {'bike': 1, 'car':1, 'walk':1},
	'bridleway': {'bike': 0.8, 'walk':1},
	'walkway': {'bike': 0.2, 'walk':1},
	'steps': {'walk':1, 'bike':0.3},
	}
	try:
		return(Weightings[wayType][transport])
	except KeyError:
		# Default: if no weighting is defined, then assume it can't be routed
		return 0


def equivalent(tag):
	equivalent = { \
		"primary_link":"primary",
		"trunk":"primary",
		"trunk_link":"primary",
		"secondary_link":"secondary",
		"tertiary":"secondary",
		"tertiary_link":"secondary",
		"residential":"unclassified",
		"minor":"unclassified",
		"steps":"footway",
		"driveway":"service",
		"pedestrian":"footway",
		"bridleway":"cycleway",
		"track":"cycleway",
		"arcade":"footway",
		"canal":"river",
		"riverbank":"river",
		"lake":"river",
		"light_rail":"railway"
		}
	try:
		return equivalent[tag]
	except KeyError:
		return tag

class RoutingHelper:
	@staticmethod
	def get_kd_tuple(node_list): # node_list = [(ID,[lat,lon])...]
		idx_map = {}
		for i in xrange(len(node_list)):
			idx_map[i] = node_list[i][0]
		x = [item[1][0] for item in node_list]
		y = [item[1][1] for item in node_list]
		tree = spatial.KDTree(zip(x,y));
		return (idx_map,tree);

	@staticmethod
	def queryNN(pointlist, kd_tuple):   # len(pointlist) == 1
		(dis,idx) = kd_tuple[1].query(pointlist,k=1);
		mapping = kd_tuple[0];
		node_data = kd_tuple[1].data;
		return (mapping[idx[0]],node_data[idx[0]][0], node_data[idx[0]][1], dis[0])




class Routing:
	Route = {};
	RouteType = ('bike','walk','car');
	CanRouteFrom = {}
	CanRouteFrom_kdTuple = {}
	Points = None
	Ways = None
	Nid2Coord = OtherUtils.GetNid2Coord();

	@classmethod
	def addPath(cls,fr,to,rt,w):
		# print 'here'
		Routing.CanRouteFrom[rt].add(fr);
		try:
			if to in Routing.Route[rt][fr].keys():
				return
			Routing.Route[rt][fr][to] = w
		except KeyError:
			Routing.Route[rt][fr] = {to: w}

	@classmethod
	def Build(cls):
		if len(Routing.Route) > 0:  return;
		if os.path.exists(WORK_DIR+"data/route.dat"):
			print ">>>>> Loading Routing dat ..."
			Routing.Route,Routing.CanRouteFrom = joblib.load(WORK_DIR+"data/route.dat")
		else:
			print ">>>>> Generating Routing dat ..."
			Routing.Points = {}
			Routing.Ways = {}

			for rt in Routing.RouteType:
				Routing.Route[rt] = {}
				Routing.CanRouteFrom[rt] = set()


			dbh = DBHelper();
			# raw = dbh.executeAndFetchAll("select id, latitude, longitude from current_nodes")
			# for tp in raw:
			# 	Routing.Points[tp[0]] = Point(id=tp[0],lat=tp[1],lon=tp[2])
			raw = dbh.executeAndFetchAll("select id from current_ways")
			for tp in raw:
				Routing.Ways[tp[0]] = Way(id=tp[0]);
			raw = dbh.executeAndFetchAll("select * from current_way_nodes");
			for tp in raw:
				Routing.Ways[tp[0]].addNodes(tp[2],tp[1]);
			raw = dbh.executeAndFetchAll("select * from current_way_tags where k='highway' or k='oneway'");
			for tp in raw:
				Routing.Ways[tp[0]].addTags(tp[1],tp[2]);

			# print "no.Points:",len(Routing.Points)
			# print 'no.Ways',len(Routing.Ways) 

			for way_id in Routing.Ways.keys():
				# print way_id
				way = Routing.Ways[way_id]
				highway = equivalent(way.tags.get('highway',''))
				# print highway
				oneway = way.tags.get('oneway', '')
				reversible = (oneway != 'yes')

				canGo = {}
				canGo['bike'] = highway in ('primary','secondary','tertiary','unclassified','minor','cycleway','residential', 'track','service')
				canGo['car'] = highway in ('motorway','trunk','primary','secondary','tertiary','unclassified','minor','residential', 'service')
				canGo['walk'] = canGo['bike'] or highway in('footway','steps')

				last = -1
				for i in [tp[1] for tp in sorted(way.nds.iteritems(), key=lambda d:d[0])]:
					# print way_id,i
					if (last != -1):
						for rt in Routing.RouteType:
							# print rt,canGo[rt]
							if (canGo[rt]):
								wei = getWeight(rt,highway);
								Routing.addPath(last,i,rt,wei);
								if reversible or rt == 'walk':
									Routing.addPath(i,last,rt,wei);
					last = i;
			joblib.dump((Routing.Route,Routing.CanRouteFrom),WORK_DIR+"data/route.dat", compress = 3)

		print ">>>>> Generating Routing KDTree ..."
		# Nid2Coord = OtherUtils.GetNid2Coord();
		for rt in Routing.CanRouteFrom.keys():
			nodeli = [(nid,Routing.Nid2Coord[nid]) for nid in Routing.CanRouteFrom[rt]]
			# print nodeli[0]
			Routing.CanRouteFrom_kdTuple[rt] = RoutingHelper.get_kd_tuple(nodeli);
		Routing.Points = None
		Routing.Ways = None
		Routing.CanRouteFrom = {}
		gc.collect()
		print ">>>>> Done Initialization"

	def __init__(self, routeType):
		assert(routeType in Routing.RouteType)
		self.routeType = routeType;
		Routing.Build();
		self.queue = [];
		self.terminal = -1;
	def push(self, start, end, curItem, wei=1):
		import bisect
		from Utils import DistanceUtils
		if wei == 0: return
		distance_ori = DistanceUtils.spherical_distance(Routing.Nid2Coord[start],Routing.Nid2Coord[end])
		distance = distance_ori/wei;
		cur_distance = curItem[1]

		realItem = (cur_distance+DistanceUtils.spherical_distance(Routing.Nid2Coord[end],Routing.Nid2Coord[self.terminal]),\
					cur_distance + distance,\
					curItem[2]+","+str(end),\
					end,\
					curItem[4] + distance_ori);
		if (len(self.queue) == 0):
			self.queue.append(realItem);
		else:
			bisect.insort_left(self.queue,realItem);


	
	def findNearestRoutable(self,coord_int,rt):
		return RoutingHelper.queryNN(np.array([coord_int]),Routing.CanRouteFrom_kdTuple[rt]);

	def findRoute(self,start_coord, end_coord,max_iter=1000000):
		
		from Utils import coord_scale_default as csd;
		# Nid2Coord= OtherUtils.GetNid2Coord();
		start_coord_int = [int(item*csd) for item in start_coord];
		end_coord_int = [int(item*csd) for item in end_coord];

		mod_start = self.findNearestRoutable(start_coord_int,self.routeType)[0]
		mod_end = self.findNearestRoutable(end_coord_int,self.routeType)[0]

		print 'Adjusted Start:',Routing.Nid2Coord[mod_start]
		print 'Adjusted End:',Routing.Nid2Coord[mod_end]

		self.terminal = mod_end;
		vi = set([mod_start]);
		self.queue = [];

		# queueItem = (expect_dis, cur_dis_wei, nodes_list_str,end,cur_dis)
		dummyItem = (sys.maxint,0,str(mod_start),-1,0)

		try:
			for i, weight in Routing.Route[self.routeType][mod_start].items():
				self.push(mod_start, i, dummyItem, weight)
		except KeyError:
			return('fail at beginning',-1,[])


		iter_num = 0;
		while iter_num <= max_iter:
			iter_num += 1;
			try:
				nextItem = self.queue.pop(0)
			except IndexError:
				return('fail at middle',-1,[])

			x = nextItem[3]
			if x in vi:
				continue
			if x == mod_end:
				# success
				return ('success',nextItem[4],[(nid,Routing.Nid2Coord[int(nid)]) for nid in nextItem[2].split(',')])
			vi.add(x)
			try:
				for i, weight in Routing.Route[self.routeType][x].items():
					if i not in vi:
						self.push(x, i, nextItem, weight)
			except: pass
		return ('exceed max_iter',-1,[]);

if __name__ == '__main__':
	Routing.Build()
	ro = Routing('car')
	print ro.findRoute([31.1981978,121.4152321],[31.2075866,121.6090868])



