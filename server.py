#!/usr/bin/env python3
"""Turnajovy scheduler - Prague Crocodiles"""

import asyncio, json, datetime, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

try:
    from spond import spond as spond_lib
    SPOND_AVAILABLE = True
except ImportError:
    SPOND_AVAILABLE = False
    print("pip install spond")

MEMBERS_BY_TEAM = {
    "Muži": [
        "Ales Hanacek", "Jan Illetško", "jakub kopáč", "Jakub Strejc",
        "marek Černý", "Martin Černík", "Petr Marschall",
        "Samuel Lepšík", "Tomáš reiter", "Vil K",
    ],
    "Ženy": [
        "Anna Tomiová", "Eliška Lněničková", "Jana Možíšová",
        "Jitka Vondráčková", "Kamča K", "Kateřina Jochová",
        "Luci Beránkova", "Lucie Vobořilová Vaňkátová", "Vanesa Langerová",
    ],
    "Mix A": [
        "Jan Illetško", "jakub kopáč", "Jana Možíšová",
        "Jitka Vondráčková", "Kamča K", "Luci Beránkova",
        "Martin Černík", "Petr Marschall", "slv _", "Tomáš reiter",
    ],
    "Mix B": [
        "Ales Hanacek", "Anna Tomiová", "Eliška Lněničková",
        "Kateřina Jochová", "Lucie Vobořilová Vaňkátová",
        "marek Černý", "Samuel Lepšík", "Vanesa Langerová", "Vil K",
    ],
}

STATE = {
    "members": {k: list(v) for k, v in MEMBERS_BY_TEAM.items()},
    "attending": None,
    "matches": [],
    "day_timestamps": [],
    "assignments": [],
    "stats": {},
    "selected_event_ts": None,
    "preferences": {},  # jmeno -> "ref" | "server" | None
    "vocas": [],  # jmena Vocasu - vzdy dostupni
}

def fetch_tournify_firebase(live_link):
    PROJECT = "tournamentsoftware-a1b3d"
    BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
    API_KEY = "AlzaSyDp28xKByfY8JOl2v_RoG2XpHkVdnbO-zM"

    def fs_list(path):
        docs = []
        token = None
        while True:
            url = f"{BASE}/{path}?key={API_KEY}&pageSize=200"
            if token: url += f"&pageToken={token}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            docs += data.get("documents", [])
            token = data.get("nextPageToken")
            if not token: break
        return docs

    def fv(field):
        for k, v in field.items():
            if k == "stringValue": return v
            if k == "integerValue": return int(v)
        return None

    url_q = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents:runQuery?key={API_KEY}"
    query = json.dumps({"structuredQuery": {
        "from": [{"collectionId": "tournaments"}],
        "where": {"fieldFilter": {"field": {"fieldPath": "liveLink"}, "op": "EQUAL", "value": {"stringValue": live_link}}},
        "limit": 1
    }}).encode()
    req = urllib.request.Request(url_q, data=query, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        results = json.loads(r.read())

    tournament_doc = next((x["document"] for x in results if "document" in x), None)
    if not tournament_doc:
        raise ValueError(f"Turnaj '{live_link}' nebyl nalezen")
    tournament_id = tournament_doc["name"].split("/")[-1]

    days_docs = fs_list(f"tournaments/{tournament_id}/days")
    day_map = {}
    for d in days_docs:
        day_id = d["name"].split("/")[-1]
        ts = fv(d.get("fields", {}).get("date", {}))
        day_map[day_id] = ts or 0

    teams_docs = fs_list(f"tournaments/{tournament_id}/teams")
    poule_team_map = {}
    team_id_map = {}  # doc_id -> name
    for t in teams_docs:
        tf = t.get("fields", {})
        name = fv(tf.get("name", {})) or "?"
        doc_id = t["name"].split("/")[-1]
        team_id_map[doc_id] = name
        num = fv(tf.get("numInPoule0", {}))
        poule0 = fv(tf.get("poule0", {}))
        if poule0 is not None and num is not None:
            poule_team_map[(poule0, int(num))] = name

    poules_docs = fs_list(f"tournaments/{tournament_id}/poules")
    poule_map = {p["name"].split("/")[-1]: fv(p.get("fields", {}).get("name", {})) or p["name"].split("/")[-1]
                 for p in poules_docs}

    matches_docs = fs_list(f"tournaments/{tournament_id}/matches")
    matches = []
    for i, m in enumerate(matches_docs):
        mf = m.get("fields", {})
        day_id = fv(mf.get("day", {})) or ""
        if day_id not in day_map: continue
        st = fv(mf.get("st", {})) or ""
        field_num = fv(mf.get("field", {})) or "0"
        poule_id = fv(mf.get("poule", {})) or ""
        t1 = fv(mf.get("team1", {}))
        t2 = fv(mf.get("team2", {}))
        home = poule_team_map.get((poule_id, t1), f"Tym {t1}")
        away = poule_team_map.get((poule_id, t2), f"Tym {t2}")
        # Rozhodci - pole "referee" obsahuje doc ID tymu
        ref_doc_id = fv(mf.get("referee", {})) or ""
        ref_team_name = team_id_map.get(ref_doc_id, "")
        day_ts = day_map[day_id]
        try:
            day_str = datetime.datetime.fromtimestamp(day_ts).strftime("%d.%m.")
        except: day_str = "?"
        matches.append({
            "slot": i, "time": f"{day_str} {st}", "day_ts": day_ts, "st": st,
            "home": home, "away": away, "ref_team": ref_team_name,
            "field": f"Kurt {int(field_num)+1}" if str(field_num).isdigit() else str(field_num),
            "poule": poule_map.get(poule_id, ""),

        })

    matches.sort(key=lambda x: (x["day_ts"], x["st"]))
    for i, m in enumerate(matches): m["slot"] = i
    return matches


async def fetch_spond_events(username, password, group_id, day_timestamps):
    """Nacte vsechny nadchazejici akce, oznaci ktere sednou na Tournify dny."""
    s = spond_lib.Spond(username=username, password=password)
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        events = await s.get_events(group_id=group_id, min_start=now,
                                     max_end=now + datetime.timedelta(days=90))
        result = []
        for event in events:
            try:
                dt = datetime.datetime.fromisoformat(event.get("startTimestamp","").replace("Z","+00:00"))
                event_ts = int(dt.timestamp())
                day_str = dt.strftime("%d. %m. %Y")
            except: continue
            matches_tournify = any(abs(event_ts - d) < 86400 * 1.5 for d in day_timestamps)
            result.append({
                "id": event.get("id",""),
                "name": event.get("heading","(bez nazvu)"),
                "day": day_str,
                "ts": event_ts,
                "matches_tournify": matches_tournify,
            })
        result.sort(key=lambda x: x["ts"])
        return result
    finally:
        await s.clientsession.close()


async def fetch_spond_attendance(username, password, group_id, event_id):
    """Nacte ucast pro konkretni akci."""
    s = spond_lib.Spond(username=username, password=password)
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        events = await s.get_events(group_id=group_id, min_start=now,
                                     max_end=now + datetime.timedelta(days=90))
        found_event = next((e for e in events if e.get("id") == event_id), None)
        if not found_event:
            return {"found": False, "message": "Akce nenalezena."}

        group = await s.get_group(group_id)
        import unicodedata
        def clean_name(first, last):
            name = f"{first} {last}".strip()
            name = unicodedata.normalize("NFC", name)
            return " ".join(name.split())  # odstran dvojite mezery
        id_to_name = {m["id"]: clean_name(m.get("firstName",""), m.get("lastName",""))
                      for m in group.get("members", [])}

        responses = found_event.get("responses", {})
        def extract_ids(lst):
            ids = set()
            for item in lst:
                if isinstance(item, str): ids.add(item)
                elif isinstance(item, dict): ids.add(item.get("uid", item.get("id", "")))
            return ids

        accepted = extract_ids(responses.get("acceptedIds", []))
        declined = extract_ids(responses.get("declinedIds", []))
        all_ids = set(id_to_name.keys())

        try:
            dt = datetime.datetime.fromisoformat(found_event.get("startTimestamp","").replace("Z","+00:00"))
            event_ts = int(dt.timestamp())
        except:
            event_ts = None

        return {
            "found": True,
            "event_name": found_event.get("heading", ""),
            "event_ts": event_ts,
            "attending": sorted(id_to_name[i] for i in accepted if i in id_to_name),
            "declined": sorted(id_to_name[i] for i in declined if i in id_to_name),
            "unresponded": sorted(id_to_name[i] for i in (all_ids - accepted - declined) if i in id_to_name),
        }
    finally:
        await s.clientsession.close()


def get_active_members(attending_names, vocas=None):
    """
    attending_names: seznam jmen potvrzenych hracu (None = vsichni)
    vocas: seznam jmen "Vocasu" - pridaji se vzdy, bez ohledu na attending
    """
    import unicodedata
    def norm(s):
        s = unicodedata.normalize("NFC", s).strip()
        # odstran dvojite mezery, normalize apostrofy
        return " ".join(s.split()).lower()

    if attending_names is None:
        result = {k: list(v) for k, v in MEMBERS_BY_TEAM.items()}
    else:
        attending_norm = {norm(n) for n in attending_names}
        result = {}
        for team, members in MEMBERS_BY_TEAM.items():
            present = [m for m in members if norm(m) in attending_norm]
            if present:
                result[team] = present

    # Vocasi - pridej do vsech tymu kde jsou clenove, pokud tam jeste nejsou
    if vocas:
        vocas_norm = {norm(v): v for v in vocas}
        for team, members in MEMBERS_BY_TEAM.items():
            for member in members:
                if norm(member) in vocas_norm:
                    if team not in result:
                        result[team] = []
                    if member not in result[team]:
                        result[team].append(member)

    return result


# Mapovani nazvu tymu z Tournify na nase podskupiny
TOURNIFY_TO_SUBGROUP = {
    "Prague Crocodiles A MIX": "Mix A",
    "Prague Crocodiles B MIX": "Mix B",
    "Prague Crocodiles M":     "Muži",
    "Prague Crocodiles Ž":     "Ženy",
}

# Kdo podava kdyz dany tym hraje
PLAYING_SERVED_BY = {
    "Mix A":  "Mix B",
    "Mix B":  "Mix A",
    "Muži": "Ženy",
    "Ženy": "Muži",
}

# Kdo piska kdyz dany tym rozhodcuje
REF_TEAM_WHISTLES = {
    "Mix A":  "Mix A",
    "Mix B":  "Mix B",
    "Muži": "Muži",
    "Ženy": "Ženy",
}


def tournify_to_sg(team_name):
    """Prevede nazev tymu z Tournify na nazev podskupiny, nebo None."""
    return TOURNIFY_TO_SUBGROUP.get(team_name)


def assign_duties(matches, subgroups, preferences=None, vocas=None):
    """
    preferences: dict jmeno -> "ref" | "server" | None
    vocas: list jmen - vzdy dostanou sluzbu pokud nehraji (bez ohledu na spravedlnost)
    """
    if preferences is None:
        preferences = {}
    if vocas is None:
        vocas = []

    def sg_key(name):
        mapping = {
            "Muži": "Muži", "Muzi": "Muži",
            "Ženy": "Ženy", "Zeny": "Ženy",
            "Mix A": "Mix A", "Mix B": "Mix B",
        }
        return mapping.get(name, name)

    norm_sg = {sg_key(k): v for k, v in subgroups.items()}

    all_members = {m: {"duties": 0, "busy_times": set()}
                   for ms in subgroups.values() for m in ms}

    result = []
    for match in matches:
        slot = match["slot"]
        # Pouzij cas jako klic busy - aby se kryly soubehy zapasu ve stejny cas
        time_key = match.get("st") or match.get("time", str(slot))

        home_sg = tournify_to_sg(match["home"])
        away_sg = tournify_to_sg(match["away"])
        playing_sgs = {sg_key(sg) for sg in [home_sg, away_sg] if sg}

        # Celý hrající tým je busy
        for sg in playing_sgs:
            if sg in norm_sg:
                for m in norm_sg[sg]:
                    all_members[m]["busy_times"].add(time_key)

        ref_tournify = match.get("ref_team", "")
        ref_sg = tournify_to_sg(ref_tournify) if ref_tournify else None
        whistle_sg = sg_key(ref_sg) if ref_sg else None

        def pick_n(sg_name, n, exclude=None, prefer_role=None):
            """
            Vyber n lidi. Vocasi jdou vzdy prvni (bez ohledu na pocet sluzeb).
            Ostatni razeni: pocet sluzeb (spravedlnost), pri rovnosti preference.
            """
            key = sg_key(sg_name) if sg_name else None
            if not key or key not in norm_sg:
                return []
            pool = [m for m in norm_sg[key]
                    if time_key not in all_members[m]["busy_times"]
                    and m not in (exclude or set())]

            import unicodedata
            def norm(s):
                return " ".join(unicodedata.normalize("NFC", s).strip().split()).lower()
            vocas_norm = {norm(v) for v in vocas}

            def sort_key(m):
                is_vocas = norm(m) in vocas_norm  # Vocas jde vzdy prvni
                duties = all_members[m]["duties"]
                pref = preferences.get(m)
                if prefer_role is None:
                    pref_score = 0
                elif pref == prefer_role:
                    pref_score = 0
                elif pref is None:
                    pref_score = 1
                else:
                    pref_score = 2
                # is_vocas=False (0) jde pred True (1) -> vocas ma prioritu
                return (not is_vocas, duties, pref_score)

            pool.sort(key=sort_key)
            chosen = pool[:n]
            for m in chosen:
                all_members[m]["duties"] += 1
                all_members[m]["busy_times"].add(time_key)
            return chosen

        # Žádný Crocodiles tým se nezúčastní → přeskočit
        ref_is_crocodiles = whistle_sg and whistle_sg in norm_sg and whistle_sg not in playing_sgs
        playing_is_crocodiles = len(playing_sgs) > 0

        if not playing_is_crocodiles and not ref_is_crocodiles:
            # Skryt - Crocodiles nic nedela
            continue

        # ── Rozhodčí ──
        referees = []
        if ref_is_crocodiles:
            referees = pick_n(whistle_sg, 4, prefer_role="ref")

        # ── Podávající ──
        serving_sg = None
        for sg in [home_sg, away_sg]:
            if sg:
                candidate = PLAYING_SERVED_BY.get(sg_key(sg))
                if candidate and candidate not in playing_sgs:
                    serving_sg = candidate
                    break

        servers = []
        if serving_sg:
            # Vzdy vyluc uz vybrane rozhodci (bez ohledu na tym - clovek nemuze delat dve veci naraz)
            already = set(referees)
            servers = pick_n(serving_sg, 3, exclude=already, prefer_role="server")

        result.append({**match,
            "ref_team": whistle_sg or ref_tournify or "-",
            "serving_team": serving_sg or "-",
            "referees": referees,
            "servers": servers,
            "playing": list(playing_sgs),
        })
    return result

def compute_stats(assignments, subgroups):
    duty_count = {m: {"team": t, "count": 0} for t, ms in subgroups.items() for m in ms}
    for match in assignments:
        for m in match["referees"] + match["servers"]:
            if m in duty_count: duty_count[m]["count"] += 1
    return duty_count


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            with open("frontend.html", encoding="utf-8") as f:
                self.send_html(f.read())
        elif path == "/api/status":
            self.send_json({"members": {t: len(m) for t, m in STATE["members"].items()},
                            "matches_loaded": len(STATE["matches"]), "attending": STATE["attending"]})
        elif path == "/api/assignments":
            self.send_json({"assignments": STATE["assignments"], "stats": STATE["stats"]})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = json.loads(self.read_body() or b"{}")

        if path == "/api/load_tournify":
            live_link = data.get("live_link", "").strip()
            try:
                matches = fetch_tournify_firebase(live_link)
                STATE["matches"] = matches
                STATE["assignments"] = []
                day_timestamps = sorted(set(m["day_ts"] for m in matches if m["day_ts"]))
                STATE["day_timestamps"] = day_timestamps
                self.send_json({"ok": True, "count": len(matches), "matches": matches, "day_timestamps": day_timestamps})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)

        elif path == "/api/list_events":
            if not SPOND_AVAILABLE:
                self.send_json({"error": "pip install spond"}, 500)
                return
            try:
                events = asyncio.run(fetch_spond_events(
                    data.get("username",""), data.get("password",""),
                    data.get("group_id",""), STATE["day_timestamps"]))
                self.send_json({"ok": True, "events": events})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)

        elif path == "/api/check_attendance":
            if not SPOND_AVAILABLE:
                self.send_json({"error": "pip install spond"}, 500)
                return
            try:
                result = asyncio.run(fetch_spond_attendance(
                    data.get("username",""), data.get("password",""),
                    data.get("group_id",""), data.get("event_id","")))
                # Uloz event_ts do STATE pro filtrovani zapasu
                if result.get("event_ts"):
                    STATE["selected_event_ts"] = result["event_ts"]
                self.send_json({"ok": True, **result})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)

        elif path == "/api/set_vocas":
            # {"vocas": ["Petr Marschall", "jakub kopac"]}
            STATE["vocas"] = data.get("vocas", [])
            # Prepocitej aktivni cleny s novymi vocasy
            STATE["members"] = get_active_members(STATE["attending"], STATE["vocas"])
            self.send_json({"ok": True, "vocas": STATE["vocas"]})

        elif path == "/api/set_preferences":
            # {"preferences": {"Jan Novak": "ref", "Eva Nova": "server", "Petr X": null}}
            STATE["preferences"] = {k: v for k, v in data.get("preferences", {}).items() if v}
            self.send_json({"ok": True, "count": len(STATE["preferences"])})

        elif path == "/api/set_attending":
            attending = data.get("attending", None)
            STATE["attending"] = attending
            STATE["members"] = get_active_members(attending, STATE.get("vocas", []))
            # Volitelne: rucne vybrane datum (pres date picker)
            if data.get("selected_event_ts"):
                STATE["selected_event_ts"] = data["selected_event_ts"]
            self.send_json({"ok": True, "active": {t: len(m) for t, m in STATE["members"].items()}})

        elif path == "/api/replace_player":
            # {"slot": 5, "old_name": "Jan Novak", "new_name": "Petr Stary"}
            slot = data.get("slot")
            old_name = data.get("old_name", "")
            new_name = data.get("new_name", "")
            replaced = False
            for match in STATE["assignments"]:
                if match["slot"] == slot:
                    for lst_key in ("referees", "servers"):
                        lst = match[lst_key]
                        if old_name in lst:
                            lst[lst.index(old_name)] = new_name
                            replaced = True
            if replaced:
                STATE["stats"] = compute_stats(STATE["assignments"], STATE["members"])
                self.send_json({"ok": True, "assignments": STATE["assignments"], "stats": STATE["stats"]})
            else:
                self.send_json({"error": "Hráč nenalezen v daném zápase"}, 400)

        elif path == "/api/assign":
            if not STATE["matches"]:
                self.send_json({"error": "Nacti nejdriv rozpis z Tournify"}, 400)
                return
            try:
                # Filtruj zapasy pro vybrane datum (den Spond akce)
                matches_to_use = STATE["matches"]
                if STATE.get("selected_event_ts"):
                    evt_ts = STATE["selected_event_ts"]
                    matches_to_use = [m for m in STATE["matches"]
                                      if abs(m["day_ts"] - evt_ts) < 86400 * 1.5]
                assignments = assign_duties(matches_to_use, STATE["members"], STATE.get("preferences", {}), STATE.get("vocas", []))
                stats = compute_stats(assignments, STATE["members"])
                STATE["assignments"] = assignments
                STATE["stats"] = stats
                self.send_json({"ok": True, "assignments": assignments, "stats": stats})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)

        else:
            self.send_json({"error": "Not found"}, 404)


if __name__ == "__main__":
    port = 8765
    print(f"""
Turnajovy scheduler - Prague Crocodiles
Otevri: http://localhost:{port}
Zastav: Ctrl+C

Clenove:""")
    for team, members in MEMBERS_BY_TEAM.items():
        print(f"  {team}: {', '.join(members)}")
    HTTPServer(("localhost", port), Handler).serve_forever()
