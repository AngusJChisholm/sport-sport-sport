"""SSS Pro Match Score: which brands a property should approach, and which properties a brand should target.

Reads deals.json + entities.json and writes pro/matches.json (read by the Matches tab in pro.html).
Also backtests itself: scores everything as the archive stood on a past date, then checks how many of the
new deals signed since were in each property's top 20. The result goes in the same file, so the accuracy
number on the page always belongs to the formula that made the suggestions.

    python3 tools/match.py            # build matches + backtest
    python3 tools/match.py --test     # backtest only, print the numbers

Match Score (0-100) = Gate x (Fit 74 + Whitespace 13 + Sport DNA 9 + Audience fit 4)
  Sport DNA    How much more often brands in this slot back this sport worldwide than sport overall
               (watches and champagne for racing). Brings in brands with no lookalike deal yet.
  Audience fit Overlap between the brand's profile and the property's (tools/profiles.py): audience,
               what they stand for, and positioning (premium, mid, value).
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

Peers depend on the kind of property: clubs compare with their league and sport, plus clubs in other codes in
the same city (tools/locations.py); leagues, governing bodies,
events and national teams compare with the same kind of property across every code.

Second list, "International brands": for ANZ properties with national or global reach, brands whose deals are
mostly overseas (no more than one ANZ deal) and active in the last 18 months, scored on Gap 30 (no partner
in that sub-category, more if peers have one), Fit 30 (backs this sport, and this kind of property, overseas),
Appetite 20, Capacity 10 and Entry 10
(first ANZ deal in the last 12 months, or none yet). Not backtested: brands new to ANZ have little history to
test against.
"""
import json, math, re, sys, datetime, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_profiles import norm, slugify, split, many  # same name -> slug rules as the site
from subcat_rules import classify as subcat
from locations import CITY
from profiles import brand_profile, property_profile, alignment

# City links only make sense between team-sport clubs (fans pick a club in their city). For racing, golf,
# motorsport, tennis and the rest, the sport and the property's profile lead.
TEAM_SPORTS = {"AFL", "AFLW", "NRL", "NRLW", "Football", "Basketball", "Netball", "Cricket", "Rugby union", "Rugby league",
               "Ice hockey", "Baseball", "NFL", "Hockey", "Volleyball", "Water polo"}

TIER = {"Naming rights": 5, "Title sponsor": 5, "Principal & major": 4, "Shirt & kit placement": 4, "Kit & apparel": 3,
        "Investment & ownership": 3, "Official partner": 2, "Media & broadcast": 2, "Licensing & merchandise": 1,
        "Ambassador & endorsement": 1}
REACH = {"Local": 1, "National": 2, "Global": 3}
# Property class decides who a property is compared with. Clubs compare with their league and sport;
# leagues, governing bodies, events and national teams compare with the same kind of property across
# every code (the AFL looks at the NRL, Cricket Australia and the NBL, not at AFL clubs).
CLASS = {"Club & team": "club", "League & competition": "body", "Governing body": "body", "Event": "event",
         "National team": "national", "Athlete & talent": "athlete", "Venue": "venue"}
TOPN, MIN_SHOW, LISTED_W = 15, 40, 0.6
W_FIT, W_WS, W_DNA, W_AL = 74, 13, 9, 4  # chosen by backtest (Nov 2026); rerun tools/match.py --test before changing


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
        self.pclass = {p: (ent.get(p) or {}).get("class") or CLASS.get((ent.get(p) or {}).get("ptype"), "other") for p in self.P}
        self.city = {p: (ent.get(p) or {}).get("city") or CITY.get(p) for p in self.P}
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
        self.by_sport, self.by_rr, self.by_class, self.by_city = (collections.defaultdict(set) for _ in range(4))
        for p in self.P:
            self.by_sport[self.sport[p]].add(p)
            self.by_rr[(self.region[p], self.reach[p])].add(p)
            self.by_class[(self.pclass[p], self.region[p])].add(p)
            if self.city[p]:
                self.by_city[self.city[p]].add(p)
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
        # profiles
        nm = lambda x: (ent.get(x) or {}).get("name") or self.name.get(x, x)
        self.bprof = {b: brand_profile(b, ent, self.sub.get(b), self.cat.get(b)) for b in self.B}
        self.pprof = {p: property_profile(p, ent, self.sport[p], self.pclass[p], self.reach[p], nm(p)) for p in self.P}
        # sport DNA: how much more often a slot (sub-category, else category) backs this sport than sport overall,
        # counted across every region, smoothed so thin sports don't swing on one deal
        slot = lambda b: self.sub.get(b) or self.cat.get(b)
        n_all, n_slot, n_sport, n_ss = 0, collections.Counter(), collections.Counter(), collections.Counter()
        for b, rs in self.B.items():
            k = slot(b)
            if not k:
                continue
            for r in rs:
                sp = r["d"].get("sport")
                n_all += 1
                n_slot[k] += 1
                n_sport[sp] += 1
                n_ss[(sp, k)] += 1
        self._dna = {}
        for (sp, k), n in n_ss.items():
            p_s = (n + 0.5) / (n_sport[sp] + 10)
            base_p = n_slot[k] / max(1, n_all)
            self._dna[(sp, k)] = (p_s / base_p if base_p else 1, n)
        self.slot = slot
        # brands active in the last 24 months, by slot, for profile-led candidates
        self.active_by_slot = collections.defaultdict(set)
        for b, rs in self.B.items():
            if slot(b) and any(r["age"] <= 24 for r in rs):
                self.active_by_slot[slot(b)].add(b)

    def dna(self, sport, b):
        """0-1 sport DNA for brand b's slot in this sport, plus the lift behind it."""
        k = self.slot(b)
        lift, n = self._dna.get((sport, k), (0, 0))
        if lift <= 1:
            return 0.0, lift, n
        return min(1.0, math.log(lift) / math.log(5)), lift, n

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
        c = self.pclass[p]
        if c == "club":
            return ("L", self.league_of[p]) if p in self.league_of else ("S", self.sport[p], self.reach[p])
        if c in ("body", "event", "national"):  # same kind of property, any code, same region and reach
            return ("C", c, self.region[p], self.reach[p])
        return ("S", self.sport[p], self.reach[p])

    def peers(self, p):
        if self.pclass[p] in ("body", "event", "national"):
            # same kind of property; global properties compare worldwide. Same sport first, then the majors.
            c, rg, rc = self.pclass[p], self.region[p], self.reach[p]
            pool = [q for q in self.P if q != p and self.pclass[q] == c and self.reach[q] == rc and (rc == "Global" or self.region[q] == rg)]
            pool.sort(key=lambda q: (self.sport[q] != self.sport[p], -len(self.P[q])))
            return set(pool[:15])
        return self.groups[self._gkey(p)] - {p}

    def sim(self, p, q):
        if p == q:
            return 0
        a, b = {r["b"] for r in self.P[p]}, {r["b"] for r in self.P[q]}
        j = len(a & b) / max(1, len(a | b))
        same_sport, same_class = self.sport[p] == self.sport[q], self.pclass[p] == self.pclass[q]
        rg, rc = self.region[p] == self.region[q], self.reach[p] == self.reach[q]
        if self.pclass[p] == "club":
            same_city = (self.city[p] is not None and self.city[p] == self.city[q]
                         and self.sport[p] in TEAM_SPORTS and self.sport[q] in TEAM_SPORTS and self.pclass[q] == "club")
            if same_sport:
                s = 1 + (self.league_of.get(p) is not None and self.league_of.get(p) == self.league_of.get(q)) + rg * 0.5 + rc * 0.5 + 3 * j
            else:  # cross-sport lookalike counts, at a lower weight
                s = rg * 0.3 + rc * 0.2 + 3 * j
            if same_city:  # clubs in other codes in the same city share a market and a fan base
                s += 1.2
            return s * (1 if same_class else 0.6)
        # leagues and governing bodies: the kind of property and market matter more than the code (the AFL
        # learns from the NRL and Cricket Australia). Events and national teams: the sport defines the audience
        # (racing learns from racing, tennis from tennis), so it weighs as much as the kind of property.
        w_sport = 0.4 if self.pclass[p] == "body" else 1.5
        s = same_class * 1.5 + rg * 0.5 + rc * 0.7 + same_sport * w_sport + 3 * j
        if not same_class:
            # a different kind of property counts for less, unless it's the same sport (for the AO, the ATP
            # and WTA tours are close peers; an AFL club says little about what the AFL should sell)
            s *= 0.8 if same_sport and self.pclass[p] != "body" else 0.35
        return s

    def score_property(self, p, top=TOPN, keep_all=False):
        """All candidate brands for property p, best first: [(score, brand, parts, why, flags)]."""
        sims = {}
        cand_props = set(self.by_sport[self.sport[p]]) | self.by_rr[(self.region[p], self.reach[p])] | self.by_class[(self.pclass[p], self.region[p])]
        if self.city[p]:
            cand_props |= self.by_city[self.city[p]]
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
        # profile-led candidates: brands in slots that strongly back this sport anywhere in the world, even
        # with no lookalike deal yet (a watch brand for racing)
        for (spk, k), (lift, n) in self._dna.items():
            if spk == self.sport[p] and lift >= 2 and n >= 2:
                for b in self.active_by_slot.get(k, ()):
                    cf.setdefault(b, 0.0)
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
            if sp in self.bprof[b].get("avoid", []):
                continue  # researched: the brand stays away from this sport
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
            dn, lift, dn_n = self.dna(sp, b)
            al, al_on = alignment(self.bprof[b], self.pprof[p])
            Dn, Al = W_DNA * dn, W_AL * al
            total = F + Wsp + Dn + Al  # Timing, Capacity and Appetite are shown as signals, not scored (see header)
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
            if self.pclass[p] == "club" and self.city[p]:
                local = [q for _, q in top_ev if self.city.get(q) == self.city[p] and self.sport[q] != sp]
                if local:
                    ln = self.ent.get(local[0], {}).get("name") or self.name.get(local[0], local[0])
                    if ln not in names:
                        why.append(f"Already in {self.city[p]} with {ln}")
            if why_t:
                why.append(why_t)
            if n12:
                why.append(f"{n12} new deal{'s' if n12 > 1 else ''} in the last 12 months")
            if sub and peers and adopt:
                why.append(f"No {sub} partner here. {adopt} of {len(peers)} peers have one")
            conf = "High" if len(rs) >= 5 else "Medium" if len(rs) >= 2 else "Low"
            if dn >= 0.4 and len(why) < 4:
                why.append(f"{self.slot(b)} brands back {sp} {lift:.0f}x more than sport overall" if lift >= 2 else f"{self.slot(b)} brands over-index in {sp}")
            if al >= 0.5 and al_on and len(why) < 4:
                why.append("Fits the audience: " + ", ".join(al_on[:4]))
            out.append((round(total), b, [round(T), round(F), round(C), round(A), round(Wsp), round(Dn), round(Al)], why[:4], flags, conf, total))
        out.sort(key=lambda x: -x[6])
        out = [x[:6] for x in out]
        return out if keep_all else out[:top]


    def slots(self, p):
        """Slot map: every sub-category this property or its peers have filled, marked sold, ending or open."""
        yr = self.now // 12
        peers = self.peers(p)
        have = collections.defaultdict(list)
        for r in self.P[p]:
            sub = self.sub.get(r["b"])
            if r["live"] and sub:
                have[sub].append(r)
        subs = set(have)
        for q in peers:
            subs |= self.live_sub[q]
        out = []
        for sub in subs:
            adopt = sum(1 for q in peers if sub in self.live_sub[q])
            rs = have.get(sub, [])
            if not rs and adopt < 2:
                continue
            cat = next((self.cat.get(r["b"]) for r in rs), None)
            if not cat:
                for q in peers:
                    for r in self.P[q]:
                        if self.sub.get(r["b"]) == sub:
                            cat = self.cat.get(r["b"]); break
                    if cat:
                        break
            if rs:
                ends = [r["d"].get("ends") for r in rs if r["d"].get("ends")]
                firm = self.sub_hold[p].get(sub)
                ending = (ends and min(ends) <= yr + 1) or not firm
                names = []
                for r in sorted(rs, key=lambda r: -r["ym"]):
                    n = self.ent.get(r["b"], {}).get("name") or self.name.get(r["b"], r["b"])
                    if n not in names:
                        names.append(n)
                out.append({"u": sub, "c": cat or "", "st": "ending" if ending else "sold", "b": names[:3],
                            "e": min(ends) if ends else None, "a": adopt, "n": len(peers)})
            else:
                out.append({"u": sub, "c": cat or "", "st": "open", "b": [], "e": None, "a": adopt, "n": len(peers)})
        order = {"open": 0, "ending": 1, "sold": 2}
        out.sort(key=lambda x: (order[x["st"]], -x["a"], x["u"]))
        return out

    def entrants(self, p, top=8):
        """International brands that could come into Australia/NZ through property p.

        For ANZ properties with national or global reach. Candidates are brands whose deals are mostly outside
        ANZ (75%+ by weight), with at most one ANZ deal, active in the last 18 months. They can't come through
        the lookalike score (they have no local deals to look alike), so they get their own list, scored on
        appetite, capacity, the property's sub-category gap, sport fit and a market-entry signal."""
        if self.region[p] != "ANZ" or REACH[self.reach[p]] < 2:
            return []
        peers, sp = self.peers(p), self.sport[p]
        out = []
        for b, rs in self.B.items():
            if len(rs) < 2 or b in self.live_b[p] or not self.cat.get(b):
                continue
            Wt = sum(r["w"] for r in rs)
            glob = sum(r["w"] for r in rs if r["d"].get("region") == "Global")
            anz = [r for r in rs if r["d"].get("region") == "ANZ"]
            if glob / Wt < 0.75 or len(anz) > 1 or min(r["age"] for r in rs) > 18:
                continue
            cat, sub = self.cat[b], self.sub.get(b)
            flags = []
            if sub and sub in self.live_sub[p]:
                if self.sub_hold[p].get(sub):
                    continue
                flags.append("Slot may open")
            if cat == "Betting & wagering":
                if cat not in self.live_cat[p]:
                    flags.append("Check betting policy")
            App = min(20, 4 * Wt)
            Cap = max(TIER.get(r["d"].get("tier"), 2) for r in rs) / 5 * 10
            key = sub or cat
            have = (lambda q: key in self.live_sub[q]) if sub else (lambda q: key in self.live_cat[q])
            adopt = sum(1 for q in peers if have(q)) if peers else 0
            open_here = not (sub and sub in self.live_sub[p]) and not (not sub and cat in self.live_cat[p])
            Gap = 30 * open_here * (0.35 + 0.65 * adopt / len(peers)) if peers else 30 * open_here * 0.35
            # fit: does it already back this sport, and this kind of property, overseas?
            f_sport = sum(r["w"] for r in rs if r["d"].get("sport") == sp) / Wt
            f_class = sum(r["w"] for r in rs if self.pclass.get(r["p"]) == self.pclass[p]) / Wt
            Fit = 18 * f_sport + 12 * f_class
            Ent = 10 if anz and anz[0]["age"] <= 12 else 5 if not anz else 0
            total = round(App + Cap + Gap + Fit + Ent)
            if total < MIN_SHOW:
                continue
            nm = lambda x: self.ent.get(x, {}).get("name") or self.name.get(x, x)
            recent = sorted(rs, key=lambda r: r["age"])
            props = []
            for r in recent:
                if r["d"].get("region") != "ANZ" and nm(r["p"]) not in props:
                    props.append(nm(r["p"]))
                if len(props) == 3:
                    break
            why = [f"Global sponsor: {len(rs)} deals, incl. {join(props)}" if props else f"Global sponsor: {len(rs)} deals"]
            if anz:
                why.append(f"First ANZ deal: {nm(anz[0]['p'])} in {fmt_ym(anz[0]['ym'])}")
            else:
                why.append("No Australian or NZ deal yet")
            if open_here and peers and adopt:
                why.append(f"No {key} partner here. {adopt} of {len(peers)} peers have one")
            elif open_here:
                why.append(f"No {key} partner here")
            if f_sport >= 0.2:
                why.append(f"Already backs {sp} overseas")
            out.append((total, b, [round(App), round(Cap), round(Gap), round(Fit), Ent], why[:3], flags,
                        "High" if len(rs) >= 5 else "Medium"))
        out.sort(key=lambda x: -x[0])
        return out[:top]


def verified_dates(ent):
    """Property slug -> date its official partners page was last checked (coverage.json lastChecked)."""
    look = {}
    for slug, x in ent.items():
        look[norm(x["name"])] = slug
        for a in x.get("aliases", []):
            look[norm(a)] = slug
    out = {}
    try:
        cov = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))
    except Exception:
        return out
    for c in cov.get("properties", []):
        if c.get("lastChecked"):
            out[look.get(norm(c["name"])) or slugify(c["name"])] = c["lastChecked"]
    return out


def load_feedback():
    """pro/feedback.json: [{"p": property slug, "b": brand slug, "s": "nofit"|"pitched"|"won", "d": date}].
    Exported from the Matches tab. "nofit" hides the pair; "pitched" and "won" show as flags and count toward
    the hit rate."""
    try:
        fb = json.loads((ROOT / "pro" / "feedback.json").read_text(encoding="utf-8"))
        return {(x["p"], x["b"]): x["s"] for x in fb.get("items", []) if x.get("p") and x.get("b")}
    except Exception:
        return {}


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


def profile_queue(n):
    """Brands to research next: the ones suggested most often (top 15s) that don't have a researched profile."""
    data = json.loads((ROOT / "pro" / "matches.json").read_text(encoding="utf-8"))
    ent = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))["entities"]
    cnt = collections.Counter()
    for pr in data["props"].values():
        for r in pr["m"] + pr.get("e", []):
            cnt[r["b"]] += 1
    out = [(b, c) for b, c in cnt.most_common() if not (ent.get(b) or {}).get("profiled")][:n]
    for b, c in out:
        e = ent.get(b) or {}
        print(f"{b}\t{e.get('name', b)}\t{e.get('domain', '')}\tsuggested {c}x")


def main():
    if "--profile-queue" in sys.argv:
        i = sys.argv.index("--profile-queue")
        return profile_queue(int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 20)
    ent, deals, league_of = load()
    bt = backtest(ent, deals, league_of)
    print("Backtest", bt)
    if "--test" in sys.argv:
        return
    today = datetime.date.today()
    m = Model(ent, deals, league_of, today.year * 12 + today.month - 1)
    nm = lambda s: m.ent.get(s, {}).get("name") or m.name.get(s, s)
    ver, fb = verified_dates(ent), load_feedback()

    def apply_fb(p, rows):
        keep = []
        for row in rows:
            st = fb.get((p, row[1]))
            if st == "nofit":
                continue
            if st:
                row[4].append({"pitched": "Pitched", "won": "Won"}[st])
            keep.append(row)
        return keep
    props, brands, entry = {}, collections.defaultdict(list), collections.defaultdict(list)
    for p, rs in m.P.items():
        if len(rs) < 3:
            continue
        res = apply_fb(p, m.score_property(p, top=200))
        ent_list = apply_fb(p, m.entrants(p))
        props[p] = {"n": nm(p), "s": m.sport[p], "r": m.reach[p], "t": m.pclass[p], "v": ver.get(p), "sl": m.slots(p),
                    "e": [{"b": b, "n": nm(b), "c": m.cat.get(b) or "", "u": m.sub.get(b) or "", "x": sc, "f": conf, "p": parts, "w": why, "g": flags}
                          for sc, b, parts, why, flags, conf in ent_list],
                    "pf": {k: m.pprof[p][k] for k in ("pos", "aud", "align")},
                    "m": [{"b": b, "n": nm(b), "c": m.cat.get(b) or "", "u": m.sub.get(b) or "", "x": sc, "k": band(sc), "f": conf, "p": parts, "w": why, "g": flags,
                           "pf": [m.bprof[b]["pos"], m.bprof[b]["mkt"], m.bprof[b]["researched"]]}
                          for sc, b, parts, why, flags, conf in res[:TOPN]]}
        for sc, b, parts, why, flags, conf in ent_list:
            entry[b].append({"p": p, "n": nm(p), "s": m.sport[p], "r": m.reach[p], "v": ver.get(p), "x": sc, "f": conf, "pt": parts, "w": why, "g": flags})
        for sc, b, parts, why, flags, conf in res:
            brands[b].append({"p": p, "n": nm(p), "s": m.sport[p], "r": m.reach[p], "v": ver.get(p), "x": sc, "k": band(sc), "f": conf, "pt": parts, "w": why, "g": flags})
    bout = {}
    for b in set(brands) | set(entry):
        if len(m.B.get(b, [])) < 2:
            continue
        lst = sorted(brands.get(b, []), key=lambda x: -x["x"])
        ent_r = sorted(entry.get(b, []), key=lambda x: -x["x"])
        bout[b] = {"n": nm(b), "c": m.cat.get(b) or "", "u": m.sub.get(b) or "", "m": lst[:TOPN], "e": ent_r[:TOPN]}
    fbs = collections.Counter(fb.values())
    feedback = {"nofit": fbs.get("nofit", 0), "pitched": fbs.get("pitched", 0), "won": fbs.get("won", 0)}
    out = {"generated": today.isoformat(), "version": 4, "backtest": bt, "verified": sum(1 for p in props if props[p]["v"]),
           "feedback": feedback, "props": props, "brands": bout}
    (ROOT / "pro").mkdir(exist_ok=True)
    (ROOT / "pro" / "matches.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote pro/matches.json: {len(props)} properties, {len(bout)} brands")


if __name__ == "__main__":
    main()
