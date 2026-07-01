# GPU FinOps Optimization Write-up

## 1. Baseline vs. Optimized

NimbusAI's monthly baseline GPU spend is **$27,133**. After applying the FinOps
levers in the lab, optimized spend drops to **$14,626**, saving **$12,507/month**
or **46%**.

For inference traffic, the baseline unit cost is **$6.488/1M-token**. The
optimized unit cost is **$1.126/1M-token**, saving **82.6%** through cascade
routing, prompt caching, and batch API discounts.

## 2. Savings by Lever

| Lever | Monthly savings |
|---|---:|
| Inference: cascade/cache/batch | $1,212 |
| Purchasing: spot/reserved | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

The highest-impact lever is purchasing strategy. Moving interruptible jobs to
spot and steady high-duty-cycle jobs to reserved capacity saves **$10,040/month**.
Inference optimization is also strong at the request level because batch and
cache discounts multiply, but the absolute monthly saving is smaller than the
GPU purchasing change in this dataset.

## 3. GPU-Util Lie

The audit finds two GPU-Util lie cases:

| GPU | Type | GPU-Util | MFU |
|---|---|---:|---:|
| gpu-h100-4 | H100 | 98.2% | 0.194 |
| gpu-a10g-1 | A10G | 96.9% | 0.268 |

This means the GPU clock appears busy, but the workload is not using the rented
compute efficiently. `nvidia-smi` GPU-Util measures activity, not useful FLOPs.
For `gpu-h100-4`, NimbusAI is paying for a full H100 hour while getting about
one fifth of the available FLOPs. The practical action is to profile the
workload, right-size the GPU tier, or move memory-bound inference to a cheaper
GPU with enough bandwidth.

## 4. Extensions Implemented

### Extension 1: Cache Economics

I added `cache_break_even_reads()` and `cache_is_worth_it()` in
`finops/pricing.py`, then used the cache gate in M2 before counting prompt-cache
savings.

Measured result:

- Cached requests observed: **2,400**
- Average cached-prefix reads: **150.00**
- Break-even reads: **0.28**
- Decision: cache is worth it and is counted in the optimized case

Insight: prompt caching is economically justified for this dataset because
observed reuse is far above the break-even point.

### Extension 2: Reasoning Budget

I extended M2 and M5 to split reasoning traffic from normal inference traffic.

Measured result:

- Reasoning traffic: **8.4%** of requests and **16.5%** of tokens
- Reasoning optimized cost: **$1.40/day**, or **16.5%** of optimized inference cost
- Reasoning energy: **29,787.7 Wh/day**, or **94.0%** of inference energy

Insight: reasoning traffic is a small request share but dominates energy usage
because reasoning queries use an 80x energy multiplier in this lab model. The
recommended routing rule is to use reasoning only for low-confidence or
high-complexity requests and default routine traffic to non-reasoning routes.

## 5. Recommendations for NimbusAI

1. Apply the purchasing policy first: spot for interruptible jobs, reserved for
   steady high-utilization inference, and on-demand only for spiky workloads.
2. Track inference unit economics in `$/1M-token`, not only `$/GPU-hour`, so
   cascade, caching, and batching improvements are visible.
3. Use MFU/MBU in GPU reviews and flag high-utilization, low-MFU workloads before
   buying more capacity.
4. Enforce tag coverage before chargeback. The current dataset has **92%** tag
   coverage, so chargeback is ready.
5. Add a reasoning budget policy because reasoning accounts for most inference
   energy despite being a small share of requests.
