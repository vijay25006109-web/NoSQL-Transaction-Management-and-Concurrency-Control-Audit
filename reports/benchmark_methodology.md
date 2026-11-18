# Benchmark methodology

Enter measured output in `benchmark_calculation_sheet.csv`.

- Average latency (ms/op) = elapsed_ms / operations
- Throughput (ops/sec) = operations / (elapsed_ms / 1000)
- Query efficiency: inspect `executionStats.totalDocsExamined` and `totalKeysExamined`.

Use the same cluster, region, dataset, indexes and workload. Warm up first; run at least five rounds; report median and average. Include cluster tier, MongoDB version, document count, client location and date. Each additional index adds storage and write-maintenance cost. Do not report fabricated results.
