# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Extension: Cache Economics

- Cached requests observed: 2,400
- Average cached-prefix reads: 150.00
- Break-even reads: 0.28
- Cache counted in optimized case: True

## Extension: Reasoning Budget

- Reasoning traffic: 8.4% of requests, 16.5% of tokens
- Reasoning optimized cost: $1.40/day (16.5% of optimized inference cost)
- Reasoning energy: 29,787.7 Wh/day (94.0% of inference energy)
- Routing rule: reserve reasoning for low-confidence or high-complexity requests; default routine traffic to non-reasoning routes.

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

_Figures are June-2026 as-of snapshots; re-baseline before acting._