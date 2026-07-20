# FIX PROMPT 05 — End-to-End Data Setup & Full Integration Test

## Context
After applying Fixes 01-04, run this prompt to create test data for all modules and verify the system works end-to-end. Use credentials: superadmin / SuperAdmin@123.

Pre-requisites:
- Fixes 01-04 applied
- School created: `bfe88bea-e4c2-42d7-83f4-829b98748901`
- Academic Year 2025-2026 created: `0254801d-ce06-41ad-889d-2c94b55f0cde`
- Backend running at http://localhost:8000

---

## Step 1 — Login & Get Token

```powershell
$base = "http://localhost:8000/api/v1"
$r = Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
    -ContentType "application/json" `
    -Body '{"username":"superadmin","password":"SuperAdmin@123"}'
$token = $r.data.access_token
$h = @{Authorization = "Bearer $token"; "Content-Type" = "application/json"}
$schoolId = "bfe88bea-e4c2-42d7-83f4-829b98748901"
$ayId = "0254801d-ce06-41ad-889d-2c94b55f0cde"
echo "Token: $($token.Substring(0,20))..."
```

---

## Step 2 — Create Departments

```powershell
$dept1 = Invoke-RestMethod -Method Post -Uri "$base/staff/departments" -Headers $h `
    -Body "{`"name`":`"Science`",`"description`":`"Science Department`"}"
$dept2 = Invoke-RestMethod -Method Post -Uri "$base/staff/departments" -Headers $h `
    -Body "{`"name`":`"Mathematics`",`"description`":`"Math Department`"}"
$deptId = $dept1.data.id
echo "Dept: $deptId"
```

---

## Step 3 — Create Classes & Sections

```powershell
# Create Classes (Grade 1-5)
$classes = @()
for ($i = 1; $i -le 5; $i++) {
    $c = Invoke-RestMethod -Method Post -Uri "$base/classes" -Headers $h `
        -Body "{`"name`":`"Grade $i`",`"academic_year_id`":`"$ayId`",`"numeric_level`":$i}"
    $classes += $c.data.id
    echo "Class Grade $i: $($c.data.id)"
}

# Create Sections for Grade 1
$secA = Invoke-RestMethod -Method Post -Uri "$base/sections" -Headers $h `
    -Body "{`"class_id`":`"$($classes[0])`",`"name`":`"A`",`"capacity`":40}"
$secB = Invoke-RestMethod -Method Post -Uri "$base/sections" -Headers $h `
    -Body "{`"class_id`":`"$($classes[0])`",`"name`":`"B`",`"capacity`":40}"
echo "Section A: $($secA.data.id)"
```

---

## Step 4 — Create Subjects

```powershell
$subjects = @("Mathematics", "Science", "English", "Social Studies", "Hindi")
$codes = @("MATH", "SCI", "ENG", "SS", "HIN")
$subjectIds = @()
for ($i = 0; $i -lt 5; $i++) {
    $s = Invoke-RestMethod -Method Post -Uri "$base/subjects" -Headers $h `
        -Body "{`"name`":`"$($subjects[$i])`",`"code`":`"$($codes[$i])`",`"full_marks`":100,`"pass_marks`":40}"
    $subjectIds += $s.data.id
}
echo "Subjects created: $($subjectIds.Count)"
```

---

## Step 5 — Create Staff Users

```powershell
# Create a teacher user account first
$teacherUser = Invoke-RestMethod -Method Post -Uri "$base/users" -Headers $h `
    -Body "{`"username`":`"teacher1`",`"email`":`"teacher1@school.com`",`"password`":`"Teacher@123`",`"is_active`":true}"

# Create staff profile
$staff = Invoke-RestMethod -Method Post -Uri "$base/staff" -Headers $h -Body @"
{
    "user_id": "$($teacherUser.data.id)",
    "employee_id": "EMP001",
    "first_name": "Rajesh",
    "last_name": "Kumar",
    "department_id": "$deptId",
    "date_of_joining": "2020-06-01",
    "employment_type": "permanent",
    "salary_type": "monthly",
    "monthly_salary": 35000,
    "gender": "male",
    "date_of_birth": "1985-03-15"
}
"@
echo "Staff: $($staff.data.id)"
```

---

## Step 6 — Create Student Users

```powershell
# Create student user account
$studentUser = Invoke-RestMethod -Method Post -Uri "$base/users" -Headers $h `
    -Body "{`"username`":`"student001`",`"email`":`"student001@school.com`",`"password`":`"Student@123`",`"is_active`":true}"

# Create student profile
$student = Invoke-RestMethod -Method Post -Uri "$base/students" -Headers $h -Body @"
{
    "user_id": "$($studentUser.data.id)",
    "admission_number": "2025001",
    "first_name": "Aarav",
    "last_name": "Sharma",
    "admission_date": "2025-04-01",
    "gender": "male",
    "date_of_birth": "2016-07-10",
    "class_id": "$($classes[0])",
    "section_id": "$($secA.data.id)",
    "phone": "9876543210",
    "email": "parent@email.com",
    "address": "123 Main St",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
}
"@
echo "Student: $($student.data.id)"
```

---

## Step 7 — Test Fee Module (Already Working)

```powershell
# Create fee category
$feeCat = Invoke-RestMethod -Method Post -Uri "$base/fees/categories" -Headers $h `
    -Body "{`"name`":`"Tuition Fee`",`"description`":`"Monthly tuition`",`"is_active`":true}"

# Create fee structure
$feeStruct = Invoke-RestMethod -Method Post -Uri "$base/fees/structures" -Headers $h -Body @"
{
    "academic_year_id": "$ayId",
    "class_id": "$($classes[0])",
    "fee_category_id": "$($feeCat.data.id)",
    "amount": 5000,
    "frequency": "monthly",
    "due_day": 10
}
"@

echo "Fee Structure: $($feeStruct.data.id)"
```

---

## Step 8 — Test Attendance

```powershell
# Create attendance session
$session = Invoke-RestMethod -Method Post -Uri "$base/attendance/sessions" -Headers $h -Body @"
{
    "class_id": "$($classes[0])",
    "section_id": "$($secA.data.id)",
    "academic_year_id": "$ayId",
    "date": "$(Get-Date -Format 'yyyy-MM-dd')",
    "session_type": "morning"
}
"@

# Mark attendance
$att = Invoke-RestMethod -Method Post -Uri "$base/attendance/student" -Headers $h -Body @"
{
    "session_id": "$($session.data.id)",
    "student_id": "$($student.data.id)",
    "status": "present"
}
"@
echo "Attendance: $($att.data.id)"
```

---

## Step 9 — Test Library

```powershell
# Create book category
$bookCat = Invoke-RestMethod -Method Post -Uri "$base/library/categories" -Headers $h `
    -Body "{`"name`":`"Science Fiction`",`"description`":`"Sci-fi books`"}"

# Add a book
$book = Invoke-RestMethod -Method Post -Uri "$base/library/books" -Headers $h -Body @"
{
    "title": "A Brief History of Time",
    "author": "Stephen Hawking",
    "isbn": "9780553380163",
    "publisher": "Bantam Books",
    "publication_year": 1988,
    "category_id": "$($bookCat.data.id)",
    "total_copies": 3,
    "language": "English",
    "rack_number": "SF-01"
}
"@
echo "Book: $($book.data.id)"
```

---

## Step 10 — Test Homework

```powershell
$hw = Invoke-RestMethod -Method Post -Uri "$base/homework" -Headers $h -Body @"
{
    "academic_year_id": "$ayId",
    "class_id": "$($classes[0])",
    "section_id": "$($secA.data.id)",
    "subject_id": "$($subjectIds[0])",
    "title": "Chapter 1 Exercise",
    "description": "Complete exercises 1-10",
    "due_date": "$(([datetime]::Today.AddDays(3)).ToString('yyyy-MM-dd'))"
}
"@
echo "Homework: $($hw.data.id)"
```

---

## Step 11 — Test Announcements

```powershell
$ann = Invoke-RestMethod -Method Post -Uri "$base/announcements" -Headers $h -Body @"
{
    "title": "School Annual Day",
    "body": "Annual day celebrations will be held on March 15, 2026.",
    "audience": "all",
    "publish_at": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')",
    "expires_at": "2026-03-15T00:00:00"
}
"@
echo "Announcement: $($ann.data.id)"
```

---

## Step 12 — Test Calendar Event

```powershell
$event = Invoke-RestMethod -Method Post -Uri "$base/calendar/events" -Headers $h -Body @"
{
    "title": "Parent Teacher Meeting",
    "event_type": "meeting",
    "start_datetime": "2025-09-15T10:00:00",
    "end_datetime": "2025-09-15T13:00:00",
    "location": "School Auditorium",
    "audience": "parents",
    "academic_year_id": "$ayId",
    "color_tag": "#FF5733"
}
"@
echo "Calendar Event: $($event.data.id)"
```

---

## Step 13 — Test Reports

```powershell
# Get available reports
$reports = Invoke-RestMethod -Uri "$base/reports/available" -Headers $h
echo "Available reports: $($reports.data.Count)"

# Try fetching a specific report
Invoke-RestMethod -Uri "$base/reports/attendance-summary?academic_year_id=$ayId" -Headers $h
```

---

## Step 14 — Full Status Check

Run this final verification:

```powershell
$endpoints = @(
    "/students", "/staff", "/classes", "/sections", "/subjects",
    "/attendance/holidays", "/attendance/sessions",
    "/fees/categories", "/fees/structures", "/fees/invoices",
    "/library/books", "/library/members",
    "/accounting/income", "/accounting/expenses",
    "/inventory/items", "/inventory/categories",
    "/homework", "/calendar/events", "/announcements",
    "/notifications", "/notification-templates",
    "/staff/departments", "/staff/leaves", "/staff/payroll",
    "/timetable", "/exams", "/exam-types",
    "/transport/vehicles", "/transport/routes",
    "/audit-logs", "/reports/available"
)

$pass = 0; $fail = 0
foreach ($ep in $endpoints) {
    try {
        $r = Invoke-RestMethod -Uri "$base$ep" -Headers $h
        Write-Host "✅ $ep" -ForegroundColor Green
        $pass++
    } catch {
        Write-Host "❌ $ep — $($_.Exception.Message)" -ForegroundColor Red
        $fail++
    }
}
Write-Host "`n=== RESULTS: $pass PASS / $fail FAIL ==="
```

---

## Expected Final State

After all fixes applied and data created:
- All GET list endpoints return 200
- Classes, Sections, Students can be created
- Attendance can be recorded
- Fees can be invoiced and paid
- Library books can be issued and returned
- Homework can be assigned
- Staff payroll can be generated
- Reports can be generated
- Calendar events visible to users
- Announcements published to target audience
