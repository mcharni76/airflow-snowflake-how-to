from __future__ import annotations

import hashlib
import os
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query

app = FastAPI(
    title="EventHub Mock Ticketing API",
    description=(
        "CDC-aware mock ticketing vendor. Generates new tickets continuously. "
        "Supports watermark-based incremental extraction via `since` parameter (ISO timestamp). "
        "First call without `since` returns historical backfill data."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

API_TOKEN = os.getenv("API_TOKEN", "dev-token-events-2026")
TICKETS_PER_INTERVAL = int(os.getenv("TICKETS_PER_INTERVAL", "15"))
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "300"))
BACKFILL_DAYS = int(os.getenv("BACKFILL_DAYS", "7"))

START_TIME = datetime(2026, 6, 4, 0, 0, 0, tzinfo=timezone.utc)

EVENTS = [
    {"event_id": "EVT-2026-001", "event_name": "Music Festival 2026", "venue": "Stadium Arena"},
    {"event_id": "EVT-2026-002", "event_name": "Formula Racing Championship", "venue": "Grand Prix Circuit"},
    {"event_id": "EVT-2026-003", "event_name": "Pro Wrestling Showdown", "venue": "Convention Center"},
    {"event_id": "EVT-2026-004", "event_name": "International Film Festival", "venue": "Amphitheater"},
    {"event_id": "EVT-2026-005", "event_name": "Electronic Music Conference", "venue": "Exhibition Hall"},
    {"event_id": "EVT-2026-006", "event_name": "Summer Concert Series", "venue": "Open Air Park"},
]

CATEGORIES = ["VIP", "Premium", "Standard", "Economy"]
STATUSES = ["confirmed", "pending", "cancelled", "refunded"]
PRICE_MAP = {"VIP": (200, 800), "Premium": (100, 250), "Standard": (40, 120), "Economy": (15, 50)}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _generate_ticket(ticket_index: int, created_at: datetime) -> dict:
    rng = random.Random(ticket_index)
    event = rng.choice(EVENTS)
    category = rng.choice(CATEGORIES)
    price_range = PRICE_MAP[category]
    price = round(rng.uniform(*price_range), 2)
    status = rng.choices(STATUSES, weights=[70, 15, 10, 5])[0]

    email_raw = f"attendee_{ticket_index}@example.com"
    email_hash = hashlib.sha256(email_raw.encode()).hexdigest()[:16]

    return {
        "ticket_id": f"EVH-{created_at.strftime('%Y%m%d')}-{ticket_index:06d}",
        "event_id": event["event_id"],
        "event_name": event["event_name"],
        "venue": event["venue"],
        "category": category,
        "price": price,
        "currency": "USD",
        "status": status,
        "purchase_timestamp": created_at.isoformat(),
        "attendee_email_hash": email_hash,
    }


def _get_all_tickets_since(since: datetime) -> list[dict]:
    now = _now_utc()
    tickets = []
    global_index = 0

    current = START_TIME
    while current < now:
        interval_end = current + timedelta(seconds=INTERVAL_SECONDS)
        rng = random.Random(int(current.timestamp()))
        count = rng.randint(TICKETS_PER_INTERVAL - 5, TICKETS_PER_INTERVAL + 10)

        for i in range(count):
            ticket_time = current + timedelta(seconds=rng.randint(0, INTERVAL_SECONDS - 1))
            if ticket_time > since and ticket_time <= now:
                tickets.append(_generate_ticket(global_index + i, ticket_time))
            global_index += 1

        current = interval_end

    tickets.sort(key=lambda t: t["purchase_timestamp"])
    return tickets


@app.get(
    "/api/v1/tickets",
    summary="List tickets (CDC incremental)",
    description=(
        "Returns tickets created AFTER the `since` timestamp. "
        "If `since` is omitted, returns historical backfill (last 7 days). "
        "Supports pagination for large result sets."
    ),
)
def get_tickets(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(50, ge=1, le=500, description="Records per page"),
    since: Optional[str] = Query(
        None,
        description="Watermark timestamp (ISO format). Returns tickets AFTER this time.",
        examples=["2026-06-20T10:00:00Z"],
    ),
    authorization: Optional[str] = Header(None),
):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    now = _now_utc()

    if since:
        try:
            watermark = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            try:
                watermark = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid since format: {since}. Use ISO 8601.")
    else:
        watermark = now - timedelta(days=BACKFILL_DAYS)

    all_tickets = _get_all_tickets_since(watermark)
    total = len(all_tickets)

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    page_tickets = all_tickets[start_idx:end_idx]

    return {
        "data": page_tickets,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, (total + per_page - 1) // per_page),
            "watermark_used": watermark.isoformat(),
            "current_server_time": now.isoformat(),
            "has_more": end_idx < total,
        },
    }


@app.get("/api/v1/tickets/stats", summary="Ticket generation statistics")
def get_stats(authorization: Optional[str] = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "total_events": len(EVENTS),
        "categories": CATEGORIES,
        "tickets_per_interval": TICKETS_PER_INTERVAL,
        "interval_seconds": INTERVAL_SECONDS,
        "backfill_days": BACKFILL_DAYS,
        "server_time": _now_utc().isoformat(),
        "start_time": START_TIME.isoformat(),
    }


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok", "service": "eventhub-mock-api", "version": "2.0.0"}
