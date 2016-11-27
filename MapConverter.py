# -*- coding:utf-8 -*- 
from DBHelper import *
from sklearn.externals import joblib
import random
from Utils import OtherUtils
from Utils import coord_scale_default as csd
from Graph import Graph
from Config import *
import datetime


# This Converter would be used by visualization
class MapConverter:
	def __init__(self):
		self.clear();

	def __del__(self):
		self.__root_points = None;
		self.__target_points = None
		self.__target_lines = None
		self.__target_bounder = None
		self.__target_range = None
		self.__background_lines = None
		self.__url = None;
		# import gc
		# gc.collect()

	def clear(self):
		self.__root_points = [] #root_points[i] = (lat1, lon1)
		self.__target_points = [] #target_points[i] = (lat1, lon1)
		self.__target_lines = [] # target_lines[i] = [(lat1,lon1)...(latn,lonn)]
		self.__background_lines = [] # background_lines[i] = [(lat1,lon1)...(latn,lonn)]
		self.__target_bounder = tuple() #(minLat, minLon, maxLat, maxLon)
		self.__target_range = tuple() # ((lat,lon),radius)
		self.__dbh = DBHelper();
		self.__url = ""

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

	def add_root_point_byid(self,pointid):
		Nid2Coord = OtherUtils.GetNid2Coord();
		self.__root_points.append(tuple([item/csd for item in Nid2Coord[pointid]]));

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
	
	def get_root_points(self):
		return self.__root_points;
	def get_target_points(self):
		self.unique_target_points();
		return self.__target_points;

	def set_target_lines(self,lines):
		self.__target_lines = lines;

	def add_target_line(self,line):
		self.__target_lines.append(line)

	def __line2pointlists(self,lineid):
		raw = self.__dbh.executeAndFetchAll("select node_id from current_way_nodes where id=%s order by sequence_id",params=(lineid,));
		node_id_list = [tp[0] for tp in raw];
		Nid2Coord = OtherUtils.GetNid2Coord();
		return [tuple([item/csd for item in Nid2Coord[pid]]) for pid in node_id_list]

	def set_target_lines_byid(self,lineids):
		self.__target_lines = [self.__line2pointlists(lineid) for lineid in set(lineids)]

	def add_target_line_byid(self,lineid):
		self.__target_lines.append(self.__line2pointlists(lineid));

	def get_target_lines(self):
		return self.__target_lines;

	def set_target_bounder(self,bounder):
		self.__target_bounder = bounder;

	def __is_in_bounder(self,point):
		(minLat, minLon, maxLat, maxLon) = self.get_target_bounder();
		return point[0]<=maxLat and point[0] >= minLat and point[1] <= maxLon and point[1] >= minLon

	def get_target_bounder(self,border_ratio=0.1,width_height_ratio=(9.0,16.0)):
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

			for line in iter(self.__target_lines):
				for point in iter(line):
					minLat = min(point[0],minLat);
					maxLat = max(point[0],maxLat);
					minLon = min(point[1],minLon);
					maxLon = max(point[1],maxLon);
			if self.__target_range != None and len(self.__target_range) > 0:
				(lat,lon),radius = self.__target_range;
				minLat = min(minLat,lat-radius);
				maxLat = max(maxLat,lat+radius);
				minLon = min(minLon,lon-radius);
				maxLon = max(maxLon,lon+radius);

			latDiff = maxLat-minLat;
			lonDiff = maxLon-minLon;
			minLat -= latDiff*border_ratio;
			maxLat += latDiff*border_ratio;
			minLon -= lonDiff*border_ratio;
			maxLon += lonDiff*border_ratio;

			if (maxLat-minLat)*1.0/(maxLon-minLon) > width_height_ratio[0]/width_height_ratio[1]:
				added = (maxLat-minLat)/width_height_ratio[0]*width_height_ratio[1]-(maxLon-minLon);
				maxLon += added * 0.5;
				minLon -= added * 0.5;
			else:
				added = (maxLon-minLon)/width_height_ratio[1]*width_height_ratio[0]-(maxLat-minLat);
				maxLat += added * 0.5;
				minLat -= added * 0.5;

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
		return random.sample(self.__target_points,sample_n);

	def downsampling_target_lines(self,num=None,ratio=1.0):
		if num != None:
			if int(len(self.__target_lines)/num) <= 1:
				return;
			sample_n = num;
		else:
			sample_n = int(len(self.__target_lines)*ratio)
		import random
		return random.sample(self.__target_lines,sample_n);

	def get_background_points(self,num=None,ratio=1.0):
		(minLat, minLon, maxLat, maxLon) = self.get_target_bounder();
		bgp = self.__dbh.executeAndFetchAll("select latitude/1e7, longitude/1e7 from current_nodes inner join"+\
			" (select distinct node_id from current_node_tags) as a on current_nodes.id=a.node_id "+\
			"where (latitude/1e7 between %s and %s) and (longitude/1e7 between %s and %s)",\
			params = (minLat,maxLat,minLon,maxLon));
		sample_n = 0;
		if num != None:
			if int(len(bgp)/num) <= 1:
				return bgp;
			sample_n = num;
		
		sample_n = max(sample_n,int(len(bgp)*ratio))
		import random

		sample_bgp = random.sample(bgp,sample_n);
		bgp = None;
		import gc
		gc.collect();
		return sample_bgp

	def set_background_lines_byid(self,lineids):
		self.__background_lines = [self.__line2pointlists(lineid) for lineid in set(lineids)]

	def add_background_line_byid(self,lineid):
		self.__background_lines.append(self.__line2pointlists(lineid));

	def __filter_lines_by_bounder(self,lines):
		for i in xrange(len(lines)):
			for j in xrange(len(lines[i])):
				if not self.__is_in_bounder(lines[i][j]):
					lines[i][j]="";
			while "" in lines[i]: lines[i].remove("")
		while [] in lines: lines.remove([]);
		return lines;

	def get_background_lines(self,num=None,ratio=1.0):
		self.__background_lines = self.__filter_lines_by_bounder(self.__background_lines);
		if num != None:
			if int(len(self.__background_lines)/num) <= 1:
				return;
			sample_n = num;
		else:
			sample_n = int(len(self.__background_lines)*ratio)
		if sample_n == len(self.__background_lines): return self.__background_lines;
		import random
		return random.sample(self.__background_lines,sample_n)

	def set_target_range(self,coord,radius):
		self.__target_range = ((coord[0],coord[1]),radius);

	def get_target_range(self):
		return self.__target_range;

	def report(self):
		print "\n###################\nMap Report:"
		print "[Range]\nminLat=%f, minLon=%f\nmaxLat=%f, maxLon=%f" % self.get_target_bounder();
		print "[Size Info]"
		print "#root_points: %d" % len(self.get_root_points());
		print "#target_points: %d" % len(self.get_target_points());
		print "#target_lines: %d" % sum([len(line)-1 for line in self.get_target_lines()]);
		print "#background_lines: %d" % sum([len(line)-1 for line in self.get_background_lines()]);
		print "###################\n"

	def get_url(self):
		return self.__url;

	def set_url(self,url):
		self.__url = url

	def convert(self,directory=WORK_DIR,qname=""):
		print ">>>>> Converting to graph ..."
		self.report();
		mg = Graph()
		mg.add_target_points(self.get_target_points());
		mg.add_root_points(self.get_root_points());
		mg.add_target_lines(self.get_target_lines()); 

		mg.add_background_points(self.get_background_points(num=20000,ratio=0.65))
		mg.add_background_lines(self.get_background_lines());
		if not os.path.exist(directory):
			os.mkdir(directory);
		fname = directory+qname+str(hash(datetime.datetime.now()))+'.png';
		mg.xml_render(fname);
		self.set_url(fname)


if __name__ == '__main__':
	mpcnvtr = MapConverter();
	mpcnvtr.load("MapConverter.dump");
	mpcnvtr.report();
	mg = Graph()
	ways = mpcnvtr.get_target_lines();

	for item in ways:
		mg.add_target_points(item);
		mg.add_target_lines(item); 
	mg.add_background_points(mpcnvtr.get_background_points())
	

