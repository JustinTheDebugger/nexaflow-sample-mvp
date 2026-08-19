from datetime import date, timedelta
import pandas as pd

TODAY = date.today()

SAMPLES = [
    {
        "sample_id": "SMP-001",
        "product_name": "Kitpac Pro X-Large",
        "product_code": "0250501-001",
        "category": "Furniture",
        "location": "Warehouse B · Rack 01 · Bin 04",
        "holder": "Warehouse",
        "holder_team": "Operations",
        "condition": "Excellent",
        "usage_count": 18,
        "last_inspection": TODAY - timedelta(days=12),
        "photo": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
        "next_available": TODAY,
        "next_booking": TODAY + timedelta(days=3),
        "next_booking_team": "Marketing",
        "status": "Available Today",
        "notes": "Latest released sample with updated packaging.",
    },
    {
        "sample_id": "SMP-002",
        "product_name": "Aerospeed 4 Tent",
        "product_code": "0247304-001",
        "category": "Tent",
        "location": "With Justin",
        "holder": "Justin",
        "holder_team": "Marketing",
        "condition": "Good",
        "usage_count": 42,
        "last_inspection": TODAY - timedelta(days=31),
        "photo": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?auto=format&fit=crop&w=1200&q=80",
        "next_available": TODAY + timedelta(days=2),
        "next_booking": TODAY + timedelta(days=6),
        "next_booking_team": "Sales",
        "status": "Checked Out",
        "notes": "Currently used for product photography.",
    },
    {
        "sample_id": "SMP-003",
        "product_name": "Monstamat Twin",
        "product_code": "0262402-001",
        "category": "Sleeping",
        "location": "Trade Show · Auckland",
        "holder": "Events Team",
        "holder_team": "Trade Show",
        "condition": "Fair",
        "usage_count": 27,
        "last_inspection": TODAY - timedelta(days=47),
        "photo": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
        "next_available": TODAY + timedelta(days=5),
        "next_booking": TODAY + timedelta(days=12),
        "next_booking_team": "Photography",
        "status": "In Use",
        "notes": "Inspect seam before next checkout.",
    },
    {
        "sample_id": "SMP-004",
        "product_name": "Roadiebase Air Shelter",
        "product_code": "0269101-001",
        "category": "Shelter",
        "location": "Warehouse A · Repair Bench",
        "holder": "Warehouse",
        "holder_team": "Operations",
        "condition": "Damaged",
        "usage_count": 11,
        "last_inspection": TODAY - timedelta(days=2),
        "photo": "https://images.unsplash.com/photo-1475483768296-6163e08872a1?auto=format&fit=crop&w=1200&q=80",
        "next_available": TODAY + timedelta(days=14),
        "next_booking": None,
        "next_booking_team": None,
        "status": "Damaged",
        "notes": "Valve damage reported after customer demonstration.",
    },
    {
        "sample_id": "SMP-005",
        "product_name": "Aero TXL Pro",
        "product_code": "0267408-001",
        "category": "Tent",
        "location": "Sales · Christchurch",
        "holder": "Regional Sales",
        "holder_team": "Sales",
        "condition": "Good",
        "usage_count": 35,
        "last_inspection": TODAY - timedelta(days=20),
        "photo": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "next_available": TODAY - timedelta(days=1),
        "next_booking": TODAY + timedelta(days=8),
        "next_booking_team": "Trade Show",
        "status": "Overdue",
        "notes": "Return was due yesterday.",
    },
]

BOOKINGS = [
    {"sample_id": "SMP-001", "start": TODAY + timedelta(days=3), "end": TODAY + timedelta(days=5), "team": "Marketing", "purpose": "Campaign photography"},
    {"sample_id": "SMP-001", "start": TODAY + timedelta(days=9), "end": TODAY + timedelta(days=11), "team": "Sales", "purpose": "Customer demonstration"},
    {"sample_id": "SMP-002", "start": TODAY - timedelta(days=2), "end": TODAY + timedelta(days=1), "team": "Marketing", "purpose": "Product photography"},
    {"sample_id": "SMP-002", "start": TODAY + timedelta(days=6), "end": TODAY + timedelta(days=8), "team": "Sales", "purpose": "Dealer presentation"},
    {"sample_id": "SMP-003", "start": TODAY - timedelta(days=1), "end": TODAY + timedelta(days=4), "team": "Trade Show", "purpose": "Auckland expo"},
    {"sample_id": "SMP-003", "start": TODAY + timedelta(days=12), "end": TODAY + timedelta(days=13), "team": "Photography", "purpose": "Studio shoot"},
    {"sample_id": "SMP-005", "start": TODAY - timedelta(days=5), "end": TODAY - timedelta(days=1), "team": "Sales", "purpose": "Regional customer visits"},
    {"sample_id": "SMP-005", "start": TODAY + timedelta(days=8), "end": TODAY + timedelta(days=12), "team": "Trade Show", "purpose": "South Island expo"},
]

TIMELINE = [
    {"sample_id": "SMP-001", "date": TODAY - timedelta(days=190), "event": "Received from Factory", "detail": "Initial production sample received."},
    {"sample_id": "SMP-001", "date": TODAY - timedelta(days=170), "event": "Quality Inspection", "detail": "Approved for internal use."},
    {"sample_id": "SMP-001", "date": TODAY - timedelta(days=80), "event": "Marketing Shoot", "detail": "Used for seasonal campaign."},
    {"sample_id": "SMP-001", "date": TODAY - timedelta(days=77), "event": "Returned", "detail": "Returned to Warehouse B."},
    {"sample_id": "SMP-002", "date": TODAY - timedelta(days=250), "event": "Received from Factory", "detail": "Pre-production sample received."},
    {"sample_id": "SMP-002", "date": TODAY - timedelta(days=95), "event": "Sales Demo", "detail": "Used for dealer presentation."},
    {"sample_id": "SMP-002", "date": TODAY - timedelta(days=2), "event": "Checked Out", "detail": "Checked out by Justin for photography."},
    {"sample_id": "SMP-003", "date": TODAY - timedelta(days=130), "event": "Received from Factory", "detail": "Launch sample received."},
    {"sample_id": "SMP-003", "date": TODAY - timedelta(days=1), "event": "Trade Show", "detail": "Moved to Auckland exhibition venue."},
    {"sample_id": "SMP-004", "date": TODAY - timedelta(days=90), "event": "Received from Factory", "detail": "Customer demonstration sample."},
    {"sample_id": "SMP-004", "date": TODAY - timedelta(days=3), "event": "Damage Reported", "detail": "Valve damage identified after demonstration."},
    {"sample_id": "SMP-004", "date": TODAY - timedelta(days=2), "event": "Moved to Repair", "detail": "Moved to Warehouse A repair bench."},
    {"sample_id": "SMP-005", "date": TODAY - timedelta(days=205), "event": "Received from Factory", "detail": "Production sample received."},
    {"sample_id": "SMP-005", "date": TODAY - timedelta(days=5), "event": "Checked Out", "detail": "Regional Sales checkout."},
    {"sample_id": "SMP-005", "date": TODAY - timedelta(days=1), "event": "Return Overdue", "detail": "Automated overdue flag created."},
]

ACTIVITY = [
    {"time": "09:42", "action": "Marketing checked out Aerospeed 4 Tent", "type": "Checkout"},
    {"time": "09:18", "action": "Roadiebase Air Shelter moved to repair", "type": "Movement"},
    {"time": "Yesterday", "action": "Kitpac Pro X-Large reserved by Marketing", "type": "Reservation"},
    {"time": "Yesterday", "action": "Aero TXL Pro return became overdue", "type": "Overdue"},
    {"time": "2 days ago", "action": "Monstamat Twin moved to Auckland Trade Show", "type": "Movement"},
]

def samples_df() -> pd.DataFrame:
    return pd.DataFrame(SAMPLES)

def bookings_df() -> pd.DataFrame:
    return pd.DataFrame(BOOKINGS)

def timeline_df() -> pd.DataFrame:
    return pd.DataFrame(TIMELINE)
