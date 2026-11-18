# NoSQL Transaction Management and Concurrency Control Audit

Practical MongoDB coursework project for unstructured claim audit logs. Includes Python and Node.js integration scripts, CRUD operations, index creation, optimistic concurrency control, query-plan inspection, benchmark runners and a CSV calculation sheet.

> Sample data is fictional. Do not use real claim/customer data or commit credentials.

## Structure
- `data/sample_claim_logs.json` — fictional seed records
- `src/python/audit.py` — PyMongo CRUD, indexes, concurrency and benchmark
- `src/node/audit.js` — Node MongoDB driver equivalent
- `reports/benchmark_calculation_sheet.csv` — enter actual measured timings
- `notebooks/benchmark_analysis.ipynb` — calculation/interpretation starter

## Setup
1. Create a MongoDB Atlas cluster or use local MongoDB. Configure your IP access list and database user.
2. Copy `.env.example` to `.env`, then set `MONGODB_URI`. Never commit `.env`.
3. Python: `cd src/python`, `pip install -r requirements.txt`, then `python audit.py --seed --benchmark`.
4. Node: `cd src/node`, `npm install`, then `node audit.js --seed --benchmark`.

Both scripts use database `claims_audit_demo`, collection `claim_audit_logs`.

## Index strategy
- `{claimId: 1}` unique claim lookup
- `{status: 1, createdAt: -1}` status filtering + newest-first listing
- `{claimantRef: 1, createdAt: -1}` claimant history
- Optional TTL index: run with `--create-ttl` only in a disposable lab. TTL deletion is asynchronous; do not apply it to regulated audit records without retention approval.

## Concurrency
MongoDB single-document writes are atomic. The demo's `version` compare-and-set update lets one writer succeed and rejects a stale writer. Handle a zero `matchedCount` by re-reading and applying bounded, safe retry logic. Multi-document transactions require a replica set or sharded cluster; Atlas supports transactions. Keep transactions short.

## Benchmark
Scripts warm up then measure indexed reads and insert/delete pairs. They print elapsed time, average latency, throughput and `explain` execution statistics. Results depend on cluster tier, region, network, cache and dataset. Populate the CSV with your own run results; do not claim the template is measured evidence.

## Important scope
This demonstrates optimistic concurrency, not a database-wide lock manager or guaranteed pessimistic lock. MongoDB uses document-level concurrency controls internally. The scripts do not configure a production sharded/replica-set topology. For real multi-document transactions, use Atlas or a replica-set lab and test rollback/commit behavior separately.
