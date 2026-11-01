#!/usr/bin/env python3
"""Confidence-aware rolling listening trends for Tricky Daily."""
import json, math, re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCROBBLES=Path("data/scrobbles.json")
PROFILES=Path("assistant_data/music/artist_profiles.json")
OUTPUT=Path("assistant_data/spotify/listening_trends.json")
VERSION="listening-trends-v1"

def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()

def timestamp(row):
    value=row.get("timestamp") or row.get("uts") or row.get("date")
    if isinstance(value,dict): value=value.get("uts") or value.get("#text")
    try:
        if isinstance(value,(int,float)) or str(value).isdigit():
            return datetime.fromtimestamp(int(value),timezone.utc)
        parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (TypeError,ValueError,OverflowError,OSError): return None

def artist_of(row):
    value=row.get("artist") or row.get("artist_name") or ""
    return (value.get("#text") or value.get("name") or "") if isinstance(value,dict) else value

def profile_index(payload):
    rows=payload.values() if isinstance(payload,dict) else payload if isinstance(payload,list) else []
    result={}
    for row in rows:
        if isinstance(row,dict):
            name=row.get("artist") or row.get("name")
            if name: result[norm(name)]=row
    return result

def tags_of(row):
    tags=[]
    for field in ("genres","tags","genre_tags"):
        values=row.get(field) or []
        if isinstance(values,dict): values=values.keys()
        for value in values:
            if isinstance(value,dict): value=value.get("name") or value.get("tag")
            label=norm(value)
            if label and label not in tags: tags.append(label)
    return tags

def _count(events,start,end):
    return Counter(artist for when,artist in events if start<=when<end)

def _momentum(recent,baseline,recent_days,baseline_days):
    if recent<=0 or baseline<=0: return None
    lift=(recent/recent_days)/(baseline/baseline_days)
    return round(max(0.0,min(1.0,0.5+math.log(max(.25,lift),4)/2)),4)

def build_trends(scrobbles,artist_profiles=None,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: now=now.replace(tzinfo=timezone.utc)
    now=now.astimezone(timezone.utc)
    events=[]; malformed=0
    for row in scrobbles:
        if not isinstance(row,dict): malformed+=1; continue
        name=norm(artist_of(row)); when=timestamp(row)
        if not name or when is None or when>now: malformed+=1; continue
        events.append((when,name))
    events.sort()
    d7=now-timedelta(days=7); d30=now-timedelta(days=30); d90=now-timedelta(days=90)
    d14=now-timedelta(days=14)
    c7=_count(events,d7,now+timedelta(microseconds=1))
    prev7=_count(events,d14,d7)
    c30=_count(events,d30,now+timedelta(microseconds=1))
    c90=_count(events,d90,now+timedelta(microseconds=1))
    prev60=_count(events,d90,d30)
    alltime=Counter(artist for _,artist in events)
    profiles=profile_index(artist_profiles or {})
    artists={}
    for artist in set(c90)|set(prev60)|set(alltime):
        recent,short,baseline=c30[artist],c7[artist],prev60[artist]
        mom30=_momentum(recent,baseline,30,60)
        mom7=_momentum(short,prev7[artist],7,7)
        artists[artist]={
            "plays_7d":short,"plays_30d":recent,"plays_previous_60d":baseline,
            "plays_90d":c90[artist],"plays_previous_7d":prev7[artist],"plays_all_time":alltime[artist],
            "momentum_30d":mom30,"momentum_7d":mom7,"tags":tags_of(profiles.get(artist,{})),
            "trend_confidence":"high" if recent>=8 and baseline>=8 else "medium" if recent>=3 and baseline>=3 else "low"
        }
    genre_counts=Counter(); genre_previous=Counter()
    for row in artists.values():
        for tag in row["tags"]:
            genre_counts[tag]+=row["plays_30d"]
            genre_previous[tag]+=row["plays_previous_60d"]
    total30=sum(c30.values()); totalprev=sum(prev60.values())
    return {
        "version":VERSION,"generated_at":now.isoformat(),"source":"data/scrobbles.json",
        "coverage":{"scrobbles_total":len(events),"malformed_rows":malformed,
            "recent_30d_scrobbles":total30,"previous_60d_scrobbles":totalprev,
            "status":"available" if total30>=10 and totalprev>=10 else "low"},
        "windows":{"7d":dict(c7),"30d":dict(c30),"previous_60d":dict(prev60),"90d":dict(c90)},
        "artists":artists,
        "genres":[{"tag":tag,"plays_30d":count,"plays_previous_60d":genre_previous[tag],
                    "momentum_30d":_momentum(count,genre_previous[tag],30,60),
                    "share_30d":round(count/total30,4) if total30 else 0}
                  for tag,count in genre_counts.most_common(40)],
        "baseline":{"all_time_scrobbles":len(events),"unique_artists":len(alltime),
            "recent_vs_previous_60d_rate":round((total30/30)/(totalprev/60),4) if totalprev else None},
        "method":{"recent_window_days":30,"short_window_days":7,"short_comparison_window_days":7,"comparison_window_days":60,
            "sparse_history_is_unknown":True,"daily_rotation_is_not_negative":True}
    }

def candidate_affinity(artist,report,candidate_tags=None):
    report=report or {}
    row=report.get("artists",{}).get(norm(artist),{})
    artist_score=row.get("momentum_30d") if row.get("trend_confidence") in ("medium","high") else None
    genre_rows={item.get("tag"):item for item in report.get("genres",[]) if isinstance(item,dict)}
    matched=[genre_rows[tag] for tag in (candidate_tags or []) if tag in genre_rows
             and genre_rows[tag].get("momentum_30d") is not None
             and (genre_rows[tag].get("plays_30d",0)>=8 or genre_rows[tag].get("plays_previous_60d",0)>=8)]
    genre_score=sum(item["momentum_30d"] for item in matched)/len(matched) if matched else None
    signals=[value for value in (artist_score,genre_score) if value is not None]
    if not signals:
        return 0.0,"low",[]
    score=sum(signals)/len(signals)
    confidence="high" if (artist_score is not None and row.get("trend_confidence")=="high") or len(matched)>=2 else "medium"
    reasons=[]
    if artist_score is not None: reasons.append("artist is present in recent listening")
    if genre_score is not None: reasons.append("candidate tags overlap with rising listening trends")
    if row.get("momentum_7d") is not None and row["momentum_7d"]>=.65:
        reasons.append("artist is gaining short-term momentum")
    return max(0,min(1,score)),confidence,reasons

def generate(scrobbles_path=SCROBBLES,profiles_path=PROFILES,output_path=OUTPUT,now=None):
    scrobbles=json.loads(scrobbles_path.read_text(encoding="utf-8"))
    profiles=json.loads(profiles_path.read_text(encoding="utf-8")) if profiles_path.is_file() else {}
    report=build_trends(scrobbles,profiles,now)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    temp=output_path.with_suffix(output_path.suffix+".tmp")
    temp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(output_path)
    return report

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scrobbles",type=Path,default=SCROBBLES)
    parser.add_argument("--profiles",type=Path,default=PROFILES)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args()
    result=generate(args.scrobbles,args.profiles,args.output)
    print("Listening trends:",result["coverage"]["status"],"| recent scrobbles:",result["coverage"]["recent_30d_scrobbles"])

# FILE OVERVIEW
# Purpose: User-wide listening momentum and established-taste profile for Daily.
# Inputs: Last.fm scrobbles and artist genre/tag metadata.
# Outputs: 7/30/90-day activity, prior-60-day comparisons, tags, confidence, coverage.
# Safety: Sparse data is unknown; trend scores never hard-filter recommendations.
