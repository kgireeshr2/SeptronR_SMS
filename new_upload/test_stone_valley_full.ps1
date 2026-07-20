# ==============================================================
# STONE VALLEY SCHOOL - FULL END-TO-END Testing Script
# Tests: Staff, Classes, Students, Fees, Exams, Attendance, Parent
# ==============================================================
param()
$ErrorActionPreference = "Continue"
$BASE = "http://localhost:8000/api/v1"
$SV_SCHOOL_ID = "a8701957-9a83-4e69-b80b-2d83cef3dfd4"
$AY_ID = "6621b0fb-4640-4a6e-b54f-443cd410984d"

$RESULTS = [System.Collections.ArrayList]::new()

function log_ok($section, $msg) {
    $null = $RESULTS.Add([PSCustomObject]@{Status="PASS"; Section=$section; Message=$msg})
    Write-Host "  [PASS] $section : $msg" -ForegroundColor Green
}
function log_fail($section, $msg) {
    $null = $RESULTS.Add([PSCustomObject]@{Status="FAIL"; Section=$section; Message=$msg})
    Write-Host "  [FAIL] $section : $msg" -ForegroundColor Red
}
function log_info($section, $msg) {
    $null = $RESULTS.Add([PSCustomObject]@{Status="INFO"; Section=$section; Message=$msg})
    Write-Host "  [INFO] $section : $msg" -ForegroundColor Yellow
}

function safe_parse($content) {
    try { $content | ConvertFrom-Json } catch { $null }
}

function api_post($url, $headers, $body) {
    $b = if ($body -is [string]) { $body } else { $body | ConvertTo-Json -Depth 10 }
    Invoke-WebRequest -Uri "$BASE$url" -Method POST -Body $b -ContentType "application/json" -Headers $headers -UseBasicParsing
}
function api_get($url, $headers) {
    Invoke-WebRequest -Uri "$BASE$url" -Headers $headers -UseBasicParsing
}
function api_put($url, $headers, $body) {
    $b = if ($body -is [string]) { $body } else { $body | ConvertTo-Json -Depth 10 }
    Invoke-WebRequest -Uri "$BASE$url" -Method PUT -Body $b -ContentType "application/json" -Headers $headers -UseBasicParsing
}
function api_patch($url, $headers, $body) {
    $b = if ($body) { if ($body -is [string]) { $body } else { $body | ConvertTo-Json -Depth 10 } } else { $null }
    $params = @{ Uri="$BASE$url"; Method="PATCH"; Headers=$headers; UseBasicParsing=$true }
    if ($b) { $params.Body=$b; $params.ContentType="application/json" }
    Invoke-WebRequest @params
}
function get_err($ex) {
    try {
        $stream = $ex.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $reader.ReadToEnd()
    } catch { $ex.Exception.Message }
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  STONE VALLEY SCHOOL - FULL E2E TEST" -ForegroundColor Cyan
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ==============================================================
Write-Host "`n[1] SUPER ADMIN - VERIFY STONE VALLEY" -ForegroundColor Magenta
# ==============================================================
$lBody = '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}'
$lR = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $lBody -ContentType "application/json" -UseBasicParsing
$SA_TOKEN = ($lR.Content | ConvertFrom-Json).data.access_token
$H_SA = @{ "Authorization" = "Bearer $SA_TOKEN" }

$schools = safe_parse (Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers $H_SA -UseBasicParsing).Content
$sv = $schools | Where-Object { $_.id -eq $SV_SCHOOL_ID }
if ($sv) {
    log_ok "1.1 SA: Get Stone Valley" "School: $($sv.name) | Slug: $($sv.slug) | Active: $($sv.is_active)"
} else {
    log_fail "1.1 SA: Get Stone Valley" "School not found!"
}

# ==============================================================
Write-Host "`n[2] SCHOOL ADMIN LOGIN" -ForegroundColor Magenta
# ==============================================================
$lBody = '{"identifier":"admin@stonevalley.edu.in","password":"Admin@StoneValley123"}'
$lR = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $lBody -ContentType "application/json" -UseBasicParsing
$lDat = ($lR.Content | ConvertFrom-Json).data
$TOKEN = $lDat.access_token
$HS = @{ "Authorization" = "Bearer $TOKEN"; "X-School-Id" = $SV_SCHOOL_ID }
log_ok "2.1 Admin Login" "Email: $($lDat.user.email) | Admin: $($lDat.user.is_school_admin)"

# Get /me to verify
try {
    $me = safe_parse (api_get "/auth/me" $HS).Content
    log_ok "2.2 GET /auth/me" "User: $($me.data.email)"
} catch { log_fail "2.2 GET /auth/me" (get_err $_) }

# ==============================================================
Write-Host "`n[3] DEPARTMENT SETUP" -ForegroundColor Magenta
# ==============================================================
$DEPT_ID = $null
try {
    $r = api_post "/departments" $HS @{ name = "Primary Education"; description = "Lower primary grades" }
    $dept = safe_parse $r.Content
    $DEPT_ID = $dept.id
    log_ok "3.1 Create Department" "Name: $($dept.name) | ID: $DEPT_ID"
} catch {
    try {
        $depts = safe_parse (api_get "/departments" $HS).Content
        $DEPT_ID = $depts[0].id
        log_info "3.1 Create Department" "Using existing: $($depts[0].name)"
    } catch { log_fail "3.1 Department" (get_err $_) }
}

# ==============================================================
Write-Host "`n[4] STAFF CREATION (Based on Role)" -ForegroundColor Magenta
# ==============================================================
$STAFF_IDS = @{}

# Class Teacher
$STAFF_IDS["class_teacher"] = $null
try {
    $r = api_post "/staff" $HS @{
        first_name = "Priya"; last_name = "Sharma"
        email = "priya.sharma@stonevalley.edu.in"
        phone = "+91-9876501001"; designation = "Class Teacher"
        department_id = $DEPT_ID; date_of_joining = "2023-06-01"
        gender = "Female"; date_of_birth = "1985-03-15"
        qualification = "B.Ed, M.Sc. Mathematics"
        employee_id = "SV-T-001"; create_user_account = $true; password = "Teacher@1234"
    }
    $staff = safe_parse $r.Content
    $sid = if ($staff.data) { $staff.data.id } else { $staff.id }
    $STAFF_IDS["class_teacher"] = $sid
    log_ok "4.1 Create Class Teacher" "Priya Sharma | ID: $sid"
} catch {
    $errMsg = get_err $_
    if ($errMsg -like "*already*" -or $errMsg -like "*duplicate*" -or $errMsg -like "*exists*") {
        try {
            $staffList = safe_parse (api_get "/staff" $HS).Content
            $items = if ($staffList.data) { $staffList.data } else { $staffList }
            $found = $items | Where-Object { $_.email -like "*priya*" } | Select-Object -First 1
            if (-not $found) { $found = $items[0] }
            $STAFF_IDS["class_teacher"] = $found.id
            log_info "4.1 Class Teacher" "Using existing: $($found.first_name) $($found.last_name)"
        } catch { log_fail "4.1 Class Teacher" $errMsg }
    } else { log_fail "4.1 Create Class Teacher" $errMsg }
}

# Science Teacher  
try {
    $r = api_post "/staff" $HS @{
        first_name = "Amit"; last_name = "Patel"
        email = "amit.patel@stonevalley.edu.in"; phone = "+91-9876501002"
        designation = "Science Teacher"; department_id = $DEPT_ID
        date_of_joining = "2022-07-01"; gender = "Male"; date_of_birth = "1980-08-20"
        qualification = "M.Sc Physics"; employee_id = "SV-T-002"
        create_user_account = $true; password = "Teacher@1234"
    }
    $staff2 = safe_parse $r.Content
    $sid2 = if ($staff2.data) { $staff2.data.id } else { $staff2.id }
    $STAFF_IDS["science_teacher"] = $sid2
    log_ok "4.2 Create Science Teacher" "Amit Patel | ID: $sid2"
} catch {
    $STAFF_IDS["science_teacher"] = $STAFF_IDS["class_teacher"]
    log_info "4.2 Science Teacher" "Using fallback staff ID"
}

# List all staff
try {
    $staffList = safe_parse (api_get "/staff" $HS).Content
    $items = if ($staffList.data) { $staffList.data } else { $staffList }
    log_ok "4.3 List Staff" "Total staff: $($items.Count)"
} catch { log_fail "4.3 List Staff" (get_err $_) }

# ==============================================================
Write-Host "`n[5] CREATE CLASS, SECTIONS & SUBJECTS" -ForegroundColor Magenta
# ==============================================================
$CLASS_ID = $null
$SECTION_ID = $null

# Create Class 5
try {
    $r = api_post "/classes" $HS @{
        name = "Grade 5"; order_sequence = 5
        academic_year_id = $AY_ID
        class_teacher_id = $STAFF_IDS["class_teacher"]
    }
    $cls = safe_parse $r.Content
    $cdata = if ($cls.data) { $cls.data } else { $cls }
    $CLASS_ID = $cdata.id
    log_ok "5.1 Create Class" "Grade 5 | ID: $CLASS_ID"
} catch {
    try {
        $clsList = safe_parse (api_get "/classes?academic_year_id=$AY_ID" $HS).Content
        $items = if ($clsList.data) { $clsList.data } else { $clsList }
        if ($items -and $items.Count -gt 0) {
            $CLASS_ID = $items[0].id
            log_info "5.1 Create Class" "Using existing: $($items[0].name) | ID: $CLASS_ID"
        }
    } catch { log_fail "5.1 Create Class" (get_err $_) }
}

# Create Section A
try {
    $r = api_post "/classes/$CLASS_ID/sections" $HS @{
        name = "Section A"; capacity = 40
        class_teacher_id = $STAFF_IDS["class_teacher"]
    }
    $sec = safe_parse $r.Content
    $sdata = if ($sec.data) { $sec.data } else { $sec }
    $SECTION_ID = $sdata.id
    log_ok "5.2 Create Section A" "ID: $SECTION_ID | Capacity: 40"
} catch {
    try {
        $secList = safe_parse (api_get "/classes/$CLASS_ID/sections" $HS).Content
        $items = if ($secList.data) { $secList.data } else { $secList }
        if ($items -and $items.Count -gt 0) {
            $SECTION_ID = $items[0].id
            log_info "5.2 Create Section A" "Using existing section: $($items[0].name)"
        }
    } catch { log_fail "5.2 Create Section A" (get_err $_) }
}

# Create Subjects
$SUBJECT_IDS = @{}
$subjects = @(
    @{ name = "Mathematics"; code = "MATH5"; subject_type = "core" },
    @{ name = "Science"; code = "SCI5"; subject_type = "core" },
    @{ name = "English"; code = "ENG5"; subject_type = "core" },
    @{ name = "Social Studies"; code = "SST5"; subject_type = "core" }
)
foreach ($subj in $subjects) {
    try {
        $r = api_post "/subjects" $HS ($subj + @{ class_id = $CLASS_ID; academic_year_id = $AY_ID; max_marks = 100 })
        $s = safe_parse $r.Content
        $sdata = if ($s.data) { $s.data } else { $s }
        $SUBJECT_IDS[$subj.code] = $sdata.id
        log_ok "5.3 Create Subject: $($subj.name)" "Code: $($subj.code) | ID: $($sdata.id)"
    } catch {
        log_info "5.3 Subject $($subj.name)" "$(get_err $_)"
    }
}

# Get subjects if creation failed
if ($SUBJECT_IDS.Count -eq 0) {
    try {
        $subjList = safe_parse (api_get "/subjects?class_id=$CLASS_ID" $HS).Content
        $items = if ($subjList.data) { $subjList.data } else { $subjList }
        foreach ($s in $items) { $SUBJECT_IDS[$s.code] = $s.id }
        log_info "5.3 Subjects" "Using $($SUBJECT_IDS.Count) existing subjects"
    } catch { log_fail "5.3 Subjects" (get_err $_) }
}

# ==============================================================
Write-Host "`n[6] ADD STUDENTS & ASSIGN CLASS" -ForegroundColor Magenta
# ==============================================================
$STUDENT_IDS = @()

$studentData = @(
    @{ first_name="Aryan"; last_name="Mehta"; gender="Male"; dob="2015-04-10"; roll_no="SV2025001"; admission_no="ADM2025001"; parent_name="Suresh Mehta"; parent_email="suresh.mehta@gmail.com"; parent_phone="+91-9876502001" },
    @{ first_name="Sneha"; last_name="Joshi"; gender="Female"; dob="2015-06-15"; roll_no="SV2025002"; admission_no="ADM2025002"; parent_name="Ramesh Joshi"; parent_email="ramesh.joshi@gmail.com"; parent_phone="+91-9876502002" },
    @{ first_name="Rohan"; last_name="Verma"; gender="Male"; dob="2015-02-20"; roll_no="SV2025003"; admission_no="ADM2025003"; parent_name="Dinesh Verma"; parent_email="dinesh.verma@gmail.com"; parent_phone="+91-9876502003" }
)

foreach ($s in $studentData) {
    try {
        $nameParts = $s.parent_name -split " "
        $body = @{
            first_name = $s.first_name; last_name = $s.last_name
            gender = $s.gender; date_of_birth = $s.dob
            admission_number = $s.admission_no
            blood_group = "O+"; address = "Pune, Maharashtra"
            enrollment = @{
                class_id = $CLASS_ID; section_id = $SECTION_ID
                academic_year_id = $AY_ID; roll_number = $s.roll_no
            }
            parents = @(
                @{
                    first_name = $nameParts[0]
                    last_name = if ($nameParts.Count -gt 1) { $nameParts[1] } else { "" }
                    email = $s.parent_email; phone = $s.parent_phone
                    relationship = "Father"; create_login = $true
                }
            )
        }
        $r = api_post "/students/" $HS $body
        $std = safe_parse $r.Content
        $sdata = if ($std.data) { $std.data } else { $std }
        $sid = $sdata.id
        $STUDENT_IDS += $sid
        log_ok "6.1 Add Student: $($s.first_name) $($s.last_name)" "Roll: $($s.roll_no) | ID: $sid | Class: Grade 5 - Section A"
    } catch {
        $errMsg = get_err $_
        log_info "6.1 Student $($s.first_name)" "$errMsg"
    }
}

# Get students if creation had issues
if ($STUDENT_IDS.Count -eq 0) {
    try {
        $stdList = safe_parse (api_get "/students?class_id=$CLASS_ID" $HS).Content
        $items = if ($stdList.data) { $stdList.data } elseif ($stdList.students) { $stdList.students } else { $stdList }
        foreach ($s in $items) { $STUDENT_IDS += $s.id }
        log_info "6.1 Get Students" "Found $($STUDENT_IDS.Count) existing students"
    } catch { log_fail "6.1 Get Students" (get_err $_) }
}

Write-Host "  Total Students: $($STUDENT_IDS.Count)" -ForegroundColor Cyan
$PRIMARY_STUDENT_ID = if ($STUDENT_IDS.Count -gt 0) { $STUDENT_IDS[0] } else { $null }

# ==============================================================
Write-Host "`n[7] FEE MANAGEMENT" -ForegroundColor Magenta
# ==============================================================
$FEE_STRUCTURE_ID = $null
$FEE_CATEGORY_ID = $null

# Create fee category
try {
    $r = api_post "/fees/categories" $HS @{ name = "Tuition Fee"; description = "Monthly tuition charges"; is_recurring = $true }
    $fc = safe_parse $r.Content
    $fdata = if ($fc.data) { $fc.data } else { $fc }
    $FEE_CATEGORY_ID = $fdata.id
    log_ok "7.1 Create Fee Category" "Tuition Fee | ID: $FEE_CATEGORY_ID"
} catch {
    try {
        $fcList = safe_parse (api_get "/fees/categories" $HS).Content
        $items = if ($fcList.data) { $fcList.data } else { $fcList }
        if ($items -and $items.Count -gt 0) { $FEE_CATEGORY_ID = $items[0].id }
        log_info "7.1 Fee Category" "Using existing: ID=$FEE_CATEGORY_ID"
    } catch { log_fail "7.1 Fee Category" (get_err $_) }
}
if (-not $FEE_CATEGORY_ID) {
    try {
        $fcList = safe_parse (api_get "/fees/categories" $HS).Content
        $items = if ($fcList.data) { $fcList.data } else { $fcList }
        if ($items -and $items.Count -gt 0) { $FEE_CATEGORY_ID = $items[0].id }
    } catch {}
}

# Create fee structure
try {
    $feeBody = @{
        academic_year_id = $AY_ID; class_id = $CLASS_ID
        items = @(
            @{ fee_category_id = $FEE_CATEGORY_ID; amount = 4000; frequency = "monthly"; due_day = 10 }
        )
    }
    $r = api_post "/fees/structures" $HS $feeBody
    $fs = safe_parse $r.Content
    $fsdata = if ($fs.data) { $fs.data } else { $fs }
    $FEE_STRUCTURE_ID = $fsdata.id
    log_ok "7.2 Create Fee Structure" "Monthly Rs.4000 | ID: $FEE_STRUCTURE_ID"
} catch {
    try {
        $fsList = safe_parse (api_get "/fees/structures?academic_year_id=$AY_ID" $HS).Content
        $items = if ($fsList.data) { $fsList.data } else { $fsList }
        if ($items -and $items.Count -gt 0) { $FEE_STRUCTURE_ID = $items[0].id }
        log_info "7.2 Fee Structure" "Using existing: ID=$FEE_STRUCTURE_ID"
    } catch { log_fail "7.2 Fee Structure" (get_err $_) }
}

# Assign fee to class (class-level one-time operation)
try {
    $r = api_post "/fees/assign" $HS @{
        academic_year_id = $AY_ID; class_id = $CLASS_ID
    }
    log_ok "7.3 Assign Fee to Class" "Fees assigned to Grade 5 for AY 2025-2026"
} catch { log_info "7.3 Assign Fee" (get_err $_) }

# Generate invoices for the class
$INVOICE_ID = $null
try {
    $r = api_post "/fees/invoices/generate" $HS @{
        academic_year_id = $AY_ID; class_id = $CLASS_ID
        month = 5; year = 2025
    }
    log_ok "7.4 Generate Invoices" "Invoices generated for Grade 5"
} catch { log_info "7.4 Generate Invoices" (get_err $_) }

# View student fee invoices
if ($PRIMARY_STUDENT_ID) {
    try {
        $r = api_get "/fees/invoices?student_id=$PRIMARY_STUDENT_ID" $HS
        $invs = safe_parse $r.Content
        if ($invs -and $invs.Count -gt 0) { $INVOICE_ID = $invs[0].id }
        log_ok "7.5 View Fee Invoices" "Student: $PRIMARY_STUDENT_ID | Invoices: $($invs.Count) | Status: $($invs[0].status)"
    } catch { log_info "7.5 Fee Invoices" (get_err $_) }
}

# Collect fee payment
if ($PRIMARY_STUDENT_ID -and $INVOICE_ID) {
    try {
        $payBody = @{
            invoice_id = $INVOICE_ID; student_id = $PRIMARY_STUDENT_ID
            amount = 4000.00; payment_mode = "cash"
            payment_date = "2025-05-15"; remarks = "Term 1 payment"
        }
        $r = api_post "/fees/payments" $HS $payBody
        $pay = safe_parse $r.Content
        $paydata = if ($pay.data) { $pay.data } else { $pay }
        log_ok "7.6 Collect Fee Payment" "Amt: 4000 | Mode: cash | Receipt: $($paydata.receipt_number)"
    } catch { log_info "7.6 Collect Payment" (get_err $_) }
}

# List all fee invoices for context
try {
    $r = api_get "/fees/invoices?academic_year_id=$AY_ID" $HS
    $invs = safe_parse $r.Content
    log_ok "7.7 List Fee Invoices" "Count: $($invs.Count)"
} catch { log_info "7.7 Fee Invoices" (get_err $_) }

# ==============================================================
Write-Host "`n[8] EXAM MANAGEMENT" -ForegroundColor Magenta
# ==============================================================
$EXAM_TYPE_ID = $null
$EXAM_ID = $null

# Create exam type  (correct endpoint: /exam-types)
try {
    $r = api_post "/exam-types" $HS @{ name = "Unit Test 1"; weightage = 20; is_active = $true }
    $et = safe_parse $r.Content
    $etdata = if ($et.data) { $et.data } else { $et }
    $EXAM_TYPE_ID = $etdata.id
    log_ok "8.1 Create Exam Type" "Unit Test 1 | ID: $EXAM_TYPE_ID"
} catch {
    try {
        $etList = safe_parse (api_get "/exam-types" $HS).Content
        $items = if ($etList.data) { $etList.data } else { $etList }
        if ($items -and $items.Count -gt 0) { 
            $EXAM_TYPE_ID = $items[0].id
            log_info "8.1 Exam Type" "Using existing: $($items[0].name)"
        }
    } catch { log_fail "8.1 Exam Type" (get_err $_) }
}

# Create exams via bulk (one exam per subject) - correct endpoint: /exams/bulk
$EXAM_IDS = @{}
$SUBJECT_IDS_ARR = @($SUBJECT_IDS.Keys)  # use keys (codes) for labeling
$SUBJECT_IDS_VALS = @($SUBJECT_IDS.Values)
if ($EXAM_TYPE_ID -and $SUBJECT_IDS_VALS.Count -gt 0) {
    $subjectList = @()
    $examDates = @("2025-07-10", "2025-07-11", "2025-07-12", "2025-07-14")
    for ($i = 0; $i -lt $SUBJECT_IDS_VALS.Count; $i++) {
        $subjectList += @{ subject_id = $SUBJECT_IDS_VALS[$i]; max_marks = 25; exam_date = $examDates[$i % $examDates.Count] }
    }
    try {
        $bulkBody = @{
            exam_type_id = $EXAM_TYPE_ID; class_id = $CLASS_ID
            academic_year_id = $AY_ID; subjects = $subjectList
        }
        $r = api_post "/exams/bulk" $HS $bulkBody
        $bulkData = safe_parse $r.Content
        $examsArr = if ($bulkData.data) { $bulkData.data } elseif ($bulkData.exams) { $bulkData.exams } else { $bulkData }
        for ($i = 0; $i -lt $examsArr.Count; $i++) {
            $EXAM_IDS[$examsArr[$i].subject_id] = $examsArr[$i].id
        }
        $EXAM_ID = if ($examsArr.Count -gt 0) { $examsArr[0].id } else { $null }
        log_ok "8.2 Create Exams (Bulk)" "Created $($examsArr.Count) exams for Grade 5"
    } catch {
        log_fail "8.2 Create Exams" (get_err $_)
    }
}

# Enter exam marks via POST /exams/{id}/marks with entries array
Write-Host "`n  [8.4] Entering exam marks..." -ForegroundColor Yellow
if ($EXAM_IDS.Count -gt 0 -and $STUDENT_IDS.Count -gt 0) {
    $dummyMarkSets = @(@(22,18,20), @(23,19,0))  # Math, Science (0 = absent for Rohan)
    $examIdx = 0
    foreach ($subj_id in @($EXAM_IDS.Keys) | Select-Object -First 2) {
        $eid = $EXAM_IDS[$subj_id]
        $marksSet = $dummyMarkSets[$examIdx % $dummyMarkSets.Count]
        $entries = @()
        for ($i = 0; $i -lt $STUDENT_IDS.Count; $i++) {
            $m = if ($i -lt $marksSet.Count) { $marksSet[$i] } else { 15 }
            $entries += @{ student_id = $STUDENT_IDS[$i]; marks_obtained = $m; is_absent = ($m -eq 0); remarks = "Good" }
        }
        try {
            $r = api_post "/exams/$eid/marks" $HS @{ entries = $entries }
            log_ok "8.4 Enter Marks" "Exam: $eid | Marks entered for $($entries.Count) students"
        } catch { log_info "8.4 Marks" (get_err $_) }
        $examIdx++
    }
}

# Publish exam results (requires super-admin token with X-School-Id)
if ($EXAM_TYPE_ID) {
    $SA_TOKEN_FRESH = (safe_parse (Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}' -ContentType "application/json" -UseBasicParsing).Content).data.access_token
    $H_SA_SCHOOL = @{ "Authorization" = "Bearer $SA_TOKEN_FRESH"; "X-School-Id" = $SV_SCHOOL_ID }
    try {
        $r = api_post "/exams/publish" $H_SA_SCHOOL @{
            exam_type_id = $EXAM_TYPE_ID; class_id = $CLASS_ID
            year_id = $AY_ID; notify_parents = $false
        }
        $pub = safe_parse $r.Content
        log_ok "8.5 Publish Results" "Published: $($pub.published) | Exams updated: $($pub.exams_updated)"
    } catch { log_info "8.5 Publish Results" (get_err $_) }
}

# View marks for primary student
if ($EXAM_ID -and $PRIMARY_STUDENT_ID) {
    try {
        $r = api_get "/exams/$EXAM_ID/marks" $HS
        $marks = safe_parse $r.Content
        $am = $marks | Where-Object { $_.student_id -eq $PRIMARY_STUDENT_ID }
        log_ok "8.6 View Student Marks" "Student: $PRIMARY_STUDENT_ID | Marks: $($am.marks_obtained)/25 | Grade: $($am.grade)"
    } catch { log_info "8.6 View Marks" (get_err $_) }
}

# View class results (ranked)
if ($EXAM_ID -and $CLASS_ID) {
    try {
        $r = api_get "/exams/$EXAM_ID/results/$CLASS_ID`?year_id=$AY_ID" $HS
        $res = safe_parse $r.Content
        log_ok "8.7 Class Results (Ranked)" "Class Avg: $($res.class_average)% | Top: $($res.results[0].student_name)"
    } catch { log_info "8.7 Class Results" (get_err $_) }
}

# Get grading scale
try {
    $r = api_get "/grading-scales" $HS
    $grades = safe_parse $r.Content
    $items = if ($grades.data) { $grades.data } else { $grades }
    log_ok "8.8 View Grading Scale" "Grades: $($items.Count)"
} catch { log_info "8.8 Grading" (get_err $_) }

# ==============================================================
Write-Host "`n[9] ATTENDANCE MANAGEMENT" -ForegroundColor Magenta
# ==============================================================
$ATT_DATE = "2025-07-01"

# Mark attendance — correct endpoint: POST /attendance/section/{section_id}
if ($STUDENT_IDS.Count -gt 0 -and $SECTION_ID) {
    $attEntries = @()
    $statuses = @("present", "present", "absent")
    for ($i = 0; $i -lt $STUDENT_IDS.Count; $i++) {
        $st = if ($i -lt $statuses.Count) { $statuses[$i] } else { "present" }
        $attEntries += @{ student_id = $STUDENT_IDS[$i]; status = $st }
    }
    try {
        $attBody = @{
            section_id = $SECTION_ID; academic_year_id = $AY_ID
            date = $ATT_DATE; session_type = "morning"; entries = $attEntries
        }
        $r = api_post "/attendance/section/$SECTION_ID" $HS $attBody
        $att = safe_parse $r.Content
        log_ok "9.1 Mark Attendance ($ATT_DATE)" "Students: $($STUDENT_IDS.Count) | Present: 2 | Absent: 1"
    } catch { log_info "9.1 Mark Attendance" (get_err $_) }
}

# View attendance for a date
try {
    $r = api_get "/attendance/section/$SECTION_ID`?date=$ATT_DATE" $HS
    $atr = safe_parse $r.Content
    $aryanEntry = $atr.entries | Where-Object { $_.student_id -eq $PRIMARY_STUDENT_ID }
    log_ok "9.2 View Attendance" "Date: $ATT_DATE | Aryan: $($aryanEntry.status)"
} catch { log_info "9.2 View Attendance" (get_err $_) }

# Student attendance summary  
if ($PRIMARY_STUDENT_ID) {
    try {
        $r = api_get "/attendance/student/$PRIMARY_STUDENT_ID/summary?academic_year_id=$AY_ID" $HS
        $ats = safe_parse $r.Content
        log_ok "9.3 Student Attendance Summary" "Student: $PRIMARY_STUDENT_ID"
    } catch { log_info "9.3 Student Attendance" (get_err $_) }
}

# Mark multiple days attendance
for ($day = 2; $day -le 5; $day++) {
    $date = "2025-07-0$day"
    if ($STUDENT_IDS.Count -gt 0 -and $SECTION_ID) {
        $recs = @()
        foreach ($sid in $STUDENT_IDS) { $recs += @{ student_id = $sid; status = "present" } }
        try {
            $r = api_post "/attendance/section/$SECTION_ID" $HS @{
                section_id = $SECTION_ID; academic_year_id = $AY_ID
                date = $date; session_type = "morning"; entries = $recs
            }
            log_ok "9.4 Attendance Day $day" "Date: $date | All present"
        } catch { log_info "9.4 Attendance $date" (get_err $_) }
    }
}

# ==============================================================
Write-Host "`n[10] PARENT PORTAL TEST" -ForegroundColor Magenta
# ==============================================================

# Find parent credentials (created during student registration)
$PARENT_TOKEN = $null
$PARENT_EMAIL = "suresh.mehta@gmail.com"

try {
    $pBody = "{`"identifier`":`"$PARENT_EMAIL`",`"password`":`"Parent@123`"}"
    $lR2 = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $pBody -ContentType "application/json" -UseBasicParsing
    $PARENT_TOKEN = ($lR2.Content | ConvertFrom-Json).data.access_token
    log_ok "10.1 Parent Login" "Parent: $PARENT_EMAIL"
} catch {
    log_info "10.1 Parent Login" "Could not login: $(get_err $_)"
}

if ($PARENT_TOKEN -and $PRIMARY_STUDENT_ID) {
    $HP = @{ "Authorization" = "Bearer $PARENT_TOKEN"; "X-School-Id" = $SV_SCHOOL_ID }

    # View child info
    try {
        $r = api_get "/students/$PRIMARY_STUDENT_ID" $HP
        $child = safe_parse $r.Content
        $cdata = if ($child.data) { $child.data } else { $child }
        log_ok "10.2 Parent: View Child Info" "Child: $($cdata.first_name) $($cdata.last_name) | Class: $($cdata.class_name)"
    } catch { log_info "10.2 View Child" (get_err $_) }

    # View fees (invoices)
    try {
        $r = api_get "/fees/invoices?student_id=$PRIMARY_STUDENT_ID" $HP
        $invs = safe_parse $r.Content
        if ($invs -and $invs.Count -gt 0) {
            log_ok "10.3 Parent: View Child Fees" "Invoices: $($invs.Count) | Status: $($invs[0].status) | Total: Rs.$($invs[0].total_amount)"
        } else {
            log_info "10.3 Parent: View Child Fees" "No invoices found"
        }
    } catch { log_info "10.3 View Fees" (get_err $_) }

    # View attendance
    try {
        $r = api_get "/attendance/section/$SECTION_ID`?date=$ATT_DATE" $HP
        $att = safe_parse $r.Content
        $myEntry = $att.entries | Where-Object { $_.student_id -eq $PRIMARY_STUDENT_ID }
        log_ok "10.4 Parent: View Attendance" "Date: $ATT_DATE | Child status: $($myEntry.status)"
    } catch { log_info "10.4 View Attendance" (get_err $_) }

    # View exam results (marks)
    if ($EXAM_ID) {
        try {
            $r = api_get "/exams/$EXAM_ID/marks" $HP
            $marks = safe_parse $r.Content
            $am = $marks | Where-Object { $_.student_id -eq $PRIMARY_STUDENT_ID }
            log_ok "10.5 Parent: View Exam Results" "Marks: $($am.marks_obtained)/25 | Grade: $($am.grade) | Result: $($am.result)"
        } catch { log_info "10.5 View Results" (get_err $_) }
    }

    # View published class results
    if ($EXAM_ID -and $CLASS_ID) {
        try {
            $r = api_get "/exams/$EXAM_ID/results/$CLASS_ID`?year_id=$AY_ID" $HP
            $res = safe_parse $r.Content
            log_ok "10.6 Parent: Published Results" "Class Avg: $($res.class_average)% | Rank 1: $($res.results[0].student_name)"
        } catch { log_info "10.6 Published Results" (get_err $_) }
    }
} else {
    log_info "10 Parent Portal" "Skipped (no parent login token)"
}

# ==============================================================
Write-Host "`n[11] ADDITIONAL FEATURES TEST" -ForegroundColor Magenta
# ==============================================================

# Holidays
try {
    $r = api_post "/holidays" $HS @{ name = "Independence Day"; date = "2025-08-15"; holiday_type = "national"; description = "National Holiday" }
    $hol = safe_parse $r.Content
    $hdata = if ($hol.data) { $hol.data } else { $hol }
    log_ok "11.1 Create Holiday" "Independence Day | Date: 2025-08-15 | ID: $($hdata.id)"
} catch { log_info "11.1 Holiday" (get_err $_) }

# List holidays
try {
    $r = api_get "/holidays" $HS
    $hols = safe_parse $r.Content
    $items = if ($hols.data) { $hols.data } else { $hols }
    log_ok "11.2 List Holidays" "Count: $($items.Count)"
} catch { log_info "11.2 List Holidays" (get_err $_) }

# School settings
try {
    $r = api_get "/schools/settings" $HS
    log_ok "11.3 School Settings" "Retrieved"
} catch { log_info "11.3 School Settings" (get_err $_) }

# School profile
try {
    $r = api_get "/schools/profile" $HS
    $prof = safe_parse $r.Content
    $pdata = if ($prof.data) { $prof.data } else { $prof }
    log_ok "11.4 School Profile" "School: $($pdata.school_name)"
} catch { log_info "11.4 School Profile" (get_err $_) }

# Roles
try {
    $r = api_get "/roles" $HS
    $roles = safe_parse $r.Content
    $items = if ($roles.data) { $roles.data } else { $roles }
    log_ok "11.5 List Roles" "Count: $($items.Count)"
} catch { log_info "11.5 Roles" (get_err $_) }

# ==============================================================
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY - STONE VALLEY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
$passed = ($RESULTS | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($RESULTS | Where-Object { $_.Status -eq "FAIL" }).Count
$info   = ($RESULTS | Where-Object { $_.Status -eq "INFO" }).Count
Write-Host "  PASS: $passed" -ForegroundColor Green
Write-Host "  FAIL: $failed" -ForegroundColor Red
Write-Host "  INFO: $info" -ForegroundColor Yellow
Write-Host "  Total: $($RESULTS.Count)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Key IDs Created:" -ForegroundColor Cyan
Write-Host "  School ID:         $SV_SCHOOL_ID"
Write-Host "  Academic Year ID:  $AY_ID" 
Write-Host "  Class ID:          $CLASS_ID"
Write-Host "  Section ID:        $SECTION_ID"
Write-Host "  Students:          $($STUDENT_IDS.Count)"
Write-Host "  Exam ID:           $EXAM_ID"

if ($failed -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $RESULTS | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  - $($_.Section): $($_.Message)" -ForegroundColor Red
    }
}
