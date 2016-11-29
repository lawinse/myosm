import os,sys

if 'www' in os.getcwd().lower():
	WORK_DIR = "./app/myosm/"
	sys.path.append(WORK_DIR)
	DRAW_DIR = "./app/static/maps/"
else:
	WORK_DIR = "./"
	DRAW_DIR = "./"
LAZY_START = True