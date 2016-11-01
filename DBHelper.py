# -*- coding:utf-8 -*-  
import sys,os
reload(sys)
sys.setdefaultencoding("utf-8")
import MySQLdb


class DBHelper:
	DBC = MySQLdb.connect(host="localhost",user="osm",passwd="osm",db="api06_test",charset='utf8');
	LOGGER = [];
	def __init__(self):
		self.cursor = DBHelper.DBC.cursor();
	def executeAndFetchAll(self, sql):
		self.execute(sql);
		data = self.cursor.fetchall();
		return data;
	def fetchNext(self,num=1):
		if num==1:
			data = self.cursor.fetchone();
		else:
			data = self.cursor.fetchmany(num);
		return data;
	def execute(self, sql, need_commit=False):
		DBHelper.LOGGER.append(sql);
		if need_commit:
			try:
				self.cursor.execute(sql);
				DBHelper.DBC.commit();
			except:
				DBHelper.PrintLog();
				DBHelper.DBC.rollback();
				
		else:
			try:
				self.cursor.execute(sql);
			except:
				DBHelper.PrintLog();
	@classmethod
	def PrintLog(cls,num = 10):
		print "\n\n###### Query Log #######"
		cnt = num;
		i = len(DBHelper.LOGGER)-1;
		while(i>=0 and cnt > 0):
			print DBHelper.LOGGER[i];
			i-=1;
			cnt-=1;
		print "#########\n\n"
		

		

if __name__ == '__main__':
	dbh = DBHelper();
	# print dbh.executeAndFetchAll("select * from current_relation_members limit 0,10");
	poi1 = '酒店'.decode('utf8')
	poi2 = '加油加气站'.decode('utf8')
	num=5
	coord = [31.1977664,121.4147976]
	raw = dbh.executeAndFetchAll(\
	"select * from "
	"(select p1.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi1+"') as p1 left join current_nodes on p1.node_id=current_nodes.id) as v1, "+\
	"(select p2.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi2+"') as p2 left join current_nodes on p2.node_id=current_nodes.id) as v2 "+\
	"order by sqrt(pow(v1.latitude/1e7-v2.latitude/1e7,2)+pow(v1.longitude/1e7-v2.longitude/1e7,2)) + sqrt(least(pow(v1.latitude/1e7-"+str(coord[0])+",2)+pow(v1.longitude/1e7-"+str(coord[1])+",2), pow(v2.latitude/1e7-"+str(coord[0])+",2)+pow(v2.longitude/1e7-"+str(coord[1])+",2))) "+\
	"limit 0,"+str(num))
	print raw
	# print dbh.executeAndFetchAll("select id from current_way_nodes where node_id=28111345");
	# a = "金融".decode('utf8');
	# print [a]
	# print dbh.executeAndFetchAll("select distinct v from current_node_tags where k='poitype' and v='"+a+"'");

