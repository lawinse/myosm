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
	print dbh.executeAndFetchAll("select * from current_relation_members limit 0,10");
	# print dbh.executeAndFetchAll("select id from current_way_nodes where node_id=28111345");
	# a = "金融".decode('utf8');
	# print [a]
	# print dbh.executeAndFetchAll("select distinct v from current_node_tags where k='poitype' and v='"+a+"'");

