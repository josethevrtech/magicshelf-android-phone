#pragma once
#include "openvr.h"
#include "phone_controls.h"
#include <string>
#include <iostream>
struct ControllerNav {
 vr::VRActionSetHandle_t set=0;vr::VRActionHandle_t scroll=0,click=0,back=0,home=0,grip=0,pinch=0;vr::VRInputValueHandle_t hand[2]{};
 bool available=false,wasFocused=false,wasPinch=false;NeutralGate neutral;float wheelX=0,wheelY=0;
 explicit ControllerNav(const std::string&base){auto*i=vr::VRInput();auto e=i->SetActionManifestPath((base+"/assets/input/actions.json").c_str());if(e)return;
  e=i->GetActionSetHandle("/actions/phone",&set);for(auto p:{std::pair<const char*,vr::VRActionHandle_t*>{"scroll",&scroll},{"click",&click},{"back",&back},{"home",&home},{"grip",&grip},{"pinch",&pinch}})e=(vr::EVRInputError)(e|i->GetActionHandle((std::string("/actions/phone/in/")+p.first).c_str(),p.second));
  i->GetInputSourceHandle("/user/hand/left",&hand[0]);i->GetInputSourceHandle("/user/hand/right",&hand[1]);available=e==vr::VRInputError_None;
 }
 struct Result{float scrollX=0,scrollY=0,depthY=0;int x=0,y=0;bool click=false,back=false,home=false,axisAvailable=false,grip=false,gripPressed=false,gripAvailable=false,pinch=false,depth=false;};
 static float deflection(float v){return std::isfinite(v)&&std::abs(v)>.25f?std::copysign((std::min(std::abs(v),1.f)-.25f)/.75f,v):0;}
 Result update(bool focused,int role,float dt,bool grabbing=false,int ownerRole=0){
  Result out;auto*i=vr::VRInput();bool valid=role>=1&&role<=2;focused=focused&&valid;
  if(available){vr::VRActiveActionSet_t active{};active.ulActionSet=set;active.nPriority=vr::k_nActionSetOverlayGlobalPriorityMin+1;i->UpdateActionState(focused?&active:nullptr,sizeof(active),focused?1:0);}
  auto digital=[&](vr::VRActionHandle_t h,int r,bool edge){vr::InputDigitalActionData_t d{};return available&&h&&r>=1&&r<=2&&i->GetDigitalActionData(h,&d,sizeof(d),hand[r-1])==vr::VRInputError_None&&d.bActive&&d.bState&&(!edge||(wasFocused&&d.bChanged));};
  auto axis=[&](int r,float&x,float&y){if(r<1||r>2)return false;vr::InputAnalogActionData_t a{};
   if(available&&i->GetAnalogActionData(scroll,&a,sizeof(a),hand[r-1])==vr::VRInputError_None&&a.bActive){x=a.x;y=a.y;return true;}
   auto index=vr::VRSystem()->GetTrackedDeviceIndexForControllerRole((vr::ETrackedControllerRole)r);vr::VRControllerState_t state{};
   if(index>=vr::k_unMaxTrackedDeviceCount||!vr::VRSystem()->GetControllerState(index,&state,sizeof(state)))return false;
   for(int n=0;n<5;n++)if(vr::VRSystem()->GetInt32TrackedDeviceProperty(index,(vr::ETrackedDeviceProperty)(vr::Prop_Axis0Type_Int32+n))==vr::k_eControllerAxis_Joystick){x=state.rAxis[n].x;y=state.rAxis[n].y;return true;}return false;
  };
  int holding=grabbing?ownerRole:role;vr::InputDigitalActionData_t g{};out.gripAvailable=available&&holding>=1&&holding<=2&&i->GetDigitalActionData(grip,&g,sizeof(g),hand[holding-1])==vr::VRInputError_None&&g.bActive;out.grip=out.gripAvailable&&g.bState;out.gripPressed=wasFocused&&out.grip&&g.bChanged;
  float x=0,y=0;out.axisAvailable=focused&&axis(role,x,y);
  bool ready=neutral.filter(focused,role,x,y);
  if(grabbing&&ownerRole>=1&&ownerRole<=2){float dx=0,dy=0;out.depth=digital(pinch,ownerRole,false);if(out.depth&&axis(ownerRole,dx,dy))out.depthY=deflection(dy);}
  if(focused){out.click=digital(click,role,true);out.back=digital(back,2,true);out.home=digital(home,1,true);out.pinch=digital(pinch,role,false)&&!(out.depth&&role==ownerRole);}
  out.pinch=out.pinch&&ready;bool releasedPinch=wasPinch&&!out.pinch;if(releasedPinch)neutral.waiting=true;wasPinch=out.pinch;
  if(ready&&!releasedPinch&&!(out.depth&&role==ownerRole)){out.scrollX=deflection(x);out.scrollY=deflection(y);}
  wheelX+=out.scrollX*10*std::clamp(dt,0.f,.1f);wheelY+=out.scrollY*10*std::clamp(dt,0.f,.1f);out.x=(int)wheelX;out.y=(int)wheelY;wheelX-=out.x;wheelY-=out.y;
  if(!focused)wheelX=wheelY=0;wasFocused=focused;return out;
 }
};