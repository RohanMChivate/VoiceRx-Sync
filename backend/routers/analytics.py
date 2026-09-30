import os
import sys

from fastapi import APIRouter, Query
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.database import get_analytics

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

router = APIRouter()


@router.get("")
def analytics_endpoint(doctor_email: str = Query(...), period: str = Query("month")):
    data = get_analytics(doctor_email, period)
    # Convert ObjectIds / datetimes for JSON
    import json
    from bson import ObjectId
    from datetime import datetime

    def serialise(obj):
        if isinstance(obj, ObjectId): return str(obj)
        if isinstance(obj, datetime):  return obj.isoformat()
        raise TypeError(f"Not serialisable: {type(obj)}")

    return json.loads(json.dumps(data, default=serialise))
