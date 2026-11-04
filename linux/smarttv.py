#!/usr/bin/env python3
"""Linux runtime for Smart TV OS: a loopback-only API compatible with web/tv.js."""
from __future__ import annotations
import argparse, configparser, json, mimetypes, os, re, shlex, shutil, socket
import subprocess, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PORT = 48765
CHUNK = 4 * 1024 * 1024
IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
VIDEO = {".mp4", ".webm", ".mkv"}
BAD = re.compile(r"[\x00-\x1f\x7f]")
FIELD = re.compile(r"%(?:[fFuUdDnNickvm])")
KNOWN = [
 ("netflix",("netflix",),"#E50914","icons/netflix.svg"),
 ("amazon",("prime video","amazon prime"),"#1A98FF","icons/prime.png"),
 ("disney",("disney+","disney plus"),"#1838C8",""),
 ("hbo.max",("hbo max","max"),"#6C3BE0","icons/max.svg"),
 ("globoplay",("globoplay",),"#FF5A1F",""),
 ("appletv",("apple tv",),"#B8BCC6","icons/appletv.svg"),
 ("youtube.leanback.v4",("youtube",),"#FF0033","icons/youtube.png"),
 ("crunchyroll",("crunchyroll",),"#F47521","icons/crunchyroll.svg"),
 ("twitch",("twitch",),"#9146FF","icons/twitch.svg"),
 ("spotify",("spotify",),"#1DB954","icons/spotify.svg"),
 ("deezer",("deezer",),"#A238FF","icons/deezer.svg"),
 ("plex",("plex",),"#E5A00D","icons/plex.svg"),
 ("jellyfin",("jellyfin",),"#AA5CC3","icons/jellyfin.svg"),
 ("vlc",("vlc media player","videolan"),"#FF8800",""),
 ("kodi",("kodi",),"#17B2E7",""),
 ("steam",("steam",),"#1B2838","icons/steam.svg"),
 ("xbox",("xbox",),"#107C10",""),
 ("battlenet",("battle.net","battle net"),"#148EFF",""),
 ("epic",("epic games store","epic games"),"#2A2A2A",""),
 ("heroic",("heroic games launcher","heroic"),"#7C4DFF",""),
 ("lutris",("lutris",),"#F0A000",""),
 ("bottles",("bottles",),"#7B61A8",""),
 ("moonlight",("moonlight",),"#5B7CFA",""),
 ("steamlink",("steam link","steamlink"),"#171A21",""),
 ("retroarch",("retroarch",),"#D94B27",""),
 ("dolphin",("dolphin emulator",),"#1E88E5",""),
 ("pcsx2",("pcsx2",),"#1565C0",""),
 ("ppsspp",("ppsspp",),"#607D8B",""),
 ("rpcs3",("rpcs3",),"#4A6FA5",""),
 ("scummvm",("scummvm",),"#333333",""),
 ("dosbox",("dosbox",),"#455A64",""),
]

GAME_LAUNCHER_IDS = {
    "steam", "lutris", "heroic", "epic", "battlenet", "bottles", "moonlight", "steamlink",
    "retroarch", "dolphin", "pcsx2", "ppsspp", "rpcs3", "scummvm", "dosbox",
}

def norm(s): return re.sub(r"[^a-z0-9]+"," ",(s or "").casefold()).strip()
def canonical_app(name):
    n=norm(name)
    for app_id,names,color,icon in KNOWN:
        if any((n == norm(x) or n.startswith(norm(x) + " ")) if x == "max" else norm(x) in n for x in names): return app_id,color,icon
    return None

def parse_desktop_file(path):
    p=configparser.ConfigParser(interpolation=None,strict=False); p.optionxform=str
    try:
        with path.open(encoding="utf-8",errors="replace") as f: p.read_file(f)
        e=p["Desktop Entry"]
    except (OSError,KeyError,configparser.Error): return None
    if e.get("Type","Application")!="Application" or e.getboolean("Hidden",fallback=False) or e.getboolean("NoDisplay",fallback=False) or e.getboolean("Terminal",fallback=False): return None
    name=e.get("Name",path.stem).strip(); command=e.get("Exec","").strip()
    if not name or not command or BAD.search(command): return None
    try: argv=shlex.split(command,posix=True)
    except ValueError: return None
    argv=[FIELD.sub("",x) for x in argv]; argv=[x for x in argv if x and not x.startswith("%")]
    if not argv: return None
    exe=argv[0]
    if os.path.isabs(exe):
        if not Path(exe).is_file(): return None
    elif shutil.which(exe) is None: return None
    found=canonical_app(name)
    app_id,color,icon=found if found else ("desktop:"+path.stem,"#344054","")
    categories={value.strip().casefold() for value in e.get("Categories","").split(";") if value.strip()}
    is_launcher = app_id in GAME_LAUNCHER_IDS
    is_game = "game" in categories or is_launcher
    is_streaming_client = app_id in ("moonlight","steamlink")
    return {"id":app_id,"title":name,"icon":icon,"color":color,
            "is_game":is_game,"is_streaming_client":is_streaming_client,
            "is_native_game":("game" in categories and not is_launcher),
            "argv":argv,"desktop_file":str(path)}

def desktop_dirs(home):
    paths=[home/".local/share/applications",home/".local/share/flatpak/exports/share/applications",
           Path("/usr/local/share/applications"),Path("/usr/share/applications"),
           Path("/var/lib/flatpak/exports/share/applications")]
    return [p for p in paths if p.is_dir()]

def steam_library_roots(home):
    roots=[home/".steam/steam",home/".local/share/Steam",
           home/".var/app/com.valvesoftware.Steam/.local/share/Steam"]
    for root in list(roots):
        vdf=root/"steamapps/libraryfolders.vdf"
        try:
            for raw in re.findall(r'"path"\s+"([^"]+)"',vdf.read_text(encoding="utf-8",errors="replace")):
                candidate=Path(raw.replace("\\\\","\\"))
                if candidate not in roots: roots.append(candidate)
        except OSError: pass
    return roots


def steam_games(home, steam_argv=None):
    games=[]; seen=set()
    for root in steam_library_roots(home):
        for manifest in sorted((root/"steamapps").glob("appmanifest_*.acf")):
            try: body=manifest.read_text(encoding="utf-8",errors="replace")
            except OSError: continue
            app=re.search(r'"appid"\s+"(\d+)"',body)
            name=re.search(r'"name"\s+"((?:\\.|[^"])*)"',body)
            if not app or not name or app.group(1) in seen: continue
            app_id=app.group(1); seen.add(app_id)
            title=re.sub(r'\\(["\\])',r'\1',name.group(1)).strip()
            if not title: continue
            command=list(steam_argv or ["steam"])
            if "-bigpicture" not in command: command.append("-bigpicture")
            command.extend(["-applaunch",app_id])
            games.append({"id":"steam-game:"+app_id,"title":title,"icon":"","color":"#1B2838",
                          "is_game":True,"is_native_game":False,
                          "argv":command,"desktop_file":""})
    return games


def gaming_config_path(home=None):
    if home is None:
        base=Path(os.environ.get("XDG_CONFIG_HOME",str(Path.home()/".config")))
    else:
        base=Path(home)/".config"
    return base/"smart-tv"/"gaming.json"


def gaming_settings(home=None):
    defaults={"profile":"tv","gamemode":True,"mangohud":False}
    try:
        saved=json.loads(gaming_config_path(home).read_text(encoding="utf-8"))
        if isinstance(saved,dict):
            if saved.get("profile") in ("tv","console"): defaults["profile"]=saved["profile"]
            for key in ("gamemode","mangohud"):
                if isinstance(saved.get(key),bool): defaults[key]=saved[key]
    except (OSError,ValueError,TypeError): pass
    return defaults


def save_gaming_settings(settings, home=None):
    path=gaming_config_path(home); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(settings,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    os.chmod(temp,0o600); temp.replace(path)


def set_gaming_setting(key, enabled, home=None):
    if key not in ("gamemode","mangohud") or not isinstance(enabled,bool): return False
    settings=gaming_settings(home); settings[key]=enabled
    save_gaming_settings(settings,home)
    return True


def set_experience_profile(profile, home=None):
    if profile not in ("tv","console"): return False
    settings=gaming_settings(home); settings["profile"]=profile
    save_gaming_settings(settings,home)
    return True


def gaming_info(home=None):
    return {**gaming_settings(home),"available":{
        "gamemode":shutil.which("gamemoderun") is not None,
        "mangohud":shutil.which("mangohud") is not None,
        "gamescope":shutil.which("gamescope") is not None}}


def discover_apps(home=None):
    home=home or Path.home(); apps={}
    for folder in desktop_dirs(home):
        for path in sorted(folder.glob("*.desktop")):
            item=parse_desktop_file(path)
            if item and item["id"] not in apps: apps[item["id"]]=item
    if "steam" in apps:
        apps["steam"]["title"]="Steam"
        if "-bigpicture" not in apps["steam"]["argv"]: apps["steam"]["argv"].append("-bigpicture")
    steam_argv=apps.get("steam",{}).get("argv")
    for game in steam_games(home,steam_argv):
        if game["id"] not in apps: apps[game["id"]]=game
    return sorted(apps.values(),key=lambda a:a["title"].casefold())


def launch_app(apps, app_id):
    item=next((a for a in apps if a["id"]==app_id),None)
    if not item: return False
    argv=list(item.get("argv") or [])
    if not argv or BAD.search("\0".join(argv)): return False
    env=os.environ.copy()
    if item.get("is_native_game"):
        settings=gaming_settings()
        if settings["gamemode"]:
            gamemoderun=shutil.which("gamemoderun")
            if gamemoderun: argv=[gamemoderun,*argv]
        if settings["mangohud"] and shutil.which("mangohud"):
            env["MANGOHUD"]="1"; env["MANGOHUD_DLSYM"]="1"
    try:
        subprocess.Popen(argv,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                         start_new_session=True,close_fds=True)
        return True
    except (OSError,ValueError): return False

def system_name():
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="): return line.split("=",1)[1].strip().strip('"')
    except OSError: pass
    return "Linux"

def local_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try: s.connect(("192.0.2.1",80)); return s.getsockname()[0]
    except OSError: return ""
    finally: s.close()

def generated_asset(web,name):
    direct=web/name
    if direct.is_file(): return direct.read_bytes(),(mimetypes.guess_type(direct.name)[0] or "application/octet-stream")
    assets=REPO/"assets"
    if name in ("config.js","coins.js"):
        source=assets/("config.json" if name=="config.js" else "coins.json")
        obj=json.loads(source.read_text(encoding="utf-8"))
        prefix="window.CONFIG = " if name=="config.js" else "window.COINS = "
        return (prefix+json.dumps(obj,ensure_ascii=False)+";\n").encode(),"application/javascript; charset=utf-8"
    if name=="i18n.js":
        catalogues={}
        for f in sorted((assets/"i18n").glob("*.json")): catalogues[f.stem]=json.loads(f.read_text(encoding="utf-8"))
        return ("window.I18N_CATALOGUES = "+json.dumps(catalogues,ensure_ascii=False,separators=(",",":"))+";\n").encode(),"application/javascript; charset=utf-8"
    return None,None

class SmartTVServer(ThreadingHTTPServer):
    daemon_threads=True; allow_reuse_address=True
    def __init__(self,address,handler,web,fundos):
        super().__init__(address,handler); self.web=web.resolve(); self.fundos=fundos.resolve()
        self.apps=discover_apps(); self.quit_requested=False

class Handler(BaseHTTPRequestHandler):
    server: SmartTVServer
    protocol_version="HTTP/1.1"
    def log_message(self,fmt,*args):
        if os.environ.get("SMARTTV_DEBUG"): super().log_message(fmt,*args)
    def send_body(self,status,body,ctype="application/json; charset=utf-8",headers=None):
        self.send_response(status); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers()
        if body: self.wfile.write(body)
    def js(self,obj,status=200): self.send_body(status,json.dumps(obj,ensure_ascii=False).encode())
    def do_GET(self):
        host=(self.headers.get("Host") or "").split(":",1)[0].strip("[]").lower()
        if host not in ("127.0.0.1","localhost"): self.js({"error":"local requests only"},403); return
        origin=self.headers.get("Origin")
        expected="http://"+host+":"+str(self.server.server_port)
        if origin and origin != expected: self.js({"error":"same-origin requests only"},403); return
        fetch_site=self.headers.get("Sec-Fetch-Site")
        if fetch_site and fetch_site not in ("same-origin","none"): self.js({"error":"same-origin requests only"},403); return
        u=urllib.parse.urlsplit(self.path); path=urllib.parse.unquote(u.path); q=urllib.parse.parse_qs(u.query,keep_blank_values=True)
        if path=="/api/apps":
            self.server.apps=discover_apps()
            self.js({"apps":[{k:a.get(k) for k in ("id","title","icon","color","is_game","is_streaming_client")} for a in self.server.apps]})
        elif path=="/api/gaming":
            key=q.get("key",[""])[0]; raw=q.get("enabled",[""])[0]
            if key:
                if raw not in ("0","1") or not set_gaming_setting(key,raw=="1"):
                    self.js({"ok":False,"error":"invalid gaming setting"},400); return
            self.js(gaming_info())
        elif path=="/api/profile":
            profile=q.get("mode",[""])[0]
            if profile and not set_experience_profile(profile):
                self.js({"ok":False,"error":"invalid profile"},400); return
            self.js(gaming_info())
        elif path=="/api/open": self.js({"ok":launch_app(self.server.apps,q.get("id",[""])[0])})
        elif path=="/api/settings": self.js({"ok":self.open_settings()})
        elif path=="/api/about":
            self.js({"model":socket.gethostname(),"firmware":"","system":system_name(),"version":"Linux 0.1","ip":local_ip()})
        elif path=="/api/wallpapers": self.js(self.wallpapers())
        elif path=="/api/autostart": self.js({"on":self.autostart(q.get("on",[None])[0])})
        elif path=="/api/quit":
            self.server.quit_requested=True; self.js({"ok":True})
            threading.Thread(target=self.server.shutdown,daemon=True).start()
        elif path.startswith("/fundos/"): self.serve_fund(path[8:])
        else: self.serve_static(path)
    def open_settings(self):
        for name in ("systemsettings","gnome-control-center","xfce4-settings-manager","mate-control-center"):
            exe=shutil.which(name)
            if exe:
                try: subprocess.Popen([exe],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return True
                except OSError: pass
        return False
    def autostart_path(self):
        base=Path(os.environ.get("XDG_CONFIG_HOME",str(Path.home()/".config")))
        return base/"autostart"/"smart-tv.desktop"
    def autostart(self,requested):
        path=self.autostart_path()
        if requested=="1":
            launcher=Path(os.environ.get("SMARTTV_LAUNCHER",str(HERE/"run.sh"))).resolve()
            path.parent.mkdir(parents=True,exist_ok=True)
            desktop_exec = '"' + str(launcher).replace("\\", "\\\\").replace('"', '\\"') + '"'
            path.write_text("[Desktop Entry]\nType=Application\nName=Smart TV\nComment=Start Smart TV at login\nExec="+desktop_exec+"\nTerminal=false\nX-GNOME-Autostart-enabled=true\n",encoding="utf-8")
        elif requested=="0":
            try: path.unlink()
            except FileNotFoundError: pass
        return path.is_file()
    def wallpapers(self):
        images=[]; videos=[]
        try: entries=sorted(self.server.fundos.iterdir(),key=lambda p:p.name.casefold())
        except OSError: entries=[]
        for f in entries:
            if not f.is_file() or f.name.startswith("."): continue
            url="/fundos/"+urllib.parse.quote(f.name)
            if f.suffix.lower() in IMAGE: images.append(url)
            elif f.suffix.lower() in VIDEO: videos.append(url)
        return {"images":images,"videos":videos}
    def serve_fund(self,name):
        if not name or "/" in name or "\\" in name or name.startswith("."): self.send_body(404,b"404","text/plain"); return
        file=(self.server.fundos/name).resolve()
        if file.parent!=self.server.fundos or not file.is_file() or file.suffix.lower() not in IMAGE|VIDEO:
            self.send_body(404,b"404","text/plain"); return
        self.serve_file(file)
    def serve_static(self,path):
        rel=path.lstrip("/") or "index.html"
        if "\\" in rel or "\0" in rel or any(x in (".","..") for x in Path(rel).parts): self.send_body(404,b"404","text/plain"); return
        data,ctype=generated_asset(self.server.web,rel)
        if data is not None: self.send_body(200,data,ctype or "application/octet-stream"); return
        file=(self.server.web/rel).resolve()
        if self.server.web not in file.parents or not file.is_file(): self.send_body(404,b"404","text/plain"); return
        self.serve_file(file)
    def serve_file(self,file):
        try:
            size=file.stat().st_size; start=0; end=size-1; status=200; extra={}
            range_header=self.headers.get("Range","")
            if range_header:
                m=re.fullmatch(r"bytes=(\d*)-(\d*)",range_header.strip())
                if not m or size==0: self.send_body(416,b"","application/octet-stream",{"Content-Range":"bytes */"+str(size)}); return
                if m.group(1): start=int(m.group(1)); end=int(m.group(2)) if m.group(2) else size-1
                else: start=max(0,size-int(m.group(2) or "0"))
                if start>=size or end<start: self.send_body(416,b"","application/octet-stream",{"Content-Range":"bytes */"+str(size)}); return
                end=min(end,size-1,start+CHUNK-1); status=206
                extra["Content-Range"]="bytes %d-%d/%d"%(start,end,size)
            length=max(0,end-start+1); ctype=mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            self.send_response(status); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(length))
            self.send_header("Accept-Ranges","bytes"); self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff")
            for k,v in extra.items(): self.send_header(k,v)
            self.end_headers()
            with file.open("rb") as f:
                f.seek(start); remaining=length
                while remaining:
                    block=f.read(min(262144,remaining))
                    if not block: break
                    self.wfile.write(block); remaining-=len(block)
        except (OSError,BrokenPipeError): return

def main():
    p=argparse.ArgumentParser(description="Smart TV OS Linux backend")
    p.add_argument("--web",type=Path,default=REPO/"web")
    p.add_argument("--fundos",type=Path,default=Path.home()/"Pictures"/"SmartTV"/"Fundos")
    p.add_argument("--port",type=int,default=PORT)
    a=p.parse_args(); web=a.web.expanduser().resolve()
    if not web.is_dir(): p.error("web directory not found: "+str(web))
    fundos=a.fundos.expanduser(); fundos.mkdir(parents=True,exist_ok=True)
    server=SmartTVServer(("127.0.0.1",a.port),Handler,web,fundos)
    print("Smart TV OS listening on http://127.0.0.1:%d/"%a.port,flush=True)
    try: server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0

if __name__=="__main__": raise SystemExit(main())
