from datetime import datetime
from workos.audit_logs import AuditLogEvent

user_organization_set = AuditLogEvent(
    {
        "action": "user.organization_set",
        "occurred_at": datetime.now().isoformat(),
        "actor": {
            "type": "user",
            "id": "user_01GBNJC3MX9ZZJW1FSTF4C5938",
        },
        "targets": [
            {
                "type": "organization",
                "id": "team_01GBNJD4MKHVKJGEWK42JNMBGS",
            },
        ],
        "context": {
            "location": "123.123.123.123",
            "user_agent": "Chrome/104.0.0.0",
        },
    }
)
