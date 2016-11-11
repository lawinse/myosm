# -*- coding:utf-8 -*-  
import sys,os
from Config import WORK_DIR
reload(sys)
sys.setdefaultencoding("utf-8")
import MySQLdb
import datetime


class DBHelper:
	DBC = None;
	LOGGER = [];
	LOG_CAP = -1
	START_AT = None
	@classmethod
	def Build(cls):
		cls.DBC = MySQLdb.connect(host="localhost",user="osm",passwd="osm",db="api06_test",charset='utf8');
		cls.LOGGER = [];
		cls.LOG_CAP = 30
		cls.START_AT = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	def __init__(self):
		try:
			self.cursor = DBHelper.DBC.cursor();
		except:
			DBHelper.Build()
			self.cursor = DBHelper.DBC.cursor();
	def __del__(self):
		self.cursor.close();
	def executeAndFetchAll(self, sql, params=None):
		if self.execute(sql,params):
			data = self.cursor.fetchall();
			return data;
		return None;
	def fetchNext(self,num=1):
		if num==1:
			data = self.cursor.fetchone();
		else:
			data = self.cursor.fetchmany(num);
		return data;
	def commit(self):
		try:
			DBHelper.DBC.commit();
		except:
			DBHelper.DBC.rollback();
			DBHelper.PrintLog();
			DBHelper.DumpLog();
	def execute(self, sql, params=None, need_commit=False):
		DBHelper.LOGGER.append(sql+(("  params:"+str(params)) if params != None else ""));
		if need_commit:
			try:
				self.cursor.execute(sql) if params == None else self.cursor.execute(sql,params);
				DBHelper.DBC.commit();
				status = 'Successful'
			except:
				DBHelper.PrintLog();
				DBHelper.DBC.rollback();
				status = 'Failed'
		else:
			try:
				self.cursor.execute(sql) if params == None else self.cursor.execute(sql,params);
				status = 'Successful'
			except:
				DBHelper.PrintLog();
				status = 'Failed'
		DBHelper.LOGGER[-1] = "["+status+"] "+DBHelper.LOGGER[-1];
		if (len(DBHelper.LOGGER) >= DBHelper.LOG_CAP or status == "Failed"):
			DBHelper.DumpLog()
		return status == 'Successful'
	def batchExecute(self, sqls):
		for i in range(len(sqls)-1):
			self.execute(sqls[i]);
		self.execute(sqls[-1],need_commit=True);
	@classmethod
	def PrintLog(cls,num = 10):
		print "\n###### Query Log #######"
		cnt = num;
		i = len(DBHelper.LOGGER)-1;
		while(i>=0 and cnt > 0):
			print DBHelper.LOGGER[i];
			i-=1;
			cnt-=1;
		print "#########\n"
	@classmethod
	def DumpLog(cls):
		if not os.path.exists(WORK_DIR+"log"): os.mkdir(WORK_DIR+"log")
		mode = 'w+' if not os.path.exists(WORK_DIR+"log/sqlquery"+cls.START_AT+".log") else "a";
		f = open(WORK_DIR+"log/sqlquery"+cls.START_AT+".log",mode);
		l = len(cls.LOGGER);
		if l > 10: l-=10;
		for line in cls.LOGGER[:l]:
			f.write('>  '+line+'\n');
		f.close()
		cls.LOGGER = cls.LOGGER[l:]
		

		

if __name__ == '__main__':
	dbh = DBHelper();
	print len(dbh.executeAndFetchAll("select * from current_nodes where id=-1"))
	# for i in range(100):
	# 	dbh.executeAndFetchAll("select * from current_nodes where id=%s",params=(26609107+i,));
	# poi1 = '酒店'.decode('utf8')
	# poi2 = '加油加气站'.decode('utf8')
	# num=5
	# coord = [31.1977664,121.4147976]
	# raw = dbh.executeAndFetchAll(\
	# "select * from "
	# "(select p1.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi1+"') as p1 left join current_nodes on p1.node_id=current_nodes.id) as v1, "+\
	# "(select p2.node_id,current_nodes.latitude,current_nodes.longitude from (select distinct node_id from current_node_tags where k='poitype' and v='"+poi2+"') as p2 left join current_nodes on p2.node_id=current_nodes.id) as v2 "+\
	# "order by sqrt(pow(v1.latitude/1e7-v2.latitude/1e7,2)+pow(v1.longitude/1e7-v2.longitude/1e7,2)) + sqrt(least(pow(v1.latitude/1e7-"+str(coord[0])+",2)+pow(v1.longitude/1e7-"+str(coord[1])+",2), pow(v2.latitude/1e7-"+str(coord[0])+",2)+pow(v2.longitude/1e7-"+str(coord[1])+",2))) "+\
	# "limit 0,"+str(num))
	# print raw
	# print dbh.executeAndFetchAll("select id from current_way_nodes where node_id=28111345");
	# a = "金融".decode('utf8');
	# print [a]
	# print dbh.executeAndFetchAll("select distinct v from current_node_tags where k='poitype' and v='"+a+"'");

