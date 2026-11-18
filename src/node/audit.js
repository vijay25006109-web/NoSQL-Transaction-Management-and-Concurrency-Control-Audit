require("dotenv").config({path:require("path").resolve(__dirname,"../../.env")});
const {MongoClient}=require("mongodb"), fs=require("fs"), path=require("path"), {performance}=require("perf_hooks");
const uri=process.env.MONGODB_URI||"mongodb://localhost:27017", dbn=process.env.MONGODB_DB||"claims_audit_demo", cn=process.env.MONGODB_COLLECTION||"claim_audit_logs";
async function main(){
 const client=new MongoClient(uri,{serverSelectionTimeoutMS:8000});
 try{
  await client.connect(); await client.db("admin").command({ping:1});
  const c=client.db(dbn).collection(cn); console.log("Connected",dbn,cn);
  await c.createIndex({claimId:1},{unique:true,name:"idx_claim_id"});
  await c.createIndex({status:1,createdAt:-1},{name:"idx_status_created"});
  await c.createIndex({claimantRef:1,createdAt:-1},{name:"idx_claimant_created"});
  if(process.argv.includes("--create-ttl")) await c.createIndex({createdAt:1},{expireAfterSeconds:31536000,name:"demo_ttl_1_year"});
  if(process.argv.includes("--seed")){
   const docs=JSON.parse(fs.readFileSync(path.resolve(__dirname,"../../data/sample_claim_logs.json")));
   for(const d of docs) await c.updateOne({claimId:d.claimId},{$setOnInsert:{...d,createdAt:new Date(d.createdAt)}},{upsert:true});
  }
  const id="NODE-"+Date.now(); await c.insertOne({claimId:id,status:"new",version:1,createdAt:new Date()});
  const found=await c.findOne({claimId:id}); await c.updateOne({claimId:id},{$set:{status:"reviewed"},$inc:{version:1}});
  const updated=await c.findOne({claimId:id}); const del=await c.deleteOne({claimId:id});
  console.log("CRUD",!!found,updated.status,del.deletedCount);
  const lockid="LOCK-"+Date.now(); await c.insertOne({claimId:lockid,status:"pending",version:1});
  const a=await c.updateOne({claimId:lockid,version:1},{$set:{status:"writer_A"},$inc:{version:1}});
  const b=await c.updateOne({claimId:lockid,version:1},{$set:{status:"writer_B"},$inc:{version:1}});
  console.log("Optimistic concurrency",{firstMatched:a.matchedCount,staleMatched:b.matchedCount,final:await c.findOne({claimId:lockid})});
  await c.deleteOne({claimId:lockid});
  if(process.argv.includes("--benchmark")){
   const n=300,q={status:"review"}; await c.find(q).sort({createdAt:-1}).limit(10).toArray();
   let read=0,write=0;
   for(let i=0;i<n;i++){let t=performance.now();await c.find(q).sort({createdAt:-1}).limit(10).toArray();read+=performance.now()-t;}
   for(let i=0;i<n;i++){const d={claimId:`BENCH-${Date.now()}-${i}-${Math.random()}`,status:"bench",createdAt:new Date()};let t=performance.now();await c.insertOne(d);await c.deleteOne({claimId:d.claimId});write+=performance.now()-t;}
   console.log("BENCHMARK",{n,readElapsedMs:read,readAvgMs:read/n,readOpsPerSecond:n/(read/1000),writePairElapsedMs:write,writePairAvgMs:write/n,writePairsPerSecond:n/(write/1000)});
   const ex=await c.find(q).sort({createdAt:-1}).limit(10).explain("executionStats"); console.log("QUERY PLAN",ex.executionStats);
  }
 }finally{await client.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
