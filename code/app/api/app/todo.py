from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import uuid


@dataclass
class Todo:
    title: str
    done: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def redis_key(self) -> str:
        return f"todo:{self.id}"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "Todo":
        return cls(**json.loads(data))
