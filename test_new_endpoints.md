# Testing New Analytics Endpoints

## Backend Implementation Complete

### Files Created:
1. ✅ `/admin_section/analytics_views.py` - All new analytics endpoints
2. ✅ `/admin_section/utils/analytics_helpers.py` - Helper functions
3. ✅ `/admin_section/utils/chart_generators.py` - Chart generation with matplotlib
4. ✅ `/admin_section/pdf_generator.py` - Comprehensive PDF report with 11 sections
5. ✅ `/admin_section/urls.py` - Updated with new routes
6. ✅ `/admin_section/views.py` - Fixed `get_school_analytics` (POST → GET, added children_count)
7. ✅ `requirements.txt` - Added weasyprint, matplotlib, cairocffi

### Required Setup Steps:

1. **Install new Python packages:**
   ```bash
   cd /Users/alfabolt/Documents/GitHub/Personal/Rafter_Backend_System
   pip install -r requirements.txt
   ```

2. **Create media/reports directory:**
   ```bash
   mkdir -p media/reports
   chmod 755 media/reports
   ```

3. **Test the endpoints:**

   a. **Test GET /admin_details/dashboard/schools/**
   ```bash
   curl http://localhost:8000/admin_details/dashboard/schools/
   ```
   Expected: List of schools with children_count field

   b. **Test GET /admin_details/dashboard/school/{school_id}/**
   ```bash
   curl "http://localhost:8000/admin_details/dashboard/school/1/?page=1&per_page=20"
   ```
   Expected: Comprehensive school summary with all metrics

   c. **Test GET /admin_details/dashboard/school/{school_id}/filter-options/**
   ```bash
   curl http://localhost:8000/admin_details/dashboard/school/1/filter-options/
   ```
   Expected: Available filter options (classes, delivery days, date presets)

   d. **Test POST /admin_details/dashboard/school/{school_id}/generate-report/**
   ```bash
   curl -X POST http://localhost:8000/admin_details/dashboard/school/1/generate-report/ \
     -H "Content-Type: application/json" \
     -d '{
       "start_date": "2024-01-01",
       "end_date": "2024-12-31",
       "include_detailed_lists": true
     }'
   ```
   Expected: PDF download URL

### API Endpoints Summary:

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/dashboard/schools/` | GET | List all schools (changed from POST) | ✅ Fixed |
| `/dashboard/school/{id}/` | GET | School summary with pagination | ✅ New |
| `/dashboard/school/{id}/filter-options/` | GET | Available filters | ✅ New |
| `/dashboard/school/{id}/generate-report/` | POST | Generate PDF report | ✅ New |

### Key Optimizations:

1. **Database-level aggregations** - Used Django ORM Count, Sum, Avg instead of Python loops
2. **Prefetch and select_related** - Minimized N+1 query issues
3. **Pagination** - School summary supports pagination for orders
4. **Performance targets:**
   - `get_school_analytics`: <500ms (was 5-10s)
   - `get_school_summary`: <2s
   - `generate_school_report`: 5-15s (acceptable for PDF generation)

### PDF Report Sections (All 11 Implemented):

1. ✅ Executive Summary
2. ✅ Weekly Order Numbers (detailed with week-over-week)
3. ✅ Registered vs Ordering Analysis
4. ✅ Weekly Non-Orderers Report
5. ✅ Class/Teacher Breakdown
6. ✅ Week-to-Week Comparisons
7. ✅ Active vs Inactive Users
8. ✅ New Sign-ups Per Week
9. ✅ Churned Parents
10. ✅ Busiest/Quietest Days
11. ✅ Meal Popularity
12. ✅ Platform Usage (iOS vs Android)

### Charts Generated:
- Weekly order trend (line chart)
- Registered vs ordering (pie chart)
- Class/teacher breakdown (horizontal bar)
- Day of week analysis (bar chart)
- Platform usage (pie chart)
- Top meals (horizontal bar)

### Next Steps:
Now proceed with frontend implementation to consume these endpoints.
