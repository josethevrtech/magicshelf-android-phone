#!/usr/bin/env python3
"""Local control for the VR phone. No network listener or Android debug port."""
import json,os,pathlib,selectors,socket,subprocess,time,struct
base=pathlib.Path(os.environ['MAGICSHELF_DATA_DIR'])
vr=pathlib.Path(os.environ['MAGICSHELF_DATA_DIR'])
endpoint=pathlib.Path(os.environ['XDG_RUNTIME_DIR'])/'android-phone-control.sock'
state=vr/'android-controls.json'
def android(command):
 p=subprocess.run(['podman','--events-backend','none','exec','lepton-magicshelf-phone','/system/bin/sh','-c',command],text=True,capture_output=True,timeout=4)
 if p.returncode:raise RuntimeError(p.stderr.strip() or 'Android command failed')
 return p.stdout.strip()
def publish(value):
 global previous
 if value==previous:return
 data={'container_pid':container_pid,'brightness':.25+.75*value/255,'android_brightness':value,'updated':time.time_ns()}
 temp=state.with_suffix('.tmp');temp.write_text(json.dumps(data));temp.replace(state);previous=value
 print('Phone brightness',value,'VR',round(data['brightness'],3),flush=True)
endpoint.unlink(missing_ok=True);state.unlink(missing_ok=True)
sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);sock.bind(str(endpoint));os.chmod(endpoint,0o600);sock.setblocking(False)
select=selectors.DefaultSelector();select.register(sock,selectors.EVENT_READ)
previous=None;container_pid=0;next_poll=0;last_error=''
def keyevent(code):
 fd=os.open(f'/proc/{container_pid}/root/dev/input/wl_keyboard_events',os.O_WRONLY|os.O_NONBLOCK)
 try:
  for value in (1,0):
   t=time.monotonic_ns();sec=t//1000000000;usec=t//1000%1000000
   os.write(fd,struct.pack('<qqHHi',sec,usec,1,code,value)+struct.pack('<qqHHi',sec,usec,0,0,0))
   if value:time.sleep(.04)
 finally:os.close(fd)
try:
 while True:
  for _,_ in select.select(max(0,min(1,next_poll-time.monotonic()))):
   try:
    message=json.loads(sock.recv(4096));operation=message.get('op')
    if operation=='brightness':
     level=max(.25,min(1,float(message['value'])));value=round((level-.25)/.75*255)
     android(f'settings put system screen_brightness_mode 0; settings put system screen_brightness {value}')
     publish(value)
    elif operation=='home':
     android('cmd statusbar collapse; am start -a android.intent.action.MAIN -c android.intent.category.HOME -f 0x10200000 -n com.android.launcher3/.uioverrides.QuickstepLauncher')
     print('Home screen opened',flush=True)
    elif operation=='back':
     keyevent(158);print('Back sent',flush=True)
   except (OSError,ValueError,KeyError,RuntimeError,subprocess.TimeoutExpired) as e:print('Phone command:',e,flush=True)
  if time.monotonic()>=next_poll:
   try:
    value=int(android('settings get system screen_brightness'))
    if not container_pid:container_pid=int(subprocess.check_output(['podman','--events-backend','none','inspect','--format','{{.State.Pid}}','lepton-magicshelf-phone'],text=True,timeout=4))
    if 0<=value<=255:publish(value)
    last_error=''
   except (ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
    container_pid=0;previous=None
    if str(e)!=last_error:print('Waiting for Android:',e,flush=True);last_error=str(e)
   next_poll=time.monotonic()+.75
finally:
 sock.close();endpoint.unlink(missing_ok=True);state.unlink(missing_ok=True)
