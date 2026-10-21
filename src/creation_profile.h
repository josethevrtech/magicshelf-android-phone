#pragma once
// This creation owns its identity and geometry. The SDK consumes this profile.
constexpr bool AndroidOnly=true;
constexpr const char* ApplicationKey="local.androidphone.vr";
constexpr const char* DeviceKey="local.androidphone.device";
constexpr const char* AppTitle="Android Phone (Virtual)";
constexpr const char* ManifestFile="androidphone.vrmanifest";
constexpr const char* SettingsFile="android-settings.json";
constexpr const char* LockFile="android-instance.lock";
constexpr const char* IconFile="android-phone-icon.png";
constexpr const char* AssetDirectory="assets/android-phone";
constexpr int ScreenWidth=720,ScreenHeight=1600;
constexpr float ScreenX=.0355f,ScreenY=ScreenX*ScreenHeight/ScreenWidth;
constexpr float ScreenCY=.0015f,ScreenZ=.00431f,PhonePlaneWidth=.202f;
constexpr float BodyX=.0385f,BodyY=.0875f,HomeY=-.0827f;
constexpr float HomeHalfX=.018f,HomeHalfY=.0038f,DefaultSize=2.2f;
constexpr int RenderWidth=3072,RenderHeight=1536;
constexpr int SettingsWidth=480,SettingsHeight=1046;
constexpr float GrabHalfWidth=.025f,GrabHalfHeight=.003f,GrabY=-BodyY-.013f;
// The transparent stereo canvas includes the handle and its larger hit target.
constexpr float InteractionPlaneWidth=2.f*(BodyY+.025f)>PhonePlaneWidth?2.f*(BodyY+.025f):PhonePlaneWidth;
