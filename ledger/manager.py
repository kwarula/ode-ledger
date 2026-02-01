import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import jsonlines

class LedgerEntry(BaseModel):
    id: str
    timestamp: datetime
    agent_id: str
    entry_type: str
    payload: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    references: Optional[List[str]] = []

    @validator('entry_type')
    def validate_entry_type(cls, v):
        allowed = [
            "OBSERVATION", "HYPOTHESIS", "CHALLENGE", 
            "RISK_ASSESSMENT", "PROPOSED_ACTION", "EXECUTION_LOG"
        ]
        if v not in allowed:
            raise ValueError(f"entry_type must be one of {allowed}")
        return v

class LedgerManager:
    def __init__(self, ledger_path: str, schema_path: str):
        self.ledger_path = ledger_path
        self.schema_path = schema_path
        
        # Ensure the ledger file exists
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'w') as f:
                pass

    def add_entry(self, agent_id: str, entry_type: str, payload: Dict[str, Any], confidence: float, references: List[str] = None):
        entry = LedgerEntry(
            id=f"evt_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(),
            agent_id=agent_id,
            entry_type=entry_type,
            payload=payload,
            confidence=confidence,
            references=references or []
        )
        
        # Prepare for storage (convert datetime to ISO string)
        data = entry.model_dump(exclude_none=True)
        data['timestamp'] = entry.timestamp.isoformat()
        
        with jsonlines.open(self.ledger_path, mode='a') as writer:
            writer.write(data)
        
        return entry

    def get_all_entries(self) -> List[Dict[str, Any]]:
        entries = []
        if os.path.exists(self.ledger_path):
            with jsonlines.open(self.ledger_path) as reader:
                for obj in reader:
                    entries.append(obj)
        return entries
