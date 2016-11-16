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
from collections import deque

class ChangeSetUtils(handler.ContentHandler):

	def build(self):
		dbh = DBHelper();
		dbh.execute(sql="create table if not exists changesets_dependence( "+\
		 "id bigint(20) NOT NULL,"+\
		 "dep_id bigint(20),"+\
		 "primary key (id),"
		 "foreign key(dep_id) references changesets(id))",need_commit=True)
		# dbh.execute(sql="insert into changesets_dependence select -1, -1 from dual where not exists(select id from changesets_dependence where id = -1)")
		# dbh.execute(sql="insert into changesets_dependence select 1, 1 from dual where not exists(select id from changesets_dependence where id = 1)")
		# dbh.commit();


	def __init__(self,filename, status=None):
		self.build();
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
		if (status != None): self.mergeChangeStatus(status);

		if (filename == None): return;
		self.process(filename);

	def __del__(self):
		self.operationType = None;
		self.isRoutingChange = False;
		self.isWayNameChange = False;
		self.isNodeNameChange = False;
		self.isNodePosChange = False;
		self.currentObjectName = None;
		self.currentObjectId = None;
		self.nodes = None;
		self.ways = None;
		self.tags = None;
		self.node_id_mapping = None;
		self.way_id_mapping = None;
		self.timestamp = None;
		self.numOfChanges = 0;
		self.changesetId = None;
		self.changesetIdList = None;
		gc.collect();

	def getChangeStatus(self):
		return (self.isRoutingChange,self.isWayNameChange,self.isNodeNameChange);
	def mergeChangeStatus(self,status):
		self.isRoutingChange |= status[0];
		self.isWayNameChange |= status[1]
		self.isNodeNameChange |= status[2]

	def process(self,filename):
		isSuccess = self.parseXML(filename);
		if not isSuccess:
			return;

		try:
			if self.operationType == 'commit':
				self.dumpDB()
			elif self.operationType == 'rollback':
				self.reverseDB();
		except Exception,e:
			print "[Error]", e;
			print ">>>>> Operation Failed, please check the log"

		if self.isNodePosChange:		# change at once since it will be used soon afterward
			DistanceUtils.Build(rebuild=True);
			

	def calcChangeSetId(self):
		dbh = DBHelper();
		raw = dbh.executeAndFetchAll("select id from changesets");
		idset = set([tp[0] for tp in raw]);
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
			if self.operationType != None:
				assert(False), "One operation per time!"
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
					self.isRoutingChange |= True;
					self.currentObjectName = 'way';
					id = int(attrs.get('id'))
					self.currentObjectId = id;
					self.ways[id] = Way(id=id,changeset=self.changesetId,timestamp=self.timestamp);

			elif name == 'nd':
				self.ways[self.currentObjectId].appendNodes(int(attrs.get('ref')))

			elif name == 'tag':
				k,v = (attrs.get('k'), attrs.get('v'))
				if self.currentObjectName == 'node':
					if 'name' in k: self.isNodeNameChange |= True;
					self.nodes[self.currentObjectId].addTags(k,v)
				elif self.currentObjectName == 'way':
					if 'name' in k: self.isWayNameChange |= True;
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
		node_id_base = dbh.executeAndFetchAll('select max(id) from current_nodes')[0][0]
		for nd in self.nodes.keys():
			lat,lon = self.nodes[nd].lat,self.nodes[nd].lon;
			tp = ds.queryNN(pointlist = np.array([[lat,lon]]))[0][0];
			if (ds.spherical_distance([lat,lon],[tp[1],tp[2]]) < 5):   # regarded as the same if two points are within distance of 5m
				self.node_id_mapping[nd] = tp[0]
				dep_id = dbh.executeAndFetchAll("select changeset_id from current_nodes where id=%s",params=(tp[0],))[0][0]
				dbh.execute(sql="insert into changesets_dependence select %s,%s from dual where not exists(select id from changesets_dependence where id = %s)",\
					params=(self.getChangeSetId(),dep_id,self.getChangeSetId()), need_commit=True);
			else:
				self.isNodePosChange |= True;
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
		assert(-1 not in self.changesetIdList and 1 not in self.changesetIdList), "Original changeset can not be reversed!"

		# changeset_id check

		dbh = DBHelper();
		raw = dbh.executeAndFetchAll("select * from changesets_dependence");
		dep_dic = {};
		for csid,dep_id in zip([tp[0] for tp in raw],[tp[1] for tp in raw]):
			if (dep_dic.has_key(dep_id)): 
				dep_dic[dep_id].append(csid);
			else:
				dep_dic[dep_id] = [csid];
		raw = dbh.executeAndFetchAll("select id,created_at from changesets");
		id_create_dic = dict(zip([tp[0] for tp in raw], [tp[1] for tp in raw]));
		idset = set([tp[0] for tp in raw]);

		self.changesetIdList = list(set(self.changesetIdList))

		for csid in self.changesetIdList:
			if not (csid in idset): 
				print "Warning: No such changeset_id %d!" % (csid);
				self.changesetIdList.remove(csid)
			if (dep_dic.has_key(csid)):
				for item in dep_dic[csid]:
					assert (item in self.changesetIdList), "can not roll back changeset %d without rolling back changeset %d" % (csid, item);
		self.changesetIdList.sort(key=lambda d:id_create_dic[d], reverse=True);



		print ">>>>> Reversing from DB ..."
		dbh = DBHelper()
		node_id = [];
		way_id = [];
		# current_nodes;
		for cs in self.changesetIdList:
			raw = dbh.executeAndFetchAll("select id from current_nodes where changeset_id=%s",params=(cs,));
			node_id += [tp[0] for tp in raw];
			if len(raw) > 0:
				self.isNodePosChange |= True;
				# dbh.execute(sql="delete from current_nodes where changeset_id=%s",params=(cs,));

			raw = dbh.executeAndFetchAll("select id from current_ways where changeset_id=%s",params=(cs,));
			way_id += [tp[0] for tp in raw];
			if len(raw) > 0:
				self.isRoutingChange |= True;
				# dbh.execute(sql="delete from current_ways where changeset_id=%s",params=(cs,));
		dbh.commit();
		for nid in node_id:
			raw = dbh.executeAndFetchAll("select distinct node_id from current_node_tags where k like %s and node_id=%s",params=("name%",nid));
			if len(raw) > 0: self.isNodeNameChange|=True;
			dbh.execute(sql="delete from current_node_tags where node_id=%s",params=(nid,));
		for wid in way_id:
			raw = dbh.executeAndFetchAll("select distinct way_id from current_way_tags where k like %s and way_id=%s",params=("name%",wid));
			if len(raw) > 0: self.isWayNameChange|=True;

			dbh.execute(sql="delete from current_way_tags where way_id=%s",params=(wid,));
			dbh.execute(sql="delete from current_way_nodes where id=%s",params=(wid,));
			dbh.execute(sql="delete from current_ways where id=%s",params=(wid,));
		for nid in node_id:
			dbh.execute(sql="delete from current_nodes where id=%s",params=(nid,));
		dbh.commit();

		for cs in self.changesetIdList:
			dbh.execute("delete from changesets_dependence where id=%s",params=(cs,))
			dbh.execute("delete from changesets where id=%s",params=(cs,));
		dbh.commit();


	@classmethod
	def rebuildData(cls,status):
		print ">>>>> Rebuilding Data ... (May Take a loooooooong time)"
		OtherUtils.GetNid2Coord(rebuild=True);
		isRoutingChange,isWayNameChange,isNodeNameChange = status;
		if isRoutingChange:
			from Routing import Routing;
			Routing.Build(rebuild=True);
		if isNodeNameChange:
			# from BM_25 import BM_25;
			NodeNameUtils.Build(rebuild=True);
			# BM_25.Build('Node',rebuild=True);
		if isWayNameChange:
			# from BM_25 import BM_25;
			WayNameUtils.Build(rebuild=True);
				# BM_25.Build('Way',rebuild=True);


class ChangeSetTask:
	def __init__(self):
		self.queue = deque();
	def push(self,filename):
		self.queue.append(filename);
	def execute(self):
		commit_ids = []    # None means a rollback opeartion
		if len(self.queue) <= 0:  return;
		cstatus = None;
		for tsk_filename in iter(self.queue):
			cs = ChangeSetUtils(tsk_filename,cstatus);
			cstatus = cs.getChangeStatus();
			commit_ids.append(cs.getChangeSetId());
		ChangeSetUtils.rebuildData(cstatus);
		return commit_ids;




if __name__ == '__main__':
	# ChangeSetUtils(WORK_DIR+"addOSM.xml");
	# # ChangeSetUtils(WORK_DIR+"addOSM2.xml")
	# ChangeSetUtils(WORK_DIR+"rollbackOSM.xml");
	task = ChangeSetTask();
	task.push(WORK_DIR+"addOSM.xml");
	task.push(WORK_DIR+"addOSM2.xml");
	task.push(WORK_DIR+"rollbackOSM.xml");
	task.execute();

		



