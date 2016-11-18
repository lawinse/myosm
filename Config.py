import os

WORK_DIR = "./app/myosm/" if 'www' in os.getcwd().lower() else "./"
LAZY_START = True