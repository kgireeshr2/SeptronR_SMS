# SMS Application - Full Test with School Context
# Uses X-School-Id header for school-scoped endpoints

$BASE = "http://localhost:8000/api/v1"
$BUGS = @()
$PASSES = @()
$INFOS = @()

function Log-Pass { param($test, $detail) $global:PASSES += [PSCustomObject]@{Test=$test;Detail=$detail}; Write-Host "  [PASS] $test" -ForegroundColor Green }
function Log-Bug  { param($test, $detail, $severity) $global:BUGS += [PSCustomObject]@{Test=$test;Detail=$detail;Severity=$severity}; Write-Host "  [BUG/$severity] $test - $detail" -ForegroundColor Red }
function Log-Info { param($test, $detail) $global:INFOS += [PSCustomObject]@{Test=$test;Detail=$detail}; Write-Host "  [INFO] $test - $detail" -ForegroundColor Yellow }

function Invoke-API {
    param($Method="GET", $Path, $Body, $Headers, $SchoolId)
    $h = if ($Headers) { $Headers.Clone() } else { @{} }
    if ($SchoolId) { $h["X-School-Id"] = $SchoolId }
    $params = @{ Uri="$BASE$Path"; Method=$Method; Headers=$h; UseBasicParsing=$true; ErrorAction="Stop" }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Compress); $params.ContentType = "application/json" }
    return Invoke-WebRequest @params
}

# =============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SMS APPLICATION - FULL QA TEST SUITE" -ForegroundColor Cyan
Write-Host "  Testing as End User + Break Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# --- GET TOKEN ---
$lResp = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}' -ContentType "application/json" -UseBasicParsing | ConvertFrom-Json
$TOKEN = $lResp.data.access_token
$H = @{ "Authorization" = "Bearer $TOKEN" }
Write-Host "Logged in as: $($lResp.data.user.email) | Super Admin: $($lResp.data.user.is_super_admin)" -ForegroundColor Cyan

# --- GET SCHOOL ID ---
$schools = (Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers $H -UseBasicParsing | ConvertFrom-Json)
$SCHOOL_ID = $schools[0].id
$SCHOOL_NAME = $schools[0].name
Write-Host "Using school: $SCHOOL_NAME ($SCHOOL_ID)`n" -ForegroundColor Cyan
$HS = @{ "Authorization" = "Bearer $TOKEN"; "X-School-Id" = $SCHOOL_ID }  # Headers WITH school context

# =============================================
Write-Host "--- [1] AUTHENTICATION ---" -ForegroundColor Magenta

# 1.1: GET /auth/me with valid token
$r = Invoke-WebRequest -Uri "$BASE/auth/me" -Headers $H -UseBasicParsing
$u = ($r.Content | ConvertFrom-Json).data
if ($r.StatusCode -eq 200 -and $u.is_super_admin -eq $true) { Log-Pass "1.1 GET /auth/me" "User $($u.email) authenticated" }
else { Log-Bug "1.1 GET /auth/me" "Unexpected response" "HIGH" }

# 1.2: Wrong password
try { Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{"identifier":"superadmin@sms.com","password":"WRONG"}' -ContentType "application/json" -UseBasicParsing
    Log-Bug "1.2 Wrong password login" "Allowed login with wrong password!" "CRITICAL" }
catch { if ([int]$_.Exception.Response.StatusCode -eq 401) { Log-Pass "1.2 Wrong password blocked" "Returns 401" } else { Log-Bug "1.2 Wrong password" "Got $([int]$_.Exception.Response.StatusCode) not 401" "MEDIUM" } }

# 1.3: No token
try { Invoke-WebRequest -Uri "$BASE/students" -UseBasicParsing
    Log-Bug "1.3 Unauthenticated access" "No token accepted!" "CRITICAL" }
catch { if ([int]$_.Exception.Response.StatusCode -in @(401,403)) { Log-Pass "1.3 No token blocked" "Returns $([int]$_.Exception.Response.StatusCode)" } else { Log-Info "1.3 No token" "Got $([int]$_.Exception.Response.StatusCode)"} }

# 1.4: Empty login body
try { $r = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{}' -ContentType "application/json" -UseBasicParsing
    $d = ($r.Content | ConvertFrom-Json); Log-Bug "1.4 Empty login body" "Status $($r.StatusCode) - Should reject" "MEDIUM" }
catch { Log-Pass "1.4 Empty login body rejected" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [2] SUPER ADMIN: SCHOOLS ---" -ForegroundColor Magenta

# 2.1: List schools
$r = Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers $H -UseBasicParsing
$allSchools = ($r.Content | ConvertFrom-Json)
Log-Pass "2.1 List schools" "Found $($allSchools.Count) schools"
$allSchools | Select-Object name, is_active | Format-Table -AutoSize | Out-Host

# 2.2: Toggle school active/inactive
try { 
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/schools/$SCHOOL_ID/toggle-active?is_active=false" -Method PATCH -Headers $H -UseBasicParsing
    $deact = ($r.Content | ConvertFrom-Json)
    # Toggle back
    Invoke-WebRequest -Uri "$BASE/superadmin/schools/$SCHOOL_ID/toggle-active?is_active=true" -Method PATCH -Headers $H -UseBasicParsing | Out-Null
    Log-Pass "2.2 Toggle school active/inactive" "Can deactivate and reactivate school"
} catch { Log-Bug "2.2 Toggle school" "Error: $($_)" "MEDIUM" }

# 2.3: Non-superadmin cannot list schools (using invalid token)
try { Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers @{"Authorization"="Bearer fake_token"} -UseBasicParsing
    Log-Bug "2.3 Unauthorized superadmin access" "Accepted fake token!" "CRITICAL" }
catch { Log-Pass "2.3 Unauthorized blocked" "$([int]$_.Exception.Response.StatusCode)" }

# 2.4: Toggle non-existent school
try { Invoke-WebRequest -Uri "$BASE/superadmin/schools/00000000-0000-0000-0000-000000000000/toggle-active?is_active=false" -Method PATCH -Headers $H -UseBasicParsing
    Log-Bug "2.4 Toggle non-existent school" "Should return 404" "MEDIUM" }
catch { $sc = [int]$_.Exception.Response.StatusCode; if ($sc -eq 404) { Log-Pass "2.4 Non-existent school 404" "Correctly returns 404" } else { Log-Info "2.4 Non-existent school" "Got $sc" } }

# =============================================
Write-Host "`n--- [3] SUBSCRIPTION PLANS ---" -ForegroundColor Magenta

# 3.1 List plans
$r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Headers $H -UseBasicParsing
$plans = ($r.Content | ConvertFrom-Json)
Log-Pass "3.1 List plans" "Found $($plans.Count) plans"

# 3.2 Create valid plan
$newPlanData = @{ name="QA Test Plan"; description="Plan for QA"; price=1999.99; max_students=1000; max_staff=100; features=@{attendance=$true;fees=$true;library=$false}; duration_days=365 }
try {
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Method POST -Headers $H -Body ($newPlanData | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    $np = ($r.Content | ConvertFrom-Json)
    $PLAN_ID = $np.id
    if ($r.StatusCode -eq 201) { Log-Pass "3.2 Create plan" "Created: $($np.name) - ID: $PLAN_ID" }
    else { Log-Bug "3.2 Create plan" "Got $($r.StatusCode) not 201" "LOW" }
} catch { Log-Bug "3.2 Create plan" "$($_)" "MEDIUM" }

# 3.3 BUG CHECK: Create plan with empty name
try {
    $badPlan = @{ name=""; price=100; max_students=10; max_staff=5; duration_days=30 }
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Method POST -Headers $H -Body ($badPlan | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "3.3 Empty plan name accepted" "Created plan with empty name! Status: $($r.StatusCode)" "MEDIUM"
} catch { Log-Pass "3.3 Empty plan name rejected" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 3.4 Create plan with negative price
try {
    $badPlan = @{ name="Negative Price Plan"; price=-500; max_students=10; max_staff=5; duration_days=30 }
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Method POST -Headers $H -Body ($badPlan | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "3.4 Negative price plan accepted" "Price=-500 accepted! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "3.4 Negative price rejected" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 3.5 Duplicate plan name
if ($PLAN_ID) {
    try {
        $dupPlan = @{ name="QA Test Plan"; price=999; max_students=100; max_staff=10; duration_days=100 }
        $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Method POST -Headers $H -Body ($dupPlan | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        Log-Bug "3.5 Duplicate plan name" "Allowed duplicate plan name" "LOW"
    } catch { Log-Pass "3.5 Duplicate plan name blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }
}

# Update plan
if ($PLAN_ID) {
    try {
        $upd = @{ name="QA Test Plan Updated"; price=2999.99; max_students=2000; max_staff=200; features=@{attendance=$true}; duration_days=730 }
        $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans/$PLAN_ID" -Method PUT -Headers $H -Body ($upd | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        Log-Pass "3.6 Update plan" "Updated to: $(($r.Content | ConvertFrom-Json).name)"
    } catch { Log-Bug "3.6 Update plan" "$($_)" "MEDIUM" }
}

# =============================================
Write-Host "`n--- [4] SUPERADMIN: FEATURE FLAGS ---" -ForegroundColor Magenta

# 4.1 Get feature flags
try {
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/schools/$SCHOOL_ID/features" -Headers $H -UseBasicParsing
    $flags = ($r.Content | ConvertFrom-Json)
    Log-Pass "4.1 Get feature flags" "Flags count: $($flags.Count)"
} catch { Log-Bug "4.1 Get feature flags" "$([int]$_.Exception.Response.StatusCode): $($_)" "HIGH" }

# 4.2 Set a feature flag (PUT not POST)
try {
    $flagData = @{ feature_key="library"; is_enabled=$true }
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/schools/$SCHOOL_ID/features" -Method PUT -Headers $H -Body ($flagData | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Pass "4.2 Set feature flag" "Status: $($r.StatusCode)"
} catch { Log-Bug "4.2 Set feature flag" "$([int]$_.Exception.Response.StatusCode): $($_)" "MEDIUM" }

# 4.3 Set feature flag for non-existent school
try {
    $flagData = @{ feature_key="library"; is_enabled=$true }
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/schools/00000000-0000-0000-0000-000000000000/features" -Method PUT -Headers $H -Body ($flagData | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "4.3 Feature flag on fake school" "Should be 404, got $($r.StatusCode)" "MEDIUM"
} catch { $sc=[int]$_.Exception.Response.StatusCode; if($sc -in @(404,400)){Log-Pass "4.3 Fake school feature flag" "Blocked: $sc"}else{Log-Info "4.3 Fake school flag" "Got $sc"} }

# =============================================
Write-Host "`n--- [5] SUBSCRIPTIONS ---" -ForegroundColor Magenta

# 5.1 List subscriptions
try {
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/subscriptions" -Headers $H -UseBasicParsing
    $subs = ($r.Content | ConvertFrom-Json)
    Log-Pass "5.1 List subscriptions" "Count: $($subs.Count)"
} catch { Log-Bug "5.1 List subscriptions" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 5.2 Create subscription for a school
if ($PLAN_ID) {
    try {
        $subData = @{ school_id=$SCHOOL_ID; plan_id=$PLAN_ID; start_date="2026-04-15"; end_date="2027-04-14" }
        $r = Invoke-WebRequest -Uri "$BASE/superadmin/subscriptions" -Method POST -Headers $H -Body ($subData | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        if ($r.StatusCode -in @(200,201)) {
            $SUB_ID = ($r.Content | ConvertFrom-Json).id
            Log-Pass "5.2 Create subscription" "Created subscription ID: $SUB_ID"
        }
    } catch { Log-Bug "5.2 Create subscription" "$([int]$_.Exception.Response.StatusCode): $($_)" "MEDIUM" }
}

# 5.3 Subscription with end before start date
try {
    $badSub = @{ school_id=$SCHOOL_ID; plan_id=$PLAN_ID; start_date="2026-12-01"; end_date="2026-01-01" }
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/subscriptions" -Method POST -Headers $H -Body ($badSub | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "5.3 Sub end before start" "Accepted invalid date range! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "5.3 Sub end before start blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [6] SCHOOLS MANAGEMENT ---" -ForegroundColor Magenta

# 6.1 List schools via schools endpoint
try {
    $r = Invoke-WebRequest -Uri "$BASE/schools" -Headers $H -UseBasicParsing
    Log-Pass "6.1 List schools endpoint" "Status: $($r.StatusCode)"
} catch { Log-Bug "6.1 Schools endpoint" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 6.2 Create a new school
try {
    $schoolData = @{ name="QA Test School"; code="QTS"; email="qa@testschool.com"; phone="9999999999"; address="123 Test Street"; city="TestCity"; state="TS"; country="India"; currency="INR" }
    $r = Invoke-WebRequest -Uri "$BASE/schools" -Method POST -Headers $H -Body ($schoolData | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    $NEW_SCHOOL_ID = ($r.Content | ConvertFrom-Json).id
    Log-Pass "6.2 Create school" "Created school ID: $NEW_SCHOOL_ID"
} catch { $sc=[int]$_.Exception.Response.StatusCode; if($sc -in @(400,403,409)){Log-Pass "6.2 Create school (blocked)" "Status: ${sc} - May need super admin"}else{Log-Bug "6.2 Create school" "${sc}: $_" "HIGH"} }

# 6.3 Create school with duplicate name
try {
    $dupSchool = @{ name="Demo High School"; code="DHS2"; email="dup@school.com"; phone="8888888888"; address="456 Dup St"; city="City"; state="ST"; country="India"; currency="INR" }
    $r = Invoke-WebRequest -Uri "$BASE/schools" -Method POST -Headers $H -Body ($dupSchool | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "6.3 Duplicate school name" "Status: $($r.StatusCode) - Allowed duplicate name!" "MEDIUM"
} catch { Log-Pass "6.3 Duplicate school name blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [7] ACADEMIC YEARS (with school context) ---" -ForegroundColor Magenta

# 7.1 List academic years
try {
    $r = Invoke-WebRequest -Uri "$BASE/academic-years" -Headers $HS -UseBasicParsing
    $years = ($r.Content | ConvertFrom-Json)
    $yearData = if ($years.data) { $years.data } elseif ($years -is [array]) { $years } else { @() }
    Log-Pass "7.1 List academic years" "Count: $($yearData.Count)"
    if ($yearData.Count -gt 0) { $YEAR_ID = $yearData[0].id; Write-Host "    Year: $($yearData[0].name)" -ForegroundColor DarkGray }
} catch { Log-Bug "7.1 List academic years" "$([int]$_.Exception.Response.StatusCode): $($_)" "HIGH" }

# 7.2 Create academic year
try {
    $yearData2 = @{ name="2027-2028"; start_date="2027-04-01"; end_date="2028-03-31"; is_active=$false }
    $r = Invoke-WebRequest -Uri "$BASE/academic-years" -Method POST -Headers $HS -Body ($yearData2 | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    if ($r.StatusCode -in @(200,201)) { $NEW_YEAR_ID = ($r.Content | ConvertFrom-Json).id; Log-Pass "7.2 Create academic year" "Created 2027-2028" }
    else { Log-Bug "7.2 Create academic year" "Got $($r.StatusCode)" "MEDIUM" }
} catch { Log-Bug "7.2 Create academic year" "$([int]$_.Exception.Response.StatusCode): $($_)" "HIGH" }

# 7.3 Create year with end before start
try {
    $badYear = @{ name="2029-Bad"; start_date="2029-12-31"; end_date="2029-01-01"; is_active=$false }
    $r = Invoke-WebRequest -Uri "$BASE/academic-years" -Method POST -Headers $HS -Body ($badYear | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "7.3 Year end before start" "Accepted invalid date range! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "7.3 Year end before start blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 7.4 Overlapping academic years 
if ($YEAR_ID) {
    try {
        $overlapYear = @{ name="Overlap Year"; start_date="2026-06-01"; end_date="2027-05-31"; is_active=$false }
        $r = Invoke-WebRequest -Uri "$BASE/academic-years" -Method POST -Headers $HS -Body ($overlapYear | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        Log-Bug "7.4 Overlapping academic year" "Accepted overlapping dates! Status: $($r.StatusCode)" "HIGH"
    } catch { Log-Pass "7.4 Overlapping year blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }
}

# =============================================
Write-Host "`n--- [8] CLASSES & SECTIONS (with school context) ---" -ForegroundColor Magenta

# 8.1 List classes
try {
    $r = Invoke-WebRequest -Uri "$BASE/classes" -Headers $HS -UseBasicParsing
    $classes = ($r.Content | ConvertFrom-Json)
    $classData = if ($classes.data) { $classes.data } elseif ($classes -is [array]) { $classes } else { @() }
    Log-Pass "8.1 List classes" "Count: $($classData.Count)"
    if ($classData.Count -gt 0) { $CLASS_ID = $classData[0].id; Write-Host "    Class: $($classData[0].name)" -ForegroundColor DarkGray }
} catch { Log-Bug "8.1 List classes" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 8.2 Create class
try {
    if ($YEAR_ID) {
        $clsData = @{ name="QA Class 12"; academic_year_id=$YEAR_ID; order_index=12 }
        $r = Invoke-WebRequest -Uri "$BASE/classes" -Method POST -Headers $HS -Body ($clsData | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        $NEW_CLASS_ID = ($r.Content | ConvertFrom-Json).id
        Log-Pass "8.2 Create class" "Created QA Class 12"
    } else { Log-Info "8.2 Create class" "Skipped - no year ID" }
} catch { Log-Bug "8.2 Create class" "$([int]$_.Exception.Response.StatusCode): $($_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [9] SUBJECTS (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/subjects" -Headers $HS -UseBasicParsing
    $subjects = ($r.Content | ConvertFrom-Json)
    $subjData = if ($subjects.data) { $subjects.data } elseif ($subjects -is [array]) { $subjects } else { @() }
    Log-Pass "9.1 List subjects" "Count: $($subjData.Count)"
    if ($subjData.Count -gt 0) { $SUBJECT_ID = $subjData[0].id }
} catch { Log-Bug "9.1 List subjects" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [10] STUDENTS (with school context) ---" -ForegroundColor Magenta

# 10.1 List students
try {
    $r = Invoke-WebRequest -Uri "$BASE/students" -Headers $HS -UseBasicParsing
    $studs = ($r.Content | ConvertFrom-Json)
    $studData = if ($studs.data) { $studs.data } elseif ($studs -is [array]) { $studs } else { @() }
    Log-Pass "10.1 List students" "Count: $($studData.Count)"
    if ($studData.Count -gt 0) { $STUDENT_ID = $studData[0].id; Write-Host "    Student: $($studData[0].first_name) $($studData[0].last_name)" -ForegroundColor DarkGray }
} catch { Log-Bug "10.1 List students" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# 10.2 Get single student
if ($STUDENT_ID) {
    try {
        $r = Invoke-WebRequest -Uri "$BASE/students/$STUDENT_ID" -Headers $HS -UseBasicParsing
        Log-Pass "10.2 Get student by ID" "Status: $($r.StatusCode)"
    } catch { Log-Bug "10.2 Get student by ID" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }
}

# 10.3 Get non-existent student
try {
    Invoke-WebRequest -Uri "$BASE/students/00000000-0000-0000-0000-000000000000" -Headers $HS -UseBasicParsing
    Log-Bug "10.3 Non-existent student" "Should return 404" "MEDIUM"
} catch { $sc=[int]$_.Exception.Response.StatusCode; if($sc -eq 404){Log-Pass "10.3 404 for non-existent student" "Correctly 404"}else{Log-Info "10.3 Non-existent student" "Got $sc"} }

# 10.4 Create student with XSS payload
try {
    $xssStudent = @{ 
        first_name='<script>alert(1)</script>'; last_name="Test"; 
        date_of_birth="2010-01-01"; gender="male"; enrollment_number="XSS001"
        academic_year_id=$YEAR_ID
    }
    $r = Invoke-WebRequest -Uri "$BASE/students" -Method POST -Headers $HS -Body ($xssStudent | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    $created = ($r.Content | ConvertFrom-Json)
    if ($created.data.first_name -like "*<script>*") {
        Log-Bug "10.4 XSS in student name stored" "XSS payload stored as-is!" "HIGH"
    } else { Log-Pass "10.4 XSS in student name" "Sanitized or accepted safely: $($created.data.first_name)" }
} catch { Log-Bug "10.4 Create student" "$([int]$_.Exception.Response.StatusCode): $($_)" "LOW" }

# 10.5 Create student with invalid date of birth (future)
try {
    $futureStud = @{ first_name="Future"; last_name="Student"; date_of_birth="2099-12-31"; gender="male"; enrollment_number="FUTURE001"; academic_year_id=$YEAR_ID }
    $r = Invoke-WebRequest -Uri "$BASE/students" -Method POST -Headers $HS -Body ($futureStud | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "10.5 Future DOB accepted" "Student with DOB 2099 created! Status: $($r.StatusCode)" "MEDIUM"
} catch { Log-Pass "10.5 Future DOB rejected" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 10.6 Duplicate enrollment number
if ($studData -and $studData.Count -gt 0) {
    $existingEnroll = $studData[0].enrollment_number
    try {
        $dupStud = @{ first_name="Dup"; last_name="Student"; date_of_birth="2010-06-15"; gender="female"; enrollment_number=$existingEnroll; academic_year_id=$YEAR_ID }
        $r = Invoke-WebRequest -Uri "$BASE/students" -Method POST -Headers $HS -Body ($dupStud | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        Log-Bug "10.6 Duplicate enrollment" "Allowed duplicate enrollment number $existingEnroll! Status: $($r.StatusCode)" "HIGH"
    } catch { Log-Pass "10.6 Duplicate enrollment blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }
}

# =============================================
Write-Host "`n--- [11] STAFF (with school context) ---" -ForegroundColor Magenta

# 11.1 List staff
try {
    $r = Invoke-WebRequest -Uri "$BASE/staff" -Headers $HS -UseBasicParsing
    $staffList = ($r.Content | ConvertFrom-Json)
    $staffData = if ($staffList.data) { $staffList.data } elseif ($staffList -is [array]) { $staffList } else { @() }
    Log-Pass "11.1 List staff" "Count: $($staffData.Count)"
    if ($staffData.Count -gt 0) { $STAFF_ID = $staffData[0].id; Write-Host "    Staff: $($staffData[0].first_name)" -ForegroundColor DarkGray }
} catch { Log-Bug "11.1 List staff" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# 11.2 Create staff with invalid email
try {
    $badStaff = @{ first_name="Bad"; last_name="Email"; email="not-an-email"; phone="1234567890"; employee_id="EMP999"; role="teacher"; joining_date="2026-01-01" }
    $r = Invoke-WebRequest -Uri "$BASE/staff" -Method POST -Headers $HS -Body ($badStaff | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "11.2 Invalid email accepted" "Staff created with invalid email! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "11.2 Invalid email blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 11.3 List leaves
try {
    $r = Invoke-WebRequest -Uri "$BASE/leaves" -Headers $HS -UseBasicParsing
    Log-Pass "11.3 List leaves" "Status: $($r.StatusCode)"
} catch { Log-Bug "11.3 List leaves" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 11.4 List payroll
try {
    $r = Invoke-WebRequest -Uri "$BASE/payroll" -Headers $HS -UseBasicParsing
    Log-Pass "11.4 List payroll" "Status: $($r.StatusCode)"
} catch { Log-Bug "11.4 List payroll" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [12] ATTENDANCE (with school context) ---" -ForegroundColor Magenta

# 12.1 List attendance (need class-based query)
try {
    $r = Invoke-WebRequest -Uri "$BASE/attendance?date=2026-04-15" -Headers $HS -UseBasicParsing
    Log-Pass "12.1 List attendance" "Status: $($r.StatusCode)"
} catch { Log-Bug "12.1 List attendance" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 12.2 Staff attendance
try {
    $r = Invoke-WebRequest -Uri "$BASE/staff-attendance" -Headers $HS -UseBasicParsing
    Log-Pass "12.2 Staff attendance" "Status: $($r.StatusCode)"
} catch { Log-Bug "12.2 Staff attendance" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 12.3 Holidays
try {
    $r = Invoke-WebRequest -Uri "$BASE/holidays" -Headers $HS -UseBasicParsing
    $hols = ($r.Content | ConvertFrom-Json)
    $holData = if ($hols.data) { $hols.data } elseif ($hols -is [array]) { $hols } else { @() }
    Log-Pass "12.3 List holidays" "Count: $($holData.Count)"
} catch { Log-Bug "12.3 List holidays" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [13] FEES (with school context) ---" -ForegroundColor Magenta

# 13.1 List fee structures
try {
    $r = Invoke-WebRequest -Uri "$BASE/fees/structures" -Headers $HS -UseBasicParsing
    $feeStructs = ($r.Content | ConvertFrom-Json)
    $feeData = if ($feeStructs.data) { $feeStructs.data } elseif ($feeStructs -is [array]) { $feeStructs } else { @() }
    Log-Pass "13.1 List fee structures" "Count: $($feeData.Count)"
    if ($feeData.Count -gt 0) { $FEE_STRUCT_ID = $feeData[0].id }
} catch { Log-Bug "13.1 List fee structures" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# 13.2 Fee collections
try {
    $r = Invoke-WebRequest -Uri "$BASE/fees/collections" -Headers $HS -UseBasicParsing
    $fc = ($r.Content | ConvertFrom-Json)
    $fcData = if ($fc.data) { $fc.data } elseif ($fc -is [array]) { $fc } else { @() }
    Log-Pass "13.2 Fee collections" "Count: $($fcData.Count)"
} catch { Log-Bug "13.2 Fee collections" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 13.3 Create fee with negative amount
try {
    $negFee = @{ name="Negative Fee"; amount=-1000; fee_type="tuition" }
    $r = Invoke-WebRequest -Uri "$BASE/fees/structures" -Method POST -Headers $HS -Body ($negFee | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "13.3 Negative fee amount" "Accepted fee with amount=-1000! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "13.3 Negative fee blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 13.4 Fee discount > 100%
try {
    $bigDisc = @{ student_id="00000000-0000-0000-0000-000000000000"; discount_percentage=150; reason="Test" }
    $r = Invoke-WebRequest -Uri "$BASE/fees/discounts" -Method POST -Headers $HS -Body ($bigDisc | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "13.4 Discount > 100%" "Accepted 150% discount! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "13.4 Discount >100% blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [14] EXAMS (with school context) ---" -ForegroundColor Magenta

# 14.1 List exam types
try {
    $r = Invoke-WebRequest -Uri "$BASE/exam-types" -Headers $HS -UseBasicParsing
    $et = ($r.Content | ConvertFrom-Json)
    $etData = if ($et.data) { $et.data } elseif ($et -is [array]) { $et } else { @() }
    Log-Pass "14.1 List exam types" "Count: $($etData.Count)"
} catch { Log-Bug "14.1 Exam types" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 14.2 List grading scales
try {
    $r = Invoke-WebRequest -Uri "$BASE/grading-scales" -Headers $HS -UseBasicParsing
    Log-Pass "14.2 Grading scales" "Status: $($r.StatusCode)"
} catch { Log-Bug "14.2 Grading scales" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 14.3 List exams
try {
    $r = Invoke-WebRequest -Uri "$BASE/exams" -Headers $HS -UseBasicParsing
    $exams = ($r.Content | ConvertFrom-Json)
    $examData = if ($exams.data) { $exams.data } elseif ($exams -is [array]) { $exams } else { @() }
    Log-Pass "14.3 List exams" "Count: $($examData.Count)"
    if ($examData.Count -gt 0) { $EXAM_ID = $examData[0].id }
} catch { Log-Bug "14.3 List exams" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# 14.4 Marks > max marks validation
try {
    $badResult = @{ student_id="00000000-0000-0000-0000-000000000000"; exam_id="00000000-0000-0000-0000-000000000000"; marks_obtained=200; max_marks=100 }
    $r = Invoke-WebRequest -Uri "$BASE/exams/results" -Method POST -Headers $HS -Body ($badResult | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "14.4 Marks > max_marks" "Accepted marks=200 > max=100! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "14.4 Marks > max_marks blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [15] TRANSPORT (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/transport/vehicles" -Headers $HS -UseBasicParsing
    $veh = ($r.Content | ConvertFrom-Json)
    $vehData = if ($veh.data) { $veh.data } elseif ($veh -is [array]) { $veh } else { @() }
    Log-Pass "15.1 List vehicles" "Count: $($vehData.Count)"
} catch { Log-Bug "15.1 List vehicles" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/transport/routes" -Headers $HS -UseBasicParsing
    $routes = ($r.Content | ConvertFrom-Json)
    $routeData = if ($routes.data) { $routes.data } elseif ($routes -is [array]) { $routes } else { @() }
    Log-Pass "15.2 List routes" "Count: $($routeData.Count)"
} catch { Log-Bug "15.2 List routes" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/transport" -Headers $HS -UseBasicParsing
    Log-Pass "15.3 Transport assignments" "Status: $($r.StatusCode)"
} catch { Log-Bug "15.3 Transport" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 15.4 Vehicle capacity = 0
try {
    $zeroCapVeh = @{ registration_number="ZZ0000"; vehicle_type="bus"; capacity=0; driver_name="Test Driver" }
    $r = Invoke-WebRequest -Uri "$BASE/transport/vehicles" -Method POST -Headers $HS -Body ($zeroCapVeh | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "15.4 Vehicle capacity=0" "Accepted vehicle with 0 capacity! Status: $($r.StatusCode)" "MEDIUM"
} catch { Log-Pass "15.4 Zero capacity blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [16] LIBRARY (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/library/categories" -Headers $HS -UseBasicParsing
    Log-Pass "16.1 Library categories" "Status: $($r.StatusCode)"
} catch { Log-Bug "16.1 Library categories" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/library/books" -Headers $HS -UseBasicParsing
    $books = ($r.Content | ConvertFrom-Json)
    $bookData = if ($books.data) { $books.data } elseif ($books -is [array]) { $books } else { @() }
    Log-Pass "16.2 List books" "Count: $($bookData.Count)"
    if ($bookData.Count -gt 0) { $BOOK_ID = $bookData[0].id }
} catch { Log-Bug "16.2 List books" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/library/members" -Headers $HS -UseBasicParsing
    Log-Pass "16.3 Library members" "Status: $($r.StatusCode)"
} catch { Log-Bug "16.3 Library members" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/library/issues" -Headers $HS -UseBasicParsing
    Log-Pass "16.4 Book issues" "Status: $($r.StatusCode)"
} catch { Log-Bug "16.4 Book issues" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 16.5 Issue book with past due date
try {
    $pastDue = @{ book_id="00000000-0000-0000-0000-000000000000"; member_id="00000000-0000-0000-0000-000000000000"; due_date="2020-01-01" }
    $r = Invoke-WebRequest -Uri "$BASE/library/issues" -Method POST -Headers $HS -Body ($pastDue | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "16.5 Past due date accepted" "Issued book with past due date 2020-01-01! Status: $($r.StatusCode)" "MEDIUM"
} catch { Log-Pass "16.5 Past due date blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [17] INVENTORY (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/inventory/categories" -Headers $HS -UseBasicParsing
    Log-Pass "17.1 Inventory categories" "Status: $($r.StatusCode)"
} catch { Log-Bug "17.1 Inventory categories" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/inventory/items" -Headers $HS -UseBasicParsing
    $items = ($r.Content | ConvertFrom-Json)
    $itemData = if ($items.data) { $items.data } elseif ($items -is [array]) { $items } else { @() }
    Log-Pass "17.2 List items" "Count: $($itemData.Count)"
} catch { Log-Bug "17.2 Inventory items" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/inventory/suppliers" -Headers $HS -UseBasicParsing
    Log-Pass "17.3 Suppliers" "Status: $($r.StatusCode)"
} catch { Log-Bug "17.3 Suppliers" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 17.4 Negative quantity
try {
    $negItem = @{ name="Negative Item"; quantity=-50; unit_price=10 }
    $r = Invoke-WebRequest -Uri "$BASE/inventory/items" -Method POST -Headers $HS -Body ($negItem | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "17.4 Negative quantity" "Accepted qty=-50! Status: $($r.StatusCode)" "HIGH"
} catch { Log-Pass "17.4 Negative quantity blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [18] ACCOUNTING (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/income-categories" -Headers $HS -UseBasicParsing
    Log-Pass "18.1 Income categories" "Status: $($r.StatusCode)"
} catch { Log-Bug "18.1 Income categories" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/expense-categories" -Headers $HS -UseBasicParsing
    Log-Pass "18.2 Expense categories" "Status: $($r.StatusCode)"
} catch { Log-Bug "18.2 Expense categories" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/income" -Headers $HS -UseBasicParsing
    Log-Pass "18.3 Income records" "Status: $($r.StatusCode)"
} catch { Log-Bug "18.3 Income" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/expenses" -Headers $HS -UseBasicParsing
    Log-Pass "18.4 Expense records" "Status: $($r.StatusCode)"
} catch { Log-Bug "18.4 Expenses" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/budgets" -Headers $HS -UseBasicParsing
    Log-Pass "18.5 Budgets" "Status: $($r.StatusCode)"
} catch { Log-Bug "18.5 Budgets" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/summary" -Headers $HS -UseBasicParsing
    Log-Pass "18.6 Accounting summary" "Status: $($r.StatusCode)"
} catch { Log-Bug "18.6 Accounting summary" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [19] COMMUNICATION (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/announcements" -Headers $HS -UseBasicParsing
    $anns = ($r.Content | ConvertFrom-Json)
    $annData = if ($anns.data) { $anns.data } elseif ($anns -is [array]) { $anns } else { @() }
    Log-Pass "19.1 Announcements" "Count: $($annData.Count)"
} catch { Log-Bug "19.1 Announcements" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/notifications" -Headers $HS -UseBasicParsing
    Log-Pass "19.2 Notifications" "Status: $($r.StatusCode)"
} catch { Log-Bug "19.2 Notifications" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/communications/templates" -Headers $HS -UseBasicParsing
    Log-Pass "19.3 Comm templates" "Status: $($r.StatusCode)"
} catch { Log-Bug "19.3 Comm templates" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 19.4 Send empty announcement
try {
    $emptyAnn = @{ title=""; body="" }
    $r = Invoke-WebRequest -Uri "$BASE/announcements" -Method POST -Headers $HS -Body ($emptyAnn | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "19.4 Empty announcement" "Accepted empty title/body! Status: $($r.StatusCode)" "MEDIUM"
} catch { Log-Pass "19.4 Empty announcement blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
Write-Host "`n--- [20] CALENDAR (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/calendar" -Headers $HS -UseBasicParsing
    Log-Pass "20.1 Calendar" "Status: $($r.StatusCode)"
} catch { 
    # try with /events
    try { 
        $r = Invoke-WebRequest -Uri "$BASE/calendar/events" -Headers $HS -UseBasicParsing
        Log-Pass "20.1 Calendar events" "Status: $($r.StatusCode)"
    } catch { Log-Bug "20.1 Calendar" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" } 
}

# =============================================
Write-Host "`n--- [21] HOMEWORK & PTM (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/homework" -Headers $HS -UseBasicParsing
    $hw = ($r.Content | ConvertFrom-Json)
    $hwData = if ($hw.data) { $hw.data } elseif ($hw -is [array]) { $hw } else { @() }
    Log-Pass "21.1 Homework" "Count: $($hwData.Count)"
} catch { Log-Bug "21.1 Homework" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/lesson-plans" -Headers $HS -UseBasicParsing
    Log-Pass "21.2 Lesson plans" "Status: $($r.StatusCode)"
} catch { Log-Bug "21.2 Lesson plans" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/ptm" -Headers $HS -UseBasicParsing
    Log-Pass "21.3 PTM meetings" "Status: $($r.StatusCode)"
} catch { Log-Bug "21.3 PTM" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [22] DOCUMENT TEMPLATES (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/document-templates" -Headers $HS -UseBasicParsing
    $dt = ($r.Content | ConvertFrom-Json)
    $dtData = if ($dt.data) { $dt.data } elseif ($dt -is [array]) { $dt } else { @() }
    Log-Pass "22.1 Document templates" "Count: $($dtData.Count)"
} catch { Log-Bug "22.1 Document templates" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [23] AUDIT LOGS (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/audit-logs" -Headers $HS -UseBasicParsing
    $al = ($r.Content | ConvertFrom-Json)
    $alData = if ($al.data) { $al.data } elseif ($al -is [array]) { $al } else { @() }
    Log-Pass "23.1 Audit logs" "Count: $($alData.Count)"
} catch { Log-Bug "23.1 Audit logs" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# =============================================
Write-Host "`n--- [24] SETTINGS (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/settings" -Headers $HS -UseBasicParsing
    Log-Pass "24.1 Settings" "Status: $($r.StatusCode)"
} catch { Log-Bug "24.1 Settings" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# =============================================
Write-Host "`n--- [25] DASHBOARD (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/dashboard" -Headers $HS -UseBasicParsing
    Log-Pass "25.1 Dashboard" "Status: $($r.StatusCode)"
} catch { 
    try {
        $r = Invoke-WebRequest -Uri "$BASE/dashboard/overview" -Headers $HS -UseBasicParsing
        Log-Pass "25.1 Dashboard overview" "Status: $($r.StatusCode)"
    } catch { Log-Bug "25.1 Dashboard" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }
}

# =============================================
Write-Host "`n--- [26] REPORTS (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/reports" -Headers $HS -UseBasicParsing
    Log-Pass "26.1 Reports" "Status: $($r.StatusCode)"
} catch { Log-Bug "26.1 Reports" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [27] ROLES & PERMISSIONS (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/roles" -Headers $HS -UseBasicParsing
    $roles = ($r.Content | ConvertFrom-Json)
    $roleData = if ($roles.data) { $roles.data } elseif ($roles -is [array]) { $roles } else { @() }
    Log-Pass "27.1 List roles" "Count: $($roleData.Count)"
    if ($roleData.Count -gt 0) { $ROLE_ID = $roleData[0].id }
} catch { Log-Bug "27.1 List roles" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

try {
    $r = Invoke-WebRequest -Uri "$BASE/permissions" -Headers $H -UseBasicParsing
    Log-Pass "27.2 List permissions" "Status: $($r.StatusCode)"
} catch { Log-Bug "27.2 Permissions" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 27.3 Create role with no permissions
try {
    $emptyRole = @{ name="Empty Role"; permissions=@() }
    $r = Invoke-WebRequest -Uri "$BASE/roles" -Method POST -Headers $HS -Body ($emptyRole | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    $newRole = ($r.Content | ConvertFrom-Json)
    $NEW_ROLE_ID = if ($newRole.data) { $newRole.data.id } else { $newRole.id }
    Log-Pass "27.3 Create role (no perms)" "Created: $NEW_ROLE_ID"
} catch { Log-Bug "27.3 Create empty role" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# 27.4 Delete non-existent role
try {
    Invoke-WebRequest -Uri "$BASE/roles/00000000-0000-0000-0000-000000000000" -Method DELETE -Headers $HS -UseBasicParsing
    Log-Bug "27.4 Delete fake role" "No 404 returned" "MEDIUM"
} catch { $sc=[int]$_.Exception.Response.StatusCode; if($sc -eq 404){Log-Pass "27.4 Delete fake role 404" "Correctly 404"}else{Log-Info "27.4 Delete fake" "Got $sc"} }

# =============================================
Write-Host "`n--- [28] ADMISSIONS (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/admissions" -Headers $HS -UseBasicParsing
    $adm = ($r.Content | ConvertFrom-Json)
    $admData = if ($adm.data) { $adm.data } elseif ($adm -is [array]) { $adm } else { @() }
    Log-Pass "28.1 List admissions" "Count: $($admData.Count)"
} catch { Log-Bug "28.1 Admissions" "$([int]$_.Exception.Response.StatusCode)" "HIGH" }

# =============================================
Write-Host "`n--- [29] TIMETABLE (with school context) ---" -ForegroundColor Magenta

try {
    $r = Invoke-WebRequest -Uri "$BASE/timetable" -Headers $HS -UseBasicParsing
    Log-Pass "29.1 Timetable" "Status: $($r.StatusCode)"
} catch { Log-Bug "29.1 Timetable" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }

# =============================================
Write-Host "`n--- [30] SECURITY EDGE CASES ---" -ForegroundColor Magenta

# 30.1 IDOR: Can super admin access one school's data via another school's ID?
$SECOND_SCHOOL_ID = if ($allSchools.Count -gt 1) { $allSchools[1].id } else { $null }
if ($SECOND_SCHOOL_ID) {
    try {
        $HS2 = @{ "Authorization" = "Bearer $TOKEN"; "X-School-Id" = $SECOND_SCHOOL_ID }
        $r = Invoke-WebRequest -Uri "$BASE/students" -Headers $HS2 -UseBasicParsing
        $s2 = ($r.Content | ConvertFrom-Json)
        $s2Data = if ($s2.data) { $s2.data } elseif ($s2 -is [array]) { $s2 } else { @() }
        Log-Info "30.1 Cross-school data access" "School 2 students: $($s2Data.Count) - Super admin can see all schools"
    } catch { Log-Bug "30.1 Cross-school access" "$([int]$_.Exception.Response.StatusCode)" "MEDIUM" }
}

# 30.2 SQL Injection in search param
try {
    $r = Invoke-WebRequest -Uri "$BASE/students?search='; DROP TABLE students; --" -Headers $HS -UseBasicParsing
    Log-Info "30.2 SQL Injection in search" "Returned $($r.StatusCode) - check if query executed safely"
} catch { Log-Pass "30.2 SQLi in search blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 30.3 Very large pagination limit
try {
    $r = Invoke-WebRequest -Uri "$BASE/students?page=1&per_page=100000" -Headers $HS -UseBasicParsing
    $bigResp = ($r.Content | ConvertFrom-Json)
    $bigData = if ($bigResp.data) { $bigResp.data } elseif ($bigResp -is [array]) { $bigResp } else { @() }
    Log-Info "30.3 Large per_page=100000" "Returned $($bigData.Count) records - check if capped"
} catch { Log-Pass "30.3 Large pagination blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 30.4 Negative page number
try {
    $r = Invoke-WebRequest -Uri "$BASE/students?page=-1" -Headers $HS -UseBasicParsing
    Log-Info "30.4 Negative page number" "Status: $($r.StatusCode)"
} catch { Log-Pass "30.4 Negative page blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 30.5 Upload endpoint with non-file content type
try {
    $r = Invoke-WebRequest -Uri "$BASE/students" -Method POST -Headers $HS -Body "NOT JSON AT ALL" -ContentType "text/plain" -UseBasicParsing
    Log-Bug "30.5 Plain text body accepted" "Returned $($r.StatusCode)" "LOW"
} catch { Log-Pass "30.5 Non-JSON body blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 30.6 Extremely long string field
try {
    $longStr = "A" * 10000
    $longStud = @{ first_name=$longStr; last_name="Test"; date_of_birth="2010-01-01"; gender="male"; enrollment_number="LONG001" }
    $r = Invoke-WebRequest -Uri "$BASE/students" -Method POST -Headers $HS -Body ($longStud | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    Log-Bug "30.6 Extremely long string" "Accepted 10000-char first_name! Status: $($r.StatusCode)" "MEDIUM"
} catch { Log-Pass "30.6 Long string blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# 30.7 Access super admin endpoints as regular user (using wrong token type)
# Super admin trying school staff endpoints
try {
    $adminBody = '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}'
    $r = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $adminBody -ContentType "application/json" -UseBasicParsing | ConvertFrom-Json
    Log-Info "30.7 Token scope" "Super admin logged in, school_id=null in JWT: $($r.data.user.school_id -eq $null)"
} catch { Log-Info "30.7 Token check" "Could not verify" }

# 30.8 Mass assignment - try to set is_super_admin via profile update
try {
    $r = Invoke-WebRequest -Uri "$BASE/auth/me" -Method PATCH -Headers $H -Body '{"is_super_admin":false,"username":"hacked"}' -ContentType "application/json" -UseBasicParsing
    $upd = ($r.Content | ConvertFrom-Json)
    Log-Bug "30.8 Mass assignment profile" "Accepted is_super_admin=false in PATCH /me! Status: $($r.StatusCode)" "CRITICAL"
} catch { Log-Pass "30.8 Mass assignment blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }

# =============================================
# SUPERADMIN IMPERSONATION TEST
# =============================================
Write-Host "`n--- [31] IMPERSONATION ---" -ForegroundColor Magenta

# 31.1 Start impersonation - need a valid user in the school
try {
    $impReq = @{ school_id=$SCHOOL_ID; user_id="00000000-0000-0000-0000-000000000000" }
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/impersonate" -Method POST -Headers $H -Body ($impReq | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
    $imp = ($r.Content | ConvertFrom-Json)
    $IMP_ID = if ($imp.id) { $imp.id } else { $null }
    Log-Pass "31.1 Start impersonation" "Created log: $IMP_ID"
} catch { $sc=[int]$_.Exception.Response.StatusCode; if($sc -eq 404){Log-Pass "31.1 Impersonate fake user 404" "Correctly 404"}else{Log-Info "31.1 Impersonation" "Got $sc"} }

# =============================================
# TIMETABLE CONFLICT TEST
# =============================================
Write-Host "`n--- [32] TIMETABLE CONFLICTS ---" -ForegroundColor Magenta
if ($CLASS_ID -and $SUBJECT_ID) {
    try {
        # Try to create two timetable entries for same class/day/period
        $tt1 = @{ class_id=$CLASS_ID; subject_id=$SUBJECT_ID; day_of_week="monday"; period=1; start_time="08:00"; end_time="09:00"; academic_year_id=$YEAR_ID }
        $r1 = Invoke-WebRequest -Uri "$BASE/timetable" -Method POST -Headers $HS -Body ($tt1 | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        $tt2 = @{ class_id=$CLASS_ID; subject_id=$SUBJECT_ID; day_of_week="monday"; period=1; start_time="08:30"; end_time="09:30"; academic_year_id=$YEAR_ID }
        $r2 = Invoke-WebRequest -Uri "$BASE/timetable" -Method POST -Headers $HS -Body ($tt2 | ConvertTo-Json -Compress) -ContentType "application/json" -UseBasicParsing
        Log-Bug "32.1 Timetable conflict" "Allowed two entries for same class/day/period!" "HIGH"
    } catch { Log-Pass "32.1 Timetable conflict blocked" "Status: $([int]$_.Exception.Response.StatusCode)" }
} else { Log-Info "32.1 Timetable conflict" "Skipped - missing class_id or subject_id" }

# =============================================
# FINAL SUMMARY
# =============================================
Write-Host "`n`n========================================" -ForegroundColor Cyan
Write-Host "  TEST RESULTS SUMMARY" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Total PASS: $($PASSES.Count)" -ForegroundColor Green
Write-Host "  Total BUGS: $($BUGS.Count)" -ForegroundColor Red
Write-Host "  Total INFO: $($INFOS.Count)" -ForegroundColor Yellow
Write-Host ""

Write-Host "BUGS FOUND:" -ForegroundColor Red
$BUGS | Sort-Object Severity | Format-Table Test, Severity, Detail -AutoSize -Wrap

Write-Host "`nINFO / OBSERVATIONS:" -ForegroundColor Yellow
$INFOS | Format-Table Test, Detail -AutoSize -Wrap

Write-Host "`nALL PASSES:" -ForegroundColor Green
$PASSES | Format-Table Test, Detail -AutoSize -Wrap
