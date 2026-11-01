"""Hawkish/dovish word-list scoring of central bankers' speeches (no AI): EconPulse's own lists.

Each speech is split into sentences and searched for phrases that signal a tighter or an
easier monetary policy stance: price pressures rising or easing, risks to inflation on the
upside or the downside, rates going up or down, a strong or a weak economy. The score is the
net share of hawkish matches,

    score = 100 x (hawkish - dovish) / (hawkish + dovish)

from -100 (every match dovish) to +100 (every match hawkish). Speeches with fewer than
MIN_MATCHES matches, or in which under MIN_POLICY_SHARE of sentences mention monetary policy,
inflation or interest rates at all (the policy share), have no monetary-policy stance to score:
a speech on payments or supervision can use "strong demand" without saying anything about rates.

The lists count changes and risks, not levels: "higher inflation" and "lower inflation" count,
"high" and "low" do not, nor a bare "accommodative", because speeches use those to describe
the past (the low-inflation decade) as often as the outlook. Word lists are still crude next
to a reader: they miss negation ("not yet time to cut" counts as a cut) and context. The lists
are published on the page so anyone can see what is counted.
"""

import re

VERSION = 2   # bump when the lists or rules change: stored scores are then recomputed
MIN_MATCHES = 4
MIN_POLICY_SHARE = 0.05   # and at least this share of sentences about monetary policy, inflation or rates

_PRICES = (r"(inflation|price pressures?|price growth|prices|wage growth|wages|core inflation|underlying inflation|"
           r"services inflation|inflation expectations|second-round effects|unit labour costs)")
_ECONOMY = r"(growth|economy|economic activity|activity|demand|labour markets?|employment)"
_RATES = r"((key |policy |interest |deposit facility )?(interest )?rates?)"

HAWKISH = {
    "Price pressures rising": [
        rf"\b(higher|elevated|rising|persistent|stubborn|sticky|strong|accelerat\w*|upward|excessive|surg\w*|increas\w*)\b[^.;]{{0,40}}\b{_PRICES}\b",
        rf"\b{_PRICES}\b[^.;]{{0,30}}\b(remains? (too )?high|is (too )?high|(is |are )?rising|picking up|accelerat\w*|above (our |the )?(2% )?target|de-?anchor\w*)\b",
    ],
    "Upside risks to inflation": [
        r"\bupside risks?\b[^.;]{0,30}\binflation\b",
        r"\brisks? to (the )?inflation( outlook)?\b[^.;]{0,25}\bupside\b",
    ],
    "Rates up or staying restrictive": [
        rf"\b(rais\w*|hik\w*|increas\w*|tighten\w*)\b[^.;]{{0,15}}\b{_RATES}\b",
        r"\b(rate (hikes?|rises?|increases?)|further tightening|more tightening|restrictive (stance|territory|policy|levels?)|"
        r"remain restrictive|sufficiently restrictive|higher for longer|premature to (cut|ease|lower)|"
        r"too early to (cut|ease|lower|declare victory)|wage-price spiral)\b",
    ],
    "Strong economy or tight labour market": [
        rf"\b(strong|robust|resilient|solid|buoyant|overheat\w*)\b[^.;]{{0,15}}\b{_ECONOMY}\b",
        r"\b(tight labour markets?|low unemployment|labour shortages?)\b",
    ],
}

DOVISH = {
    "Price pressures easing": [
        rf"\b(lower|falling|declin\w*|eas\w*|moderat\w*|subdued|slow\w*|weak\w*|downward|decreas\w*|reced\w*|abat\w*|dampen\w*)\b[^.;]{{0,40}}\b{_PRICES}\b",
        rf"\b{_PRICES}\b[^.;]{{0,30}}\b(is |are )?(falling|declin\w*|eas\w*|moderat\w*|coming down|below (our |the )?(2% )?target|undershoot\w*|on track to (return|reach))\b",
    ],
    "Downside risks to inflation": [
        r"\bdownside risks?\b[^.;]{0,30}\binflation\b",
        r"\brisks? to (the )?inflation( outlook)?\b[^.;]{0,25}\bdownside\b",
        r"\b(undershoot\w*)\b",
    ],
    "Rates down or less restrictive": [
        rf"\b(cut\w*|lower\w*|reduc\w*|eas\w*)\b[^.;]{{0,15}}\b{_RATES}\b",
        r"\b(rate cuts?|less restrictive|more accommodative|stimulus|dial(ling)? back|remove (some )?(policy )?restriction|"
        r"support (the )?(economy|growth|demand))\b",
    ],
    "Weak economy or rising unemployment": [
        rf"\b(weak|weaker|sluggish|stagnat\w*|subdued|soft|fragile)\b[^.;]{{0,15}}\b{_ECONOMY}\b",
        r"\b(recession|contraction|downturn|downside risks? to (growth|the economy|economic activity)|rising unemployment)\b",
    ],
}

POLICY = re.compile(r"\b(monetary policy|inflation|interest rates?|policy rates?|price stability|key ecb|deposit facility)\b", re.I)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_COMPILED = {side: {group: [re.compile(p, re.I) for p in patterns] for group, patterns in lists.items()}
             for side, lists in (("hawkish", HAWKISH), ("dovish", DOVISH))}


def score(text: str) -> dict:
    """Counts and score for one speech."""
    sentences = [s for s in _SENTENCE.split(" ".join(text.split())) if len(s) > 20]
    counts = {"hawkish": 0, "dovish": 0}
    groups: dict[str, int] = {}
    policy = 0
    for s in sentences:
        if POLICY.search(s):
            policy += 1
        for side, lists in _COMPILED.items():
            for group, patterns in lists.items():
                n = sum(len(p.findall(s)) for p in patterns)
                if n:
                    counts[side] += n
                    groups[group] = groups.get(group, 0) + n
    total = counts["hawkish"] + counts["dovish"]
    return {"hawkish": counts["hawkish"], "dovish": counts["dovish"], "sentences": len(sentences),
            "policy_share": round(policy / len(sentences), 3) if sentences else 0.0,
            "score": round(100 * (counts["hawkish"] - counts["dovish"]) / total, 1)
            if total >= MIN_MATCHES and sentences and policy / len(sentences) >= MIN_POLICY_SHARE else None,
            "groups": groups}


def word_lists() -> dict:
    """The lists as shown on the page: side -> group -> patterns."""
    return {"hawkish": HAWKISH, "dovish": DOVISH}


# What each group counts, in words, for the page (the exact patterns are shown too).
GROUP_NOTES = {
    "Price pressures rising": "rising, higher, elevated, persistent, sticky, accelerating or upward near inflation, prices, "
                              "wages, inflation expectations or second-round effects; and inflation “remaining high”, "
                              "“picking up” or “above target”",
    "Upside risks to inflation": "“upside risks to inflation”, “risks to the inflation outlook … to the upside”",
    "Rates up or staying restrictive": "raising, hiking or tightening rates; rate hikes; further tightening; restrictive "
                                       "stance; higher for longer; too early to cut; wage-price spiral",
    "Strong economy or tight labour market": "strong, robust, resilient or solid growth, demand or labour market; tight "
                                             "labour markets; low unemployment; labour shortages",
    "Price pressures easing": "lower, falling, declining, easing, moderating, subdued or downward near inflation, prices or "
                              "wages; and inflation “coming down”, “below target” or “on track to return”",
    "Downside risks to inflation": "“downside risks to inflation”, undershooting",
    "Rates down or less restrictive": "cutting, lowering or easing rates; rate cuts; less restrictive; more accommodative; "
                                      "stimulus; dialling back; supporting the economy",
    "Weak economy or rising unemployment": "weak, sluggish, subdued or fragile growth or demand; recession; contraction; "
                                           "downturn; downside risks to growth; rising unemployment",
}
