#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <thread>
#include <cstring>
#include <queue>
using namespace std;
#define PI 3.14159265358979323846
#define R 6370996.81
#define ROUGH_BASE 10000

struct Point{
	int id;
    double angle;
    double t_angle;
    bool operator < (const Point& a)const{
        return angle!=a.angle?angle<a.angle:id>a.id;
    }
};

double lw(double a, double b, double c){
	a = fmax(a,b);
	a = fmin(a,c);
	return a;
}

double ew(double a, double b, double c){
	while(a>c) a-= (c-b);
	while(a<b) a+= (c-b);
	return a;
}

inline double oi(double a){
	return PI*a/180;
}

inline double io(double a){
	return a*180/PI;
}
inline double Td(double a, double b, double c, double d){
	return R * acos(sin(c) * sin(d) + cos(c) * cos(d) * cos(b - a));
}

inline double dist(double x1, double y1, double x2, double y2) {
    // y1 = ew(y1,-180,180);
    // x1 = lw(x1,-74,74);
    // y2 = ew(y2,-180,180);
    // x2 = lw(x2,-74,74);
    return Td(oi(y1),oi(y2),oi(x1),oi(x2));
}

inline double order_dist_part(double x, double y, double x1, double y1, double x2, double y2, bool order_sensitive){
	return order_sensitive 
			? dist(x,y,x1,y1)
			: fmin(dist(x,y,x2,y2),dist(x,y,x1,y1)); 
}

inline double order_dist(double x, double y, double x1, double y1, double x2, double y2, bool order_sensitive){
	return dist(x1,y1,x2,y2) + order_dist_part(x,y,x1,y1,x2,y2,order_sensitive);
}

int sample(int id, int &num, double *px, double *py) {
	if (num<ROUGH_BASE*1.5) return 1;
	srand(time(0)*(id+1));
	int thed = int(round(num*1.0/ROUGH_BASE));
	int cnt = 0;
	for (int i=0; i<num; ++i) {
		if (rand()%thed == 0){
			px[cnt] = px[i];
			py[cnt++] = py[i];
		}
	}
	printf(">>>>> Random downsampling from %d to %d\n",num,cnt );
	num = cnt;
	return thed;
}

void _solve_circle_point(int id, double r, int num, double *px, double *py,double *ret,bool precise){
		int n = num, thed = 1;
		if (!precise) thed = sample(id,n,px,py);
		Point * p = new Point[2*n+10];
		// double *ret = new double[3];
		ret[0] = ret[1] = ret[2] = -1;
		int ans = 1, ans_id = -1;
		double ans_x = -1,ans_y = -1;
		int i,j,k,tot;
		for (i=0; i<n; ++i){
			for (j=k=0; j<n; ++j) {
				if (j == i || dist(px[i],py[i],px[j],py[j]) > (2*r)) continue;
				double angle = atan2(py[i]-py[j],px[i]-px[j]);
				double phi = acos(dist(px[i],py[i],px[j],py[j])/(2*r));
				p[k].angle = angle-phi;p[k].t_angle = atan2(py[j]-py[i],px[j]-px[i])-phi; p[k++].id=1;
				p[k].angle = angle+phi;p[k].t_angle = atan2(py[j]-py[i],px[j]-px[i])+phi; p[k++].id=-1;
			}
			sort(p,p+k);
			for (tot=1,j=0;j<k;++j){
				tot += p[j].id;
				if (tot > ans) {
					ans = tot;
					ans_id = i;
					ans_x = px[i] + io(r*cos(p[j].t_angle)/R);   // maybe a little bit errors but can be tolerated
					ans_y = py[i] + io(r*sin(p[j].t_angle)/R);
				}
			}
		}
		if (ans_id != -1) {
			ret[0] = ans*thed;
			ret[1] = ans_x;
			ret[2] = ans_y;
		}
		delete []p;
		return;
	}

extern "C"{
	double* solve_circle_point(double r, int num, double *px, double *py, bool precise){
		double *ret = new double[3];
		if (num > ROUGH_BASE*1.5 && !precise) {
			const int REPEAT = 4;
			printf(">>>>> %d works concurrently ...\n",REPEAT);
			thread t[REPEAT];
			double ** Px = new double *[REPEAT];
			double ** Py = new double *[REPEAT];
			double Ret[REPEAT][3];
			for (int i=0; i<REPEAT; ++i) {
				Px[i] = new double [num];
				Py[i] = new double [num];
				memcpy(Px[i],px,sizeof(double)*num);
				memcpy(Py[i],py,sizeof(double)*num);
				t[i] = thread(_solve_circle_point,i,r,num,Px[i],Py[i],Ret[i],precise);
			}
			for (int i=0; i<REPEAT; ++i){
				t[i].join();
			}

			ret[0] = ret[1] = ret[2] = 0;
			for (int i=0; i<REPEAT; ++i) {
				ret[0] += Ret[i][0];
				ret[1] += Ret[i][1];
				ret[2] += Ret[i][2];
			}
			ret[0] /= REPEAT;
			ret[1] /= REPEAT;
			ret[2] /= REPEAT;
		} else {
			_solve_circle_point(0,r,num,px,py,ret,precise);
		}

		return ret;
	}

	int solve_poi_pair(int n1, int *id1, double *x1, double *y1, 
		int n2, int*id2, double *x2, double *y2, 
		double x, double y, int k, bool order_sensitive,
		int *idret1, double * xret1, double *yret1, int* idret2, double *xret2, double *yret2, double* disret){

		// printf("%f %f\n", x,y);

        auto comp = [x,y,x1,y1,x2,y2,order_sensitive](pair<int, int> a, pair<int, int> b) {

        	double dis_a = order_dist(x,y,x1[a.first],y1[a.first],x2[a.second],y2[a.second],order_sensitive);
        	double dis_b = order_dist(x,y,x1[b.first],y1[b.first],x2[b.second],y2[b.second],order_sensitive);

            return dis_a < dis_b;};
        priority_queue<pair<int, int>, vector<pair<int, int>>, decltype(comp)> min_heap(comp);
        int i,j;
        for (i=0; i<n1; ++i) {
        	for (j=0; j<n2; ++j) {

	        	if (min_heap.size() < k) min_heap.emplace(i,j);
	        	else {
	        		pair<int,int> cur_p = min_heap.top();
	        		double cur_max_dis = order_dist(x,y,x1[cur_p.first],y1[cur_p.first],x2[cur_p.second],y2[cur_p.second],order_sensitive);
	        		double new_dis = order_dist(x,y,x1[i],y1[i],x2[j],y2[j],order_sensitive);
	        		// if (new_dis < 100) {
	        		// 	printf("%f\n", new_dis);
	        		// }
	        		if (new_dis < cur_max_dis) {
	        			min_heap.pop();
	        			min_heap.emplace(i,j);
	        		} else if (order_dist_part(x,y,x1[i],y1[i],x2[j],y2[j],order_sensitive) > cur_max_dis) {
	        			continue;
	        		}

	        	}
	        }

        }

        for (i=k-1;i>=0;--i){
        	pair<int,int> cur_p = min_heap.top(); min_heap.pop();
        	int a = cur_p.first;
        	int b = cur_p.second;
        	idret1[i] = id1[a];
        	idret2[i] = id2[b];
        	xret1[i] = x1[a];
        	yret1[i] = y1[a];
        	xret2[i] = x2[b];
        	yret2[i] = y2[b];
        	disret[i] = order_dist(x,y,x1[a],y1[a],x2[b],y2[b],order_sensitive);
        }




        return 0;
        
	}

}