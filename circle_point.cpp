#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <ctime>
using namespace std;
#define PI 3.14159265358979323846
#define R 6370996.81

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

int sample(int &num, double *px, double *py, int rough_base=10000) {
	if (num<rough_base*1.5) return 1;
	srand(time(0));
	int thed = int(round(num*1.0/rough_base));
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

extern "C"{
	double* solve(double r, int num, double *px, double *py, bool precise){
		int n = num, thed = 1;
		if (!precise) thed = sample(n,px,py);
		Point * p = new Point[2*n+10];
		double *ret = new double[3];
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
		return ret;
	}

}