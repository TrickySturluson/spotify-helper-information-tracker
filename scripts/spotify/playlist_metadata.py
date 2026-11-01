#!/usr/bin/env python3
"""Enrich playlist artist metadata from Last.fm without changing playlist contents."""
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import playlist_intelligence as intelligence

PROFILE_PATH = Path('assistant_data/music/artist_profiles.json')
MOOD_TAGS = {'dark','happy','sad','melancholic','aggressive','dreamy','chill','energetic','romantic','haunting','eerie','angry','uplifting','nostalgic','atmospheric','moody'}
NON_GENRE_TAGS = {'american','british','canadian','german','french','japanese','russian','swedish','australian','new york','brooklyn','united states','usa','uk','male vocalists','female vocalists','seen live','favorites','favorite'}

def enrich_artists(artists, api_key, path=PROFILE_PATH, sleep=time.sleep):
    profiles = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    known = {intelligence.norm(row.get('artist')) for row in profiles.values() if isinstance(row, dict)}
    missing = list(dict.fromkeys(name for name in artists if intelligence.norm(name) not in known))
    enriched, unavailable = [], []
    for artist in missing:
        query = urllib.parse.urlencode({'method':'artist.getTopTags','artist':artist,'api_key':api_key,'format':'json','autocorrect':1})
        request = urllib.request.Request('https://ws.audioscrobbler.com/2.0/?'+query, headers={'User-Agent':'TrickyLastFM/1.0 (playlist metadata enrichment)'})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode('utf-8'))
            raw = (payload.get('toptags') or {}).get('tag') or []
            tags = [{'tag':str(row.get('name','')).strip(),'count':int(row.get('count') or 0)} for row in raw if row.get('name')]
            tags.sort(key=lambda row: -row['count'])
            if not tags:
                unavailable.append(artist)
                continue
            genres = [row['tag'] for row in tags if row['count'] >= 10 and intelligence.norm(row['tag']) not in NON_GENRE_TAGS][:6]
            moods = [row['tag'] for row in tags if intelligence.norm(row['tag']) in MOOD_TAGS][:6]
            themes = [row['tag'] for row in tags if row['tag'] not in genres and row['tag'] not in moods][:8]
            key = 'name:' + hashlib.sha1(intelligence.norm(artist).encode('utf-8')).hexdigest()[:16]
            profiles[key] = {'artist_id':key,'artist':artist,'artist_mbid':None,'plays':0,'status':'matched','tags':tags[:20],'genres':genres,'moods':moods,'themes':themes,'source':'Last.fm artist.getTopTags (playlist enrichment)','checked_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'retry_after':0}
            enriched.append(artist)
        except Exception:
            unavailable.append(artist)
        sleep(0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return {'requested':len(missing),'enriched':enriched,'unavailable':unavailable,'known_before':len(artists)-len(missing)}
