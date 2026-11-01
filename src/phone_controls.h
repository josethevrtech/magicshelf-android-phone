#pragma once
#include "placement.h"
#include <json-c/json.h>
struct WristConfig{
 int hand=0;float x=0,y=.055f,z=-.10f,pitch=0,roll=0,yaw=0,scale=.55f;
 static float bounded(json_object*j,const char*k,float fallback,float lo,float hi){json_object*v=nullptr;if(!j||!json_object_object_get_ex(j,k,&v))return fallback;if(!json_object_is_type(v,json_type_double)&&!json_object_is_type(v,json_type_int))return fallback;float n=json_object_get_double(v);return std::isfinite(n)?std::clamp(n,lo,hi):fallback;}
 void load(json_object*j){hand=(int)bounded(j,"hand",0,0,1);x=bounded(j,"x",0,-.2,.2);y=bounded(j,"y",.055,-.1,.25);z=bounded(j,"z",-.10,-.35,.1);pitch=bounded(j,"pitch",0,-1.5,1.5);roll=bounded(j,"roll",0,-1.5,1.5);yaw=bounded(j,"yaw",0,-1.5,1.5);scale=bounded(j,"scale",.55,.3,1.4);}
 json_object*json()const{auto*j=json_object_new_object();json_object_object_add(j,"hand",json_object_new_int(hand));for(auto p:{std::pair<const char*,float>{"x",x},{"y",y},{"z",z},{"pitch",pitch},{"roll",roll},{"yaw",yaw},{"scale",scale}})json_object_object_add(j,p.first,json_object_new_double(p.second));return j;}
 M transform()const{float c=cosf(pitch),s=sinf(pitch),r=cosf(roll),t=sinf(roll);M a=pose({1,0,0},{0,c,s},{0,-s,c},{0,0,0});M b=pose({r,t,0},{-t,r,0},{0,0,1},{0,0,0});return mm(pose({1,0,0},{0,0,-1},{0,1,0},{x,y,z}),mm(a,mm(pose({cosf(yaw),0,-sinf(yaw)},{0,1,0},{sinf(yaw),0,cosf(yaw)},{0,0,0}),b)));}
};
struct PhoneRay{bool hit=false;V local{};};
PhoneRay phoneRay(M model,float size,M controller){
 M inv=inverse(model);V a=mul(point(inv,point(controller,{0,0,0})),1/size),b=mul(point(inv,point(controller,{0,0,-1})),1/size);V d=sub(b,a);
 if(a[2]<=ScreenZ||d[2]>=-.00001f)return {};
 float t=(ScreenZ-a[2])/d[2];if(t<0||t>3)return {};V p=add(a,mul(d,t));return {onGameScreen(p),p};
}
struct NeutralGate{bool waiting=true;int role=0;bool focus=false;bool filter(bool active,int hand,float x,float y){if(!active){focus=false;waiting=true;return false;}if(!focus||role!=hand)waiting=true;focus=true;role=hand;if(waiting){if(std::abs(x)<=.25f&&std::abs(y)<=.25f)waiting=false;return false;}return true;}};
inline bool phoneDepthConsumesGesture(bool held,int owner,int pointer,bool pressed){return held&&owner==pointer&&pressed;}
inline void phoneCursor(std::vector<unsigned char>&pixels,int width,int height,int x,int y){
 if(width<=0||height<=0||pixels.size()!=(size_t)width*height*4)return;
 for(int dy=-7;dy<=7;dy++)for(int dx=-7;dx<=7;dx++){int px=x+dx,py=y+dy;if(px<0||py<0||px>=width||py>=height)continue;int d=dx*dx+dy*dy;if(d<12||d>49)continue;auto i=((size_t)py*width+px)*4;pixels[i]=255;pixels[i+1]=d>30?255:155;pixels[i+2]=d>30?255:40;pixels[i+3]=255;}
}

inline bool phoneRayMayFocus(bool dashboard,bool ownHover){return !dashboard||ownHover;}

inline float phoneDockFit(float requested,float height,float spacing){
 float gap=std::min(.012f,spacing*.1f);
 return std::min({requested,height/(2*BodyY),std::max(.02f,spacing-gap)/(2*ActualBodyHalfWidth)});
}
