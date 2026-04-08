"""
Analytics engine for Event Director Analytics.

Contains core metric calculations for:
- Year-over-Year comparisons
- Category performance
- Retention and churn analysis
- Loyalty cohorts
- Geographic analysis
- Ecosystem benchmarking
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime


def _haversine_miles(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two lat/lon points using haversine formula."""
    R = 3959  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


class EventAnalytics:
    """Analytics engine for a specific promoter's events."""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with enriched entries DataFrame for a promoter.

        Args:
            df: DataFrame from get_promoter_data() with all entry/event info
        """
        self.df = df
        self._participants = None

    @property
    def participants(self) -> pd.DataFrame:
        """Get unique participants with aggregated stats."""
        if self._participants is None:
            self._participants = self._build_participant_summary()
        return self._participants

    def _build_participant_summary(self) -> pd.DataFrame:
        """Build participant-level summary with attendance history."""
        if self.df.empty:
            return pd.DataFrame()

        return self.df.groupby("participant_id").agg({
            "FName": "first",
            "LName": "first",
            "DOB": "first",
            "gender": "first",
            "Latitude": "first",
            "Longitude": "first",
            "EventID": "nunique",
            "event_year": lambda x: sorted(x.dropna().unique().astype(int).tolist()),
            "EventDate": ["min", "max", "count"],
        }).reset_index()

    def get_yoy_metrics(self, year1: int, year2: int) -> dict:
        """
        Calculate year-over-year comparison metrics.

        Returns dict with:
        - total_participants: count for each year
        - returning: participants who were in year1 and came back in year2
        - new: participants in year2 who weren't in year1
        - churned: participants in year1 who didn't come to year2
        - revenue: sum of entry fees
        - change_pct: percentage changes
        """
        df1 = self.df[self.df["event_year"] == year1]
        df2 = self.df[self.df["event_year"] == year2]

        participants1 = set(df1["participant_id"].unique())
        participants2 = set(df2["participant_id"].unique())

        returning = participants1 & participants2
        new = participants2 - participants1
        churned = participants1 - participants2

        total1 = len(participants1)
        total2 = len(participants2)

        revenue1 = df1["EntryFee"].sum()
        revenue2 = df2["EntryFee"].sum()

        def pct_change(old, new):
            if old == 0:
                return 0 if new == 0 else 100
            return round((new - old) / old * 100, 1)

        return {
            "year1": year1,
            "year2": year2,
            "metrics": {
                "total_participants": {
                    year1: total1,
                    year2: total2,
                    "change_pct": pct_change(total1, total2),
                },
                "returning": {
                    "count": len(returning),
                    "pct_of_year1": round(len(returning) / total1 * 100, 1) if total1 > 0 else 0,
                },
                "new": {
                    "count": len(new),
                    "pct_of_year2": round(len(new) / total2 * 100, 1) if total2 > 0 else 0,
                },
                "churned": {
                    "count": len(churned),
                    "pct_of_year1": round(len(churned) / total1 * 100, 1) if total1 > 0 else 0,
                },
                "revenue": {
                    year1: revenue1,
                    year2: revenue2,
                    "change_pct": pct_change(revenue1, revenue2),
                },
            },
        }

    def get_category_performance(self, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get category performance metrics.

        Returns DataFrame with:
        - Category name
        - Participant count
        - Revenue
        - Avg entry fee
        - YoY growth (if prior year exists)
        """
        df = self.df if year is None else self.df[self.df["event_year"] == year]

        if df.empty:
            return pd.DataFrame()

        result = df.groupby("Catagory").agg({
            "participant_id": "nunique",
            "EntryFee": ["sum", "mean"],
            "EventID": "nunique",
        }).reset_index()

        result.columns = ["category", "participants", "total_revenue", "avg_fee", "event_count"]
        result = result.sort_values("participants", ascending=False)

        # Calculate YoY growth if we have a specific year
        if year is not None and year > self.df["event_year"].min():
            prior_year = year - 1
            prior_df = self.df[self.df["event_year"] == prior_year]
            prior_counts = prior_df.groupby("Catagory")["participant_id"].nunique()

            def calc_growth(row):
                prior = prior_counts.get(row["category"], 0)
                if prior == 0:
                    return None
                return round((row["participants"] - prior) / prior * 100, 1)

            result["yoy_growth"] = result.apply(calc_growth, axis=1)

        return result

    def get_retention_rate(self, year: int) -> float:
        """Calculate retention rate: % of prior year participants who returned."""
        prior_year = year - 1
        df_prior = self.df[self.df["event_year"] == prior_year]
        df_current = self.df[self.df["event_year"] == year]

        if df_prior.empty:
            return 0.0

        prior_participants = set(df_prior["participant_id"].unique())
        current_participants = set(df_current["participant_id"].unique())

        returning = prior_participants & current_participants
        return round(len(returning) / len(prior_participants) * 100, 1)

    def get_loyalty_cohorts(self) -> dict:
        """
        Segment participants by loyalty (attendance frequency).

        Returns:
        - one_timers: attended exactly once
        - regulars: attended 2-3 times
        - super_fans: attended 4+ times
        """
        if self.df.empty:
            return {"one_timers": 0, "regulars": 0, "super_fans": 0}

        attendance = self.df.groupby("participant_id")["EventID"].nunique()

        return {
            "one_timers": int((attendance == 1).sum()),
            "regulars": int(((attendance >= 2) & (attendance <= 3)).sum()),
            "super_fans": int((attendance >= 4).sum()),
            "total": len(attendance),
        }

    def get_top_participants(self, n: int = 10) -> pd.DataFrame:
        """Get most frequent participants (VIPs)."""
        if self.df.empty:
            return pd.DataFrame()

        top = self.df.groupby("participant_id").agg({
            "FName": "first",
            "LName": "first",
            "EventID": "nunique",
            "event_year": lambda x: sorted(x.dropna().unique().astype(int).tolist()),
            "EntryFee": "sum",
        }).reset_index()

        top.columns = ["participant_id", "first_name", "last_name", "events_attended",
                       "years_attended", "total_spent"]
        top = top.sort_values("events_attended", ascending=False).head(n)

        return top

    def get_churn_list(self, current_year: int, min_attendance: int = 2) -> pd.DataFrame:
        """
        Get list of churned participants for re-engagement.

        Args:
            current_year: Year to check for absence
            min_attendance: Minimum prior attendance to include

        Returns:
            DataFrame of participants who attended min_attendance+ times but not in current_year
        """
        if self.df.empty:
            return pd.DataFrame()

        # Get participants not in current year
        current_participants = set(
            self.df[self.df["event_year"] == current_year]["participant_id"].unique()
        )

        # Filter to those with prior attendance
        prior_df = self.df[self.df["event_year"] < current_year]
        attendance = prior_df.groupby("participant_id").agg({
            "FName": "first",
            "LName": "first",
            "EventID": "nunique",
            "event_year": lambda x: sorted(x.dropna().unique().astype(int).tolist()),
            "Catagory": "last",  # Most recent category
        }).reset_index()

        attendance.columns = ["participant_id", "first_name", "last_name",
                             "times_attended", "years_attended", "last_category"]

        # Filter: attended enough and not in current year
        churned = attendance[
            (attendance["times_attended"] >= min_attendance) &
            (~attendance["participant_id"].isin(current_participants))
        ].sort_values("times_attended", ascending=False)

        return churned

    def get_cohort_retention(self) -> pd.DataFrame:
        """
        Build SaaS-style cohort retention table.

        Returns DataFrame where:
        - Rows are cohort start years
        - Columns are years since start (0, 1, 2, ...)
        - Values are retention percentages
        """
        if self.df.empty:
            return pd.DataFrame()

        years = sorted(self.df["event_year"].dropna().unique().astype(int))
        if len(years) < 2:
            return pd.DataFrame()

        # Find first year for each participant
        first_year = self.df.groupby("participant_id")["event_year"].min().reset_index()
        first_year.columns = ["participant_id", "cohort_year"]

        # Merge cohort year back
        df_with_cohort = self.df.merge(first_year, on="participant_id")

        cohort_data = []
        for cohort_year in years[:-1]:  # Exclude last year (no retention to measure)
            cohort_participants = set(
                df_with_cohort[df_with_cohort["cohort_year"] == cohort_year]["participant_id"]
            )
            if len(cohort_participants) == 0:
                continue

            row = {"cohort_year": int(cohort_year), "cohort_size": len(cohort_participants)}

            for offset, year in enumerate(range(cohort_year, max(years) + 1)):
                active_in_year = set(
                    self.df[self.df["event_year"] == year]["participant_id"]
                )
                retained = cohort_participants & active_in_year
                row[f"year_{offset}"] = round(len(retained) / len(cohort_participants) * 100, 1)

            cohort_data.append(row)

        return pd.DataFrame(cohort_data)

    def get_geographic_distribution(self) -> pd.DataFrame:
        """Get participant geographic distribution with counts."""
        if self.df.empty:
            return pd.DataFrame()

        # Get unique participants with lat/lon
        geo = self.df.groupby("participant_id").agg({
            "Latitude": "first",
            "Longitude": "first",
        }).reset_index()

        # Remove invalid coordinates
        geo = geo[
            (geo["Latitude"].notna()) &
            (geo["Longitude"].notna()) &
            (geo["Latitude"] != 0) &
            (geo["Longitude"] != 0)
        ]

        return geo

    def get_distance_distribution(self, event_lat: float, event_lon: float) -> dict:
        """
        Calculate participant travel distances to event location.

        Returns:
        - counts by distance bucket
        - average distance
        - max distance
        """
        geo = self.get_geographic_distribution()
        if geo.empty:
            return {}

        distances = geo.apply(
            lambda row: _haversine_miles(row["Latitude"], row["Longitude"], event_lat, event_lon),
            axis=1
        )

        buckets = {
            "under_25": int((distances < 25).sum()),
            "25_to_50": int(((distances >= 25) & (distances < 50)).sum()),
            "50_to_100": int(((distances >= 50) & (distances < 100)).sum()),
            "over_100": int((distances >= 100).sum()),
        }

        return {
            "buckets": buckets,
            "avg_miles": round(distances.mean(), 1),
            "max_miles": round(distances.max(), 1),
            "total_with_location": len(geo),
        }

    def get_registration_timing(self, year: Optional[int] = None) -> pd.DataFrame:
        """
        Analyze registration timing patterns.

        Note: This would need registration date from entries, which we may not have.
        For now, returns event date distribution as proxy.
        """
        df = self.df if year is None else self.df[self.df["event_year"] == year]

        if df.empty:
            return pd.DataFrame()

        # Group by event date (as proxy for registration patterns)
        timing = df.groupby(df["EventDate"].dt.date).agg({
            "participant_id": "nunique"
        }).reset_index()
        timing.columns = ["date", "participants"]

        return timing

    def get_age_distribution(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get participant age distribution."""
        df = self.df if year is None else self.df[self.df["event_year"] == year]

        if df.empty:
            return pd.DataFrame()

        # Get unique participants with age
        ages = df.groupby("participant_id")["participant_age"].first().dropna()

        # Create age buckets
        bins = [0, 18, 25, 35, 45, 55, 65, 100]
        labels = ["Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

        age_groups = pd.cut(ages, bins=bins, labels=labels)
        distribution = age_groups.value_counts().sort_index()

        return pd.DataFrame({
            "age_group": distribution.index.tolist(),
            "count": distribution.values,
        })

    def get_gender_distribution(self, year: Optional[int] = None) -> dict:
        """Get participant gender distribution."""
        df = self.df if year is None else self.df[self.df["event_year"] == year]

        if df.empty:
            return {}

        gender = df.groupby("participant_id")["gender"].first()
        counts = gender.value_counts()

        return {
            "M": int(counts.get("M", 0)),
            "F": int(counts.get("F", 0)),
            "other": int(counts.get("", 0) + counts.drop(["M", "F"], errors="ignore").sum()),
        }

    def get_experience_distribution(self, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get participant experience level distribution.

        Counts how many events each participant has done with this director
        (up to and including the given year), scoped to that year's participants.

        Returns DataFrame with columns: experience_level, count
        """
        if self.df.empty:
            return pd.DataFrame()

        if year is not None:
            # Only participants who appeared in this year
            year_participants = set(
                self.df[self.df["event_year"] == year]["participant_id"].unique()
            )
            # Count events up to and including this year
            df_up_to = self.df[self.df["event_year"] <= year]
            attendance = df_up_to[
                df_up_to["participant_id"].isin(year_participants)
            ].groupby("participant_id")["EventID"].nunique()
        else:
            attendance = self.df.groupby("participant_id")["EventID"].nunique()

        buckets = pd.cut(
            attendance,
            bins=[0, 1, 3, 6, float("inf")],
            labels=["First-timer (1)", "Developing (2-3)", "Experienced (4-6)", "Veteran (7+)"],
        )
        distribution = buckets.value_counts().sort_index()

        return pd.DataFrame({
            "experience_level": distribution.index.tolist(),
            "count": distribution.values,
        })

    def get_retention_segments(self, year: int) -> dict:
        """
        Classify participants in a given year as returning, first-time, or lapsed-reactivated.

        Returns dict with counts, percentages, and a tagged participants DataFrame.
        """
        if self.df.empty:
            return {"returning": 0, "first_time": 0, "lapsed_reactivated": 0, "total": 0}

        current = set(self.df[self.df["event_year"] == year]["participant_id"].unique())
        prior_year = set(self.df[self.df["event_year"] == year - 1]["participant_id"].unique())
        all_prior = set(self.df[self.df["event_year"] < year]["participant_id"].unique())

        returning = current & prior_year
        first_time = current - all_prior
        lapsed_reactivated = (current - prior_year) & all_prior

        total = len(current)
        safe_pct = lambda n: round(n / total * 100, 1) if total > 0 else 0

        # Build tagged DataFrame
        records = []
        for pid in current:
            if pid in returning:
                segment = "Returning"
            elif pid in first_time:
                segment = "First-time"
            else:
                segment = "Lapsed Reactivated"
            records.append({"participant_id": pid, "segment": segment})

        return {
            "returning": len(returning),
            "returning_pct": safe_pct(len(returning)),
            "first_time": len(first_time),
            "first_time_pct": safe_pct(len(first_time)),
            "lapsed_reactivated": len(lapsed_reactivated),
            "lapsed_reactivated_pct": safe_pct(len(lapsed_reactivated)),
            "total": total,
            "participants": pd.DataFrame(records) if records else pd.DataFrame(),
        }

    def get_retention_trend(self) -> pd.DataFrame:
        """Get retention segments for every year (skipping the first)."""
        if self.df.empty:
            return pd.DataFrame()

        years = sorted(self.df["event_year"].dropna().unique().astype(int))
        if len(years) < 2:
            return pd.DataFrame()

        rows = []
        for year in years[1:]:
            seg = self.get_retention_segments(year)
            rows.append({
                "year": year,
                "returning": seg["returning"],
                "first_time": seg["first_time"],
                "lapsed_reactivated": seg["lapsed_reactivated"],
                "total": seg["total"],
                "returning_pct": seg["returning_pct"],
                "first_time_pct": seg["first_time_pct"],
                "lapsed_reactivated_pct": seg["lapsed_reactivated_pct"],
            })

        return pd.DataFrame(rows)

    def get_demographic_trend(self) -> dict:
        """
        Track how age distribution and gender split change year over year.

        Returns dict with age_by_year, gender_by_year, and median_age_by_year DataFrames.
        """
        if self.df.empty:
            return {"age_by_year": pd.DataFrame(), "gender_by_year": pd.DataFrame(),
                    "median_age_by_year": pd.DataFrame()}

        years = sorted(self.df["event_year"].dropna().unique().astype(int))

        age_rows = []
        gender_rows = []
        median_rows = []

        for year in years:
            year_df = self.df[self.df["event_year"] == year]

            # Age distribution
            age_dist = self.get_age_distribution(year)
            total = age_dist["count"].sum() if not age_dist.empty else 0
            for _, row in age_dist.iterrows():
                age_rows.append({
                    "year": year,
                    "age_group": row["age_group"],
                    "count": row["count"],
                    "pct": round(row["count"] / total * 100, 1) if total > 0 else 0,
                })

            # Median age
            ages = year_df.groupby("participant_id")["participant_age"].first().dropna()
            if len(ages) > 0:
                median_rows.append({"year": year, "median_age": float(ages.median())})

            # Gender distribution
            gender = self.get_gender_distribution(year)
            g_total = sum(gender.values()) if gender else 0
            for g, count in gender.items():
                gender_rows.append({
                    "year": year,
                    "gender": g,
                    "count": count,
                    "pct": round(count / g_total * 100, 1) if g_total > 0 else 0,
                })

        return {
            "age_by_year": pd.DataFrame(age_rows),
            "gender_by_year": pd.DataFrame(gender_rows),
            "median_age_by_year": pd.DataFrame(median_rows),
        }

    def get_filtered_segment(
        self,
        age_range: Optional[tuple[int, int]] = None,
        genders: Optional[list[str]] = None,
        event_types: Optional[list[str]] = None,
        max_distance_miles: Optional[float] = None,
        event_lat: Optional[float] = None,
        event_lon: Optional[float] = None,
        min_attendance: Optional[int] = None,
        max_attendance: Optional[int] = None,
        years: Optional[list[int]] = None,
        categories: Optional[list[str]] = None,
    ) -> dict:
        """
        Flexible segment builder: filter participants by multiple criteria.

        Returns dict with participants DataFrame, count, demographics summary,
        and pct_of_total.
        """
        if self.df.empty:
            return {"participants": pd.DataFrame(), "count": 0, "demographics": {}, "pct_of_total": 0}

        df = self.df
        if years:
            df = df[df["event_year"].isin(years)]

        total_unique = df["participant_id"].nunique()

        # Build per-participant profile (sort by year so "last" = most recent)
        df = df.sort_values("event_year")
        participants = df.groupby("participant_id").agg({
            "FName": "first",
            "LName": "first",
            "participant_age": "last",
            "gender": "first",
            "Latitude": "first",
            "Longitude": "first",
            "EventID": "nunique",
            "EventType": lambda x: list(x.dropna().unique()),
            "Catagory": lambda x: list(x.dropna().unique()),
        }).reset_index()
        participants.columns = [
            "participant_id", "first_name", "last_name", "age", "gender",
            "latitude", "longitude", "events_attended", "event_types", "categories",
        ]

        # Apply filters
        mask = pd.Series(True, index=participants.index)

        if age_range is not None:
            mask &= (participants["age"] >= age_range[0]) & (participants["age"] <= age_range[1])

        if genders:
            mask &= participants["gender"].isin(genders)

        if event_types:
            mask &= participants["event_types"].apply(
                lambda types: bool(set(types) & set(event_types))
            )

        if categories:
            mask &= participants["categories"].apply(
                lambda cats: bool(set(cats) & set(categories))
            )

        if min_attendance is not None:
            mask &= participants["events_attended"] >= min_attendance

        if max_attendance is not None:
            mask &= participants["events_attended"] <= max_attendance

        if max_distance_miles is not None and event_lat is not None and event_lon is not None:
            valid_coords = (
                participants["latitude"].notna() &
                participants["longitude"].notna() &
                (participants["latitude"] != 0) &
                (participants["longitude"] != 0)
            )
            distances = participants.apply(
                lambda row: _haversine_miles(row["latitude"], row["longitude"], event_lat, event_lon)
                if valid_coords[row.name] else float("inf"),
                axis=1,
            )
            mask &= distances <= max_distance_miles

        filtered = participants[mask].copy()
        count = len(filtered)

        # Demographics summary
        demographics = {}
        if count > 0:
            valid_ages = filtered["age"].dropna()
            demographics["median_age"] = float(valid_ages.median()) if len(valid_ages) > 0 else None
            demographics["gender_split"] = filtered["gender"].value_counts().to_dict()
            demographics["avg_attendance"] = round(filtered["events_attended"].mean(), 1)

            valid_geo = filtered[
                filtered["latitude"].notna() & filtered["longitude"].notna() &
                (filtered["latitude"] != 0) & (filtered["longitude"] != 0)
            ]
            if len(valid_geo) > 0 and event_lat is not None and event_lon is not None:
                dists = valid_geo.apply(
                    lambda row: _haversine_miles(row["latitude"], row["longitude"], event_lat, event_lon),
                    axis=1,
                )
                demographics["avg_distance"] = round(dists.mean(), 1)

        # Drop list columns for display
        display_df = filtered.drop(columns=["event_types", "categories"])

        return {
            "participants": display_df.sort_values("events_attended", ascending=False),
            "count": count,
            "demographics": demographics,
            "pct_of_total": round(count / total_unique * 100, 1) if total_unique > 0 else 0,
        }

    def get_audience_profile(
        self,
        event_lat: Optional[float] = None,
        event_lon: Optional[float] = None,
        year: Optional[int] = None,
    ) -> dict:
        """
        Comprehensive audience profile for sponsor pitch generation.

        Aggregates demographics, loyalty, retention, and geography into
        a single data package.
        """
        if self.df.empty:
            return {}

        years = sorted(self.df["event_year"].dropna().unique().astype(int))
        target_year = year or max(years)

        profile = {
            "total_unique_participants": int(self.df["participant_id"].nunique()),
            "total_entries": len(self.df),
            "years_of_data": len(years),
            "year_range": f"{min(years)}-{max(years)}",
        }

        # Age
        age_dist = self.get_age_distribution(target_year)
        profile["age_distribution"] = age_dist.to_dict("records") if not age_dist.empty else []
        ages = self.df[self.df["event_year"] == target_year].groupby("participant_id")["participant_age"].first().dropna()
        profile["median_age"] = float(ages.median()) if len(ages) > 0 else None

        # Gender
        profile["gender_split"] = self.get_gender_distribution(target_year)

        # Loyalty
        profile["loyalty_cohorts"] = self.get_loyalty_cohorts()

        # Experience
        exp = self.get_experience_distribution(target_year)
        profile["experience_distribution"] = exp.to_dict("records") if not exp.empty else []

        # Retention
        if target_year > min(years):
            profile["retention_rate"] = self.get_retention_rate(target_year)
        else:
            profile["retention_rate"] = None

        # YoY growth
        if len(years) >= 2:
            y1, y2 = years[-2], years[-1]
            p1 = self.df[self.df["event_year"] == y1]["participant_id"].nunique()
            p2 = self.df[self.df["event_year"] == y2]["participant_id"].nunique()
            profile["yoy_growth_pct"] = round((p2 - p1) / p1 * 100, 1) if p1 > 0 else 0
        else:
            profile["yoy_growth_pct"] = None

        # Geography
        if event_lat is not None and event_lon is not None:
            profile["geographic"] = self.get_distance_distribution(event_lat, event_lon)

        # Top categories
        cat_counts = self.df[self.df["event_year"] == target_year].groupby("Catagory")["participant_id"].nunique()
        profile["top_categories"] = cat_counts.sort_values(ascending=False).head(10).to_dict()

        # Event types
        profile["event_types"] = self.df["EventType"].dropna().unique().tolist()

        # Avg entry fee
        profile["avg_entry_fee"] = round(self.df["EntryFee"].mean(), 2)

        # Event location (for context in the pitch)
        profile["event_states"] = self.df["EventState"].dropna().unique().tolist()

        return profile


class EcosystemBenchmark:
    """Benchmarking against the broader event ecosystem."""

    def __init__(self, all_entries_df: pd.DataFrame):
        """
        Initialize with full enriched entries DataFrame (all promoters).
        """
        self.df = all_entries_df

    def get_benchmark_metrics(
        self,
        promoter_id: int,
        event_type: Optional[str] = None,
        state: Optional[str] = None,
    ) -> dict:
        """
        Compare a promoter's metrics against ecosystem averages.

        Args:
            promoter_id: The promoter to benchmark
            event_type: Filter comparison to same event type
            state: Filter comparison to same state

        Returns dict with your_event and comparison metrics.
        """
        # Get promoter's data
        promoter_df = self.df[self.df["PromoterID"] == promoter_id]
        promoter_analytics = EventAnalytics(promoter_df)

        # Build comparison set
        comparison_df = self.df[self.df["PromoterID"] != promoter_id]
        if event_type:
            comparison_df = comparison_df[comparison_df["EventType"] == event_type]
        if state:
            comparison_df = comparison_df[comparison_df["EventState"] == state]

        # Calculate metrics for comparison
        def calc_avg_fee(df):
            return df["EntryFee"].mean() if not df.empty else 0

        def calc_retention(df, year):
            analytics = EventAnalytics(df)
            return analytics.get_retention_rate(year)

        def calc_yoy_growth(df, year):
            if df.empty:
                return 0
            prior = df[df["event_year"] == year - 1]["participant_id"].nunique()
            current = df[df["event_year"] == year]["participant_id"].nunique()
            if prior == 0:
                return 0
            return round((current - prior) / prior * 100, 1)

        # Get most recent year with data
        current_year = int(promoter_df["event_year"].max())

        # Calculate per-promoter metrics for comparison set
        comparison_by_promoter = comparison_df.groupby("PromoterID")

        promoter_avg_fee = calc_avg_fee(promoter_df)
        promoter_retention = calc_retention(promoter_df, current_year)
        promoter_growth = calc_yoy_growth(promoter_df, current_year)

        # Comparison averages
        comp_fees = [calc_avg_fee(group) for _, group in comparison_by_promoter]
        comp_retentions = [calc_retention(group, current_year) for _, group in comparison_by_promoter]
        comp_growths = [calc_yoy_growth(group, current_year) for _, group in comparison_by_promoter]

        return {
            "your_event": {
                "avg_entry_fee": round(promoter_avg_fee, 2),
                "retention_rate": promoter_retention,
                "yoy_growth": promoter_growth,
                "total_categories": promoter_df["Catagory"].nunique(),
            },
            "comparison": {
                "avg_entry_fee": round(np.mean(comp_fees), 2) if comp_fees else 0,
                "retention_rate": round(np.mean(comp_retentions), 1) if comp_retentions else 0,
                "yoy_growth": round(np.mean(comp_growths), 1) if comp_growths else 0,
                "avg_categories": round(np.mean([g["Catagory"].nunique() for _, g in comparison_by_promoter]), 1) if len(list(comparison_by_promoter)) > 0 else 0,
                "num_events_compared": comparison_df["PromoterID"].nunique(),
            },
            "filters": {
                "event_type": event_type,
                "state": state,
            }
        }

    def get_participant_overlap(self, promoter_id: int) -> pd.DataFrame:
        """
        Find other events that share participants with this promoter.

        Answers: "Which other events do my participants also attend?"
        """
        # Get this promoter's participants
        promoter_participants = set(
            self.df[self.df["PromoterID"] == promoter_id]["participant_id"].unique()
        )

        # Find overlaps with other promoters
        other_df = self.df[self.df["PromoterID"] != promoter_id]

        overlap_data = []
        for other_promoter, group in other_df.groupby("PromoterID"):
            other_participants = set(group["participant_id"].unique())
            shared = promoter_participants & other_participants

            if len(shared) > 0:
                overlap_data.append({
                    "promoter_id": other_promoter,
                    "event_name": group["EventName"].iloc[0],
                    "shared_participants": len(shared),
                    "pct_of_your_base": round(len(shared) / len(promoter_participants) * 100, 1),
                })

        return pd.DataFrame(overlap_data).sort_values("shared_participants", ascending=False)


if __name__ == "__main__":
    # Quick test
    from data_loader import load_enriched_entries, get_promoter_data

    # Test with a promoter
    df = get_promoter_data(7756)  # Clayton-Tokeneke Classic
    analytics = EventAnalytics(df)

    print("=== YoY Metrics (2023 vs 2024) ===")
    yoy = analytics.get_yoy_metrics(2023, 2024)
    print(yoy)

    print("\n=== Loyalty Cohorts ===")
    print(analytics.get_loyalty_cohorts())

    print("\n=== Top 5 Participants ===")
    print(analytics.get_top_participants(5))

    print("\n=== Category Performance 2024 ===")
    print(analytics.get_category_performance(2024))
