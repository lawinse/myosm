# -*- coding:utf-8 -*- 
import gensim
from gensim import corpora
import math
import jieba
from DBHelper import *
from sklearn.externals import joblib
import os


if not os.path.exists("./data"):
	os.mkdir("./data")

class BM_25:
	BM_MDL_ND = None;
	BM_MDL_WAY = None;
	# MDL: [N,DocAvglen,Doc2DocTF_id,DocTF,DocIDF,Dic]
	@classmethod
	def Build(cls, typ):
		if typ == 'Node' and BM_25.BM_MDL_ND != None: return
		if typ == 'Way' and BM_25.BM_MDL_WAY != None: return 
		if not os.path.exists("./data/BM_25_"+typ+".mdl"):
			from Utils import NodeNameUtils, WayNameUtils
			print ">>>>> Building BM_25 Model ..."
			dbh = DBHelper();
			raw = dbh.executeAndFetchAll("select distinct v from current_"+typ.lower()+"_tags where k='name'");
			nameSet = set([NodeNameUtils.cleanName(tp[0]) for tp in raw]);
			Dic = corpora.Dictionary();
			rawdata = []
			docTtlLen = 0;
			N = len(nameSet)
			print N
			DF = {}
			DocTF = [0 for i in range(N)]
			DocIDF = {}
			Doc2DocTF_id = {}
			cnt=0
			for name in nameSet:
				seg = " ".join(jieba.cut(name));
				rawdata.append(seg.strip().split());
			Dic.add_documents(raw);

			for name in nameSet:
				seg = " ".join(jieba.cut(name));
				doc = seg.strip().split()
				docTtlLen += len(doc)
				bow = dict([(term, freq*1.0/len(doc)) for term, freq in Dic.doc2bow(doc)])
				for term, tf in bow.items():
					if DF.has_key(term):
						DF[term] += 1;
					else: 
						DF[term] = 1
				DocTF[cnt] = bow
				Doc2DocTF_id[seg.strip()] = cnt
				cnt += 1
			for term in DF:
				DocIDF[term] = math.log((N - DF[term] +0.5) / (DF[term] + 0.5), math.e)
			DocAvglen = docTtlLen/N;
			mdl = [N,DocAvglen,Doc2DocTF_id,DocTF,DocIDF,Dic];
			joblib.dump(mdl, "./data/BM_25_"+typ+".mdl", compress=3)
			if typ == "Node":
				BM_25.BM_MDL_ND = mdl;
			else:
				BM_25.BM_MDL_WAY = mdl;
		else:
			print ">>>>> Loading BM_25 Model ..."
			if typ == "Node":
				BM_25.BM_MDL_ND = joblib.load("./data/BM_25_"+typ+".mdl");
			else:
				BM_25.BM_MDL_WAY = joblib.load("./data/BM_25_"+typ+".mdl");
		print ">>>>> Done Initialization"
	def __init__(self, typ):
		assert(typ in ['Node','Way'])
		BM_25.Build(typ);
		self.typ = typ;
	def score(self, query, candidates, k1=1.2, b=0.75):
		N,DocAvglen,Doc2DocTF_id,DocTF,DocIDF,Dic = (BM_25.BM_MDL_ND if self.typ=='Node' else BM_25.BM_MDL_WAY);
		# print " ".join(jieba.cut(query, cut_all=True))
		q_bow = Dic.doc2bow(" ".join(jieba.cut(query)).split());
		scores = [0 for i in range(len(candidates))];
		for i in range(len(candidates)):
			can = (" ".join(jieba.cut(candidates[i]))).strip();
			doc_terms_len = len(can.split())
			tfid = Doc2DocTF_id[can];
			# print "tfid", tfid
			doc = DocTF[tfid];
			common = set(dict(q_bow).keys()) & set(doc.keys())
			tmp_score = []
			# print "common", common
			for term in common:
				nu = (doc[term]*(k1+1));
				de = ((doc[term]) + k1*(1 - b + b*doc_terms_len/DocAvglen))
				tmp_score.append(DocIDF[term]*nu/de);
			# print sum(tmp_score)
			scores[i] = sum(tmp_score);
		return scores;

if __name__ == '__main__':
	nodeBm = BM_25(typ='Node');
	wayBm = BM_25(typ='Way');
	
			



