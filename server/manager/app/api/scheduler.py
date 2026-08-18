from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from manager.app.database.database import get_db
from manager.app.core.config import settings
from manager.app.services.scheduler_service import scheduler_snapshot
router=APIRouter(prefix="/scheduler",tags=["scheduler"])
@router.get("/scores")
def scores(db:Session=Depends(get_db)):
    return scheduler_snapshot(db,settings.heartbeat_warning_seconds,settings.heartbeat_offline_seconds)
@router.get("/recommendation")
def recommendation(db:Session=Depends(get_db)):
    result=scheduler_snapshot(db,settings.heartbeat_warning_seconds,settings.heartbeat_offline_seconds)
    if not result["selected"]: raise HTTPException(503,"No active machine is available")
    return result
