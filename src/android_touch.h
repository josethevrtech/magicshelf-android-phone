#pragma once
#include "input.h"
#include <linux/input.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <ctime>
#include <vector>
#include <memory>
#include <iostream>
struct AndroidTouch {
 std::unique_ptr<GameInput> keyboard;int fd=-1,pid=0,width=720,height=1600,serial=100;
 bool pressed=false,scrolling=false,pinching=false,autoRelease=false;float sx=0,sy=0,radius=80;
 std::chrono::steady_clock::time_point deadline;
 explicit AndroidTouch(const std::string&display):keyboard(std::make_unique<GameInput>(display,true)){width=keyboard->width;height=keyboard->height;}
 AndroidTouch(int output,int w,int h):fd(output),width(w),height(h){} // Event-pipe tests, no X server.
 ~AndroidTouch(){end();if(fd>=0)close(fd);}
 struct Event{unsigned short type,code;int value;};
 bool send(std::initializer_list<Event> values){
  if(fd<0)return false;timespec now{};clock_gettime(CLOCK_MONOTONIC,&now);std::vector<input_event> events;
  for(auto value:values){input_event e{};e.time.tv_sec=now.tv_sec;e.time.tv_usec=now.tv_nsec/1000;e.type=value.type;e.code=value.code;e.value=value.value;events.push_back(e);}
  input_event sync{};sync.time=events.back().time;sync.type=EV_SYN;sync.code=SYN_REPORT;events.push_back(sync);
  bool ok=write(fd,events.data(),events.size()*sizeof(input_event))==(ssize_t)(events.size()*sizeof(input_event));
  if(!ok){close(fd);fd=-1;pressed=scrolling=pinching=autoRelease=false;}return ok;
 }
 void configure(int newPid){
  if(newPid<=1){end();if(fd>=0)close(fd);fd=-1;pid=0;return;}if(newPid!=pid){end();if(fd>=0)close(fd);fd=-1;pid=newPid;}
  if(fd>=0)return;std::string path="/proc/"+std::to_string(pid)+"/root/dev/input/wl_touch_events";
  fd=open(path.c_str(),O_WRONLY|O_NONBLOCK|O_CLOEXEC);if(fd<0)return;
  struct stat st{};if(fstat(fd,&st)||!S_ISFIFO(st.st_mode)){close(fd);fd=-1;return;}
  send({{EV_ABS,ABS_MT_SLOT,0},{EV_ABS,ABS_MT_PRESSURE,0},{EV_ABS,ABS_MT_TRACKING_ID,-1},{EV_ABS,ABS_MT_SLOT,1},{EV_ABS,ABS_MT_PRESSURE,0},{EV_ABS,ABS_MT_TRACKING_ID,-1}});
 }
 void begin(int x,int y){if(pressed)return;sx=std::clamp(x,0,width-1);sy=std::clamp(y,0,height-1);
  pressed=send({{EV_ABS,ABS_MT_SLOT,0},{EV_ABS,ABS_MT_TRACKING_ID,++serial},{EV_ABS,ABS_MT_POSITION_X,(int)sx},{EV_ABS,ABS_MT_POSITION_Y,(int)sy},{EV_ABS,ABS_MT_PRESSURE,255}});
  deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);autoRelease=false;}
 void move(int x,int y){if(pressed&&!scrolling&&!pinching)position(x,y);}
 void position(int x,int y){x=std::clamp(x,0,width-1);y=std::clamp(y,0,height-1);send({{EV_ABS,ABS_MT_SLOT,0},{EV_ABS,ABS_MT_POSITION_X,x},{EV_ABS,ABS_MT_POSITION_Y,y}});deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);}
 void end(){if(pressed||pinching)send({{EV_ABS,ABS_MT_SLOT,0},{EV_ABS,ABS_MT_PRESSURE,0},{EV_ABS,ABS_MT_TRACKING_ID,-1},{EV_ABS,ABS_MT_SLOT,1},{EV_ABS,ABS_MT_PRESSURE,0},{EV_ABS,ABS_MT_TRACKING_ID,-1}});pressed=scrolling=pinching=autoRelease=false;}
 void tap(int x,int y){if(pressed)return;begin(x,y);autoRelease=true;deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(65);}
 void tick(){if((pressed||pinching)&&std::chrono::steady_clock::now()>=deadline)end();}
 void text(std::string value){if(keyboard)keyboard->text(value);}
 void stopScroll(){if(scrolling||pinching)end();}
 void stickScroll(float x,float y,float dt,int anchorX,int anchorY){
  if(pinching)end();if(x==0&&y==0){stopScroll();return;}if(pressed&&!scrolling)return;
  if(!pressed){begin(std::clamp(anchorX,100,width-100),std::clamp(anchorY,height/3,2*height/3));scrolling=pressed;}
  if(!scrolling)return;sx-=x*900*std::clamp(dt,0.f,.05f);sy+=y*1100*std::clamp(dt,0.f,.05f);position((int)sx,(int)sy);
  if(sx<65||sx>width-65||sy<120||sy>height-120)end();
 }
 void pinch(float axis,float dt,int anchorX,int anchorY){
  if(!pinching){end();sx=std::clamp(anchorX,width/4,3*width/4);sy=std::clamp(anchorY,height/4,3*height/4);radius=std::min(width,height)*.12f;
   pressed=pinching=send({{EV_ABS,ABS_MT_SLOT,0},{EV_ABS,ABS_MT_TRACKING_ID,++serial},{EV_ABS,ABS_MT_POSITION_X,(int)(sx-radius)},{EV_ABS,ABS_MT_POSITION_Y,(int)sy},{EV_ABS,ABS_MT_PRESSURE,255},{EV_ABS,ABS_MT_SLOT,1},{EV_ABS,ABS_MT_TRACKING_ID,++serial},{EV_ABS,ABS_MT_POSITION_X,(int)(sx+radius)},{EV_ABS,ABS_MT_POSITION_Y,(int)sy},{EV_ABS,ABS_MT_PRESSURE,255}});
  }
  if(!pinching)return;radius=std::clamp(radius+axis*width*.6f*std::clamp(dt,0.f,.05f),20.f,std::min(sx,width-1-sx)-8.f);
  send({{EV_ABS,ABS_MT_SLOT,0},{EV_ABS,ABS_MT_POSITION_X,(int)(sx-radius)},{EV_ABS,ABS_MT_POSITION_Y,(int)sy},{EV_ABS,ABS_MT_SLOT,1},{EV_ABS,ABS_MT_POSITION_X,(int)(sx+radius)},{EV_ABS,ABS_MT_POSITION_Y,(int)sy}});deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(300);
 }
};