# -*- coding:utf-8 -*- 
import math
import gc
from DBHelper import *
from xml.sax import make_parser, handler
import xml
from Utils import coord_scale_default as csd;
from OsmGenerator import Point, Way
from Utils import DistanceUtils, NodeNameUtils, WayNameUtils, OtherUtils
import numpy as np
import datetime

class ChangeSetUtils(handler.ContentHandler):

	def __init__(self,filename):
		
		self.operationType = None;
		self.isRoutingChange = False;
		self.isWayNameChange = False;
		self.isNodeNameChange = False;
		self.isNodePosChange = False;
		self.currentObjectName = None;
		self.currentObjectId = None;
		self.nodes = {}
		self.ways = {}
		self.tags = {};
		self.node_id_mapping = {}
		self.way_id_mapping = {}
		self.timestamp = datetime.datetime.now();
		self.numOfChanges = 0;
		self.changesetId = self.calcChangeSetId();
		self.changesetIdList = [];  # for rollback

		if (filename == None): return;
		self.process(filename);


	def process(self,filename):
		isSuccess = self.parseXML(filename);
		if not isSuccess:
			return;

		if self.operationType == 'commit':
			self.dumpDB()
		elif self.operationType == 'rollback':
			self.reverseDB();
		self.rebuildData();

	def calcChangeSetId(self):
		dbh = DBHelper();
		raw = [dbh.executeAndFetchAll("select distinct changeset_id from current_nodes"),\
			dbh.executeAndFetchAll("select distinct changeset_id from current_ways"),\
			dbh.executeAndFetchAll("select distinct changeset_id from current_relations"),]
		idset = set();
		for item in raw:
			idset = idset | set([int(tp[0]) for tp in item]);
		return abs(max(idset))+1;

	def getChangeSetId(self):
		return self.changesetId;

	def parseXML(self, filename):
		if(not os.path.exists(filename)):
			print "[Failed] No such data file %s" % filename
			return False;
		try:
			parser = make_parser()
			parser.setContentHandler(self)
			parser.parse(filename)
			return True;
		except xml.sax._exceptions.SAXParseException:
			print "[Failed] Error loading %s" % filename
			return False;

	def startElement(self, name, attrs):
		def fmttime(s):
			if s.lower() == 'now': return self.timestamp;
			else: return  datetime.datetime.strptime(s,"%Y-%m-%dT%H:%M:%SZ");

		if name == "changeset":
			self.operationType = attrs.get('operation',"");
			assert self.operationType in ("rollback","commit") , "Wrong Type operation"


		# commit 
		if self.operationType == 'commit':
			assert name != 'relation', "<Relation> is not supported."
			if name in('node','way'):
				self.tags = {}
				self.numOfChanges += 1;

				if name == 'node':
					self.currentObjectName = 'node';
					id = int(attrs.get('id'))
					lat = int(float(attrs.get('lat'))*csd)
					lon = int(float(attrs.get('lon'))*csd)
					self.currentObjectId = id;
					self.nodes[id] = Point(id=id,lat=lat,lon=lon,changeset=self.changesetId,timestamp=self.timestamp);
				else:
					self.isRoutingChange = True;
					self.currentObjectName = 'way';
					id = int(attrs.get('id'))
					self.currentObjectId = id;
					self.ways[id] = Way(id=id,changeset=self.changesetId,timestamp=self.timestamp);

			elif name == 'nd':
				self.ways[self.currentObjectId].appendNodes(int(attrs.get('ref')))

			elif name == 'tag':
				k,v = (attrs.get('k'), attrs.get('v'))
				if self.currentObjectName == 'node':
					if 'name' in k: self.isNodeNameChange = True;
					self.nodes[self.currentObjectId].addTags(k,v)
				elif self.currentObjectName == 'way':
					if 'name' in k: self.isWayNameChange = True;
					self.ways[self.currentObjectId].addTags(k,v)


		# rollback
		else:
			if name == 'target':
				if len(attrs.get('id',""))>0:
					self.changesetIdList.append(int(attrs.get('id')));
					self._from = None;
					self._to = None;
				elif len(attrs.get('created_at_from',""))>0 and len(attrs.get('created_at_to',""))>0:
					self._from = fmttime(attrs.get('created_at_from',""))
					self._to = fmttime(attrs.get('created_at_to',""))


	def endElement(self, name):
		if self.operationType == 'rollback':
			if (self._from != None and self._to != None) :
				dbh = DBHelper();
				raw = dbh.executeAndFetchAll("select id from changesets where created_at>=%s and created_at<=%s",\
					params = (datetime.datetime.strftime(self._from,"%Y-%m-%d %H:%M:%S"),datetime.datetime.strftime(self._to,"%Y-%m-%d %H:%M:%S")))
				self.changesetIdList += [tp[0] for tp in raw]
		else:
			if name in ("node","way"):
				self.currentObjectName = None;
				self.currentObjectId = None;

	def dumpDB(self):
		print ">>>>> Dumping into DB ..."
		dbh = DBHelper();
		dbh.execute("insert into changesets values (%s,-1,%s,-900000000,900000000,-1800000000,1800000000,%s,%s)",\
			params=(self.getChangeSetId(),datetime.datetime.strftime(self.timestamp,"%Y-%m-%d %H:%M:%S"),datetime.datetime.strftime(self.timestamp,"%Y-%m-%d %H:%M:%S"),self.numOfChanges),\
			need_commit=True)
		ds = DistanceUtils();
		# calc node id base
		node_id_base = max(OtherUtils.GetNid2Coord().keys());
		for nd in self.nodes.keys():
			lat,lon = self.nodes[nd].lat,self.nodes[nd].lon;
			tp = ds.queryNN(pointlist = np.array([[lat,lon]]))[0][0];
			if (ds.spherical_distance([lat,lon],[tp[1],tp[2]]) < 5):   # regarded as the same if two points are within distance of 5m
				self.node_id_mapping[nd] = tp[0]
			else:
				self.isNodePosChange = True;
				node_id_base += 1;
				self.node_id_mapping[nd] = node_id_base;
				p = self.nodes[nd];
				dbh.execute(sql = "insert into current_nodes values (%s,%s,%s,%s,%s,%s,%s,%s)",\
					params = (self.node_id_mapping[p.id],p.lat,p.lon,p.changeset,p.visible,datetime.datetime.strftime(p.timestamp,"%Y-%m-%d %H:%M:%S"),0,p.version));
				for tag in p.tags.keys():
					dbh.execute(sql="insert into current_node_tags values (%s,%s,%s)",\
						params=(self.node_id_mapping[p.id],tag,p.tags[tag]));
		dbh.commit();

		# calc way id base
		raw = dbh.executeAndFetchAll("select distinct id from current_ways");
		way_id_base = max([tp[0] for tp in raw]);
		for wy in self.ways.keys():
			way_id_base += 1;
			self.way_id_mapping[wy] = way_id_base;
			w = self.ways[wy];
			dbh.execute(sql= "insert into current_ways values (%s,%s,%s,%s,%s)",\
				params = (self.way_id_mapping[w.id],w.changeset,datetime.datetime.strftime(w.timestamp,"%Y-%m-%d %H:%M:%S"),w.visible,w.version));
			for tag in w.tags.keys():
				dbh.execute(sql="insert into current_way_tags values (%s,%s,%s)",\
					params=(self.way_id_mapping[w.id],tag,w.tags[tag]));
			for seq in w.nds.keys():
				dbh.execute(sql="insert into current_way_nodes values (%s,%s,%s)",\
					params=(self.way_id_mapping[w.id],self.node_id_mapping[w.nds[seq]],seq))
		dbh.commit();


	def reverseDB(self):
		print ">>>>> Reversing from DB ..."
		dbh = DBHelper()
		node_id = [];
		way_id = [];
		# current_nodes;
		for cs in self.changesetIdList:
			raw = dbh.executeAndFetchAll("select id from current_nodes where changeset_id=%s",params=(cs,));
			node_id += [tp[0] for tp in raw];
			if len(raw) > 0:
				self.isNodePosChange = True;
				# dbh.execute(sql="delete from current_nodes where changeset_id=%s",params=(cs,));

			raw = dbh.executeAndFetchAll("select id from current_ways where changeset_id=%s",params=(cs,));
			way_id += [tp[0] for tp in raw];
			if len(raw) > 0:
				self.isRoutingChange = True;
				# dbh.execute(sql="delete from current_ways where changeset_id=%s",params=(cs,));
		dbh.commit();
		for nid in node_id:
			raw = dbh.executeAndFetchAll("select distinct node_id from current_node_tags where k like %s and node_id=%s",params=("name%",nid));
			if len(raw) > 0: self.isNodeNameChange=True;
			dbh.execute(sql="delete from current_node_tags where node_id=%s",params=(nid,));
		for wid in way_id:
			raw = dbh.executeAndFetchAll("select distinct way_id from current_way_tags where k like %s and way_id=%s",params=("name%",wid));
			if len(raw) > 0: self.isWayNameChange=True;

			dbh.execute(sql="delete from current_way_tags where way_id=%s",params=(wid,));
			dbh.execute(sql="delete from current_way_nodes where id=%s",params=(wid,));
			dbh.execute(sql="delete from current_ways where id=%s",params=(wid,));
		for nid in node_id:
			dbh.execute(sql="delete from current_nodes where id=%s",params=(nid,));
		dbh.commit();

		for cs in self.changesetIdList:
			dbh.execute("delete from changesets where id=%s",params=(cs,));
		dbh.commit();


	def rebuildData(self):
		print ">>>>> Rebuilding Data ... (May Take a loooooooong time)"
		if self.isNodePosChange:
			OtherUtils.GetNid2Coord(rebuild=True);
			DistanceUtils.Build(rebuild=True);
		if self.isRoutingChange:
			from Routing import Routing;
			Routing.Build(rebuild=True);
		if self.isNodeNameChange:
			from BM_25 import BM_25;
			NodeNameUtils.Build(rebuild=True);
			BM_25.Build('Node',rebuild=True);
		if self.isWayNameChange:
			from BM_25 import BM_25;
			WayNameUtils.Build(rebuild=True);
			BM_25.Build('Way',rebuild=True);



if __name__ == '__main__':
	# ChangeSetUtils(WORK_DIR+"addOSM.xml");
	ChangeSetUtils(WORK_DIR+"rollbackOSM.xml");

		



