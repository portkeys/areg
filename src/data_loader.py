"""
Data loading and preprocessing module for Event Director Analytics.

Handles loading CSV files, joining tables, and creating participant deduplication.
"""

import pandas as pd
from pathlib import Path
from functools import lru_cache


DATA_DIR = Path(__file__).parent.parent / "data"


@lru_cache(maxsize=1)
def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load raw CSV files into DataFrames."""
    events = pd.read_csv(DATA_DIR / "aReg_Events.csv", parse_dates=["EventDate", "EventEndDate"])
    categories = pd.read_csv(DATA_DIR / "aReg_Categories.csv", parse_dates=["CategoryDates"])
    entries = pd.read_csv(DATA_DIR / "aReg_Entries.csv")

    return events, categories, entries


def create_participant_id(df: pd.DataFrame) -> pd.Series:
    """
    Create unique participant ID from First + Last + DOB.

    RacerID in the data is unreliable, so we create a composite key.
    """
    return (
        df["FName"].str.lower().str.strip() + "|" +
        df["LName"].str.lower().str.strip() + "|" +
        df["DOB"].astype(str)
    )


def load_enriched_entries() -> pd.DataFrame:
    """
    Load entries with joined event and category data.

    Returns DataFrame with columns:
    - participant_id: Unique identifier (FName|LName|DOB)
    - All entry columns (RacerID, ItemID, DOB, FName, LName, gender, Latitude, Longitude)
    - All category columns (EventID, RaceRecID, Catagory, CategoryDates, EntryFee)
    - All event columns (PromoterID, EventName, EventDate, EventType, etc.)
    - Derived columns (event_year, participant_age)
    """
    events, categories, entries = load_raw_data()

    # Join entries to categories on ItemID = RaceRecID
    df = entries.merge(
        categories,
        left_on="ItemID",
        right_on="RaceRecID",
        how="left"
    )

    # Join to events on EventID
    df = df.merge(
        events,
        on="EventID",
        how="left"
    )

    # Create participant ID
    df["participant_id"] = create_participant_id(df)

    # Derive event year
    df["event_year"] = df["EventDate"].dt.year

    # Calculate participant age at event (handle NaN values)
    age_days = (df["EventDate"] - pd.to_datetime(df["DOB"], errors="coerce")).dt.days
    df["participant_age"] = (age_days / 365.25).round().astype("Int64")

    return df


def get_promoter_ids() -> list[tuple[int, str]]:
    """Get list of unique promoter IDs with a sample event name."""
    events, _, _ = load_raw_data()

    promoters = (
        events.groupby("PromoterID")
        .agg({
            "EventName": "first",
            "EventID": "count"
        })
        .rename(columns={"EventID": "event_count"})
        .reset_index()
    )

    return [(row.PromoterID, row.EventName, row.event_count)
            for row in promoters.itertuples()]


def get_promoter_data(promoter_id: int) -> pd.DataFrame:
    """Get all enriched entries for a specific promoter."""
    df = load_enriched_entries()
    return df[df["PromoterID"] == promoter_id].copy()


def get_promoter_events(promoter_id: int) -> pd.DataFrame:
    """Get all events for a specific promoter."""
    events, _, _ = load_raw_data()
    return events[events["PromoterID"] == promoter_id].copy()


def get_promoter_summary(promoter_id: int) -> dict:
    """Get summary statistics for a promoter's events."""
    df = get_promoter_data(promoter_id)
    events = get_promoter_events(promoter_id)

    if df.empty:
        return {
            "total_events": 0,
            "total_entries": 0,
            "unique_participants": 0,
            "years_active": [],
            "event_types": [],
        }

    return {
        "total_events": len(events),
        "total_entries": len(df),
        "unique_participants": df["participant_id"].nunique(),
        "years_active": sorted(df["event_year"].dropna().unique().astype(int).tolist()),
        "event_types": df["EventType"].dropna().unique().tolist(),
        "date_range": {
            "first_event": df["EventDate"].min(),
            "last_event": df["EventDate"].max(),
        }
    }


def get_data_summary() -> dict:
    """Get overall data summary statistics."""
    events, categories, entries = load_raw_data()
    df = load_enriched_entries()

    return {
        "total_events": len(events),
        "total_categories": len(categories),
        "total_entries": len(entries),
        "unique_participants": df["participant_id"].nunique(),
        "unique_promoters": events["PromoterID"].nunique(),
        "event_types": events["EventType"].dropna().unique().tolist(),
        "states": events["EventState"].dropna().unique().tolist(),
        "date_range": {
            "first_event": events["EventDate"].min(),
            "last_event": events["EventDate"].max(),
        }
    }


def get_promoter_event_center(promoter_id: int) -> tuple[float, float, str, str]:
    """
    Get the representative location for a promoter's events.

    Uses median lat/lon (robust to geocoding outliers). Returns the city/state
    of the event closest to the median point.
    """
    import numpy as np

    events = get_promoter_events(promoter_id)
    geo = events[
        events["EventLat"].notna() & events["EventLon"].notna() &
        (events["EventLat"] != 0) & (events["EventLon"] != 0)
    ]

    if geo.empty:
        return (0.0, 0.0, "Unknown", "Unknown")

    med_lat = geo["EventLat"].median()
    med_lon = geo["EventLon"].median()

    # Find event closest to median for city/state label
    dists = ((geo["EventLat"] - med_lat) ** 2 + (geo["EventLon"] - med_lon) ** 2)
    closest = geo.loc[dists.idxmin()]

    return (
        float(med_lat),
        float(med_lon),
        str(closest.get("EventCity", "Unknown")),
        str(closest.get("EventState", "Unknown")),
    )


if __name__ == "__main__":
    # Quick test
    summary = get_data_summary()
    print("Data Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\nTop 5 Promoters:")
    for pid, name, count in get_promoter_ids()[:5]:
        print(f"  {pid}: {name} ({count} events)")
