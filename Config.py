import os,sys

if 'www' in os.getcwd().lower():
	WORK_DIR = "./app/myosm/"
	sys.path.append(WORK_DIR)
else:
	WORK_DIR = "./"
LAZY_START = True