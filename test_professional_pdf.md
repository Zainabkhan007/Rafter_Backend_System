# Testing the New Professional PDF Generator

## Overview
A completely redesigned PDF report generator with professional styling, brand colors, and comprehensive analytics sections.

## Key Features

### Design Improvements
- ✅ Clean cover page with logo only (no green background)
- ✅ Week dates formatted as "13 Jan - 17 Jan" instead of "Week 3"
- ✅ Compact, professional layout with better space utilization
- ✅ Brand color scheme throughout:
  - Off-White (#EDEDED)
  - Dark Forest (#053F34)
  - Pale Mint (#CAFEC7)
  - Sage Green (#009C5B)
  - Mustard Yellow (#FCCB5E)
  - Rose Pink (#F36487)
  - Soft Aqua (#C7E7EC)
  - Lavender (#DBD4F4)
  - Nude/Sand (#EACBB3)

### Content Sections
1. **Executive Summary** - KPI cards with week-over-week comparison
2. **Revenue Analysis** - Detailed revenue breakdown by user type with charts
3. **Order Analytics** - Order patterns and trends
4. **User Engagement** - Engagement rates for students, parents, and staff
5. **Menu Performance** - Top 10 menu items with charts
6. **Day-wise Analysis** - Monday-Friday breakdown (excludes weekends)
7. **Staff/Teacher Breakdown** - Individual staff stats (no "most popular meal")
8. **Inactive Users** - Lists with IDs, emails, last orders, and order IDs
9. **Trend Analysis** - Week-over-week comparison with trend indicators
10. **Recommendations** - Data-driven insights and action items

### Chart Improvements
- Compact size optimized for PDF
- Data labels on all bars/pie slices
- Brand colors used consistently
- Cleaner design with fewer grid lines

## API Usage

### Weekly Report Endpoint (NEW DEFAULT BEHAVIOR)

**URL:** `POST /admin_details/dashboard/school/{school_id}/generate-report/`

**⚡ IMPORTANT: Professional PDF is now the DEFAULT for all requests!**

**Request Body Options:**

**1. Default (Current Week) - NEW:**
```json
{}
```
Or just empty POST body - automatically generates professional PDF for current week!

**2. Specific Week (Explicit):**
```json
{
  "week_number": 3,
  "year": 2026
}
```

**3. This/Last Week (Preset):**
```json
{
  "date_range": "this_week"
}
```
or
```json
{
  "date_range": "last_week"
}
```

**4. Custom Date Range (NEW - Auto-detects Week):**
```json
{
  "start_date": "2025-12-17",
  "end_date": "2026-01-14",
  "include_detailed_lists": true
}
```
**Result:** Professional PDF using the week number from the end date!
- Date ranges ≤60 days automatically use professional PDF
- Date ranges >60 days use old flexible generator for multi-week analysis

**Example using cURL:**
```bash
curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "week_number": 3,
    "year": 2026
  }'
```

**Example using Python requests:**
```python
import requests

url = "http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}
data = {
    "week_number": 3,
    "year": 2026
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "download_url": "/media/reports/School_Name_Week3_2026_Report.pdf",
  "filename": "School_Name_Week3_2026_Report.pdf",
  "generated_at": "2026-01-14T10:30:00Z",
  "expires_at": "2026-01-15T10:30:00Z",
  "file_size_mb": 2.5
}
```

### Old Flexible Date Range Report (Still Available)

For custom date ranges, omit `week_number` and `year` and use the old format:

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "class_year": "Junior Infants",
  "teacher_id": 123,
  "delivery_days": ["Monday", "Tuesday"],
  "include_detailed_lists": true
}
```

## Testing Steps

1. **Start the Django development server:**
   ```bash
   source venv/bin/activate
   python manage.py runserver
   ```

2. **Test the endpoint:**
   ```bash
   # Using the new professional weekly report
   curl -X POST http://127.0.0.1:8000/admin_details/dashboard/school/13/generate-report/ \
     -H "Content-Type: application/json" \
     -d '{"week_number": 3, "year": 2026}'
   ```

3. **Check the generated PDF:**
   - The PDF will be saved in `MEDIA_ROOT/reports/`
   - Download URL will be returned in the response
   - Open the PDF and verify all sections are rendering correctly

## Week Logic

The PDF generator uses Friday-based week logic:
- Week starts on Saturday (day after previous Friday)
- Week ends on Friday
- This matches the school's ordering system where Friday is the cutoff

Example for Week 3, 2026:
- Week Start: Saturday, January 10, 2026
- Week End: Friday, January 16, 2026
- Displayed as: "10 Jan - 16 Jan"

## Inactive Users Details

The inactive users section now includes:
- User ID
- Full Name
- Email Address
- Last Order Date
- Last Order ID

This provides administrators with all the information needed to follow up with inactive users.

## Charts Included

1. **Orders by Weekday** - Bar chart (Monday-Friday only)
2. **Revenue by Weekday** - Bar chart (Monday-Friday only)
3. **Orders by User Type** - Pie chart (Students/Parents/Staff)
4. **Top 5 Menu Items** - Bar chart with quantities

All charts are compact, professional, and include data labels.

## Error Handling

The generator includes comprehensive error handling:
- Safe NaN/Inf handling for all numeric values
- Graceful fallback when data is missing
- Detailed error messages with full tracebacks
- Validates week numbers and years

## Future Enhancements

Potential additions for future iterations:
- Platform analytics (if Order model has platform field)
- Multi-week trend charts
- Comparison with school averages
- Export to Excel option
- Email delivery of reports
