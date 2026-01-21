# Production Integration Plan: aReg Event Director Analytics

## Context & Constraints

**Current Prototype**: Streamlit + Python + Pandas + OpenAI/Bedrock (COMPLETE)
**Production Environment**:
- Backend: .NET (existing production system)
- Frontend: React components required for easy integration
- Data: SQL Server databases (not CSV files)

---

## Architectural Options Evaluated

| Option | Dev Effort | Ops Complexity | Security | Recommendation |
|--------|-----------|----------------|----------|----------------|
| 1. Full .NET Rewrite | 8-12 weeks | Low | Cannot support NL→code | Not recommended |
| 2. Python Microservice | 5-8 weeks | Medium | Sandboxable | **Recommended** |
| 3. LLM-only Python | 6-10 weeks | Medium | Good isolation | Viable alternative |
| 4. Embedded Python.NET | 3-5 weeks | High | Poor | Not recommended |

---

## Recommended Architecture: Hybrid Python Microservice

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React Frontend                               │
│                    (Recharts or Chart.js)                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      .NET API Gateway                                │
│           (Auth, routing, caching, rate limiting)                   │
└─────────────────────────────────────────────────────────────────────┘
              │                                    │
              ▼                                    ▼
┌──────────────────────────┐        ┌──────────────────────────┐
│   Python Analytics API   │        │    Python LLM Service    │
│       (FastAPI)          │        │       (FastAPI)          │
│                          │        │                          │
│  • EventAnalytics        │        │  • Dashboard insights    │
│  • EcosystemBenchmark    │        │  • SQL generation        │
│  • Read-only DB access   │        │  • Re-engagement msgs    │
└────────────┬─────────────┘        └────────────┬─────────────┘
             │                                    │
             ▼                                    ▼
┌──────────────────────────┐        ┌──────────────────────────┐
│     SQL Server DB        │        │    OpenAI / Bedrock      │
└──────────────────────────┘        └──────────────────────────┘
```

---

## Why This Architecture?

### 1. Reuse Existing Code (90%+)
- `analytics.py` (557 lines, 15+ methods) → Expose as REST API
- `llm_client.py` (295 lines) → Minor changes for SQL generation
- Prompt templates → Copy verbatim

### 2. Security: Replace Code Execution with SQL Generation

**Current Prototype (DANGEROUS for production)**:
```python
exec(llm_generated_pandas_code)  # Arbitrary code execution!
```

**Production (SAFE)**:
```python
# LLM generates parameterized SQL instead:
SELECT participant_id, COUNT(*)
FROM entries
WHERE event_year = @year
GROUP BY participant_id
```

Benefits:
- Parameterized queries prevent SQL injection
- Read-only enforced at database level
- No arbitrary code execution

### 3. Independent Scaling
- Analytics service handles heavy data processing
- LLM service handles AI calls (can cache insights)
- React frontend is static/CDN-hosted

---

## What Gets Reused vs Rewritten

| Component | Reuse | Rewrite | Notes |
|-----------|-------|---------|-------|
| `analytics.py` | 95% | 5% | Add REST endpoints |
| `llm_client.py` | 70% | 30% | SQL generation instead of pandas |
| `data_loader.py` | 20% | 80% | CSV → SQLAlchemy |
| `app.py` (UI) | 0% | 100% | Streamlit → React |
| Prompt templates | 100% | 0% | Copy verbatim |

---

## Implementation Phases

### Phase 1: Python Analytics API (Weeks 1-3)
- Create FastAPI project
- Port `data_loader.py` to SQLAlchemy + SQL Server
- Expose REST endpoints:
  ```
  GET /promoters/{id}/yoy?year1=X&year2=Y
  GET /promoters/{id}/retention
  GET /promoters/{id}/cohorts
  GET /promoters/{id}/churn-list
  GET /promoters/{id}/geography
  GET /promoters/{id}/categories
  GET /ecosystem/benchmark/{promoter_id}
  ```

### Phase 2: Python LLM Service (Weeks 2-4)
- Create separate FastAPI service
- Port `llm_client.py`
- **Critical change**: `translate_natural_query()` → generates SQL instead of pandas
- Endpoints:
  ```
  POST /insights/dashboard     → AI metric summaries
  POST /query/natural-language → Returns SQL + explanation
  POST /messages/reengagement  → Personalized outreach
  ```

### Phase 3: .NET API Gateway (Weeks 3-5)
- HTTP clients for Python services
- Authentication/authorization
- Response caching (Redis)
- Rate limiting on LLM endpoints

### Phase 4: React Components (Weeks 4-7)
- Reusable components:
  - `<MetricCard>` - KPI with change indicator
  - `<CategoryChart>` - Bar chart (Recharts)
  - `<CohortHeatmap>` - Retention matrix
  - `<GeoMap>` - Participant locations
  - `<ChurnList>` - Table with export
  - `<QueryInterface>` - Natural language input
- State management with React Query

### Phase 5: Integration & Testing (Weeks 6-8)

---

## React Component Examples

```jsx
// KPI Card
<MetricCard
  title="Total Participants"
  value={1202}
  change={+19.2}
  changeLabel="vs 2023"
/>

// Category Performance Chart
<ResponsiveContainer>
  <BarChart data={categoryData}>
    <XAxis dataKey="category" angle={-45} />
    <YAxis />
    <Bar dataKey="participants" fill="#FFD100" />
  </BarChart>
</ResponsiveContainer>

// Cohort Retention Heatmap
<HeatmapChart
  data={cohortMatrix}
  colorScale={['#FFFFFF', '#FFD100', '#E6BC00']}
/>
```

---

## Database View Required

Create this view to match the prototype's enriched DataFrame:

```sql
CREATE VIEW vw_EnrichedEntries AS
SELECT
  e.EntryID,
  e.FName,
  e.LName,
  LOWER(e.FName) + '|' + LOWER(e.LName) + '|' +
    CAST(e.DOB AS VARCHAR) AS participant_id,
  YEAR(ev.EventDate) AS event_year,
  DATEDIFF(YEAR, e.DOB, ev.EventDate) AS participant_age,
  e.Fee,
  e.Latitude,
  e.Longitude,
  ev.EventLat,
  ev.EventLon,
  ev.PromoterID,
  c.CategoryName
FROM Entries e
JOIN Categories c ON e.ItemID = c.ItemID
JOIN Events ev ON c.EventID = ev.EventID
```

---

## Security Checklist

- [ ] Python services use read-only database connection
- [ ] SQL generation validates query is SELECT-only
- [ ] Parameterized queries for all user inputs
- [ ] LLM service has no direct DB access
- [ ] Rate limiting on LLM endpoints (cost control)
- [ ] API authentication required
- [ ] Audit logging for natural language queries

---

## Alternative: Full .NET Rewrite

If team strongly prefers single technology stack:

| Pros | Cons |
|------|------|
| Single codebase | 8-12 week rewrite |
| Existing .NET skills | Cannot support NL→code safely |
| Simpler deployment | Would need query builder UI instead |

**If choosing .NET-only**: Replace natural language queries with dropdown-based query builder using predefined query templates.

---

## Team Skills Required

| Role | Skills |
|------|--------|
| Python Dev | FastAPI, SQLAlchemy, pandas |
| .NET Dev | API Gateway, HTTP clients |
| React Dev | Recharts, React Query |
| DevOps | Docker, K8s (optional) |

---

## Key Files to Reference (Current Prototype)

| File | Purpose | Lines |
|------|---------|-------|
| `src/analytics.py` | Core analytics (YoY, retention, cohorts, churn, geography) | 557 |
| `src/llm_client.py` | LLM integration + prompt templates | 295 |
| `src/data_loader.py` | Data loading + participant deduplication | 166 |
| `src/app.py` | UI patterns + chart configurations | 994 |

---

## Key Analytics Methods to Expose as API

From `EventAnalytics` class:
- `get_yoy_metrics(year1, year2)` - Year-over-year comparison
- `get_category_performance(year)` - Category breakdown with YoY growth
- `get_retention_rate(year1, year2)` - Simple retention percentage
- `get_loyalty_cohorts()` - 1-timer / Regular / Super Fan breakdown
- `get_cohort_retention()` - SaaS-style retention matrix
- `get_churn_list(check_year)` - Lapsed participants
- `get_top_participants(n)` - VIP leaderboard
- `get_age_distribution()` - Demographics
- `get_distance_distribution()` - Geographic analysis

From `EcosystemBenchmark` class:
- `get_benchmark_metrics(promoter_id)` - Compare vs ecosystem averages
- `get_participant_overlap(promoter_id)` - Shared participants with other events

---

## Decision Summary

**Recommended**: Hybrid Python microservices (Option 2)
- 5-8 weeks to production
- Reuses 90% of analytics code
- Preserves natural language → SQL feature
- Clean security model

**Trade-off**: Requires Python expertise alongside .NET team
