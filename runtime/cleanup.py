#!/usr/bin/env python3
"""Idempotent cleanup also runs after a crash through systemd ExecStopPost."""
import json,subprocess
name='lepton-magicshelf-phone'
p=subprocess.run(['podman','--events-backend','none','ps','--all','--filter','name=^'+name+'$','--format','json'],capture_output=True,text=True,check=True,timeout=8)
for item in json.loads(p.stdout):
    if name in item.get('Names',[]) and item.get('Labels',{}).get('lepton')=='true':
        if item.get('State')=='paused':subprocess.run(['podman','unpause',item['Id']],check=True,timeout=8)
        subprocess.run(['podman','stop','--time','5',item['Id']],check=True,timeout=12)
