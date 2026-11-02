#!/usr/bin/env python3
"""Local Spotify playlist manager. Playlists are locked unless explicitly unlocked."""
import argparse, base64, hashlib, json, os, re, secrets, sys, time, urllib.error
from collections import Counter
import urllib.parse, urllib.request, webbrowser
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CID=os.environ.get("SPOTIFY_CLIENT_ID","").strip()
REDIRECT="http://127.0.0.1:8888/callback"
SCOPES="user-read-private user-library-read playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"
TOKEN=Path(".spotify_playlist_token.json")
CONFIG=Path(".spotify_playlist_manager.json")
BACKUPS=Path("playlist_backups")
AUDIT=Path("playlist_manager_audit.jsonl")
API="https://api.spotify.com/v1"
class ManagerError(RuntimeError): pass

SPOTIFY_COOLDOWN = Path(".github/spotify_api_cooldown.json")

def stamp(): return datetime.now(timezone.utc).isoformat()

def check_spotify_cooldown():
    """Fail closed while a previously reported Spotify Retry-After is active."""
    state = read(SPOTIFY_COOLDOWN, {})
    if not isinstance(state, dict):
        raise ManagerError("Spotify cooldown state is invalid; refusing API requests.")
    until = state.get("cooldown_until")
    if not until:
        return
    try:
        deadline = datetime.fromisoformat(until.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ManagerError("Spotify cooldown timestamp is invalid; refusing API requests.")
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
    if remaining > 0:
        hours, remainder = divmod(int(remaining), 3600)
        minutes = remainder // 60
        raise ManagerError(
            f"Spotify API cooldown is active until {deadline.astimezone(timezone.utc).isoformat()} "
            f"(about {hours}h {minutes}m remaining). No Spotify request was sent."
        )
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
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            detail=json.loads(e.read().decode(errors="replace"))
        except (ValueError, UnicodeDecodeError):
            detail={}
        if data.get("grant_type")=="refresh_token" and detail.get("error")=="invalid_grant":
            raise ManagerError("Spotify refresh token is expired, revoked, or invalid. Reauthorize the playlist manager locally, then update the SPOTIFY_REFRESH_TOKEN GitHub Actions secret. Spotify refresh tokens expire after six months; refreshing an access token does not extend that lifetime.") from e
        reason=detail.get("error_description") or detail.get("error") or "unknown token error"
        raise ManagerError(f"Spotify token request failed (HTTP {e.code}): {reason}") from e
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
    def __init__(self):
        check_spotify_cooldown()
        self.t=read(TOKEN,None) or authorize()
        self.refresh_token_rotated=False
        self.request_metrics = {"total_requests": 0, "by_endpoint": {}, "by_status": {}, "elapsed_ms": 0}
    @staticmethod
    def metric_endpoint(path):
        # Remove query strings and Spotify IDs; metrics must not expose playlist IDs or search terms.
        clean = path.split("?", 1)[0]
        clean = re.sub(r"/[A-Za-z0-9]{22}(?=/|$)", "/{id}", clean)
        return clean or "/"
    def record_request(self, method, path, status, elapsed_ms):
        metrics = self.request_metrics
        endpoint = f"{method.upper()} {self.metric_endpoint(path)}"
        row = metrics["by_endpoint"].setdefault(endpoint, {"count": 0, "status_counts": {}, "elapsed_ms": 0})
        row["count"] += 1
        row["elapsed_ms"] += round(elapsed_ms, 2)
        status_key = str(status)
        row["status_counts"][status_key] = row["status_counts"].get(status_key, 0) + 1
        metrics["by_status"][status_key] = metrics["by_status"].get(status_key, 0) + 1
        metrics["total_requests"] += 1
        metrics["elapsed_ms"] += round(elapsed_ms, 2)
    def bearer(self):
        if time.time()>=self.t.get("obtained_at",0)+self.t.get("expires_in",3600)-60:
            old=self.t
            self.t=token_post({"client_id":CID,"grant_type":"refresh_token","refresh_token":old["refresh_token"]})
            replacement=self.t.get("refresh_token")
            self.refresh_token_rotated=bool(replacement and replacement!=old["refresh_token"])
            self.t["refresh_token"]=replacement or old["refresh_token"]
            self.t["obtained_at"]=time.time(); write(TOKEN,self.t)
        return self.t["access_token"]
    def call(self,method,path,body=None,retry=True):
        # Re-check before every request, not only client construction. This also
        # blocks recovery/cleanup code from issuing follow-up calls after a 429.
        check_spotify_cooldown()
        h={"Authorization":"Bearer "+self.bearer()}; data=None
        if body is not None: h["Content-Type"]="application/json"; data=json.dumps(body).encode()
        req=urllib.request.Request(API+path,data=data,headers=h,method=method)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read()
                self.record_request(method, path, r.status, (time.monotonic()-started)*1000)
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            self.record_request(method, path, e.code, (time.monotonic()-started)*1000)
            if e.code==401 and retry:
                self.t["obtained_at"]=0; return self.call(method,path,body,False)
            retry_after = e.headers.get("Retry-After")
            detail = e.read().decode(errors="replace")
            retry_note = f" Retry-After: {retry_after}" if retry_after else ""
            if e.code == 429:
                try:
                    payload = json.loads(detail)
                except (TypeError, ValueError):
                    payload = {}
                api_error = payload.get("error") if isinstance(payload, dict) else {}
                api_error = api_error if isinstance(api_error, dict) else {}
                reason = str(api_error.get("reason") or api_error.get("message") or "rate limit")
                if retry_after and retry_after.isdigit():
                    seconds = int(retry_after)
                    hours, remainder = divmod(seconds, 3600)
                    minutes = remainder // 60
                    wait = f"{hours}h {minutes}m" if hours else f"{minutes}m"
                    deadline = datetime.now(timezone.utc) + timedelta(seconds=seconds)
                    write(SPOTIFY_COOLDOWN, {
                        "cooldown_until": deadline.isoformat(),
                        "recorded_at": stamp(),
                        "retry_after_seconds": seconds,
                        "reason": reason,
                        "endpoint": f"{method} {path}",
                    })
                else:
                    wait = "the interval specified by Spotify"
                raise ManagerError(
                    f"Spotify API quota/rate limit reached on {method} {path} "
                    f"(HTTP 429; {reason}). Spotify says wait {wait} "
                    f"(Retry-After: {retry_after or 'not supplied'}). "
                    "No playlist changes were attempted. Do not retry read/preview "
                    "commands until the cooldown expires; repeated requests can "
                    "extend service restrictions."
                ) from e
            raise ManagerError(f"Spotify API {method} {path}: HTTP {e.code}:{retry_note} {detail}")
    def me(self): return self.call("GET","/me")
    def playlists(self):
        out=[]; url="/me/playlists?limit=50"
        while url:
            p=self.call("GET",url); out+=p.get("items",[]); url=p.get("next","")
            if url: url=url.replace("https://api.spotify.com/v1","")
        return out
    def items(self,pid,market=None):
        out=[]
        if market is not None and market != "from_token" and not re.fullmatch(r"[A-Z]{2}", str(market)):
            raise ManagerError("Invalid Spotify market; use an ISO country code or from_token.")
        url=f"/playlists/{pid}/items?limit=50&additional_types=track,episode"
        if market is not None:
            url += f"&market={market}"
        while url:
            p=self.call("GET",url); out+=p.get("items",[]); url=p.get("next","")
            if url: url=url.replace(API,"")
        return out

    def track(self,track_id,market=None):
        if not re.fullmatch(r"[A-Za-z0-9]{22}", str(track_id or "")):
            raise ManagerError("Invalid Spotify track ID.")
        if market is not None and market != "from_token" and not re.fullmatch(r"[A-Z]{2}", str(market)):
            raise ManagerError("Invalid Spotify market; use an ISO country code or from_token.")
        url=f"/tracks/{track_id}"
        if market is not None:
            url += f"?market={market}"
        return self.call("GET",url)

def config():
    c=read(CONFIG,{"version":1,"playlists":{}})
    if not isinstance(c,dict) or not isinstance(c.get("playlists"),dict): raise ManagerError("Invalid permission config; refusing edits.")
    return c
def permission_registry():
    path = Path("assistant_data/spotify/managed_playlists.json")
    data = read(path, {"version": 1, "managed": {}, "approved_exceptions": {
        "4yUVHSMQySfWeEowfIMcx7": {"name": "Tricky Daily", "reason": "Explicitly approved by the user"}
    }})
    if not isinstance(data, dict) or not isinstance(data.get("managed"), dict) or not isinstance(data.get("approved_exceptions"), dict):
        raise ManagerError("Invalid managed-playlist registry; refusing edits.")
    return data

def assert_managed(pid):
    registry = permission_registry()
    if pid in registry["managed"] or pid in registry["approved_exceptions"]:
        return
    raise ManagerError("BLOCKED: this playlist is protected. Only assistant-created playlists and explicitly approved exceptions may be modified; an unlock or APPLY confirmation cannot override this policy.")

def register_created(pid, name):
    path = Path("assistant_data/spotify/managed_playlists.json")
    registry = permission_registry()
    registry["managed"][pid] = {"name": name, "provenance": "created_by_shit", "created_at": stamp()}
    write(path, registry)

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
    if state == "unlocked":
        assert_managed(pid)
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
    BACKUPS.mkdir(exist_ok=True); path=BACKUPS/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"_"+s["playlist"]["id"]+".json")
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
    if not isinstance(name,str) or not name.strip() or len(name)>100:
        raise ManagerError("Playlist name must be 1–100 characters.")
    if not isinstance(description,str) or len(description)>300:
        raise ManagerError("Playlist description must be 300 characters or fewer.")
    me=sp.me(); p=sp.call("POST","/me/playlists",{"name":name,"description":description,"public":public})
    # Register provenance immediately: only SHIT-created playlists may be edited.
    register_created(p["id"], p["name"])
    c=config(); c["playlists"][p["id"]]={"name":p["name"],"state":"locked","updated_at":stamp()}; write(CONFIG,c)
    audit(event="created_locked",playlist_id=p["id"],name=p["name"])
    print(f'Created "{p["name"]}" ({p["id"]}); it is LOCKED by default.')
def validate(plan):
    if not isinstance(plan,dict) or not isinstance(plan.get("playlist_id"),str) or not isinstance(plan.get("operations"),list) or not plan["operations"]: raise ManagerError("Plan needs playlist_id and a non-empty operations list.")
    ops=[]
    for op in plan["operations"]:
        if not isinstance(op, dict):
            raise ManagerError("Each plan operation must be an object.")
        a=op.get("action")
        if a in ("add","remove","replace"):
            uris=op.get("uris")
            if not isinstance(uris,list) or not uris or any(
                not isinstance(u,str) or not u.startswith("spotify:track:")
                or not u[len("spotify:track:"):].strip()
                or any(ch.isspace() for ch in u)
                for u in uris
            ):
                raise ManagerError("Use a non-empty list of valid spotify:track: URIs.")
            ops.append({"action":a,"uris":uris})
        elif a=="reorder":
            vals=[op.get(k) for k in ("range_start","insert_before","range_length")]
            if any(not isinstance(n,int) or isinstance(n,bool) or n<0 for n in vals) or vals[2]<1: raise ManagerError("Invalid reorder range.")
            ops.append({"action":a,"range_start":vals[0],"insert_before":vals[1],"range_length":vals[2]})
        elif a=="details":
            name=op.get("name")
            description=op.get("description")
            if not isinstance(name,str) or not name.strip() or len(name)>100: raise ManagerError("Playlist name must be 1–100 characters.")
            if not isinstance(description,str) or len(description)>300: raise ManagerError("Playlist description must be 300 characters or fewer.")
            ops.append({"action":a,"name":name,"description":description})
        else: raise ManagerError(f"Unsupported action: {a}")
    return plan["playlist_id"],ops
def remove(sp,pid,uris):
    assert_managed(pid)
    for i in range(0,len(uris),100):
        if not unlocked(pid): raise ManagerError("Playlist is LOCKED; remaining removals stopped.")
        sp.call("DELETE",f"/playlists/{pid}/items",{"items":[{"uri":u} for u in uris[i:i+100]]})
def add(sp,pid,uris):
    assert_managed(pid)
    for i in range(0,len(uris),100):
        if not unlocked(pid): raise ManagerError("Playlist is LOCKED; remaining additions stopped.")
        sp.call("POST",f"/playlists/{pid}/items",{"uris":uris[i:i+100]})
def apply(sp,path):
    pid,ops=validate(read(path,None))
    assert_managed(pid)
    if not unlocked(pid): raise ManagerError("BLOCKED: playlist is LOCKED. Unlock it explicitly first.")
    me,p=owned(sp,pid); before=snapshot(sp,p)
    print(f'\nPREVIEW — {p.get("name")} [{pid}]')
    print(f'Current items: {len(before["items"])}')
    present=Counter(x["uri"] for x in before["items"] if x and x.get("uri"))
    for op in ops:
        if op["action"] in ("add","remove","replace"):
            print(f'  {op["action"].upper()} {len(op["uris"])} track(s)')
            for u in op["uris"]: print("    "+u)
            repeated=[u for u,n in Counter(op["uris"]).items() if n>1]
            if op["action"]=="add":
                already=[u for u in op["uris"] if present[u]]
                if already: print(f"    NOTE: {len(already)} requested item(s) already occur in this playlist.")
            if repeated: print(f"    NOTE: {len(repeated)} URI(s) repeat within this operation.")
            if op["action"]=="remove":
                missing=[u for u in op["uris"] if not present[u]]
                if missing: print(f"    NOTE: {len(missing)} requested removal(s) are not currently present.")
        else: print(f'  REORDER start={op["range_start"]}, insert_before={op["insert_before"]}, length={op["range_length"]}')
    print("No changes have been made.")
    phrase="REPLACE" if any(o["action"]=="replace" for o in ops) else "APPLY"
    if input(f'Type {phrase} exactly to confirm (anything else cancels): ').strip()!=phrase:
        audit(event="cancelled",playlist_id=pid); print("Cancelled."); return
    assert_managed(pid)
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
    sub.add_parser("export-refresh-token", help="Print the playlist manager refresh token for copying into GitHub Actions Secrets.")
    x=sub.add_parser("inspect"); x.add_argument("playlist_id")
    for name in ("lock","unlock"):
        x=sub.add_parser(name); x.add_argument("playlist_id")
    x=sub.add_parser("create"); x.add_argument("name"); x.add_argument("--description",default=""); x.add_argument("--public",action="store_true")
    x=sub.add_parser("apply"); x.add_argument("plan_file",type=Path)
    a=ap.parse_args()
    try:
        sp=Spotify()
        if a.cmd=="list": list_playlists(sp)
        elif a.cmd=="export-refresh-token":
            token=sp.t.get("refresh_token")
            if not token: raise ManagerError("No refresh token is available; authorize again.")
            print(token)
        elif a.cmd=="inspect": inspect(sp,a.playlist_id)
        elif a.cmd=="lock": set_lock(sp,a.playlist_id,"locked")
        elif a.cmd=="unlock": set_lock(sp,a.playlist_id,"unlocked")
        elif a.cmd=="create": create(sp,a.name,a.description,a.public)
        elif a.cmd=="apply": apply(sp,a.plan_file)
        return 0
    except (ManagerError,OSError,KeyError,ValueError,urllib.error.URLError) as e:
        print("ERROR:",e,file=sys.stderr); return 1
    finally:
        if "sp" in locals():
            print("SPOTIFY_REQUEST_METRICS=" + json.dumps(sp.request_metrics, sort_keys=True), file=sys.stderr)
if __name__=="__main__": raise SystemExit(main())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Local Spotify playlist manager. Playlists are locked unless explicitly unlocked.
# Location: Maintained implementation in scripts/spotify/spotify_playlist_manager.py.
# Data flow: Uses the canonical archives and/or generated project data; consult
#            this module's configuration and command options for exact paths.
# Run: python compat/spotify_playlist_manager.py (legacy command entry point, when applicable).
# Related: tests/ contains regression coverage; docs/ contains extended guides.
# -----------------------------------------------------------------------------
