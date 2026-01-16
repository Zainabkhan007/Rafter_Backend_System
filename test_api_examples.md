# API Testing Examples for Professional PDF

## Important Update

The API endpoint `POST /admin_details/dashboard/school/13/generate-report/` now **automatically uses the new professional PDF** in these scenarios:

1. **Default (No parameters)** - Uses current week
2. **date_range: "this_week"** - Uses current week
3. **date_range: "last_week"** - Uses previous week
4. **Explicit week_number + year** - Uses specified week
5. **Custom date range (≤60 days)** - **NEW!** Uses professional PDF with week from end date
6. **Custom date range (>60 days)** - Falls back to old flexible PDF for multi-week analysis

## Test Cases

### 1. Default - Current Week (NEW BEHAVIOR)
When called with NO parameters or empty body, it now generates a professional PDF for the current week:

```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Result:** Professional PDF for current week (Week 3, 2026)

---

### 2. This Week (Explicit)
```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": "this_week"
  }'
```

**Result:** Professional PDF for current week

---

### 3. Last Week
```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": "last_week"
  }'
```

**Result:** Professional PDF for previous week

---

### 4. Specific Week (Explicit)
```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{
    "week_number": 3,
    "year": 2026
  }'
```

**Result:** Professional PDF for Week 3, 2026

---

### 5. Custom Date Range - Short (NEW - Professional PDF)
For custom date ranges ≤60 days, the professional PDF is automatically used:

```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-12-17",
    "end_date": "2026-01-14",
    "include_detailed_lists": true
  }'
```

**Result:** Professional PDF for Week 3, 2026 (using end date to determine week)

---

### 6. Custom Date Range - Long (Old PDF)
For custom date ranges >60 days, the old flexible PDF is used for multi-week analysis:

```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-01-01",
    "end_date": "2026-03-31"
  }'
```

**Result:** Old flexible date range PDF (for multi-week analysis spanning 90 days)

---

## Response Format

All endpoints return the same response format:

```json
{
  "status": "success",
  "download_url": "/media/reports/School_Name_Week3_2026_Report.pdf",
  "filename": "School_Name_Week3_2026_Report.pdf",
  "generated_at": "2026-01-15T10:30:00Z",
  "expires_at": "2026-01-16T10:30:00Z",
  "file_size_mb": 2.5
}
```

## Testing from Frontend

If your frontend is calling the API without any parameters (empty POST body), it will now automatically get the professional PDF for the current week.

### Before (Old Behavior)
```javascript
// Empty request = Error or default to last 30 days
fetch('/admin_details/dashboard/school/13/generate-report/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})  // Empty body
});
// Result: Old PDF with last 30 days
```

### After (New Behavior)
```javascript
// Empty request = Professional PDF for current week
fetch('/admin_details/dashboard/school/13/generate-report/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})  // Empty body
});
// Result: Professional PDF for current week! ✨
```

## Migration Strategy

The API is **backward compatible**:

- ✅ Existing calls with custom date ranges still work (use old PDF)
- ✅ New calls without parameters get professional PDF
- ✅ Can explicitly request specific weeks
- ✅ No breaking changes

## Quick Test Command

Test right now with:

```bash
# Test current week (professional PDF)
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{}' | jq

# Or with week 3 explicitly
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -d '{"week_number": 3, "year": 2026}' | jq
```

## What Changed

### Before
```
API Call (empty) → Old PDF Generator → Basic report with last 30 days
```

### After
```
API Call (empty) → Auto-detect → Professional PDF Generator → Modern weekly report
API Call (custom dates) → Old PDF Generator → Flexible date range report
```

The system intelligently chooses the right generator based on the request parameters!
