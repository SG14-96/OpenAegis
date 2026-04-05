class AlarmEvent:
    # Zone events — payload must include "zone_id: int"
    ZONE_OPEN       = "zone_open"
    ZONE_CLOSED     = "zone_closed"
    ZONE_BYPASSED   = "zone_bypassed"   # payload: "zone_id", "bypassed: bool"

    # Partition arm/disarm — payload must include "partition_id: int"
    ARMED_STAY      = "armed_stay"
    ARMED_AWAY      = "armed_away"
    DISARMED        = "disarmed"

    # Alarm events — payload must include "partition_id: int"
    ALARM_TRIGGERED = "alarm_triggered"
    ALARM_RESTORED  = "alarm_restored"
    ALARM_PANICKED   = "alarm_panicked"  # payload: "partition_id", "panicked: bool", "panic_type: str"

    # Plugin lifecycle
    READY           = "ready"
    ERROR           = "error"           # payload: "detail: str"
