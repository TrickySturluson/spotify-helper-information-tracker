#!/usr/bin/env python3
"""Local Spotify playlist manager. Playlists are locked unless explicitly unlocked."""
import argparse, base64, hashlib, json, os, secrets, sys, time, urllib.error
import urllib.parse, urllib.request, webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CID=os.environ.get("SPOTIFY_CLIENT_ID","").strip()
REDIRECT="http://127.0.0.1:8888/callback"
SCOPES="user-read-private playlist-read-private playlist-modify-private playlist-modify-public"
TOKEN=Path(".spotify_playlist_token.json")
CONFIG=Path(".spotify_playlist_manager.json")
BACKUPS=Path("playlist_backups")
AUDIT=Path("playlist_manager_audit.jsonl")
API="https://api.spotify.com/v1"
class ManagerError(RuntimeError): pass

def stamp(): return datetime.now(timezone.utc).isoformat()
def read(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e: raise ManagerError(f"Cannot read {path}: {e}")
def write(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    try: tmp.chmod(0o600)
    except OSError: pass
    tmp.replace(path)
def audit(**event):
    with AUDIT.open("a",encoding="utf-8") as f: f.write(json.dumps({"at":stamp(),**event})+"\n")
    try: AUDIT.chmod(0o600)
    except OSError: pass
def token_post(data):
    req=urllib.request.Request("https://accounts.spotify.com/api/token",data=urllib.parse.urlencode(data).encode(),headers={"Content-Type":"application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read())
def authorize():
    if not CID: raise ManagerError("Set SPOTIFY_CLIENT_ID to your Spotify app Client ID.")
    verifier=secrets.token_urlsafe(64)[:96]
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state=secrets.token_urlsafe(24)
    q=urllib.parse.urlencode({"client_id":CID,"response_type":"code","redirect_uri":REDIRECT,"scope":SCOPES,"state":state,"code_challenge_method":"S256","code_challenge":challenge})
    result={}
    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            p=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if p.get("state",[""])[0]!=state: result["error"]="OAuth state mismatch"
            elif "error" in p: result["error"]=p["error"][0]
            else: result["code"]=p.get("code",[""])[0]
            self.send_response(200 if "code" in result else 400); self.end_headers()
            self.wfile.write(b"Spotify authorization received. You may close this window.")
        def log_message(self,*a): pass
    try: server=HTTPServer(("127.0.0.1",8888),Callback)
    except OSError as e: raise ManagerError("Port 8888 is busy. Stop the playback tracker and retry.") from e
    server.timeout=180; url="https://accounts.spotify.com/authorize?"+q
    print("Opening Spotify authorization:",url); webbrowser.open(url); server.handle_request(); server.server_close()
    if "code" not in result: raise ManagerError(result.get("error","Spotify authorization timed out."))
    t=token_post({"client_id":CID,"grant_type":"authorization_code","code":result["code"],"redirect_uri":REDIRECT,"code_verifier":verifier})
    t["obtained_at"]=time.time(); write(TOKEN,t); return t

class Spotify:
    def __init__(self): self.t=read(TOKEN,None) or authorize()
    def bearer(self):
        if time.time()>=self.t.get("obtained_at",0)+self.t.get("expires_in",3600)-60:
            old=self.t
            self.t=token_post({"client_id":CID,"grant_type":"refresh_token","refresh_token":old["refresh_token"]})
            self.t["refresh_token"]=self.t.get("refresh_token",old["refresh_token"]); self.t["obtained_at"]=time.time(); write(TOKEN,self.t)
        return self.t["access_token"]
    def call(self,method,path,body=None,retry=True):
        h={"Authorization":"Bearer "+self.bearer()}; data=None
        if body is not None: h["Content-Type"]="application/json"; data=json.dumps(body).encode()
        req=urllib.request.Request(API+path,data=data,headers=h,method=method)
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read(); return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code==401 and retry:
                self.t["obtained_at"]=0; return self.call(method,path,body,False)
            detail=e.read().decode(errors="replace")
            raise ManagerError(f"Spotify API {method} {path}: HTTP {e.code}: {detail}")
    def me(self): return self.call("GET","/me")
    def playlists(self):
        out=[]; url="/me/playlists?limit=50"
        while url:
            p=self.call("GET",url); out+=p.get("items",[]); url=p.get("next","")
            if url: url=url.replace("https://api.spotify.com/v1","")
        return out
    def items(self,pid):
        out=[]; url=f"/playlists/{pid}/items?limit=100"
        while url:
            p=self.call("GET",url); out+=p.get("items",[]); url=p.get("next","")
            if url: url=url.replace(API,"")
        return out

def config():
    c=read(CONFIG,{"version":1,"playlists":{}})
    if not isinstance(c,dict) or not isinstance(c.get("playlists"),dict): raise ManagerError("Invalid permission config; refusing edits.")
    return c
def unlocked(pid): return config()["playlists"].get(pid,{}).get("state")=="unlocked"
def find(sp,pid):
    p=next((x for x in sp.playlists() if x.get("id")==pid),None)
    if not p: raise ManagerError("Playlist not found in your Spotify playlist collection.")
    return p
def owned(sp,pid):
    me=sp.me(); p=find(sp,pid)
    if (p.get("owner") or {}).get("id")!=me.get("id"): raise ManagerError("Only playlists owned by this account can be edited.")
    return me,p
def set_lock(sp,pid,state):
    p=find(sp,pid); c=config()
    c["playlists"][pid]={"name":p.get("name",""),"state":state,"updated_at":stamp()}
    write(CONFIG,c); audit(event="permission_changed",playlist_id=pid,name=p.get("name"),state=state)
    print(p.get("name"),"is now",state.upper())
def tracks(sp,p):
    rows=[]
    for entry in sp.items(p["id"]):
        t=entry.get("item") or entry.get("track")
        rows.append({"uri":(t or {}).get("uri"),"name":(t or {}).get("name"),"artists":[a.get("name") for a in (t or {}).get("artists",[])],"album":((t or {}).get("album") or {}).get("name")})
    return rows
def snapshot(sp,p):
    return {"created_at":stamp(),"playlist":{"id":p["id"],"name":p.get("name"),"snapshot_id":p.get("snapshot_id")},"items":tracks(sp,p)}
def save_snapshot(s):
    BACKUPS.mkdir(exist_ok=True); path=BACKUPS/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+s["playlist"]["id"]+".json")
    write(path,s); return str(path)
def list_playlists(sp):
    for p in sp.playlists():
        state="UNLOCKED" if unlocked(p["id"]) else "LOCKED"
        print(f'[{state:8}] {p.get("name")} | {(p.get("items") or p.get("tracks") or {}).get("total","?")} tracks | {p["id"]}')
def inspect(sp,pid):
    p=find(sp,pid); rows=tracks(sp,p)
    print(f'{p.get("name")} [{pid}] — {"UNLOCKED" if unlocked(pid) else "LOCKED"} — {len(rows)} items')
    for i,t in enumerate(rows,1): print(f'{i:3}. {", ".join(t["artists"] or [])} — {t["name"] or "[unavailable item]"}')
def create(sp,name,description,public):
    me=sp.me(); p=sp.call("POST","/me/playlists",{"name":name,"description":description,"public":public})
    c=config(); c["playlists"][p["id"]]={"name":p["name"],"state":"locked","updated_at":stamp()}; write(CONFIG,c)
    audit(event="created_locked",playlist_id=p["id"],name=p["name"])
    print(f'Created "{p["name"]}" ({p["id"]}); it is LOCKED by default.')
def validate(plan):
    if not isinstance(plan,dict) or not isinstance(plan.get("playlist_id"),str) or not isinstance(plan.get("operations"),list) or not plan["operations"]: raise ManagerError("Plan needs playlist_id and a non-empty operations list.")
    ops=[]
    for op in plan["operations"]:
        a=op.get("action")
        if a in ("add","remove","replace"):
            uris=op.get("uris")
            if not isinstance(uris,list) or not uris or any(not isinstance(u,str) or not u.startswith("spotify:track:") for u in uris): raise ManagerError("Use a non-empty list of spotify:track: URIs.")
            ops.append({"action":a,"uris":uris})
        elif a=="reorder":
            vals=[op.get(k) for k in ("range_start","insert_before","range_length")]
            if any(not isinstance(n,int) or n<0 for n in vals) or vals[2]<1: raise ManagerError("Invalid reorder range.")
            ops.append({"action":a,"range_start":vals[0],"insert_before":vals[1],"range_length":vals[2]})
        else: raise ManagerError(f"Unsupported action: {a}")
    return plan["playlist_id"],ops
def remove(sp,pid,uris):
    for i in range(0,len(uris),100): sp.call("DELETE",f"/playlists/{pid}/items",{"items":[{"uri":u} for u in uris[i:i+100]]})
def add(sp,pid,uris):
    for i in range(0,len(uris),100): sp.call("POST",f"/playlists/{pid}/items",{"uris":uris[i:i+100]})
def apply(sp,path):
    pid,ops=validate(read(path,None))
    if not unlocked(pid): raise ManagerError("BLOCKED: playlist is LOCKED. Unlock it explicitly first.")
    me,p=owned(sp,pid); before=snapshot(sp,p)
    print(f'\nPREVIEW — {p.get("name")} [{pid}]')
    print(f'Current items: {len(before["items"])}')
    for op in ops:
        if op["action"] in ("add","remove","replace"):
            print(f'  {op["action"].upper()} {len(op["uris"])} track(s)')
            for u in op["uris"]: print("    "+u)
        else: print(f'  REORDER start={op["range_start"]}, insert_before={op["insert_before"]}, length={op["range_length"]}')
    print("No changes have been made.")
    phrase="REPLACE" if any(o["action"]=="replace" for o in ops) else "APPLY"
    if input(f'Type {phrase} exactly to confirm (anything else cancels): ').strip()!=phrase:
        audit(event="cancelled",playlist_id=pid); print("Cancelled."); return
    if not unlocked(pid): raise ManagerError("Blocked: playlist was locked after preview.")
    me,p2=owned(sp,pid)
    if p2.get("snapshot_id")!=p.get("snapshot_id"): raise ManagerError("Playlist changed after preview. Re-run to review the latest state.")
    backup=save_snapshot(before)
    audit(event="change_started",playlist_id=pid,name=p2.get("name"),operations=ops,backup=backup,user_id=me.get("id"))
    for op in ops:
        if not unlocked(pid): raise ManagerError("Playlist was locked during the operation; remaining changes stopped.")
        a=op["action"]
        if a=="add": add(sp,pid,op["uris"])
        elif a=="remove": remove(sp,pid,op["uris"])
        elif a=="replace":
            current=[x["uri"] for x in tracks(sp,find(sp,pid)) if x.get("uri")]
            if current: remove(sp,pid,current)
            add(sp,pid,op["uris"])
        else: sp.call("PUT",f"/playlists/{pid}/items",{**{k:op[k] for k in ("range_start","insert_before","range_length")},"snapshot_id":find(sp,pid).get("snapshot_id")})
    audit(event="change_completed",playlist_id=pid,backup=backup,operations=ops)
    print("Done. Pre-change snapshot:",backup)

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list")
    x=sub.add_parser("inspect"); x.add_argument("playlist_id")
    for name in ("lock","unlock"):
        x=sub.add_parser(name); x.add_argument("playlist_id")
    x=sub.add_parser("create"); x.add_argument("name"); x.add_argument("--description",default=""); x.add_argument("--public",action="store_true")
    x=sub.add_parser("apply"); x.add_argument("plan_file",type=Path)
    a=ap.parse_args()
    try:
        sp=Spotify()
        if a.cmd=="list": list_playlists(sp)
        elif a.cmd=="inspect": inspect(sp,a.playlist_id)
        elif a.cmd=="lock": set_lock(sp,a.playlist_id,"locked")
        elif a.cmd=="unlock": set_lock(sp,a.playlist_id,"unlocked")
        elif a.cmd=="create": create(sp,a.name,a.description,a.public)
        elif a.cmd=="apply": apply(sp,a.plan_file)
        return 0
    except (ManagerError,OSError,KeyError,ValueError,urllib.error.URLError) as e:
        print("ERROR:",e,file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
