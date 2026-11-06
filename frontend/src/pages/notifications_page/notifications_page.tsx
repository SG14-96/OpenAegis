import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card, Empty, List, Spin, Tag, Typography } from "antd";
import { useAppStore } from "../../store/appStore";
import { getAlarmEvents } from "../../services/alarm";
import type { AlarmHistoryEvent } from "../../types/alarm";

const { Title, Text } = Typography;

const PAGE_SIZE = 50;

const EVENT_CONFIG: Record<string, { label: string; color: string }> = {
  armed_stay: { label: "Armed - Stay", color: "gold" },
  armed_away: { label: "Armed - Away", color: "red" },
  disarmed: { label: "Disarmed", color: "green" },
  alarm_triggered: { label: "Alarm Triggered", color: "red" },
  alarm_restored: { label: "Alarm Restored", color: "green" },
  alarm_panicked: { label: "Panic", color: "red" },
};

const PANIC_LABELS: Record<string, string> = {
  panic: "Panic",
  fire: "Fire",
  auxiliary: "Auxiliary (medical)",
};

function describe(event: AlarmHistoryEvent): string {
  const parts = [`Partition ${event.partition_id}`];
  if (event.trigger_type) parts.push(PANIC_LABELS[event.trigger_type] ?? event.trigger_type);
  if (event.last_user !== null) parts.push(`Panel user ${event.last_user}`);
  return parts.join(" · ");
}

const NotificationsPage = () => {
  const historyVersion = useAppStore((s) => s.historyVersion);
  const [events, setEvents] = useState<AlarmHistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reloads the newest page. Runs on mount and whenever the websocket
  // reports a new history event (historyVersion bump).
  const loadLatest = useCallback(() => {
    getAlarmEvents(PAGE_SIZE)
      .then((rows) => {
        setEvents(rows);
        setHasMore(rows.length === PAGE_SIZE);
        setError(null);
      })
      .catch(() => setError("Failed to load event history."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(loadLatest, [loadLatest, historyVersion]);

  const loadMore = () => {
    const oldest = events[events.length - 1];
    if (!oldest) return;
    setLoadingMore(true);
    getAlarmEvents(PAGE_SIZE, oldest.created_at)
      .then((rows) => {
        setEvents((prev) => [...prev, ...rows]);
        setHasMore(rows.length === PAGE_SIZE);
      })
      .catch(() => setError("Failed to load older events."))
      .finally(() => setLoadingMore(false));
  };

  return (
    <div>
      <Title level={1}>Notifications</Title>
      <Card title="Alarm History">
        {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 12 }} />}
        {loading ? (
          <div style={{ textAlign: "center", padding: 24 }}>
            <Spin />
          </div>
        ) : events.length === 0 ? (
          <Empty
            description="No arm, disarm or alarm events recorded yet."
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <>
            <List
              dataSource={events}
              rowKey="id"
              renderItem={(event) => {
                const config = EVENT_CONFIG[event.event_type] ?? { label: event.event_type, color: "default" };
                return (
                  <List.Item>
                    <div style={{ display: "flex", justifyContent: "space-between", width: "100%", gap: 12 }}>
                      <div>
                        <Tag color={config.color}>{config.label}</Tag>
                        <Text type="secondary">{describe(event)}</Text>
                      </div>
                      <Text type="secondary">{new Date(event.created_at).toLocaleString()}</Text>
                    </div>
                  </List.Item>
                );
              }}
            />
            {hasMore && (
              <div style={{ textAlign: "center", marginTop: 12 }}>
                <Button loading={loadingMore} onClick={loadMore}>
                  Load older events
                </Button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
};

export default NotificationsPage;
