"""M2 - Inference Cost Levers: $/1M-token, batch x cache x cascade.

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output), illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}
CACHE_WRITE_COST_PER_M = 0.25


def _cache_reuse_stats(rows: list[dict]) -> dict:
    """Estimate cached-prefix reuse from the tags available in token_usage.csv."""
    cached_rows = [r for r in rows if int(num(r.get("cached_input_tokens", 0))) > 0]
    groups = {
        (r.get("team", ""), r.get("project", ""), r.get("route_tier", ""))
        for r in cached_rows
    }
    avg_reads = len(cached_rows) / len(groups) if groups else 0.0
    break_even = pricing.cache_break_even_reads(CACHE_WRITE_COST_PER_M)
    return {
        "cached_requests": len(cached_rows),
        "avg_cache_reads": avg_reads,
        "break_even_reads": break_even,
        "cache_worth_it": pricing.cache_is_worth_it(avg_reads, CACHE_WRITE_COST_PER_M),
    }


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    cache_stats = _cache_reuse_stats(rows)
    base_cost = opt_cost = 0.0
    reasoning_cost = non_reasoning_cost = 0.0
    reasoning_wh = non_reasoning_wh = 0.0
    reasoning_tokens = non_reasoning_tokens = 0
    reasoning_requests = 0
    total_tokens = 0

    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"])) if cache_stats["cache_worth_it"] else 0
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r.get("is_reasoning", 0))))
        tokens = inp + out
        total_tokens += tokens

        # Baseline: everything on the large model, no cache, no batch.
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)

        # Optimized: cascade route tier, prompt caching when economic, and batch API.
        pin, pout = MODEL_PRICES[r["route_tier"]]
        req_cost = pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)
        opt_cost += req_cost

        wh = sustainability.wh_per_query(tokens, is_reasoning=is_reasoning)
        if is_reasoning:
            reasoning_requests += 1
            reasoning_tokens += tokens
            reasoning_cost += req_cost
            reasoning_wh += wh
        else:
            non_reasoning_tokens += tokens
            non_reasoning_cost += req_cost
            non_reasoning_wh += wh

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0
    total_wh = reasoning_wh + non_reasoning_wh
    reasoning_share = reasoning_requests / len(rows) * 100 if rows else 0.0
    reasoning_cost_share = reasoning_cost / opt_cost * 100 if opt_cost else 0.0
    reasoning_wh_share = reasoning_wh / total_wh * 100 if total_wh else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(
            f"cache gate: avg reads={cache_stats['avg_cache_reads']:.1f}, "
            f"break-even={cache_stats['break_even_reads']:.2f}, "
            f"worth it? {cache_stats['cache_worth_it']}"
        )
        print(
            f"reasoning budget: {reasoning_share:.1f}% requests -> "
            f"{reasoning_cost_share:.1f}% optimized cost, {reasoning_wh_share:.1f}% inference Wh"
        )

    return {
        "baseline_daily": round(base_cost, 2),
        "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3),
        "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1),
        "total_tokens": total_tokens,
        "cache": {
            "avg_cache_reads": round(cache_stats["avg_cache_reads"], 2),
            "break_even_reads": round(cache_stats["break_even_reads"], 2),
            "cache_worth_it": cache_stats["cache_worth_it"],
            "cached_requests": cache_stats["cached_requests"],
        },
        "reasoning": {
            "requests": reasoning_requests,
            "request_share_pct": round(reasoning_share, 1),
            "tokens": reasoning_tokens,
            "token_share_pct": round(reasoning_tokens / total_tokens * 100, 1) if total_tokens else 0.0,
            "optimized_cost_daily": round(reasoning_cost, 2),
            "non_reasoning_cost_daily": round(non_reasoning_cost, 2),
            "cost_share_pct": round(reasoning_cost_share, 1),
            "wh_daily": round(reasoning_wh, 2),
            "non_reasoning_wh_daily": round(non_reasoning_wh, 2),
            "wh_share_pct": round(reasoning_wh_share, 1),
        },
    }


if __name__ == "__main__":
    run()
