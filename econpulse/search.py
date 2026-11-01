"""The site search index (site/data/search.js), loaded by the browser the first time the search opens.

One entry per page, section, chart and series: [kind, title, context, href, extra]. kind is 0 for a
page, 1 a section, 2 a chart and 3 a series; context says where it is (the page, and the source of a
series); extra holds words that match but are not shown (a series' Spanish name, a chart's subtitle).
A series links to the section that shows it, or to its row on the Data page.
"""

PAGE, SECTION, CHART, SERIES = 0, 1, 2, 3


def build_index(nav: list[dict], page_charts: list[tuple[str, str, list[dict]]], items: list[dict],
                anchors: dict[str, tuple[str, str]]) -> list[list]:
    """nav: the tabs with their dropdown entries; page_charts: (href, page title, chart specs);
    items: the snapshot's indicators; anchors: indicator id -> (href, page title)."""
    out, seen = [], set()

    def add(kind, title, context, href, extra=""):
        key = (kind, title, href)
        if title and key not in seen:
            seen.add(key)
            out.append([kind, title, context, href, extra])

    for tab in nav:
        add(PAGE, tab["label"], "Page", tab["href"])
        for child in tab["children"]:
            if "#" in child["href"]:
                add(SECTION, child["title"], tab["label"], child["href"])
            else:                                   # a page of its own under this tab (Every industry, Fiscal Explorer)
                add(PAGE, child["title"], tab["label"], child["href"])
    add(PAGE, "About and methods", "Page", "about.html", "sources methodology")
    for href, title, charts in page_charts:
        for c in charts or []:
            add(CHART, c["title"], title, f"{href}#fig-{c['id']}", c.get("subtitle", ""))
    for i in items:
        href, where = anchors.get(i["id"], (f"data.html#ind-{i['id']}", "Data"))
        add(SERIES, i["label"], f"{where} · {i['source']}", href, i.get("label_es", ""))
    return out
