#include "placement.h"
#include "phone_ui.h"
#include "dock_layout.h"
#include <cassert>
void near(M a,M b){for(int i=0;i<16;i++)assert(fabsf(a[i]-b[i])<.00002f);}
M rotate(float angle,V position){return pose({cosf(angle),0,-sinf(angle)},{0,1,0},{sinf(angle),0,cosf(angle)},position);}
int main(){
 int tested=0;
 {std::ifstream mesh(std::string(AssetDirectory)+"/device.mesh",std::ios::binary);char magic[4];uint32_t batches=0,count=0;mesh.read(magic,4);mesh.read((char*)&batches,4);mesh.read((char*)&count,4);assert(mesh&&std::string(magic,4)=="DPH2");mesh.seekg(12+batches*16);float extent=0;for(uint32_t i=0;i<count;i++){Vertex v{};mesh.read((char*)&v,sizeof(v));extent=std::max(extent,fabsf(v.x));}assert(mesh&&fabsf(extent-ActualBodyHalfWidth)<.000001f);}
 assert(extraActionAt(3,120,800)==PhoneAction::ConfirmHide);
 assert(extraActionAt(4,240,450)==PhoneAction::DisplayTablet);
 assert(extraActionAt(4,0,450)==PhoneAction::NoAction);
 assert(extraActionAt(1,350,680)==PhoneAction::WristYawRight);

 for(float spacing:{.12f,.13f,.18f,.5f}){float fitted=phoneDockFit(3,.18f,spacing);assert(2*ActualBodyHalfWidth*fitted<=spacing-std::min(.012f,spacing*.1f)+.000001f);M displayed=dockObjectPose(identity(),fitted);assert(fabsf(point(displayed,{0,-BodyY*fitted,0})[1])<.000001f);}
 assert(fabsf(phoneDockFit(3,.18f,.18f)-dockObjectSize(3,.18f))<.000001f);
 assert(phoneDockFit(.6f,.18f,.18f)==.6f);

 for(int n=0;n<500;n++){
  float angle=n*.013f,size=.6f+(n%25)*.1f;
  M model=rotate(angle,{-.2f,1.2f,-.7f});
  V local{((n%19)-9)*ScreenX/10,ScreenCY+((n%17)-8)*ScreenY/9,ScreenZ};
  V goal=point(model,mul(local,size)),origin{.25f,1.3f,0};
  V center=point(model,{0,0,ScreenZ*size}),z=norm(sub(origin,center)),x=norm(cross({0,1,0},z)),y=cross(z,x);
  M plane=pose(x,y,z,center);
  V a=point(inverse(plane),origin),b=point(inverse(plane),goal);float t=-a[2]/(b[2]-a[2]);
  V target=point(plane,add(a,mul(sub(b,a),t)));
  a=mul(point(inverse(model),origin),1/size);b=mul(point(inverse(model),target),1/size);
  // Match the runtime guard for a nearly edge-on ray.
  if(fabsf(b[2]-a[2])<.0001f)continue;
  t=(ScreenZ-a[2])/(b[2]-a[2]);V hit=add(a,mul(sub(b,a),t));
  assert(fabsf(hit[0]-local[0])<ScreenX/ScreenWidth&&fabsf(hit[1]-local[1])<ScreenY/ScreenHeight); // less than half a game pixel
  assert(onGameScreen(hit));
  auto pixel=screenPixel(hit),expected=screenPixel(local);
  assert(abs(pixel[0]-expected[0])<=1&&abs(pixel[1]-expected[1])<=1);

  // Settings use exactly the game screen's perspective hit mapping.
  const auto&button=phoneButtons[n%phoneButtons.size()];
  int bx=button.x+button.w/2,by=button.y+button.h/2;
  V control{(bx/480.f*2-1)*ScreenX,ScreenCY+(1-by/1046.f*2)*ScreenY,ScreenZ};
  goal=point(model,mul(control,size));
  a=point(inverse(plane),origin);b=point(inverse(plane),goal);t=-a[2]/(b[2]-a[2]);
  target=point(plane,add(a,mul(sub(b,a),t)));
  a=mul(point(inverse(model),origin),1/size);b=mul(point(inverse(model),target),1/size);
  // Match the runtime guard for a nearly edge-on ray.
  if(fabsf(b[2]-a[2])<.0001f)continue;
  t=(ScreenZ-a[2])/(b[2]-a[2]);hit=add(a,mul(sub(b,a),t));pixel=screenPixel(hit,SettingsWidth,SettingsHeight);
  assert(phoneActionAt(pixel[0],pixel[1])==button.action);

  M hand=rotate(-angle,{.2f,1.1f,-.3f});
  RoomGrab grab;grab.begin(4,hand,model,true);near(grab.follow(hand),model);
  M movedHand=rotate(-angle+.7f,{-1.2f,.4f,1.1f}); // behind the user's original view
  M movedPhone=grab.follow(movedHand);
  near(mm(inverse(movedHand),movedPhone),mm(inverse(hand),model));
  assert(validRoomPose(movedPhone));grab.end();assert(!grab.active);tested++;
 }
 assert((screenPixel({-ScreenX,ScreenCY+ScreenY,ScreenZ})==std::array<int,2>{0,0}));
 assert((screenPixel({ScreenX,ScreenCY-ScreenY,ScreenZ})==std::array<int,2>{ScreenWidth-1,ScreenHeight-1}));
 assert((screenPixel({0,ScreenCY,ScreenZ})==std::array<int,2>{ScreenWidth/2,ScreenHeight/2}));
 assert(onHomeButton({0,HomeY,ScreenZ})&&!onGameScreen({0,HomeY,ScreenZ}));
 assert(onPhoneBody({BodyX-.001f,0,ScreenZ})&&!onGameScreen({BodyX-.001f,0,ScreenZ}));
 assert(!onPhoneBody({BodyX+.01f,0,ScreenZ}));
 M malformed=identity();malformed[0]=2;assert(!validRoomPose(malformed));
 malformed=identity();malformed[3]=.5;assert(!validRoomPose(malformed));
 assert(phoneActionAt(120,260)==PhoneAction::FontSettings);
 assert(phoneActionAt(350,240)==PhoneAction::Apps);
 assert(appActionAt(120,440)==PhoneAction::Spotify);
 assert(appActionAt(350,440)==PhoneAction::AppleMusic);
 assert(appActionAt(120,911)==PhoneAction::RetryApps);
 assert(std::string(phoneAppId(PhoneAction::Music))=="music");
 assert(phoneAppId(PhoneAction::Back)==nullptr);
 assert(fontActionAt(120,440)==PhoneAction::FontSmaller);
 assert(fontActionAt(350,440)==PhoneAction::FontLarger);
 assert(fontActionAt(240,570)==PhoneAction::FontReset);
 assert(fontActionAt(240,720)==PhoneAction::NoAction);
 assert(phoneActionAt(240,570)==PhoneAction::NoAction); // gap between size buttons
 assert(phoneActionAt(479,1045)==PhoneAction::NoAction);
 assert(fabsf(ScreenX/ScreenY-(float)ScreenWidth/ScreenHeight)<.00001f);
 std::cout<<AppTitle<<": "<<tested<<" screen-ray, phone-settings and room-grab cases passed; screen edges, home button and pose validation passed\n";
}
