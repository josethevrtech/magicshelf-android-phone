"""Creation-owned display selection; unknown/corrupt settings keep phone mode."""
import json

def display_profile(path):
    try:
        value=json.loads(path.read_text())
        tablet=isinstance(value,dict) and value.get('display_mode')=='tablet'
    except (OSError,ValueError):
        tablet=False
    return (960,1280,240) if tablet else (720,1600,320)