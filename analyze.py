import json, collections

with open("seed_shows.json", "r") as f:
    data = json.load(f)

VALID_SECTIONS = {"featured","series","minisodes","songs"}
VALID_CATEGORIES = {"adventure","folk","friendship","india","language","learning","maths","music","nature","reading","science","singalong","stories","travel","values"}
VALID_LANGUAGES = {"en","hi"}

print("=== 1. SECTIONS ===")
for ep in data:
    s = ep.get("section")
    if s not in VALID_SECTIONS:
        print(f"  {ep['episode_id']} ({ep['show_title']}) section={repr(s)}")

print("\n=== 2. DUPLICATE (content_group, language) ===")
seen = {}
for ep in data:
    key = (ep["content_group"], ep["language"])
    if key in seen:
        print(f"  DUPE: {ep['episode_id']} clashes with {seen[key]['episode_id']}")
        print(f"    cg={ep['content_group']}, lang={ep['language']}")
        print(f"    title1={seen[key]['episode_title']!r}, title2={ep['episode_title']!r}")
        print(f"    ep_num1={seen[key]['episode_number']}, ep_num2={ep['episode_number']}")
    else:
        seen[key] = ep

print("\n=== 3. CASING ANOMALIES ===")
for ep in data:
    t = ep.get("episode_title","")
    if t == t.lower() and len(t.split()) > 1:
        print(f"  {ep['episode_id']} all-lowercase title: {repr(t)}")
    elif len(t.split()) > 1 and all(w.isupper() for w in t.split() if w.isalpha()):
        print(f"  {ep['episode_id']} ALL-CAPS title: {repr(t)}")

print("\n=== 4. SEASON 0 TRAILERS ===")
for ep in data:
    if ep["season_number"] == 0:
        art = ep.get("artwork_available", [])
        print(f"  {ep['episode_id']} ({ep['show_title']}) art={art}, dur={ep['duration_seconds']}s status={ep['status']}")

print("\n=== 5. MISSING ARTWORK ON PUBLISHED ===")
for ep in data:
    if ep.get("status") == "published" and not ep.get("artwork_available"):
        print(f"  {ep['episode_id']} ({ep['show_title']}) s{ep['season_number']}e{ep['episode_number']} {ep['episode_title']!r}")

print("\n=== 6. NON-SEQUENTIAL IDs ===")
for ep in data:
    eid = ep["episode_id"]
    if not eid.startswith("ep_0"):
        print(f"  {eid}: s{ep['season_number']}e{ep['episode_number']} {ep['episode_title']!r} lang={ep['language']}")
        print(f"    content_group={ep['content_group']}, ep_number={ep['episode_number']}")

print("\n=== 7. STATUSES ===")
print(dict(collections.Counter(ep["status"] for ep in data)))

print("\n=== 8. SINGLE-LANGUAGE CONTENT GROUPS (no bilingual pair) ===")
cg_langs = collections.defaultdict(set)
for ep in data:
    if ep["season_number"] != 0:
        cg_langs[ep["content_group"]].add(ep["language"])
solo = {cg: langs for cg, langs in cg_langs.items() if len(langs) == 1}
by_show = collections.defaultdict(list)
for ep in data:
    if ep["content_group"] in solo:
        by_show[ep["show_title"]].append(ep["content_group"])
for show, cgs in by_show.items():
    print(f"  {show}: {len(set(cgs))} solo content groups")

print("\n=== DONE ===")
