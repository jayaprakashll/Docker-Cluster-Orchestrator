from __future__ import annotations
from dataclasses import dataclass, asdict
from manager.app.database.repository import list_machine_health

@dataclass
class MachineScore:
    machine_id: str
    name: str
    status: str
    score: float
    cpu_score: float
    memory_score: float
    container_score: float
    health_score: float
    running_containers: int

class WeightedResourceScheduler:
    """Ranks live machines. Higher score means a better deployment target."""
    def __init__(self, cpu_weight=.40, memory_weight=.35, container_weight=.15, health_weight=.10, max_containers=100):
        total=cpu_weight+memory_weight+container_weight+health_weight
        self.cpu_weight=cpu_weight/total; self.memory_weight=memory_weight/total
        self.container_weight=container_weight/total; self.health_weight=health_weight/total
        self.max_containers=max(1,max_containers)
    def score(self,m):
        status=str(m.get("status","unknown")).lower()
        cpu=max(0,min(100,float(m.get("cpu_percent",0) or 0)))
        memory=max(0,min(100,float(m.get("memory_percent",0) or 0)))
        running=max(0,int(m.get("running_containers",0) or 0))
        cpu_score=100-cpu; memory_score=100-memory
        container_score=max(0,100*(1-running/self.max_containers))
        health_score={"healthy":100,"warning":40,"offline":0}.get(status,20)
        total=0 if status=="offline" else (cpu_score*self.cpu_weight+memory_score*self.memory_weight+container_score*self.container_weight+health_score*self.health_weight)
        return MachineScore(str(m["machine_id"]),m["name"],status,round(total,2),round(cpu_score,2),round(memory_score,2),round(container_score,2),round(health_score,2),running)
    def rank(self,machines): return sorted((self.score(m) for m in machines),key=lambda x:x.score,reverse=True)
    def explain(self,machines):
        ranking=self.rank(machines)
        selected=next((x for x in ranking if x.status in ("healthy","warning")),None)
        return {"selected":asdict(selected) if selected else None,"ranking":[asdict(x) for x in ranking],"weights":{"cpu":self.cpu_weight,"memory":self.memory_weight,"containers":self.container_weight,"health":self.health_weight}}

def scheduler_snapshot(db, warning_after=10, offline_after=15):
    return WeightedResourceScheduler().explain(list_machine_health(db,warning_after,offline_after))
