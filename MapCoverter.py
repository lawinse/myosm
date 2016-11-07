# -*- coding:utf-8 -*- 
from DBHelper import *
from sklearn.externals import joblib
import random


# This Convverter would be used by visualization
class MapConverter:
	self.__target_points = [] #target_points[i] = (lat1, lon1)
	self.__target_lines = [] # target_lines[i] = [(lat1,lon1)...(latn,lonn)]
	self.__target_bounder = tuple() #(minLat, minLon, maxLat, maxLon)
	self.__target_range = tuple() # ((lat,lon),radius)
	self.__dbh = None;

	def __init__(self):
		self.__dbh = DBHelper();

	def load(self,filename): #(__target_points,__target_lines,__target_bounder,__target_range)
		(self.__target_points,\
			self.__target_lines,\
			self.__target_bounder,\
			self.__target_range) = joblib.load(filename);

	def save(self,filename):
		joblib.dump((self.__target_points,\
			self.__target_lines,\
			self.__target_bounder,\
			self.__target_range),filename,compress=3);

	def set_target_points(self,points):
		# TODO
		pass

	def add_target_point(self,point):
		# TODO
		pass

	def unique_target_points(self):
		self.__target_points = list(set(self.__target_points));
		
	def get_target_points(self):
		return self.__target_points;

	def set_target_lines(self,lines):
		# TODO
		pass

	def add_target_line(self,line):
		# TODO
		pass

	def get_target_lines(self):
		return self.__target_lines;

	def get_target_bounder(self):
		if len(self.__target_bounder) == 0:
			#TODO
			pass
		return self.__target_bounder;

	def get_background_points(self,ratio=1.0):
		#TODO
		pass

	def get_background_lines(self,ratio=1.0):
		#TODO maybe useless
		pass

	def set_target_range(self,coord, radius):
		self.__target_range = ((coord[0],coord[1]),radius);

	def get_target_range(self):
		return self.__target_range;

