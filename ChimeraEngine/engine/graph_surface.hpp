#pragma once
// Graph-compiled quasistatic surface. Coordinates and forces are SI.
// U = gamma * sum(triangle area) + F * sum(probe_weight * height).
// Runtime has no Python and no scripted vertex pose.
#include "../native/viewer3rd/json.hpp"
#include <array>
#include <vector>
#include <cmath>
#include <fstream>
#include <stdexcept>
#include <algorithm>
#include <numeric>
class GraphSurface {
public:
    using J=nlohmann::json; using V=std::array<double,3>;
    struct Face { std::array<int,3> v; V c; std::array<V,3> d; };
    J spec; std::vector<V> rest; std::vector<Face> faces; std::vector<double> h,w;
    std::vector<bool> pinned; V normal{},translation{}; double gamma=0,force=0,energy=0,residual=0;
    double reaction=0,scale=100; unsigned iterations=0,revision=0,render_revision=0;
    bool active=false,converged=false; std::string material,error;
    static V add(V a,V b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
    static V sub(V a,V b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
    static V mul(V a,double s){return {a[0]*s,a[1]*s,a[2]*s};}
    static double dot(V a,V b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
    static V cross(V a,V b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
    static void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
    void load(const std::string& path){
        std::ifstream f(path); need(bool(f),"surface scene missing"); f>>spec;
        need(spec.at("schema")=="chimera.surface.v1","surface schema");
        rest=spec.at("vertices_m").get<std::vector<V>>();
        need(rest.size()>=9&&rest.size()<=4096,"surface vertex bounds");
        normal=spec.at("normal").get<V>(); need(std::abs(dot(normal,normal)-1)<1e-9,"surface normal");
        for(auto p:rest)for(double x:p)need(std::isfinite(x),"nonfinite vertex");
        h.assign(rest.size(),0); pinned.assign(rest.size(),false);
        for(int i:spec.at("pinned")){need(i>=0&&size_t(i)<h.size(),"pin index");pinned[i]=true;}
        need(std::count(pinned.begin(),pinned.end(),true)>=3,"surface boundary missing");
        w=spec.at("probe_weights").get<std::vector<double>>();
        need(w.size()==h.size(),"probe layout"); double sum=0;
        for(size_t i=0;i<w.size();++i){need(std::isfinite(w[i])&&w[i]>=0&&(!pinned[i]||w[i]==0),"probe weight");sum+=w[i];}
        need(std::abs(sum-1)<1e-9,"probe normalization");
        faces.clear();
        for(auto raw:spec.at("triangles")){
            Face t; t.v=raw.get<std::array<int,3>>();
            for(int i:t.v)need(i>=0&&size_t(i)<h.size(),"triangle index");
            auto a=rest[t.v[0]],b=rest[t.v[1]],c=rest[t.v[2]];
            t.c=cross(sub(b,a),sub(c,a));need(dot(t.c,normal)>1e-16,"triangle winding/area");
            t.d={cross(normal,sub(b,c)),cross(normal,sub(c,a)),cross(normal,sub(a,b))};faces.push_back(t);
        }
        need(faces.size()<=8192&&!faces.empty(),"face bounds");
        scale=spec.at("render_m_to_units");need(std::isfinite(scale)&&scale>0,"render scale");
        translation=spec.at("render_translation_units").get<V>();
        for(double x:translation)need(std::isfinite(x),"render translation");
        active=true; material=spec.at("materials").at(0).at("name");
        control(J{{"material",material},{"force_N",spec.at("default_force_N")}});
    }
    void control(const J& j){
        need(active,"surface not loaded"); need(j.is_object(),"control object");
        for(auto it=j.begin();it!=j.end();++it)need(it.key()=="force_N"||it.key()=="material"||it.key()=="reset","unknown surface control");
        auto nextmat=j.value("material",material);double nextgamma=0;
        for(auto m:spec.at("materials"))if(m.at("name")==nextmat)nextgamma=m.at("gamma_N_m");
        need(std::isfinite(nextgamma)&&nextgamma>0,"material not compiled");
        double nextforce=j.value("force_N",force);
        need(std::isfinite(nextforce)&&nextforce>=0&&nextforce<=spec.at("max_force_N").get<double>(),"force out of compiled bounds");
        bool reset=j.value("reset",false);
        material=nextmat;gamma=nextgamma;force=nextforce;
        if(reset){std::fill(h.begin(),h.end(),0);force=0;}
        converged=false;error.clear();iterations=0;++revision;refresh();
    }
    double eval(const std::vector<double>& x,std::vector<double>* grad=nullptr,
                std::vector<std::array<double,9>>* H=nullptr)const{
        if(grad)grad->assign(h.size(),0);if(H)H->clear();double E=0;
        for(auto& t:faces){
            V c=t.c;for(int j=0;j<3;++j)c=add(c,mul(t.d[j],x[t.v[j]]));
            double norm=std::sqrt(dot(c,c));need(std::isfinite(norm)&&norm>0,"invalid triangle");
            E+=0.5*gamma*norm;
            if(grad)for(int j=0;j<3;++j)(*grad)[t.v[j]]+=0.5*gamma*dot(c,t.d[j])/norm;
            if(H){std::array<double,9> local{};
                for(int i=0;i<3;++i)for(int j=0;j<3;++j)
                    local[i*3+j]=0.5*gamma*(dot(t.d[i],t.d[j])/norm-dot(c,t.d[i])*dot(c,t.d[j])/(norm*norm*norm));
                H->push_back(local);
            }
        }
        for(size_t i=0;i<h.size();++i){E+=force*w[i]*x[i];if(grad)(*grad)[i]+=force*w[i];}
        need(std::isfinite(E),"nonfinite surface energy");return E;
    }
    void refresh(){
        std::vector<double> g;energy=eval(h,&g);residual=0;reaction=0;
        for(size_t i=0;i<h.size();++i)if(pinned[i])reaction+=g[i];else residual=(std::max)(residual,std::abs(g[i]));
        // Pin energy gradients give the upward support reaction under downward load.
        converged=residual<=(std::max)(1e-12,force*1e-7);
    }
    bool step(){
        if(!active||converged||!error.empty())return false;
        std::vector<double> g;std::vector<std::array<double,9>> H;
        double E=eval(h,&g,&H);size_t n=h.size();
        std::vector<double> diag(n,0);
        for(size_t f=0;f<faces.size();++f)for(int j=0;j<3;++j)diag[faces[f].v[j]]+=H[f][j*3+j];
        std::vector<double> d(n,0),r(n),z(n),p(n),q(n);double rz=0,b2=0;
        for(size_t i=0;i<n;++i)if(!pinned[i]){need(diag[i]>0,"unanchored surface");r[i]=-g[i];z[i]=r[i]/diag[i];p[i]=z[i];rz+=r[i]*z[i];b2+=r[i]*r[i];}
        for(size_t it=0;it<n*2&&rz>0;++it){
            std::fill(q.begin(),q.end(),0);
            for(size_t f=0;f<faces.size();++f)for(int i=0;i<3;++i)for(int j=0;j<3;++j)
                if(!pinned[faces[f].v[i]]&&!pinned[faces[f].v[j]])q[faces[f].v[i]]+=H[f][i*3+j]*p[faces[f].v[j]];
            double pq=std::inner_product(p.begin(),p.end(),q.begin(),0.0);
            if(pq<=0)break;double alpha=rz/pq,rr=0,next=0;
            for(size_t i=0;i<n;++i)if(!pinned[i]){d[i]+=alpha*p[i];r[i]-=alpha*q[i];rr+=r[i]*r[i];z[i]=r[i]/diag[i];next+=r[i]*z[i];}
            if(rr<=(std::max)(1e-30,b2*1e-12))break;
            for(size_t i=0;i<n;++i)p[i]=z[i]+(next/rz)*p[i];rz=next;
        }
        double gd=std::inner_product(g.begin(),g.end(),d.begin(),0.0);
        if(!(gd<0)){refresh();if(!converged)error="no descent direction";return false;}
        std::vector<double> trial(n);double a=1;bool accepted=false;
        for(int ls=0;ls<32;++ls){
            for(size_t i=0;i<n;++i)trial[i]=h[i]+a*d[i];
            if(eval(trial)<=E+1e-4*a*gd){accepted=true;break;}a*=0.5;
        }
        if(!accepted){error="no energy-decreasing step";return false;}
        h.swap(trial);++iterations;++revision;refresh();return true;
    }
    std::vector<V> positions()const{auto p=rest;for(size_t i=0;i<h.size();++i)p[i]=add(p[i],mul(normal,h[i]));return p;}
    std::vector<uint32_t> indices()const{std::vector<uint32_t> out;for(auto t:faces)for(int i:t.v)out.push_back(uint32_t(i));return out;}
    std::vector<float> mesh()const{
        auto p=positions();std::vector<V> normals(p.size(),V{0,0,0});
        for(auto t:faces){auto n=cross(sub(p[t.v[1]],p[t.v[0]]),sub(p[t.v[2]],p[t.v[0]]));for(int i:t.v)normals[i]=add(normals[i],n);}
        std::vector<float> out;out.reserve(p.size()*9);
        for(size_t i=0;i<p.size();++i){
            double norm=std::sqrt(dot(normals[i],normals[i]));auto n=mul(normals[i],1/norm);
            auto rp=add(mul(p[i],scale),translation);
            double probe=(std::min)(1.0,w[i]/(*std::max_element(w.begin(),w.end())));
            V color=pinned[i]?V{0.75,0.58,0.24}:V{0.12+0.25*probe,0.55+0.12*probe,0.68};
            for(double x:rp)out.push_back(float(x));for(double x:n)out.push_back(float(x));for(double x:color)out.push_back(float(x));
        }
        return out;
    }
    J status()const{
        J src;std::string rid;for(auto m:spec.at("materials"))if(m.at("name")==material){src=m.at("source");rid=m.at("record_id");}
        return J{{"ok",error.empty()},{"error",error},{"mode","quasistatic_height_field"},{"source",src},{"material",material},
          {"temperature_K",spec.at("temperature_K")},{"gamma_N_m",gamma},{"force_N",force},
          {"depth_m",-*std::min_element(h.begin(),h.end())},{"residual_N",residual},{"iterations",iterations},
          {"converged",converged},{"energy_J",energy},{"reaction_N",reaction},{"graph_hash",spec.at("graph_hash")},
          {"vertices",h.size()},{"triangles",faces.size()},{"positions_m",positions()},{"source_record_id",rid},
          {"render_revision",render_revision},{"state_revision",revision},{"limits",{{"max_force_N",spec.at("max_force_N")}}},
          {"materials",spec.at("materials")},{"source_scope","pure liquid-vapor correlation; idealized fixed-rim interface; not skin"}};
    }
};

