import threading


def fun(li):
	global a
	li = []
	li.append(4);

	a.append(5);

def main():
	global a;
	a = []
	t = threading.Thread(target=fun,args = (a,))
	t.start();
	print len(a)
	print a;


if __name__ == '__main__':
	main()