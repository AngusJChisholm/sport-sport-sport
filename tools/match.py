"""SSS Pro Match Score: which brands a property should approach, and which properties a brand should target.

Reads deals.json + entities.json and writes pro/matches.json (read by the Matches tab in pro.html).
Also backtests itself: scores everything as the archive stood on a past date, then checks how many of the
new deals signed since were in each property's top 20. The result goes in the same file, so the accuracy
number on the page always belongs to the formula that made the suggestions.

    python3 tools/match.py            # build matches + backtest
    python3 tools/match.py --test     # backtest only, print the numbers

Match Score (0-100) = Gate x (Fit 85 + Whitespace 15)
Timing (out of 25), Capacity (15) and Appetite (15) are worked out and shown beside the score as signals,
but don't count toward it: in the Nov 2026 backtest every mix that included them ranked real deals worse
than Fit + Whitespace alone (4.1-4.5% of new deals in the top 20 vs 5.7%). Re-test as the archive grows.
  Fit        Lookalike: brands already backing properties like this one (same sport, league, region,
             reach, partners in common). Strongest signal in testing, so it carries the most points.
  Timing     Momentum (new deals in the last 12 months) + triggers (signed in this sport in the last
             6 months, a rival in the same sub-category just signed a peer).
  Capacity   Highest tier the brand has bought. A brand that has never bought at this property's level
             (local < national < global) is flagged "Build up first".
  Appetite   How much the brand sponsors, and across how many sports.
  Whitespace The property has no partner in the brand's sub-category, scaled by how many peers do.
  Gate       Hidden if already a live partner, or if a live partner holds the same sub-category on a firm
             deal. A clash with a stale or ending deal shows as "Slot may open" instead. Betting brands at a
             property with no betting partner are flagged "Check betting policy".
  Lookalikes in other sports count too, at a lower weight (same region and reach, partners in common).
Every deal counts less as it ages: weight = 0.5 ** (months old / 18).
"""
import json, math, re, sys, datetime, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_profiles import norm, slugify, split, many  # same name -> slug rules as the site
from subcat_rules import classify as subcat

TIER = {"Naming rights": 5, "Title sponsor": 5, "Principal & major": 4, "Shirt & kit placement": 4, "Kit & apparel": 3,
        "Investment & ownership": 3, "Official partner": 2, "Media & broadcast": 2, "Licensing & merchandise": 1,
        "Ambassador & endorsement": 1}
REACH = {"Local": 1, "National": 2, "Global": 3}
TOPN, MIN_SHOW, LISTED_W = 15, 40, 0.6
W_FIT, W_WS = 85, 15  # chosen by backtest; rerun tools/match.py --test before changing


def ym(s):
    return int(s[:4]) * 12 + int(s[5:7]) - 1


def load():
    E = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))
    ent, leagues = E["entities"], E.get("leagues", [])
    look = {}
    for slug, x in ent.items():
        look[norm(x["name"])] = slug
        for a in x.get("aliases", []):
            look[norm(a)] = slug
    resolve = lambda n: look.get(norm(n)) or slugify(n)
    deals = []
    for d in json.loads((ROOT / "deals.json").read_text(encoding="utf-8"))["deals"]:
        b, p = split(d.get("deal"))
        if not p:
            continue
        when = d.get("date") or d.get("month")
        deals.append(dict(d=d, bs=[resolve(n) for n in many(b)], ps=[resolve(n) for n in many(p)],
                          names=dict(zip([resolve(n) for n in many(b)] + [resolve(n) for n in many(p)], many(b) + many(p))),
                          ym=ym(when) if when else None, listed=ym(d["listed"]) if d.get("listed") and not when else None))
    league_of = {}
    for lg in leagues:
        for c in lg.get("clubs", []):
            league_of[c] = lg["name"]
    return ent, deals, league_of


class Model:
    """Everything the score needs, built from the deals known at `now` (a year*12+month number)."""

    def __init__(self, ent, deals, league_of, now, use_listed=True):
        self.ent, self.now, self.league_of = ent, now, league_of
        yr = now // 12
        self.B, self.P, self.name = collections.defaultdict(list), collections.defaultdict(list), {}
        for x in deals:
            when = x["ym"] if x["ym"] is not None else (x["listed"] if use_listed else None)
            if when is None or when > now:
                continue
            d = x["d"]
            age = max(0, now - when)
            w = (0.5 ** (age / 18)) * (LISTED_W if x["ym"] is None else 1)
            ended = d.get("ended")
            live = not ended and (d.get("ends", 9999) >= yr if d.get("ends") else (x["ym"] is None or age <= 36))
            rec = dict(d=d, ym=when, w=w, age=age, live=live, dated=x["ym"] is not None)
            for b in x["bs"]:
                for p in x["ps"]:
                    r = dict(rec, b=b, p=p)
                    self.B[b].append(r)
                    self.P[p].append(r)
            self.name.update(x["names"])
        # brand facts
        self.cat, self.sub = {}, {}
        for b in self.B:
            e = ent.get(b, {})
            c = e.get("cat")
            self.cat[b] = c
            self.sub[b] = e.get("sub") or subcat(e.get("name") or self.name.get(b, b), e.get("domain", ""), c)
        # property facts
        self.sport, self.region, self.reach, self.live_b, self.live_sub, self.live_cat = {}, {}, {}, {}, {}, {}
        for p, rs in self.P.items():
            sp, rg = collections.Counter(), collections.Counter()
            for r in rs:
                sp[r["d"].get("sport")] += r["w"]
                rg[r["d"].get("region")] += r["w"]
            self.sport[p] = sp.most_common(1)[0][0]
            self.region[p] = rg.most_common(1)[0][0]
            self.reach[p] = self._reach(p, rg)
            lb = {r["b"] for r in rs if r["live"]}
            self.live_b[p] = lb
            self.live_sub[p] = {self.sub.get(b) for b in lb if self.sub.get(b)}
            self.live_cat[p] = {self.cat.get(b) for b in lb if self.cat.get(b)}
        self.blevel = {b: max(REACH[self.reach[r["p"]]] for r in rs) for b, rs in self.B.items()}
        # peers: same league if it has one, else same sport and reach
        self.groups = collections.defaultdict(set)
        for p in self.P:
            self.groups[self._gkey(p)].add(p)
        self.by_sport, self.by_rr = collections.defaultdict(set), collections.defaultdict(set)
        for p in self.P:
            self.by_sport[self.sport[p]].add(p)
            self.by_rr[(self.region[p], self.reach[p])].add(p)
        # live partners by sub-category, with how long each has left: a clash with a stale or ending deal
        # doesn't block, it shows as "Slot may open"
        self.sub_hold = collections.defaultdict(dict)
        for p, rs in self.P.items():
            for r in rs:
                sb = self.sub.get(r["b"])
                if not (r["live"] and sb):
                    continue
                ends = r["d"].get("ends")
                firm = (ends and ends > yr) or (not ends and r["age"] <= 24) or not r["dated"]
                cur = self.sub_hold[p].get(sb)
                self.sub_hold[p][sb] = (cur or firm) if cur is not None else firm

    def _reach(self, p, rg):
        e = self.ent.get(p, {})
        if e.get("reach") in REACH:
            return e["reach"]
        glob = rg.get("Global", 0) > rg.get("ANZ", 0)
        pt = e.get("ptype") or "Other"
        if glob:
            return "Global"
        if pt in ("National team", "Governing body", "League & competition", "Event", "Athlete & talent"):
            return "National"
        return "National" if p in self.league_of else "Local"

    def _gkey(self, p):
        return ("L", self.league_of[p]) if p in self.league_of else ("S", self.sport[p], self.reach[p])

    def peers(self, p):
        return self.groups[self._gkey(p)] - {p}

    def sim(self, p, q):
        if p == q:
            return 0
        a, b = {r["b"] for r in self.P[p]}, {r["b"] for r in self.P[q]}
        j = len(a & b) / max(1, len(a | b))
        s = (self.sport[p] == self.sport[q]) * 1 + (self.league_of.get(p) is not None and self.league_of.get(p) == self.league_of.get(q)) * 1 \
            + (self.region[p] == self.region[q]) * 0.5 + (self.reach[p] == self.reach[q]) * 0.5 + 3 * j
        if self.sport[p] != self.sport[q]:  # cross-sport lookalike counts, at a lower weight
            s = (self.region[p] == self.region[q]) * 0.3 + (self.reach[p] == self.reach[q]) * 0.2 + 3 * j
        return s

    def score_property(self, p, top=TOPN, keep_all=False):
        """All candidate brands for property p, best first: [(score, brand, parts, why, flags)]."""
        sims = {}
        cand_props = set(self.by_sport[self.sport[p]]) | self.by_rr[(self.region[p], self.reach[p])]
        for b in {r["b"] for r in self.P[p]}:
            cand_props |= {r["p"] for r in self.B[b]}
        for q in cand_props:
            s = self.sim(p, q)
            if s > 0:
                sims[q] = s
        cf = collections.defaultdict(float)
        ev = collections.defaultdict(list)
        for q, s in sims.items():
            for r in self.P[q]:
                cf[r["b"]] += s * r["w"]
                ev[r["b"]].append((s * r["w"], q))
        if not cf:
            return []
        cmax = max(cf.values())
        peers = self.peers(p)
        sp, plevel = self.sport[p], REACH[self.reach[p]]
        out = []
        for b, c in cf.items():
            if b in self.live_b[p] or b == p:
                continue
            cat, sub = self.cat.get(b), self.sub.get(b)
            flags = []
            if sub and sub in self.live_sub[p]:
                if self.sub_hold[p].get(sub):
                    continue
                flags.append("Slot may open")
            if cat == "Betting & wagering" and cat not in self.live_cat[p]:
                flags.append("Check betting policy")
            rs = self.B[b]
            F = W_FIT * math.log1p(c) / math.log1p(cmax)
            n12 = sum(1 for r in rs if r["dated"] and r["age"] <= 12)
            mom = min(15, 5 * n12)
            trig, why_t = 0, None
            if any(r["dated"] and r["age"] <= 6 and r["d"].get("sport") == sp and r["p"] != p for r in rs):
                trig += 5
            if sub:
                for q in peers:
                    hit = [r for r in self.P[q] if r["dated"] and r["age"] <= 12 and r["b"] != b and self.sub.get(r["b"]) == sub]
                    if hit:
                        trig += 5
                        h = min(hit, key=lambda r: r["age"])
                        why_t = f"Rival {self.ent.get(h['b'], {}).get('name') or self.name.get(h['b'], h['b'])} signed {self.ent.get(q, {}).get('name') or self.name.get(q, q)} in {fmt_ym(h['ym'])}"
                        break
            T = mom + min(10, trig)
            C = max(TIER.get(r["d"].get("tier"), 2) for r in rs) / 5 * 15
            W_ = sum(r["w"] for r in rs)
            A = min(10, 2 * W_) + min(5, len({r["d"].get("sport") for r in rs}))
            Wsp, adopt = 0, 0
            if sub and peers:
                adopt = sum(1 for q in peers if sub in self.live_sub[q])
                Wsp = W_WS * adopt / len(peers)
            total = F + Wsp  # Timing, Capacity and Appetite are shown as signals, not scored (see header)
            if any(r["b"] == b for r in self.P[p]):
                flags.append("Former partner")
            if self.blevel.get(b, 1) < plevel:
                flags.append("Build up first")  # flag only: capping the score tested worse
            if total < MIN_SHOW and not keep_all:
                continue
            # reasons, strongest first
            why = []
            top_ev = sorted(ev[b], reverse=True)
            seen, names = set(), []
            for _, q in top_ev:
                if q not in seen:
                    seen.add(q)
                    names.append(self.ent.get(q, {}).get("name") or self.name.get(q, q))
                if len(names) == 3:
                    break
            if names:
                why.append("Backs " + join(names))
            if why_t:
                why.append(why_t)
            if n12:
                why.append(f"{n12} new deal{'s' if n12 > 1 else ''} in the last 12 months")
            if sub and peers and adopt:
                why.append(f"No {sub} partner here. {adopt} of {len(peers)} peers have one")
            conf = "High" if len(rs) >= 5 else "Medium" if len(rs) >= 2 else "Low"
            out.append((round(total), b, [round(T), round(F), round(C), round(A), round(Wsp)], why[:3], flags, conf))
        out.sort(key=lambda x: (-x[0], -x[2][1]))
        return out if keep_all else out[:top]


def join(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def fmt_ym(v):
    return datetime.date(v // 12, v % 12 + 1, 1).strftime("%b %Y")


def band(s):
    return "Call now" if s >= 80 else "Strong" if s >= 65 else "Watch" if s >= 50 else "Low"


def backtest(ent, deals, league_of, months_back=6, today=None):
    today = today or datetime.date.today()
    now = today.year * 12 + today.month - 1
    cut = now - months_back
    m = Model(ent, deals, league_of, cut - 1, use_listed=False)  # no listings: their start dates are unknown
    tests = []
    for x in deals:
        if x["ym"] is None or x["ym"] < cut or x["d"].get("status") != "New":
            continue
        for b in x["bs"]:
            for p in x["ps"]:
                if p in m.P:
                    tests.append((b, p))
    hits20 = hits50 = 0
    cache = {}
    for b, p in tests:
        if p not in cache:
            cache[p] = [x[1] for x in m.score_property(p, keep_all=True)]
        order = cache[p]
        if b in order[:20]:
            hits20 += 1
        if b in order[:50]:
            hits50 += 1
    known = sum(1 for b, p in tests if b in m.B)
    n = max(1, len(tests))
    return {"from": fmt_ym(cut), "to": today.strftime("%b %Y"), "tested": len(tests), "top20": round(hits20 / n, 3),
            "top50": round(hits50 / n, 3), "ceiling": round(known / n, 3), "deals_before": sum(len(v) for v in m.P.values())}


def main():
    ent, deals, league_of = load()
    bt = backtest(ent, deals, league_of)
    print("Backtest", bt)
    if "--test" in sys.argv:
        return
    today = datetime.date.today()
    m = Model(ent, deals, league_of, today.year * 12 + today.month - 1)
    nm = lambda s: m.ent.get(s, {}).get("name") or m.name.get(s, s)
    props, brands = {}, collections.defaultdict(list)
    for p, rs in m.P.items():
        if len(rs) < 3:
            continue
        res = m.score_property(p, top=200)
        props[p] = {"n": nm(p), "s": m.sport[p], "r": m.reach[p],
                    "m": [{"b": b, "n": nm(b), "c": m.cat.get(b) or "", "u": m.sub.get(b) or "", "x": sc, "k": band(sc), "f": conf, "p": parts, "w": why, "g": flags}
                          for sc, b, parts, why, flags, conf in res[:TOPN]]}
        for sc, b, parts, why, flags, conf in res:
            brands[b].append({"p": p, "n": nm(p), "s": m.sport[p], "r": m.reach[p], "x": sc, "k": band(sc), "f": conf, "pt": parts, "w": why, "g": flags})
    bout = {}
    for b, lst in brands.items():
        if len(m.B.get(b, [])) < 2:
            continue
        lst.sort(key=lambda x: -x["x"])
        bout[b] = {"n": nm(b), "c": m.cat.get(b) or "", "u": m.sub.get(b) or "", "m": lst[:TOPN]}
    out = {"generated": today.isoformat(), "version": 3, "backtest": bt, "props": props, "brands": bout}
    (ROOT / "pro").mkdir(exist_ok=True)
    (ROOT / "pro" / "matches.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote pro/matches.json: {len(props)} properties, {len(bout)} brands")


if __name__ == "__main__":
    main()
