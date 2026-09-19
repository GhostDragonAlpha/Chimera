#pragma once
#include "earth_environment.hpp"
#include <map>
namespace chimera::multibody {
using namespace chimera::environment;
using Dense=std::vector<double>;
using chimera::forces::Refusal;
struct Mat {
 std::array<double,16> x{};
 double& operator()(int i,int j){return x[4*i+j];} double operator()(int i,int j)const{return x[4*i+j];}
 static Mat identity(){Mat m;for(int i=0;i<4;++i)m(i,i)=1;return m;}
};
inline Mat operator+(Mat a,const Mat& b){for(int i=0;i<16;++i)a.x[i]+=b.x[i];return a;}
inline Mat operator*(const Mat& a,const Mat& b){Mat c;for(int i=0;i<4;++i)for(int k=0;k<4;++k)for(int j=0;j<4;++j)c(i,j)+=a(i,k)*b(k,j);return c;}
inline Mat operator*(Mat a,double b){for(double& x:a.x)x*=b;return a;}
inline Mat transpose(const Mat& a){Mat b;for(int i=0;i<4;++i)for(int j=0;j<4;++j)b(i,j)=a(j,i);return b;}
inline V vector(const Mat& a,V b,double w=0){V c{};for(int i=0;i<3;++i){c[i]=a(i,3)*w;for(int j=0;j<3;++j)c[i]+=a(i,j)*b[j];}return c;}
inline Mat skew(V a){Mat b;b(0,1)=-a[2];b(0,2)=a[1];b(1,0)=a[2];b(1,2)=-a[0];b(2,0)=-a[1];b(2,1)=a[0];return b;}
inline V axial(const Mat& a){return {(a(2,1)-a(1,2))/2,(a(0,2)-a(2,0))/2,(a(1,0)-a(0,1))/2};}
inline Mat rotation(V a,double v){require(std::abs(norm(a)-1)<1e-6,"coupled_axis_not_unit");auto k=skew(a);return Mat::identity()+k*std::sin(v)+(k*k)*(1-std::cos(v));}
inline Mat frame(V p,V q){Mat a=Mat::identity();for(int i=0;i<3;++i){V axis{};axis[i]=1;a=a*rotation(axis,q[i]);}for(int i=0;i<3;++i)a(i,3)=p[i];return a;}
inline Mat inverse_rigid(const Mat& a){Mat b=Mat::identity();for(int i=0;i<3;++i){for(int j=0;j<3;++j)b(i,j)=a(j,i);b(i,3)=-dot(V{b(i,0),b(i,1),b(i,2)},V{a(0,3),a(1,3),a(2,3)});}return b;}
inline Dense multiply(const Dense& a,const Dense& v){size_t n=v.size();require(a.size()==n*n,"coupled_matrix_size");Dense out(n);for(size_t i=0;i<n;++i)for(size_t j=0;j<n;++j)out[i]+=a[i*n+j]*v[j];return out;}
inline double inner(const Dense& a,const Dense& b){require(a.size()==b.size(),"coupled_vector_size");double v=0;for(size_t i=0;i<a.size();++i)v+=a[i]*b[i];return v;}
inline Dense inverse_spd(const Dense& a,size_t n){
 require(a.size()==n*n&&n>0,"coupled_matrix_size");Dense l(n*n),inv(n*n);
 for(size_t i=0;i<n;++i)for(size_t j=0;j<=i;++j){double t=a[i*n+j];require(std::isfinite(t)&&std::abs(t-a[j*n+i])<1e-12,"coupled_mass_not_symmetric");for(size_t k=0;k<j;++k)t-=l[i*n+k]*l[j*n+k];if(i==j){require(t>0,"coupled_singular_mass");l[i*n+j]=std::sqrt(t);}else l[i*n+j]=t/l[j*n+j];}
 for(size_t col=0;col<n;++col){Dense y(n),x(n);for(size_t i=0;i<n;++i){double t=i==col?1.:0.;for(size_t k=0;k<i;++k)t-=l[i*n+k]*y[k];y[i]=t/l[i*n+i];}for(size_t ii=n;ii-->0;){double t=y[ii];for(size_t k=ii+1;k<n;++k)t-=l[k*n+ii]*x[k];x[ii]=t/l[ii*n+ii];inv[ii*n+col]=x[ii];}}
 double an=0,bn=0;for(size_t i=0;i<n;++i){double ar=0,br=0;for(size_t j=0;j<n;++j){ar+=std::abs(a[i*n+j]);br+=std::abs(inv[i*n+j]);}an=(std::max)(an,ar);bn=(std::max)(bn,br);}require(std::isfinite(an*bn)&&an*bn<1e12,"coupled_ill_conditioned_mass");return inv;
}
struct Transform {Mat t=Mat::identity(),dt{},ddt{};std::vector<Mat> d;explicit Transform(size_t n=0):d(n){};};
inline Transform fixed(Mat t,size_t n){Transform x(n);x.t=t;return x;}
inline Transform product(const Transform& a,const Transform& b){Transform c(a.d.size());c.t=a.t*b.t;c.dt=a.dt*b.t+a.t*b.dt;c.ddt=a.ddt*b.t+(a.dt*b.dt)*2+a.t*b.ddt;for(size_t i=0;i<c.d.size();++i)c.d[i]=a.d[i]*b.t+a.t*b.d[i];return c;}
struct Evaluation {
 Dense mass,gravity,bias;double potential=0;std::vector<Transform> frames;
 std::pair<V,std::vector<V>> point(size_t body,V p)const{auto& f=frames.at(body);std::vector<V> j;for(auto& d:f.d)j.push_back(vector(d,p,1));return {vector(f.t,p,1),j};}
 Dense force(size_t body,V p,V f)const{auto j=point(body,p).second;Dense result;for(auto v:j)result.push_back(dot(v,f));return result;}
 Dense acceleration(Dense tau)const{for(size_t i=0;i<tau.size();++i)tau[i]+=gravity[i]-bias[i];return multiply(inverse_spd(mass,tau.size()),tau);}
};
class Model {
 struct Axis {bool rotational;V axis;int slot;double slope,constant;};
 struct Body {std::string name;int parent=-1;double mass;V com;Mat inertia,fp,fc;std::vector<Axis> axes;};
 std::vector<Body> bodies_;
public:
 std::vector<std::string> names;Dense defaults,lower,upper;
 explicit Model(const J& model,std::vector<std::string> selected={}){
  require(model.at("schema")=="chimera.anatomical_assembly.v1","coupled_anatomy_schema");auto coords=model.at("coordinates");if(selected.empty())for(auto it=coords.begin();it!=coords.end();++it)if(!it.value().at("locked").get<bool>())selected.push_back(it.key());
  std::set<std::string> seen;for(auto name:selected){require(coords.contains(name)&&seen.insert(name).second&&!coords[name]["locked"].get<bool>(),"coupled_coordinate_selection");names.push_back(name);defaults.push_back(number(coords[name]["default_rad"]));lower.push_back(number(coords[name]["range_rad"][0]));upper.push_back(number(coords[name]["range_rad"][1]));require(lower.back()<upper.back()&&defaults.back()>=lower.back()&&defaults.back()<=upper.back(),"coupled_coordinate_range");}
  // Capacity (packet AMENDMENT 20260918 E1, extended 20260919 by the gait lane
  // -- docs/research/20260918_gait_controller_derivation.md stage D, same
  // one-token validation pattern): 16 = 2x the free-root eight-coordinate
  // selection, sized for the 14-coordinate gait walker (6-axis base + 4
  // hindlimb drives x 2 legs). Integer VALIDATION only -- no arithmetic line
  // moves; every selection <= 8 evaluates BIT-IDENTICALLY (the frozen
  // qualified/free worlds are unaffected by construction; all committed native
  // suites re-run green on this tree, gait_impl_20260919 receipt).
  require(!names.empty()&&names.size()<=16,"coupled_coordinate_capacity");std::map<std::string,J> remaining;for(auto b:model.at("bodies")){std::string name=b.at("name");require(remaining.emplace(name,b).second,"coupled_duplicate_body");}std::map<std::string,int> ids;
  while(!remaining.empty()){bool progress=false;for(auto it=remaining.begin();it!=remaining.end();){auto b=it->second;bool ground=it->first=="ground";if(!ground&&!ids.count(b.at("joint").at("parent").get<std::string>())){++it;continue;}
   Body out;out.name=it->first;out.mass=number(b.at("mass_kg"));out.com=b.at("mass_center_m").get<V>();require(out.mass>=0,"coupled_mass_negative");for(double v:out.com)require(std::isfinite(v),"coupled_com_nonfinite");auto ic=b.at("inertia_kg_m2");require(ic.size()==6,"coupled_inertia_shape");for(int i=0;i<3;++i)out.inertia(i,i)=number(ic[i]);out.inertia(0,1)=out.inertia(1,0)=number(ic[3]);out.inertia(0,2)=out.inertia(2,0)=number(ic[4]);out.inertia(1,2)=out.inertia(2,1)=number(ic[5]);
   // Source compiler performs full tensor physicality; preserve admitted values, including regularization mass.
   if(ground){require(b.at("joint").is_null(),"coupled_ground_joint");out.fp=out.fc=Mat::identity();}else{auto j=b.at("joint");out.parent=ids.at(j.at("parent").get<std::string>());out.fp=frame(j.at("parent_location_m").get<V>(),j.at("parent_orientation_rad").get<V>());out.fc=inverse_rigid(frame(j.at("child_location_m").get<V>(),j.at("child_orientation_rad").get<V>()));
    for(auto ax:j.at("axes")){std::string kind=ax.at("name"),coordinate=ax.at("coordinate"),type=ax.at("function").at("type");auto c=ax.at("function").at("coefficients");require(type=="Constant"||type=="LinearFunction","coupled_transform_function");Axis a;a.rotational=kind.rfind("rotation",0)==0;require(a.rotational||kind.rfind("translation",0)==0,"coupled_transform_axis");a.axis=ax.at("axis").get<V>();a.slot=-1;a.slope=0;a.constant=number(c[0]);if(type=="LinearFunction"){require(c.size()==2&&coords.contains(coordinate),"coupled_transform_coordinate");auto found=std::find(names.begin(),names.end(),coordinate);if(found!=names.end()){a.slot=int(found-names.begin());a.slope=number(c[0]);a.constant=number(c[1]);}else a.constant=number(c[0])*number(coords[coordinate]["default_rad"])+number(c[1]);}out.axes.push_back(a);}
   }
   ids[out.name]=int(bodies_.size());bodies_.push_back(out);it=remaining.erase(it);progress=true;
  }require(progress,"coupled_missing_or_cyclic_parent");}
 }
 size_t body(const std::string& name)const{for(size_t i=0;i<bodies_.size();++i)if(bodies_[i].name==name)return i;throw Refusal("coupled_body_missing");}
 Evaluation evaluate(const Dense& q,const Dense& v,V gravity)const{
  size_t n=names.size();require(q.size()==n&&v.size()==n,"coupled_state_shape");for(double x:q)require(std::isfinite(x),"coupled_state_nonfinite");for(double x:v)require(std::isfinite(x),"coupled_state_nonfinite");Evaluation e;e.mass.assign(n*n,0);e.gravity.assign(n,0);e.bias.assign(n,0);
  for(auto& b:bodies_){Transform f(n);if(b.parent>=0){Transform motion(n);V translation{},velocity{};std::vector<V> dj(n);
    for(auto& a:b.axes){double angle=a.constant+(a.slot<0?0:a.slope*q[a.slot]),rate=a.slot<0?0:a.slope*v[a.slot];if(a.rotational){Transform one(n);one.t=rotation(a.axis,angle);auto dr=skew(a.axis)*one.t;if(a.slot>=0)one.d[a.slot]=dr*a.slope;one.dt=dr*rate;one.ddt=skew(a.axis)*dr*(rate*rate);motion=product(motion,one);}else{translation=add(translation,mul(a.axis,angle));velocity=add(velocity,mul(a.axis,rate));if(a.slot>=0)dj[a.slot]=add(dj[a.slot],mul(a.axis,a.slope));}}
    for(int k=0;k<3;++k){motion.t(k,3)=translation[k];motion.dt(k,3)=velocity[k];for(size_t i=0;i<n;++i)motion.d[i](k,3)=dj[i][k];}f=product(product(product(e.frames[b.parent],fixed(b.fp,n)),motion),fixed(b.fc,n));
   }e.frames.push_back(f);Mat rt;for(int i=0;i<3;++i)for(int j=0;j<3;++j)rt(i,j)=f.t(j,i);Mat iw=f.t*b.inertia*rt;V p=vector(f.t,b.com,1),acc=vector(f.ddt,b.com,1),omega=axial(f.dt*rt),alpha=axial(f.ddt*rt+f.dt*transpose(f.dt));std::vector<V> jv,jw;for(auto& d:f.d){jv.push_back(vector(d,b.com,1));jw.push_back(axial(d*rt));}V moment=add(vector(iw,alpha),cross(omega,vector(iw,omega)));
   for(size_t i=0;i<n;++i){e.gravity[i]+=b.mass*dot(jv[i],gravity);e.bias[i]+=b.mass*dot(jv[i],acc)+dot(jw[i],moment);for(size_t j=0;j<n;++j)e.mass[n*i+j]+=b.mass*dot(jv[i],jv[j])+dot(jw[i],vector(iw,jw[j]));}e.potential-=b.mass*dot(gravity,p);
  }return e;
 }
};
} // namespace chimera::multibody
