#include "android_touch.h"
#include "phone_controls.h"
#include <cassert>
#include <csignal>
#include <iostream>
int main(){
 signal(SIGPIPE,SIG_IGN);int f[2];assert(pipe(f)==0);fcntl(f[0],F_SETFL,O_NONBLOCK);
 AndroidTouch touch(f[1],720,1600);touch.pinch(.8f,.02f,360,800);assert(touch.pinching);
 std::vector<input_event> events(100);auto bytes=read(f[0],events.data(),events.size()*sizeof(input_event));assert(bytes>0);events.resize(bytes/sizeof(input_event));int slot=0;int ids[2]={-1,-1};int x[2]={0,0};int syncs=0;
 for(auto e:events){if(e.type==EV_ABS&&e.code==ABS_MT_SLOT)slot=e.value;if(e.type==EV_ABS&&e.code==ABS_MT_TRACKING_ID)ids[slot]=e.value;if(e.type==EV_ABS&&e.code==ABS_MT_POSITION_X)x[slot]=e.value;if(e.type==EV_SYN)syncs++;}
 assert(ids[0]>=0&&ids[1]>=0&&ids[0]!=ids[1]);assert(x[0]<360&&x[1]>360&&syncs==2);
 touch.deadline=std::chrono::steady_clock::now()-std::chrono::seconds(1);touch.tick();assert(!touch.pinching&&!touch.pressed);
 events.resize(100);bytes=read(f[0],events.data(),events.size()*sizeof(input_event));assert(bytes>0);events.resize(bytes/sizeof(input_event));int release[2]={0,0};slot=0;
 for(auto e:events){if(e.type==EV_ABS&&e.code==ABS_MT_SLOT)slot=e.value;if(e.type==EV_ABS&&e.code==ABS_MT_TRACKING_ID&&e.value==-1)release[slot]++;}
 assert(release[0]==1&&release[1]==1);
 touch.stickScroll(0,1,.02,360,800);assert(touch.scrolling);touch.end();assert(!touch.pressed);
 NeutralGate gate;assert(!gate.filter(true,2,0,1));assert(!gate.filter(true,2,0,0));assert(gate.filter(true,2,0,1));assert(!gate.filter(true,1,0,1));gate.filter(false,0,0,0);assert(!gate.filter(true,2,0,1));
 WristConfig fit;auto*j=json_tokener_parse("{\"x\":100,\"scale\":-2,\"pitch\":2}");fit.load(j);json_object_put(j);assert(fit.x==.2f&&fit.scale==.3f&&fit.pitch==1.5f);j=fit.json();WristConfig restored;restored.load(j);json_object_put(j);assert(restored.x==fit.x&&restored.scale==fit.scale);assert(validRoomPose(fit.transform()));
 auto controller=identity();controller[14]=1;assert(phoneRay(identity(),1,controller).hit);controller[12]=2;assert(!phoneRay(identity(),1,controller).hit);controller[12]=0;controller[14]=-1;assert(!phoneRay(identity(),1,controller).hit);
 assert(phoneRayMayFocus(false,false));assert(phoneRayMayFocus(true,true));assert(!phoneRayMayFocus(true,false));
 assert(phoneDepthConsumesGesture(true,1,1,true));assert(!phoneDepthConsumesGesture(true,1,2,true));assert(!phoneDepthConsumesGesture(true,1,1,false));assert(!phoneDepthConsumesGesture(false,1,1,true));
 std::vector<unsigned char> pixel(10*10*4,0);phoneCursor(pixel,10,10,0,0);assert(pixel[3]==0);assert(pixel[4*4+3]==255);
 close(f[0]);touch.pinch(1,.02,360,800);assert(!touch.pressed&&!touch.pinching&&touch.fd==-1);
 std::cout<<"Two-contact IDs/positions/releases, timeout, disconnect, neutral routing, wrist bounds and rays passed\n";
}