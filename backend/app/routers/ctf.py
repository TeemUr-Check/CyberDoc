from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.ctf_missions import get_missions_list, get_mission, get_hint, check_answer

router = APIRouter(tags=["ctf"])


class CheckRequest(BaseModel):
    mission_id: str
    answer: str


class HintRequest(BaseModel):
    mission_id: str
    hint_index: int


@router.get("/ctf/missions")
async def list_missions():
    return get_missions_list()


@router.get("/ctf/mission/{mission_id}")
async def mission_detail(mission_id: str):
    m = get_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail="Миссия не найдена.")
    return m


@router.post("/ctf/check")
async def check(body: CheckRequest, settings: Settings = Depends(get_settings)):
    return await check_answer(body.mission_id, body.answer, settings)


@router.post("/ctf/hint")
async def hint(body: HintRequest):
    text = get_hint(body.mission_id, body.hint_index)
    if text is None:
        raise HTTPException(status_code=404, detail="Подсказка не найдена.")
    return {"hint": text}
