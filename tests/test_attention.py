"""The GitHub issue that stays open while figures await an AI check (econpulse/attention.py, scripts/ai_check_issue.sh)."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace

from econpulse import attention, forecasts, pensions, statedebt
from econpulse.sources import tesoro

ROOT = Path(__file__).resolve().parents[1]


def _waiting(monkeypatch, debt_status=statedebt.PENDING):
    imf = forecasts.Forecaster(id="imf", name="IMF World Economic Outlook", short="IMF", group="international",
                               url="https://example.org/weo", published=date(2026, 10, 13), status=forecasts.PENDING)
    doc = lambda i, status: pensions.Document(id=i, publisher="AIReF", title="Opinion", short="The opinion",
                                              published="29 May 2026", url="https://example.org/airef",
                                              figures=[], raw={}, status=status)
    monkeypatch.setattr(forecasts, "pending", lambda data: [imf])
    monkeypatch.setattr(pensions, "documents", lambda store: [doc("airef_2026", pensions.PENDING),
                                                              doc("airef_2025", pensions.CHECKED)])
    snap = {"as_of": {"letras": "2026-10-16", "bonds": "2026-10-31"}}
    monkeypatch.setattr(statedebt, "snapshot", lambda data: (snap, date(2026, 11, 3)))
    monkeypatch.setattr(statedebt, "check", lambda data: (debt_status, None))
    return attention.waiting(SimpleNamespace(store=None))


def test_everything_awaiting_a_check_is_listed(monkeypatch):
    items = _waiting(monkeypatch)
    assert [x["id"] for x in items] == ["imf", "airef_2026", "statedebt"]
    assert items[0]["edition"] == "edition of 13 Oct 2026"
    assert items[2]["edition"] == "Letras as of 16 Oct 2026, bonds as of 31 Oct 2026" and items[2]["url"] == tesoro.PAGE
    assert [x["id"] for x in _waiting(monkeypatch, statedebt.CHECKED)] == ["imf", "airef_2026"]


def test_the_issue_text(monkeypatch):
    items = _waiting(monkeypatch)
    body = attention.issue_body(items, "someone")
    assert body.splitlines()[0] == f"<!-- ai-check: {attention.key(items)} -->"
    assert "**IMF World Economic Outlook: forecasts** (edition of 13 Oct 2026): https://example.org/weo" in body
    assert "python -m econpulse confirm imf airef_2026 statedebt" in body and body.endswith("cc @someone\n")
    assert "@" not in attention.issue_body(items)
    assert attention.issue_body([]) == ""


def test_the_key_changes_with_a_new_edition_only(monkeypatch):
    items = _waiting(monkeypatch)
    assert attention.key(items) == attention.key(list(reversed(items)))
    newer = [dict(x, edition="Letras as of 13 Nov 2026") if x["id"] == "statedebt" else x for x in items]
    assert attention.key(newer) != attention.key(items)


def test_the_daily_update_keeps_the_issue_and_redeploys_on_a_check():
    workflow = (ROOT / ".github" / "workflows" / "update.yml").read_text(encoding="utf-8")
    assert "issues: write" in workflow and "run: bash scripts/ai_check_issue.sh" in workflow
    assert workflow.index('- "!data/**"') < workflow.index('- "data/*_checks.json"')    # later patterns win
    assert workflow.rstrip().endswith("run: bash scripts/ai_check_issue.sh"), "the issue step runs after the deploy"
    script = (ROOT / "scripts" / "ai_check_issue.sh").read_text(encoding="utf-8")
    assert "python -m econpulse pending" in script and "gh issue close" in script
    # `confirm` saves to data/<CHECKS>.json: the push trigger's "data/*_checks.json" must match every one
    assert all(m.CHECKS.endswith("_checks") for m in (forecasts, pensions, statedebt))
