# -*- coding:utf-8 -*- 
from Utils import coord_scale_default as csd;
from Utils import OtherUtils;
import datetime
from DBHelper import *
import gc

def bracketen(a):
	try:
		return '"' + str(a) + '"'
	except:
		return '"' + a + '"'
def batchIndent(s):
	s = s.rstrip();
	s = "\n\t".join(s.split("\n"));
	s = "\t"+s;
	return s;
def wrapOsm(name, header, body=None):
	builder = "<"+name + " ";
	builder += header
	if body == None:
		builder += "/>"
	else:
		builder += ">\n"
		body = body.rstrip();
		body = "\n\t".join(body.split("\n"));
		body = "\t" + body;
		builder += body.rstrip()+"\n"+"</"+name+">"
	return builder;
class Point:
	def __init__(self,id=None,lat=None,lon=None,visible=1,version=1,changeset=None,timestamp=None):
		self.id = id;
		self.lat = lat;
		self.lon = lon;
		self.visible = visible;
		self.version = version;
		self.changeset = changeset;
		self.timestamp = timestamp;
		self.tags = {};
	def addTags(self,k,v):
		self.tags[k] = v;
	def translate(self):
		header = 'id='+bracketen(self.id)+\
					' lat='+bracketen(self.lat/csd)+\
					' lon='+bracketen(self.lon/csd)+\
					' visible='+bracketen(str(self.visible==1).lower())+\
					' version='+bracketen(self.version)+\
					' changeset='+bracketen(self.changeset)+\
					' timestamp='+bracketen(datetime.datetime.strftime(self.timestamp,"%Y-%m-%dT%H:%M:%SZ"));


		if len(self.tags) == 0:
			return wrapOsm(name = "node",header = header);
		else:
			body = ""
			for k in self.tags.keys():
				tags_hd = 'k='+bracketen(k)+\
							' v='+bracketen(self.tags[k]);
				body += wrapOsm(name = "tag",header = tags_hd)+"\n"
			return wrapOsm(name = "node",header = header, body = body);


class Way:
	def __init__(self,id=None,visible=1,version=1,changeset=None,timestamp=None):
		self.id = id;
		self.visible = visible;
		self.version = version;
		self.changeset = changeset;
		self.timestamp = timestamp;
		self.tags = {};
		self.nds = {}

	def addTags(self,k,v):
		self.tags[k] = v;
	def addNodes(self,sq_id,nd_id):
		self.nds[sq_id] = nd_id;

	def translate(self):
		header = 'id='+bracketen(self.id)+\
					' visible='+bracketen(str(self.visible==1).lower())+\
					' version='+bracketen(self.version)+\
					' changeset='+bracketen(self.changeset)+\
					' timestamp='+bracketen(datetime.datetime.strftime(self.timestamp,"%Y-%m-%dT%H:%M:%SZ"));


		if len(self.tags) == 0 and len(self.nds) == 0: 
			return wrapOsm(name = "way",header = header);
		else:
			body = ""
			nid_list =[tp[1] for tp in sorted(self.nds.iteritems(), key=lambda d:d[0])];

			for nid in nid_list:
				ref_hd = 'ref='+bracketen(nid);
				body += wrapOsm(name = "nd", header = ref_hd) +"\n"

			for k in self.tags.keys():
				tags_hd = 'k='+bracketen(k)+\
							' v='+bracketen(self.tags[k]);
				body += wrapOsm(name = "tag",header = tags_hd)+"\n"

			return wrapOsm(name = "way",header = header, body = body);

class Relation:
	def __init__(self,id=None,visible=1,version=1,changeset=None,timestamp=None):
		self.id = id;
		self.visible = visible;
		self.version = version;
		self.changeset = changeset;
		self.timestamp = timestamp;
		self.tags = {};
		self.members = {}

	def addTags(self,k,v):
		self.tags[k] = v;
	def addMembers(self,sq_id,typ,id,role):
		self.members[sq_id] = (typ,id,role);

	def translate(self):
		header = 'id='+bracketen(self.id)+\
					' visible='+bracketen(str(self.visible==1).lower())+\
					' version='+bracketen(self.version)+\
					' changeset='+bracketen(self.changeset)+\
					' timestamp='+bracketen(datetime.datetime.strftime(self.timestamp,"%Y-%m-%dT%H:%M:%SZ"));


		if len(self.tags) == 0 and len(self.members) == 0: 
			return wrapOsm(name = "relation",header = header);
		else:
			body = ""
			mbr_list =[tp[1] for tp in sorted(self.members.iteritems(), key=lambda d:d[0])];

			for mbr in mbr_list:
				mbr_hd = 'type='+bracketen(mbr[0])+\
						' ref='+bracketen(mbr[1])+\
						' role='+bracketen(mbr[2]);
				body += wrapOsm(name = "member", header = mbr_hd) +"\n"

			for k in self.tags.keys():
				tags_hd = 'k='+bracketen(k)+\
							' v='+bracketen(self.tags[k]);
				body += wrapOsm(name = "tag",header = tags_hd)+"\n"

			return wrapOsm(name = "relation",header = header, body = body);

class OsmGenerator:
	Default_header = "<?xml version='1.0' encoding='UTF-8'?>\n<osm version='0.6' generator='OsmGenerator'>\n";
	Default_tailer = "</osm>";
	def __init__(self,fname,minLat, maxLat, minLon, maxLon):
		self.f = open(fname,"w+");
		self.f.write(OsmGenerator.Default_header);
		header = 'minlon='+bracketen(minLon)+\
					' minlat='+bracketen(minLat)+\
					' maxlon='+bracketen(maxLon)+\
					' maxlat='+bracketen(maxLat);
		self.minLat = int(minLat*csd);
		self.maxLat = int(maxLat*csd);
		self.minLon = int(minLon*csd);
		self.maxLon = int(maxLon*csd);

		self.f.write(batchIndent(wrapOsm(name="bound",header=header))+"\n");
		self.Points = {};
		self.Ways = {};
		self.Relations = {};


	def create_new_nodes(self):
		dbh = DBHelper();
		dbh.execute("create or replace view new_nodes as (select * from current_nodes where "+\
			"latitude>="+str(self.minLat)+" and "\
			"latitude<="+str(self.maxLat)+" and "\
			"longitude>="+str(self.minLon)+" and "\
			"longitude<="+str(self.maxLon)+")", need_commit = True);
		raw = dbh.executeAndFetchAll("select * from new_nodes");
		for tp in raw:
			self.Points[tp[0]] = Point(id=tp[0],lat=tp[1],lon=tp[2],visible=tp[4],version=tp[7],changeset=tp[3],timestamp=tp[5])
		raw = dbh.executeAndFetchAll("select * from current_node_tags where node_id in (select id from new_nodes)");
		for tp in raw:
			self.Points[tp[0]].addTags(tp[1],tp[2]);
	def create_new_ways(self):
		dbh = DBHelper();
		dbh.execute("create or replace view new_way_nodes as "+\
			"(select * from current_way_nodes where node_id in (select id from new_nodes))", need_commit = True);
		raw = dbh.executeAndFetchAll("select * from current_ways where id in (select distinct id from new_way_nodes)");
		for tp in raw:
			self.Ways[tp[0]] = Way(id=tp[0],visible=tp[3],version=tp[4],changeset=tp[1],timestamp=tp[2]);
		raw = dbh.executeAndFetchAll("select * from new_way_nodes");
		for tp in raw:
			self.Ways[tp[0]].addNodes(tp[2],tp[1]);
		raw = dbh.executeAndFetchAll("select * from current_way_tags where way_id in (select distinct id from new_way_nodes)");
		for tp in raw:
			self.Ways[tp[0]].addTags(tp[1],tp[2]);

	def create_new_relations(self):
		from collections import deque;
		dbh = DBHelper();
		# dbh.execute("drop table if exists new_relation_members",need_commit=True);
		dbh.execute("create or replace view new_relation_members as "+\
			"(select * from current_relation_members where (member_type='Node' and member_id in (select id from new_nodes)) "+\
			"or (member_type='Way' and member_id in (select distinct id from new_way_nodes)))", need_commit = True);
		rf = OtherUtils.GetRelationFather();


		# must reclusively cover relations
		relation_child2father=[];
		raw = dbh.executeAndFetchAll("select distinct relation_id from new_relation_members");



		start_relations = deque([tp[0] for tp in raw]);
		start_visit = set([tp[0] for tp in raw])
		while (len(start_relations)>0):
			tmp = start_relations.popleft();
			if rf.has_key(tmp):
				for fa in rf[tmp]:
					if (fa not in start_visit):
						start_relations.append(fa);
						start_visit.add(fa);
						relation_child2father.append((tmp,fa));
		if len(relation_child2father)>0:
			dbh.execute("drop table if exists new_relation_fathers",need_commit=True);
			sql = \
			'''create table new_relation_fathers (
			relation_id bigint(64) NOT NULL ,
			father_id bigint(64) NOT NULL)
			'''
			dbh.execute(sql,need_commit=True);
			values = ""
			for pair in relation_child2father:
				values += ("(%d,%d)"%(int(pair[0]),int(pair[1]))) +","
			values = values[:-1];

			sql = \
			"insert into new_relation_fathers(relation_id,father_id) values " + values;
			dbh.execute(sql,need_commit=True);



		raw = dbh.executeAndFetchAll("select * from current_relations "+\
			"where relation_id in (select distinct relation_id from new_relation_members)"+\
			" or relation_id in (select distinct father_id from new_relation_fathers)");
		for tp in raw:
			self.Relations[tp[0]] = Relation(id=tp[0],visible=tp[3],version=tp[4],changeset=tp[1],timestamp=tp[2]);

		raw = dbh.executeAndFetchAll("select * from current_relation_tags "+\
			"where id in (select distinct relation_id from new_relation_members)"+\
			" or id in (select distinct father_id from new_relation_fathers)");
		for tp in raw:
			self.Relations[tp[0]].addTags(tp[1],tp[2]);

		raw = dbh.executeAndFetchAll("select * from new_relation_members");
		for tp in raw:
			self.Relations[tp[0]].addMembers(tp[4],tp[1],tp[2],tp[3]);
		raw = dbh.executeAndFetchAll("select a.relation_id, a.member_type, a.member_id, a.member_role, a.sequence_id from current_relation_members a, new_relation_fathers b where "+\
			"a.member_type='Relation' and a.member_id=b.relation_id and a.relation_id=b.father_id" );
		for tp in raw:
			self.Relations[tp[0]].addMembers(tp[4],tp[1],tp[2],tp[3]);



	def process(self):
		print ">>>>> create_new_nodes ..."
		self.create_new_nodes();
		for pointID in self.Points.keys():
			self.f.write(batchIndent(self.Points[pointID].translate()));
			self.f.write("\n");
		self.Points = {};
		gc.collect();


		print ">>>>> create_new_ways ..."
		self.create_new_ways();
		for wID in self.Ways.keys():
			self.f.write(batchIndent(self.Ways[wID].translate()));
			self.f.write("\n");
		self.Ways = {};
		gc.collect();


		print ">>>>> create_new_relations ..."
		self.create_new_relations();
		for rID in self.Relations.keys():
			self.f.write(batchIndent(self.Relations[rID].translate()));
			self.f.write("\n");
		self.Relations = {};
		gc.collect();

		self.f.write(OsmGenerator.Default_tailer);


	def commit(self):
		self.f.close();


if __name__ == '__main__':
	gen = OsmGenerator('a.osm',minLat=30.0040639, maxLat=30.9263716, minLon=118.6901586, maxLon=120.7920180)
	gen.process();
	gen.commit();
	