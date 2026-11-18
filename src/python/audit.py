import argparse, json, os, time, statistics
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT/".env")
URI=os.getenv("MONGODB_URI","mongodb://localhost:27017")
DB=os.getenv("MONGODB_DB","claims_audit_demo")
COL=os.getenv("MONGODB_COLLECTION","claim_audit_logs")

def seed(c):
    docs=json.loads((ROOT/"data/sample_claim_logs.json").read_text())
    for d in docs:
        d["createdAt"]=datetime.fromisoformat(d["createdAt"].replace("Z","+00:00"))
        try: c.insert_one(d)
        except DuplicateKeyError: pass

def indexes(c,ttl=False):
    c.create_index([("claimId",ASCENDING)],unique=True,name="idx_claim_id")
    c.create_index([("status",ASCENDING),("createdAt",DESCENDING)],name="idx_status_created")
    c.create_index([("claimantRef",ASCENDING),("createdAt",DESCENDING)],name="idx_claimant_created")
    if ttl: c.create_index([("createdAt",ASCENDING)],expireAfterSeconds=31536000,name="demo_ttl_1_year")
    print("Indexes:",list(c.list_indexes()))

def crud(c):
    cid="PY-"+str(time.time_ns())
    c.insert_one({"claimId":cid,"status":"new","createdAt":datetime.now(timezone.utc),"version":1})
    found=c.find_one({"claimId":cid})
    c.update_one({"claimId":cid},{"$set":{"status":"reviewed"},"$inc":{"version":1}})
    updated=c.find_one({"claimId":cid})
    deleted=c.delete_one({"claimId":cid})
    print("CRUD:",bool(found),updated["status"],deleted.deleted_count)

def concurrency(c):
    cid="LOCK-"+str(time.time_ns())
    c.insert_one({"claimId":cid,"status":"pending","version":1})
    first=c.update_one({"claimId":cid,"version":1},{"$set":{"status":"writer_A"},"$inc":{"version":1}})
    stale=c.update_one({"claimId":cid,"version":1},{"$set":{"status":"writer_B"},"$inc":{"version":1}})
    final=c.find_one({"claimId":cid})
    print("Optimistic concurrency:",{"first_matched":first.matched_count,"stale_matched":stale.matched_count,"final":final["status"],"version":final["version"]})
    c.delete_one({"claimId":cid})

def benchmark(c,n=300):
    q={"status":"review"}; list(c.find(q).sort("createdAt",-1).limit(10))
    reads=[]; writes=[]
    for _ in range(n):
        t=time.perf_counter(); list(c.find(q).sort("createdAt",-1).limit(10)); reads.append((time.perf_counter()-t)*1000)
    for i in range(n):
        doc={"claimId":f"BENCH-{time.time_ns()}-{i}","status":"bench","createdAt":datetime.now(timezone.utc)}
        t=time.perf_counter(); c.insert_one(doc); c.delete_one({"claimId":doc["claimId"]}); writes.append((time.perf_counter()-t)*1000)
    for label,vals in [("indexed_read",reads),("insert_delete_pair",writes)]:
        total=sum(vals); print(label,{"operations":n,"elapsed_ms":round(total,3),"average_ms":round(statistics.mean(vals),4),"ops_per_second":round(n/(total/1000),2)})
    e=c.find(q).sort("createdAt",-1).limit(10).explain()
    print("executionStats",e.get("executionStats",{}))

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--seed",action="store_true"); p.add_argument("--benchmark",action="store_true"); p.add_argument("--create-ttl",action="store_true"); a=p.parse_args()
    client=MongoClient(URI,serverSelectionTimeoutMS=8000); client.admin.command("ping")
    col=client[DB][COL]; print("Connected",DB,COL); indexes(col,a.create_ttl)
    if a.seed: seed(col)
    crud(col); concurrency(col)
    if a.benchmark: benchmark(col)
    client.close()
