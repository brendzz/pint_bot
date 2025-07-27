from fastapi import Query, HTTPException
from datetime import datetime, timezone
from typing import Optional
import api.config as config

def ensure_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def normalize_transaction_type(type_param: Optional[str]) -> Optional[str]:
    if type_param is None:
        return None
    type_lower = type_param.strip().lower()
    if type_lower not in config.VALID_TRANSACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transaction type '{type_param}'. Must be one of: {', '.join(config.VALID_TRANSACTION_TYPES)}"
        )
    return type_lower
