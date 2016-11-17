# -*- coding:utf-8 -*- 
from DBHelper import *
from sklearn.externals import joblib
import random
from Utils import OtherUtils
from Utils import coord_scale_default as csd
import gc


# This Convverter would be used by visualization
class MapConverter:
	def __init__(self):
		self.__root_points = [] #root_points[i] = (lat1, lon1)
		self.__target_points = [] #target_points[i] = (lat1, lon1)
		self.__target_lines = [] # target_lines[i] = [(lat1,lon1)...(latn,lonn)]
		self.__background_lines = [] # background_lines[i] = [(lat1,lon1)...(latn,lonn)]
		self.__target_bounder = tuple() #(minLat, minLon, maxLat, maxLon)
		self.__target_range = tuple() # ((lat,lon),radius)
		self.__dbh = DBHelper();

	def __del__(self):
		self.__root_points = None;
		self.__target_points = None
		self.__target_lines = None
		self.__target_bounder = None
		self.__target_range = None
		self.__background_lines = None
		gc.collect()

	def load(self,filename): #(__target_points,__root_points,__target_lines,__background_lines,__target_bounder,__target_range)
		(self.__target_points,\
			self.__root_points,\
			self.__target_lines,\
			self.__background_lines,\
			self.__target_bounder,\
			self.__target_range) = joblib.load(filename);

	def save(self,filename):
		joblib.dump((self.__target_points,\
			self.__root_points,\
			self.__target_lines,\
			self.__background_lines,\
			self.__target_bounder,\
			self.__target_range),filename,compress=3);

	def set_target_points(self,points):
		self.__target_points = points;

	def add_target_point(self,point):
		self.__target_points.append(point);

	def add_root_point(self,point):
		self.__root_points.append(point);

	def set_target_points_byid(self,pointids):
		Nid2Coord = OtherUtils.GetNid2Coord();
		self.__target_points = [tuple([item/csd for item in Nid2Coord[pid]]) for pid in set(pointids)]

	def add_target_point_byid(self,pointid):
		Nid2Coord = OtherUtils.GetNid2Coord();
		self.__target_points.append(tuple([item/csd for item in Nid2Coord[pointid]]))

	def add_target_pair_points_byid(self,pid1,pid2):
		Nid2Coord = OtherUtils.GetNid2Coord();
		coord1 = tuple([item/csd for item in Nid2Coord[pid1]]);
		coord2 = tuple([item/csd for item in Nid2Coord[pid2]]);
		self.add_target_point(coord1);
		self.add_target_point(coord2);
		self.add_target_line([coord1,coord2]);

	def unique_target_points(self):
		self.__target_points = list(set(self.__target_points));
		
	def get_target_points(self):
		self.unique_target_points();
		return self.__target_points;

	def set_target_lines(self,lines):
		self.__target_lines = lines;

	def add_target_line(self,line):
		self.__target_lines.append(line)

	def __line2pointlists(self,lineid):
		raw = self.dbh.executeAndFetchAll("select node_id from current_way_nodes where id=%s order by sequence_id");
		node_id_list = [tp[0] for tp in raw];
		Nid2Coord = OtherUtils.GetNid2Coord();
		return [tuple([item/csd for item in Nid2Coord[pid]]) for pid in node_id_list]

	def set_target_lines_byid(self,lineids):
		self.__target_lines = [__line2pointlists(lineid) for lineid in set(lineids)]

	def add_target_line_byid(self,lineid):
		self.__target_lines.append(__line2pointlists(lineid));

	def get_target_lines(self):
		return self.__target_lines;

	def get_target_bounder(self):
		if len(self.__target_bounder) == 0:
			minLat=90
			minLon=180
			maxLat=-90
			maxLon=-180
			for point in iter(self.__target_points+self.__root_points):
				minLat = min(point[0],minLat);
				maxLat = max(point[0],maxLat);
				minLon = min(point[1],minLon);
				maxLon = max(point[1],maxLon);

			for line in iter(self.__target_lines+self.__background_lines):
				for point in iter(line):
					minLat = min(point[0],minLat);
					maxLat = max(point[0],maxLat);
					minLon = min(point[1],minLon);
					maxLon = max(point[1],maxLon);

			self.__target_bounder = (minLat, minLon, maxLat, maxLon)
		return self.__target_bounder;

	def downsampling_target_points(self,num=None,ratio=1.0):
		if num != None:
			if int(len(self.__target_points)/num) <= 1:
				return;
			sample_n = num;
		else:
			sample_n = int(len(self.__target_points)*ratio)
		import random
		return random.sample(self.target_points,sample_n);

	def get_background_points(self,num=None,ratio=1.0):
		(minLat, minLon, maxLat, maxLon) = self.get_target_bounder();
		bgp = dbh.executeAndFetchAll("select latitude/1e7, longitude/1e7 from cuurent_nodes"+\
			"where (latitude/1e7 between %s and %s) and (longitude/1e7 between %s and %s)",\
			params = (minLat,maxLat,minLon,maxLon));
		if num != None:
			if int(len(bgp)/num) <= 1:
				return bgp;
			sample_n = num;
		else:
			sample_n = int(len(bgp)*ratio)
		import random

		sample_bgp = random.sample(bgp,sample_n);
		bgp = None;
		gc.collect();
		return sample_bgp

	def set_background_lines_byid(self,lineids):
		self.__background_lines = [__line2pointlists(lineid) for lineid in set(lineids)]

	def add_background_line_byid(self,lineid):
		self.__background_lines.append(__line2pointlists(lineid));

	def get_background_lines(self,num=None,ratio=1.0):
		if num != None:
			if int(len(self.__background_lines)/num) <= 1:
				return;
			sample_n = num;
		else:
			sample_n = int(len(self.__background_lines)*ratio)
		import random
		return random.sample(self.__background_lines,sample_n)

	def set_target_range(self,coord,radius):
		self.__target_range = ((coord[0],coord[1]),radius);

	def get_target_range(self):
		return self.__target_range;

	def convert(self):
		MapConverter.DoConvert(self);
	@staticmethod
	def DoConvert(mpcnvtr):
		#TODO
		print ">>>>> Converting to graph ..."
	

