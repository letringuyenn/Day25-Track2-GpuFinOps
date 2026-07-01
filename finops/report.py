"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly",
                 cache: dict | None = None, reasoning: dict | None = None) -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}  ",
        f"**Baseline spend:** ${baseline_usd:,.0f}  ",
        f"**Optimized spend:** ${optimized_usd:,.0f}  ",
        f"**Projected savings:** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if cache:
        lines += [
            "",
            "## Extension: Cache Economics",
            "",
            f"- Cached requests observed: {cache.get('cached_requests', 0):,}",
            f"- Average cached-prefix reads: {cache.get('avg_cache_reads', 0):.2f}",
            f"- Break-even reads: {cache.get('break_even_reads', 0):.2f}",
            f"- Cache counted in optimized case: {cache.get('cache_worth_it', False)}",
        ]
    if reasoning:
        lines += [
            "",
            "## Extension: Reasoning Budget",
            "",
            f"- Reasoning traffic: {reasoning.get('request_share_pct', 0):.1f}% of requests, {reasoning.get('token_share_pct', 0):.1f}% of tokens",
            f"- Reasoning optimized cost: ${reasoning.get('optimized_cost_daily', 0):.2f}/day ({reasoning.get('cost_share_pct', 0):.1f}% of optimized inference cost)",
            f"- Reasoning energy: {reasoning.get('wh_daily', 0):,.1f} Wh/day ({reasoning.get('wh_share_pct', 0):.1f}% of inference energy)",
            "- Routing rule: reserve reasoning for low-confidence or high-complexity requests; default routine traffic to non-reasoning routes.",
        ]
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Energy per query: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cheapest+cleanest region: {sustainability.get('best_region', 'n/a')}",
        ]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str) -> str:
    """Write a simple savings bar chart PNG. Returns the path. No-op if matplotlib absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, vals, color="#2e548a")
    ax.set_ylabel("Savings (USD / month)")
    ax.set_title("GPU cost savings by FinOps lever")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
