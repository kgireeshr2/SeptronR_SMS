# SMS Application - Full QA Test Suite (Fixed Script)
param()
$ErrorActionPreference = "Continue"

$BASE = "http://localhost:8000/api/v1"
$BUGS  = [System.Collections.ArrayList]::new()
$PASSES = [System.Collections.ArrayList]::new()
$INFOS = [System.Collections.ArrayList]::new()

function pass_log($test, $detail) {
    [void]$BUGS  # suppress ref
    $null = $script:PASSES.Add([PSCustomObject]@{Test=$test;Detail=$detail})
    Write-Host "  [PASS] $test - $detail" -ForegroundColor Green
}
function bug_log($test, $detail, $sev="HIGH") {
    $null = $script:BUGS.Add([PSCustomObject]@{Test=$test;Detail=$detail;Sev=$sev})
    Write-Host "  [BUG-$sev] $test : $detail" -ForegroundColor Red
}
function info_log($test, $detail) {
    $null = $script:INFOS.Add([PSCustomObject]@{Test=$test;Detail=$detail})
    Write-Host "  [INFO] $test - $detail" -ForegroundColor Yellow
}

function api_get($url, $h) {
    try { return Invoke-WebRequest -Uri "$BASE$url" -Headers $h -UseBasicParsing -ErrorAction Stop }
    catch { throw $_ }
}
function api_post($url, $h, $body) {
    try {
        $b = if ($body -is [hashtable] -or $body -is [PSCustomObject]) { $body | ConvertTo-Json -Compress -Depth 10 } else { $body }
        return Invoke-WebRequest -Uri "$BASE$url" -Method POST -Headers $h -Body $b -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    } catch { throw $_ }
}
function api_put($url, $h, $body) {
    try {
        $b = if ($body -is [hashtable] -or $body -is [PSCustomObject]) { $body | ConvertTo-Json -Compress -Depth 10 } else { $body }
        return Invoke-WebRequest -Uri "$BASE$url" -Method PUT -Headers $h -Body $b -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    } catch { throw $_ }
}
function api_patch($url, $h, $body) {
    try {
        $b = if ($body) { if ($body -is [hashtable] -or $body -is [PSCustomObject]) { $body | ConvertTo-Json -Compress -Depth 10 } else { $body } } else { $null }
        $params = @{ Uri="$BASE$url"; Method="PATCH"; Headers=$h; UseBasicParsing=$true; ErrorAction="Stop" }
        if ($b) { $params.Body=$b; $params.ContentType="application/json" }
        return Invoke-WebRequest @params
    } catch { throw $_ }
}
function api_delete($url, $h) {
    try { return Invoke-WebRequest -Uri "$BASE$url" -Method DELETE -Headers $h -UseBasicParsing -ErrorAction Stop }
    catch { throw $_ }
}
function status_code($ex) { try { return [int]$ex.Exception.Response.StatusCode } catch { return 0 } }
function jsc($r) { try { return ($r.Content | ConvertFrom-Json) } catch { return $null } }

# =============================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  SMS APPLICATION - FULL QA TEST SUITE" -ForegroundColor Cyan
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "  Target: http://localhost:8000" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# LOGIN
Write-Host "`nAuthenticating..." -ForegroundColor Yellow
$lBody = '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}'
$lR = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $lBody -ContentType "application/json" -UseBasicParsing
$lDat = ($lR.Content | ConvertFrom-Json).data
$TOKEN = $lDat.access_token
$H = @{ "Authorization" = "Bearer $TOKEN" }
Write-Host "  Logged in: $($lDat.user.email) | is_super_admin=$($lDat.user.is_super_admin)" -ForegroundColor Cyan

# GET SCHOOL
$schools = (Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers $H -UseBasicParsing | ConvertFrom-Json)
$SCHOOL_ID = $schools[0].id
$SCHOOL_NAME = $schools[0].name
$HS = @{ "Authorization" = "Bearer $TOKEN"; "X-School-Id" = $SCHOOL_ID }
Write-Host "  School: $SCHOOL_NAME ($SCHOOL_ID)" -ForegroundColor Cyan
Write-Host "  Total schools in system: $($schools.Count)" -ForegroundColor Cyan

# =============================================
Write-Host "`n--- [1] AUTHENTICATION ---" -ForegroundColor Magenta

# GET /me
$r = api_get "/auth/me" $H
$u = (jsc $r).data
if ($r.StatusCode -eq 200 -and $u.is_super_admin) { pass_log "1.1 GET /auth/me" "Email=$($u.email) is_super_admin=True" }
else { bug_log "1.1 GET /auth/me" "Unexpected response $($r.StatusCode)" }

# No token -> 401
try { api_get "/auth/me" @{} ; bug_log "1.2 No auth header" "Should be 401 but succeeded!" "CRITICAL" }
catch { if ((status_code $_) -in @(401,403)) { pass_log "1.2 No auth blocked" "$(status_code $_)" } else { info_log "1.2 No auth" "Got $(status_code $_)" } }

# Wrong password
try { api_post "/auth/login" @{} '{"identifier":"superadmin@sms.com","password":"WRONG123"}' ; bug_log "1.3 Wrong password" "Login succeeded with wrong password!" "CRITICAL" }
catch { if ((status_code $_) -eq 401) { pass_log "1.3 Wrong password blocked" "Returns 401" } else { info_log "1.3 Wrong pwd" "Got $(status_code $_)" } }

# Invalid token
try { api_get "/auth/me" @{"Authorization"="Bearer INVALID_TOKEN_ABCDEF"} ; bug_log "1.4 Invalid token" "Accepted fake token!" "CRITICAL" }
catch { if ((status_code $_) -eq 401) { pass_log "1.4 Invalid token blocked" "Returns 401" } else { info_log "1.4 Token" "Got $(status_code $_)" } }

# Empty credentials
try { $er = api_post "/auth/login" @{} '{"identifier":"","password":""}'; bug_log "1.5 Empty creds" "Accepted empty credentials, status $($er.StatusCode)" "HIGH" }
catch { pass_log "1.5 Empty creds blocked" "Status $(status_code $_)" }

# Brute force (5 rapid requests)
$bfFail = 0
for ($i=0; $i -lt 5; $i++) {
    try { api_post "/auth/login" @{} '{"identifier":"superadmin@sms.com","password":"BRUTE'+"$i"+'"}' }
    catch { $bfFail++ }
}
if ($bfFail -ge 5) { pass_log "1.6 Brute force (5 requests)" "All 5 failed properly" }
else { info_log "1.6 Brute force" "$bfFail/5 failed - no rate limiting detected?" }

# =============================================
Write-Host "`n--- [2] SUPER ADMIN: SCHOOLS ---" -ForegroundColor Magenta

# List schools
$allSch = (api_get "/superadmin/schools" $H | ConvertFrom-Json)
pass_log "2.1 List schools" "Count: $($allSch.Count)"
$allSch | Select-Object @{N="#";E={[array]::IndexOf($allSch,$_)+1}}, name, is_active | Format-Table -AutoSize | Out-Host

# Toggle school active/inactive
try {
    api_patch "/superadmin/schools/$SCHOOL_ID/toggle-active?is_active=false" $H | Out-Null
    $deact = (api_get "/superadmin/schools" $H | ConvertFrom-Json) | Where-Object {$_.id -eq $SCHOOL_ID}
    api_patch "/superadmin/schools/$SCHOOL_ID/toggle-active?is_active=true" $H | Out-Null
    pass_log "2.2 Toggle school" "Deactivated: $($deact.is_active -eq $false), Re-activated OK"
} catch { bug_log "2.2 Toggle school" "Error: $($_.Exception.Message)" "MEDIUM" }

# Invalid school ID
try { api_patch "/superadmin/schools/00000000-0000-0000-0000-000000000000/toggle-active?is_active=false" $H | Out-Null; bug_log "2.3 Fake school toggle" "No 404!" "MEDIUM" }
catch { if ((status_code $_) -eq 404) { pass_log "2.3 Fake school 404" "Correct" } else { info_log "2.3 Fake school" "Got $(status_code $_)" } }

# =============================================
Write-Host "`n--- [3] SUBSCRIPTION PLANS ---" -ForegroundColor Magenta

$existingPlans = jsc (api_get "/superadmin/plans" $H)
pass_log "3.1 List plans (before)" "Count: $($existingPlans.Count)"

# Create valid plan
$newPlanBody = @{ name="QA-Plan-$(Get-Random)"; description="QA test plan"; price=1999.99; max_students=500; max_staff=50; features=@{attendance=$true;fees=$true}; duration_days=365 }
try {
    $r = api_post "/superadmin/plans" $H $newPlanBody
    $np = jsc $r
    $PLAN_ID = $np.id
    if ($r.StatusCode -eq 201) { pass_log "3.2 Create plan" "ID=$PLAN_ID Name=$($np.name)" }
    else { bug_log "3.2 Create plan" "Status $($r.StatusCode) not 201" "LOW" }
} catch { bug_log "3.2 Create plan" "Error $(status_code $_): $($_.Exception.Message)" "MEDIUM" }

# Create plan with empty name
try {
    $r = api_post "/superadmin/plans" $H @{ name=""; price=100; max_students=10; max_staff=5; duration_days=30 }
    bug_log "3.3 Empty plan name accepted" "Status $($r.StatusCode) - empty name should be rejected" "MEDIUM"
} catch { pass_log "3.3 Empty plan name rejected" "$(status_code $_)" }

# Negative price
try {
    $r = api_post "/superadmin/plans" $H @{ name="NegPricePlan"; price=-500; max_students=10; max_staff=5; duration_days=30 }
    bug_log "3.4 Negative plan price" "Accepted price=-500! Status=$($r.StatusCode)" "HIGH"
} catch { pass_log "3.4 Negative price blocked" "$(status_code $_)" }

# Zero max_students
try {
    $r = api_post "/superadmin/plans" $H @{ name="ZeroStudents"; price=100; max_students=0; max_staff=5; duration_days=30 }
    bug_log "3.5 Zero max_students" "Accepted max_students=0! Status=$($r.StatusCode)" "MEDIUM"
} catch { pass_log "3.5 Zero max_students blocked" "$(status_code $_)" }

# Update plan
if ($PLAN_ID) {
    try {
        $r = api_put "/superadmin/plans/$PLAN_ID" $H @{ name="QA-Plan-Updated"; price=2999.99; max_students=2000; max_staff=200; features=@{attendance=$true}; duration_days=730 }
        pass_log "3.6 Update plan" "$(($r.Content | ConvertFrom-Json).name)"
    } catch { bug_log "3.6 Update plan" "$(status_code $_): $($_.Exception.Message)" "MEDIUM" }
}

# =============================================
Write-Host "`n--- [4] FEATURE FLAGS ---" -ForegroundColor Magenta

try {
    $r = api_get "/superadmin/schools/$SCHOOL_ID/features" $H
    $flags = jsc $r
    pass_log "4.1 Get feature flags" "Count: $($flags.Count)"
} catch { bug_log "4.1 Get feature flags" "$(status_code $_): $($_.Exception.Message)" "HIGH" }

try {
    $r = api_put "/superadmin/schools/$SCHOOL_ID/features" $H @{ feature_key="library"; is_enabled=$true }
    pass_log "4.2 Set feature flag (PUT)" "Status $($r.StatusCode)"
} catch { bug_log "4.2 Set feature flag" "$(status_code $_): $($_.Exception.Message)" "MEDIUM" }

# Wrong method (POST)
try {
    $r = api_post "/superadmin/schools/$SCHOOL_ID/features" $H @{ feature_key="library"; is_enabled=$false }
    bug_log "4.3 Wrong HTTP method (POST) on features" "Accepted POST on features endpoint! Status=$($r.StatusCode)" "MEDIUM"
} catch { pass_log "4.3 Wrong method blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [5] SUBSCRIPTIONS ---" -ForegroundColor Magenta

try {
    $r = api_get "/superadmin/subscriptions" $H
    $subs = jsc $r
    pass_log "5.1 List subscriptions" "Count: $($subs.Count)"
} catch { bug_log "5.1 List subscriptions" "$(status_code $_)" "MEDIUM" }

if ($PLAN_ID) {
    # Valid subscription
    try {
        $r = api_post "/superadmin/subscriptions" $H @{ school_id=$SCHOOL_ID; plan_id=$PLAN_ID; start_date="2026-04-15"; end_date="2027-04-14" }
        $SUB_ID = (jsc $r).id
        pass_log "5.2 Create subscription" "ID=$SUB_ID"
    } catch { bug_log "5.2 Create subscription" "$(status_code $_)" "MEDIUM" }

    # End before start
    try {
        $r = api_post "/superadmin/subscriptions" $H @{ school_id=$SCHOOL_ID; plan_id=$PLAN_ID; start_date="2026-12-31"; end_date="2026-01-01" }
        bug_log "5.3 Sub end before start" "Accepted invalid range! Status $($r.StatusCode)" "HIGH"
    } catch { pass_log "5.3 End < start blocked" "$(status_code $_)" }

    # Overlap with existing subscription
    if ($SUB_ID) {
        try {
            $r = api_post "/superadmin/subscriptions" $H @{ school_id=$SCHOOL_ID; plan_id=$PLAN_ID; start_date="2026-06-01"; end_date="2027-06-30" }
            bug_log "5.4 Overlapping subscription" "Allowed overlapping dates! Status $($r.StatusCode)" "HIGH"
        } catch { pass_log "5.4 Overlap blocked" "$(status_code $_)" }
    }
}

# =============================================
Write-Host "`n--- [6] ACADEMIC YEARS ---" -ForegroundColor Magenta

try {
    $r = api_get "/academic-years" $HS
    $years = jsc $r
    $yearArr = if ($years.data) { $years.data } elseif ($years -is [array]) { $years } else { @($years) }
    pass_log "6.1 List academic years" "Count: $($yearArr.Count)"
    if ($yearArr.Count -gt 0) { $YEAR_ID = $yearArr[0].id; Write-Host "    Active year: $($yearArr[0].name) ($YEAR_ID)" -ForegroundColor DarkGray }
} catch { bug_log "6.1 Academic years" "$(status_code $_): $($_.Exception.Message)" "HIGH" }

# Create valid year
try {
    $r = api_post "/academic-years" $HS @{ name="2027-2028"; start_date="2027-04-01"; end_date="2028-03-31"; is_active=$false }
    $NEW_YEAR_ID = (jsc $r).id
    if ($r.StatusCode -in @(200,201)) { pass_log "6.2 Create academic year" "ID=$NEW_YEAR_ID 2027-2028" }
    else { bug_log "6.2 Create academic year" "Status $($r.StatusCode)" "MEDIUM" }
} catch { bug_log "6.2 Create academic year" "$(status_code $_): $($_.Exception.Message)" "HIGH" }

# End before start
try {
    $r = api_post "/academic-years" $HS @{ name="Bad Year"; start_date="2029-12-31"; end_date="2029-01-01"; is_active=$false }
    bug_log "6.3 Year end<start accepted" "Status $($r.StatusCode)" "HIGH"
} catch { pass_log "6.3 Year end<start blocked" "$(status_code $_)" }

# Duplicate year name
try {
    $r = api_post "/academic-years" $HS @{ name="2027-2028"; start_date="2028-01-01"; end_date="2029-01-01"; is_active=$false }
    bug_log "6.4 Duplicate year name" "Allowed duplicate name! Status $($r.StatusCode)" "MEDIUM"
} catch { pass_log "6.4 Duplicate year blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [7] CLASSES & SECTIONS ---" -ForegroundColor Magenta

try {
    $r = api_get "/classes" $HS
    $classes = jsc $r
    $classArr = if ($classes.data) { $classes.data } elseif ($classes -is [array]) { $classes } else { @() }
    pass_log "7.1 List classes" "Count: $($classArr.Count)"
    if ($classArr.Count -gt 0) { $CLASS_ID = $classArr[0].id; Write-Host "    Class: $($classArr[0].name)" -ForegroundColor DarkGray }
} catch { bug_log "7.1 List classes" "$(status_code $_)" "MEDIUM" }

if ($YEAR_ID) {
    try {
        $r = api_post "/classes" $HS @{ name="QA-Class-$(Get-Random -Minimum 1 -Maximum 999)"; academic_year_id=$YEAR_ID; order_index=99 }
        $NEW_CLASS_ID = (jsc $r).id
        pass_log "7.2 Create class" "ID=$NEW_CLASS_ID"
    } catch { bug_log "7.2 Create class" "$(status_code $_)" "MEDIUM" }
}

# =============================================
Write-Host "`n--- [8] SUBJECTS ---" -ForegroundColor Magenta

try {
    $r = api_get "/subjects" $HS
    $subj = jsc $r
    $subjArr = if ($subj.data) { $subj.data } elseif ($subj -is [array]) { $subj } else { @() }
    pass_log "8.1 List subjects" "Count: $($subjArr.Count)"
    if ($subjArr.Count -gt 0) { $SUBJECT_ID = $subjArr[0].id; Write-Host "    Subject: $($subjArr[0].name)" -ForegroundColor DarkGray }
} catch { bug_log "8.1 Subjects" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [9] TIMETABLE ---" -ForegroundColor Magenta

try {
    $r = api_get "/timetable" $HS
    pass_log "9.1 List timetable" "Status $($r.StatusCode)"
} catch { bug_log "9.1 Timetable" "$(status_code $_)" "MEDIUM" }

if ($CLASS_ID -and $SUBJECT_ID -and $YEAR_ID) {
    try {
        $tt1 = @{ class_id=$CLASS_ID; subject_id=$SUBJECT_ID; day_of_week="monday"; period=1; start_time="08:00"; end_time="09:00"; academic_year_id=$YEAR_ID }
        api_post "/timetable" $HS $tt1 | Out-Null
        $tt2 = @{ class_id=$CLASS_ID; subject_id=$SUBJECT_ID; day_of_week="monday"; period=1; start_time="08:00"; end_time="09:00"; academic_year_id=$YEAR_ID }
        $r2 = api_post "/timetable" $HS $tt2
        bug_log "9.2 Timetable conflict" "Accepted duplicate slot Mon/P1 for same class! Status $($r2.StatusCode)" "HIGH"
    } catch { pass_log "9.2 Timetable conflict blocked" "$(status_code $_)" }
} else { info_log "9.2 Timetable conflict" "Skipped: need class, subject, year IDs" }

# =============================================
Write-Host "`n--- [10] STUDENTS ---" -ForegroundColor Magenta

try {
    $r = api_get "/students" $HS
    $studs = jsc $r
    $studArr = if ($studs.data) { $studs.data } elseif ($studs -is [array]) { $studs } else { @() }
    pass_log "10.1 List students" "Count: $($studArr.Count)"
    if ($studArr.Count -gt 0) {
        $STUDENT_ID = $studArr[0].id
        Write-Host "    Sample: $($studArr[0].first_name) $($studArr[0].last_name) [Enroll: $($studArr[0].enrollment_number)]" -ForegroundColor DarkGray
    }
} catch { bug_log "10.1 Students list" "$(status_code $_)" "HIGH" }

if ($STUDENT_ID) {
    try {
        $r = api_get "/students/$STUDENT_ID" $HS
        pass_log "10.2 Get student by ID" "Status $($r.StatusCode)"
    } catch { bug_log "10.2 Get student" "$(status_code $_)" "MEDIUM" }
}

# 404 for non-existent
try { api_get "/students/00000000-0000-0000-0000-000000000000" $HS; bug_log "10.3 Fake student ID" "No 404!" "LOW" }
catch { pass_log "10.3 Fake student 404" "$(status_code $_)" }

# XSS in student name
try {
    $xss = @{ first_name="<script>alert(1)</script>"; last_name="XSSTest"; date_of_birth="2010-01-01"; gender="male"; enrollment_number="XSS$(Get-Random)" }
    $r = api_post "/students" $HS $xss
    $created = (jsc $r).data
    $fn = if ($created.first_name) { $created.first_name } else { ($r.Content | ConvertFrom-Json).first_name }
    if ($fn -like "*<script>*") { bug_log "10.4 XSS stored in DB" "first_name stored with <script> tag!" "HIGH" }
    else { pass_log "10.4 XSS sanitized" "Stored as: $fn" }
} catch { pass_log "10.4 XSS payload blocked" "$(status_code $_)" }

# Future DOB
try {
    $r = api_post "/students" $HS @{ first_name="Future"; last_name="Kid"; date_of_birth="2099-12-31"; gender="male"; enrollment_number="FUT$(Get-Random)" }
    bug_log "10.5 Future DOB accepted" "Created student DOB=2099! Status $($r.StatusCode)" "MEDIUM"
} catch { pass_log "10.5 Future DOB blocked" "$(status_code $_)" }

# Duplicate enrollment number
if ($studArr -and $studArr.Count -gt 0 -and $studArr[0].enrollment_number) {
    $dupEnroll = $studArr[0].enrollment_number
    try {
        $r = api_post "/students" $HS @{ first_name="Dup"; last_name="Student"; date_of_birth="2010-01-01"; gender="male"; enrollment_number=$dupEnroll }
        bug_log "10.6 Duplicate enrollment" "Allowed duplicate: $dupEnroll! Status $($r.StatusCode)" "HIGH"
    } catch { pass_log "10.6 Duplicate enrollment blocked" "$(status_code $_)" }
} else { info_log "10.6 Dup enrollment" "Skipped - no existing student" }

# Very long name
try {
    $long = "X" * 5000
    $r = api_post "/students" $HS @{ first_name=$long; last_name="Test"; date_of_birth="2010-01-01"; gender="male"; enrollment_number="LONG$(Get-Random)" }
    bug_log "10.7 5000-char name accepted" "Status $($r.StatusCode)" "MEDIUM"
} catch { pass_log "10.7 Long name blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [11] STAFF ---" -ForegroundColor Magenta

try {
    $r = api_get "/staff" $HS
    $staffD = jsc $r
    $staffArr = if ($staffD.data) { $staffD.data } elseif ($staffD -is [array]) { $staffD } else { @() }
    pass_log "11.1 List staff" "Count: $($staffArr.Count)"
    if ($staffArr.Count -gt 0) { $STAFF_ID = $staffArr[0].id; Write-Host "    Staff: $($staffArr[0].first_name)" -ForegroundColor DarkGray }
} catch { bug_log "11.1 Staff list" "$(status_code $_)" "HIGH" }

# Create staff with invalid email
try {
    $r = api_post "/staff" $HS @{ first_name="Test"; last_name="BadEmail"; email="notanemail"; phone="9876543210"; employee_id="BAD$(Get-Random)"; joining_date="2026-01-01" }
    bug_log "11.2 Invalid email accepted" "Status $($r.StatusCode)" "HIGH"
} catch { pass_log "11.2 Invalid email blocked" "$(status_code $_)" }

try { $r = api_get "/leaves" $HS; pass_log "11.3 List leaves" "Status $($r.StatusCode)" }
catch { bug_log "11.3 Leaves" "$(status_code $_)" "MEDIUM" }

try { $r = api_get "/payroll" $HS; pass_log "11.4 Payroll list" "Status $($r.StatusCode)" }
catch { bug_log "11.4 Payroll" "$(status_code $_)" "MEDIUM" }

try { $r = api_get "/departments" $HS; $da=jsc $r; $dArr = if($da.data){$da.data}elseif($da -is [array]){$da}else{@()}; pass_log "11.5 Departments" "Count: $($dArr.Count)" }
catch { bug_log "11.5 Departments" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [12] ATTENDANCE ---" -ForegroundColor Magenta

try { $r = api_get "/attendance?date=2026-04-15" $HS; pass_log "12.1 Student attendance" "Status $($r.StatusCode)" }
catch { bug_log "12.1 Attendance" "$(status_code $_)" "MEDIUM" }

try { $r = api_get "/staff-attendance" $HS; pass_log "12.2 Staff attendance" "Status $($r.StatusCode)" }
catch { bug_log "12.2 Staff attendance" "$(status_code $_)" "MEDIUM" }

try {
    $r = api_get "/holidays" $HS
    $hols = jsc $r; $holArr = if($hols.data){$hols.data}elseif($hols -is [array]){$hols}else{@()}
    pass_log "12.3 Holidays" "Count: $($holArr.Count)"
} catch { bug_log "12.3 Holidays" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [13] FEES ---" -ForegroundColor Magenta

try {
    $r = api_get "/fees/structures" $HS
    $fs = jsc $r; $fsArr = if($fs.data){$fs.data}elseif($fs -is [array]){$fs}else{@()}
    pass_log "13.1 Fee structures" "Count: $($fsArr.Count)"
    if ($fsArr.Count -gt 0) { $FEE_ID = $fsArr[0].id }
} catch { bug_log "13.1 Fee structures" "$(status_code $_)" "HIGH" }

try {
    $r = api_get "/fees/collections" $HS
    $fc = jsc $r; $fcArr = if($fc.data){$fc.data}elseif($fc -is [array]){$fc}else{@()}
    pass_log "13.2 Fee collections" "Count: $($fcArr.Count)"
} catch { bug_log "13.2 Fee collections" "$(status_code $_)" "MEDIUM" }

# Negative fee
try {
    $r = api_post "/fees/structures" $HS @{ name="NegFee$(Get-Random)"; amount=-1000; fee_type="tuition" }
    bug_log "13.3 Negative fee amount" "amount=-1000 accepted! Status $($r.StatusCode)" "HIGH"
} catch { pass_log "13.3 Negative fee blocked" "$(status_code $_)" }

# Discount > 100%
try {
    $r = api_post "/fees/discounts" $HS @{ student_id="00000000-0000-0000-0000-000000000000"; discount_percentage=150; reason="Overflow test" }
    bug_log "13.4 Discount >100%" "150% accepted! Status $($r.StatusCode)" "HIGH"
} catch { pass_log "13.4 Discount >100% blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [14] EXAMS ---" -ForegroundColor Magenta

try { $r=api_get "/exam-types" $HS; $et=jsc $r; $etA=if($et.data){$et.data}elseif($et -is [array]){$et}else{@()}; pass_log "14.1 Exam types" "Count: $($etA.Count)" }
catch { bug_log "14.1 Exam types" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/grading-scales" $HS; pass_log "14.2 Grading scales" "Status $($r.StatusCode)" }
catch { bug_log "14.2 Grading" "$(status_code $_)" "MEDIUM" }

try {
    $r=api_get "/exams" $HS; $ex=jsc $r; $exA=if($ex.data){$ex.data}elseif($ex -is [array]){$ex}else{@()}
    pass_log "14.3 Exams" "Count: $($exA.Count)"
    if ($exA.Count -gt 0) { $EXAM_ID = $exA[0].id }
} catch { bug_log "14.3 Exams" "$(status_code $_)" "HIGH" }

# Marks > max
try {
    $r = api_post "/exams/results" $HS @{ student_id="00000000-0000-0000-0000-000000000000"; exam_id="00000000-0000-0000-0000-000000000000"; marks_obtained=200; max_marks=100 }
    bug_log "14.4 Marks>max accepted" "200/100 accepted! Status $($r.StatusCode)" "HIGH"
} catch { pass_log "14.4 Marks>max blocked" "$(status_code $_)" }

try { $r=api_get "/report-card-templates" $HS; pass_log "14.5 Report card templates" "Status $($r.StatusCode)" }
catch { bug_log "14.5 RC Templates" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [15] TRANSPORT ---" -ForegroundColor Magenta

try { $r=api_get "/transport/vehicles" $HS; $v=jsc $r; $vA=if($v.data){$v.data}elseif($v -is [array]){$v}else{@()}; pass_log "15.1 Vehicles" "Count: $($vA.Count)" }
catch { bug_log "15.1 Vehicles" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/transport/routes" $HS; $ro=jsc $r; $roA=if($ro.data){$ro.data}elseif($ro -is [array]){$ro}else{@()}; pass_log "15.2 Routes" "Count: $($roA.Count)" }
catch { bug_log "15.2 Routes" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/transport" $HS; pass_log "15.3 Transport assignments" "Status $($r.StatusCode)" }
catch { bug_log "15.3 Transport" "$(status_code $_)" "MEDIUM" }

# Zero capacity vehicle
try {
    $r = api_post "/transport/vehicles" $HS @{ registration_number="ZZ$(Get-Random)"; vehicle_type="bus"; capacity=0; driver_name="Test" }
    bug_log "15.4 Zero capacity vehicle" "Accepted capacity=0! Status $($r.StatusCode)" "MEDIUM"
} catch { pass_log "15.4 Zero capacity blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [16] LIBRARY ---" -ForegroundColor Magenta

try { $r=api_get "/library/categories" $HS; pass_log "16.1 Lib categories" "Status $($r.StatusCode)" }
catch { bug_log "16.1 Lib cats" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/library/books" $HS; $bk=jsc $r; $bkA=if($bk.data){$bk.data}elseif($bk -is [array]){$bk}else{@()}; pass_log "16.2 Books" "Count: $($bkA.Count)"; if($bkA.Count -gt 0){$BOOK_ID=$bkA[0].id} }
catch { bug_log "16.2 Books" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/library/members" $HS; pass_log "16.3 Lib members" "Status $($r.StatusCode)" }
catch { bug_log "16.3 Lib members" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/library/issues" $HS; pass_log "16.4 Book issues" "Status $($r.StatusCode)" }
catch { bug_log "16.4 Issues" "$(status_code $_)" "MEDIUM" }

# Past due date
try {
    $r = api_post "/library/issues" $HS @{ book_id="00000000-0000-0000-0000-000000000000"; member_id="00000000-0000-0000-0000-000000000000"; due_date="2020-01-01" }
    bug_log "16.5 Past due date" "Accepted 2020-01-01! Status $($r.StatusCode)" "MEDIUM"
} catch { pass_log "16.5 Past due date blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [17] INVENTORY ---" -ForegroundColor Magenta

try { $r=api_get "/inventory/categories" $HS; pass_log "17.1 Inv categories" "Status $($r.StatusCode)" }
catch { bug_log "17.1 Inv cats" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/inventory/items" $HS; $it=jsc $r; $itA=if($it.data){$it.data}elseif($it -is [array]){$it}else{@()}; pass_log "17.2 Inv items" "Count: $($itA.Count)" }
catch { bug_log "17.2 Inv items" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/inventory/suppliers" $HS; pass_log "17.3 Suppliers" "Status $($r.StatusCode)" }
catch { bug_log "17.3 Suppliers" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/inventory/purchase-orders" $HS; pass_log "17.4 Purchase orders" "Status $($r.StatusCode)" }
catch { bug_log "17.4 POs" "$(status_code $_)" "MEDIUM" }

# Negative quantity
try {
    $r = api_post "/inventory/items" $HS @{ name="NegItem$(Get-Random)"; quantity=-50; unit_price=10 }
    bug_log "17.5 Negative quantity" "qty=-50 accepted! Status $($r.StatusCode)" "HIGH"
} catch { pass_log "17.5 Negative qty blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [18] ACCOUNTING ---" -ForegroundColor Magenta

try { $r=api_get "/accounting/income-categories" $HS; pass_log "18.1 Income cats" "Status $($r.StatusCode)" }
catch { bug_log "18.1 Income cats" "$(status_code $_)" "MEDIUM" }
try { $r=api_get "/accounting/expense-categories" $HS; pass_log "18.2 Expense cats" "Status $($r.StatusCode)" }
catch { bug_log "18.2 Expense cats" "$(status_code $_)" "MEDIUM" }
try { $r=api_get "/accounting/income" $HS; pass_log "18.3 Income records" "Status $($r.StatusCode)" }
catch { bug_log "18.3 Income" "$(status_code $_)" "MEDIUM" }
try { $r=api_get "/accounting/expenses" $HS; pass_log "18.4 Expenses" "Status $($r.StatusCode)" }
catch { bug_log "18.4 Expenses" "$(status_code $_)" "MEDIUM" }
try { $r=api_get "/accounting/budgets" $HS; pass_log "18.5 Budgets" "Status $($r.StatusCode)" }
catch { bug_log "18.5 Budgets" "$(status_code $_)" "MEDIUM" }
try { $r=api_get "/accounting/summary" $HS; pass_log "18.6 Accounting summary" "Status $($r.StatusCode)" }
catch { bug_log "18.6 Summary" "$(status_code $_)" "MEDIUM" }

# Negative expense
try {
    $r = api_post "/accounting/expenses" $HS @{ title="NegExp$(Get-Random)"; amount=-5000; date="2026-04-15"; category_id="00000000-0000-0000-0000-000000000000" }
    bug_log "18.7 Negative expense" "amount=-5000 accepted! Status $($r.StatusCode)" "HIGH"
} catch { pass_log "18.7 Negative expense blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [19] COMMUNICATION ---" -ForegroundColor Magenta

try { $r=api_get "/announcements" $HS; $an=jsc $r; $anA=if($an.data){$an.data}elseif($an -is [array]){$an}else{@()}; pass_log "19.1 Announcements" "Count: $($anA.Count)" }
catch { bug_log "19.1 Announcements" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/notifications" $HS; pass_log "19.2 Notifications" "Status $($r.StatusCode)" }
catch { bug_log "19.2 Notifications" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/communications/templates" $HS; pass_log "19.3 Comm templates" "Status $($r.StatusCode)" }
catch { bug_log "19.3 Comm templates" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/communications/bulk-messages" $HS; pass_log "19.4 Bulk messages" "Status $($r.StatusCode)" }
catch { bug_log "19.4 Bulk" "$(status_code $_)" "MEDIUM" }

# Empty announcement
try {
    $r = api_post "/announcements" $HS @{ title=""; body=""; target_roles=@() }
    bug_log "19.5 Empty announcement" "Status $($r.StatusCode) - empty accepted" "MEDIUM"
} catch { pass_log "19.5 Empty announcement blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [20] CALENDAR ---" -ForegroundColor Magenta

try { $r=api_get "/calendar" $HS; pass_log "20.1 Calendar" "Status $($r.StatusCode)" }
catch {
    try { $r=api_get "/calendar/events" $HS; pass_log "20.1 Calendar/events" "Status $($r.StatusCode)" }
    catch { bug_log "20.1 Calendar" "$(status_code $_)" "MEDIUM" }
}

# Event end before start
try {
    $r = api_post "/calendar/events" $HS @{ title="BadEvent"; start_date="2026-12-31"; end_date="2026-01-01"; event_type="holiday" }
    bug_log "20.2 Event end<start" "Accepted invalid date range! Status $($r.StatusCode)" "HIGH"
} catch { pass_log "20.2 Event end<start blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [21] HOMEWORK & PTM ---" -ForegroundColor Magenta

try { $r=api_get "/homework" $HS; $hw=jsc $r; $hwA=if($hw.data){$hw.data}elseif($hw -is [array]){$hw}else{@()}; pass_log "21.1 Homework" "Count: $($hwA.Count)" }
catch { bug_log "21.1 Homework" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/lesson-plans" $HS; pass_log "21.2 Lesson plans" "Status $($r.StatusCode)" }
catch { bug_log "21.2 Lesson plans" "$(status_code $_)" "MEDIUM" }

try { $r=api_get "/ptm" $HS; pass_log "21.3 PTM meetings" "Status $($r.StatusCode)" }
catch { bug_log "21.3 PTM" "$(status_code $_)" "MEDIUM" }

# Due date in the past for homework
try {
    $r = api_post "/homework" $HS @{ title="Past HW"; due_date="2020-01-01"; description="Test"; class_id="00000000-0000-0000-0000-000000000000" }
    bug_log "21.4 Past due date HW" "Accepted 2020-01-01! Status $($r.StatusCode)" "MEDIUM"
} catch { pass_log "21.4 Past due HW blocked" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [22] DOCUMENT TEMPLATES ---" -ForegroundColor Magenta

try { $r=api_get "/document-templates" $HS; $dt=jsc $r; $dtA=if($dt.data){$dt.data}elseif($dt -is [array]){$dt}else{@()}; pass_log "22.1 Doc templates" "Count: $($dtA.Count)" }
catch { bug_log "22.1 Templates" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [23] AUDIT LOGS ---" -ForegroundColor Magenta

try {
    $r=api_get "/audit-logs" $HS
    $al=jsc $r; $alA=if($al.data){$al.data}elseif($al -is [array]){$al}else{@()}
    pass_log "23.1 Audit logs" "Count: $($alA.Count)"
} catch { bug_log "23.1 Audit logs" "$(status_code $_)" "HIGH" }

# Try to delete audit log (should not be allowed)
try { api_delete "/audit-logs/00000000-0000-0000-0000-000000000000" $HS; bug_log "23.2 Delete audit log" "Should be 404/405 but got through!" "HIGH" }
catch { pass_log "23.2 Cannot delete audit log" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [24] SETTINGS ---" -ForegroundColor Magenta

try { $r=api_get "/settings" $HS; pass_log "24.1 Settings" "Status $($r.StatusCode)" }
catch { bug_log "24.1 Settings" "$(status_code $_)" "HIGH" }

# =============================================
Write-Host "`n--- [25] DASHBOARD ---" -ForegroundColor Magenta

try { $r=api_get "/dashboard" $HS; pass_log "25.1 Dashboard" "Status $($r.StatusCode)" }
catch {
    try { $r=api_get "/dashboard/overview" $HS; pass_log "25.1 Dashboard/overview" "Status $($r.StatusCode)" }
    catch { bug_log "25.1 Dashboard" "$(status_code $_)" "HIGH" }
}

# =============================================
Write-Host "`n--- [26] REPORTS ---" -ForegroundColor Magenta

try { $r=api_get "/reports" $HS; pass_log "26.1 Reports" "Status $($r.StatusCode)" }
catch { bug_log "26.1 Reports" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [27] ROLES & PERMISSIONS ---" -ForegroundColor Magenta

try {
    $r=api_get "/roles" $HS; $rls=jsc $r; $rlsA=if($rls.data){$rls.data}elseif($rls -is [array]){$rls}else{@()}
    pass_log "27.1 Roles" "Count: $($rlsA.Count)"
    if ($rlsA.Count -gt 0) { $ROLE_ID = $rlsA[0].id; Write-Host "    Role: $($rlsA[0].name)" -ForegroundColor DarkGray }
} catch { bug_log "27.1 Roles" "$(status_code $_)" "HIGH" }

try { $r=api_get "/permissions" $H; pass_log "27.2 Permissions" "Status $($r.StatusCode)" }
catch { bug_log "27.2 Permissions" "$(status_code $_)" "MEDIUM" }

# Create role with empty permissions
try {
    $r = api_post "/roles" $HS @{ name="QA-Empty-Role-$(Get-Random)"; permissions=@() }
    $newR = jsc $r; $NEW_ROLE_ID = if($newR.data){$newR.data.id}else{$newR.id}
    pass_log "27.3 Create empty-perm role" "ID=$NEW_ROLE_ID"
} catch { bug_log "27.3 Empty role" "$(status_code $_)" "LOW" }

# Delete non-existent role
try { api_delete "/roles/00000000-0000-0000-0000-000000000000" $HS; bug_log "27.4 Delete fake role" "No 404!" "LOW" }
catch { pass_log "27.4 Delete fake role" "$(status_code $_)" }

# =============================================
Write-Host "`n--- [28] ADMISSIONS ---" -ForegroundColor Magenta

try {
    $r=api_get "/admissions" $HS; $adm=jsc $r; $admA=if($adm.data){$adm.data}elseif($adm -is [array]){$adm}else{@()}
    pass_log "28.1 Admissions" "Count: $($admA.Count)"
} catch { bug_log "28.1 Admissions" "$(status_code $_)" "HIGH" }

# =============================================
Write-Host "`n--- [29] SECURITY TESTS ---" -ForegroundColor Magenta

# IDOR - Super admin cross-school access
if ($allSch.Count -gt 1) {
    $s2id = $allSch[1].id; $HS2 = @{"Authorization"="Bearer $TOKEN";"X-School-Id"=$s2id}
    try {
        $r=api_get "/students" $HS2; $s2D=jsc $r; $s2A=if($s2D.data){$s2D.data}elseif($s2D -is [array]){$s2D}else{@()}
        info_log "29.1 Cross-school students" "School2 has $($s2A.Count) students - SuperAdmin can see all schools as expected"
    } catch { bug_log "29.1 Cross-school" "$(status_code $_)" "MEDIUM" }
}

# SQL injection in search
try {
    $r=api_get "/students?search=%27+OR+1%3D1+--" $HS
    $inj=jsc $r; $injA=if($inj.data){$inj.data}elseif($inj -is [array]){$inj}else{@()}
    info_log "29.2 SQLi in search" "Returned $($injA.Count) records (check if all records returned - signs of SQLi)"
} catch { pass_log "29.2 SQLi in search blocked" "$(status_code $_)" }

# Huge pagination
try {
    $r=api_get "/students?page=1&per_page=999999" $HS; $big=jsc $r; $bigA=if($big.data){$big.data}elseif($big -is [array]){$big}else{@()}
    if ($bigA.Count -gt 1000) { bug_log "29.3 No pagination limit" "Returned $($bigA.Count) records for per_page=999999!" "MEDIUM" }
    else { info_log "29.3 Pagination capped" "per_page=999999 returned $($bigA.Count) records (capped)" }
} catch { pass_log "29.3 Huge per_page blocked" "$(status_code $_)" }

# Negative page
try { $r=api_get "/students?page=-1" $HS; info_log "29.4 Negative page" "Status $($r.StatusCode)" }
catch { pass_log "29.4 Negative page blocked" "$(status_code $_)" }

# CSRF-like - missing CSRF token (JWT API doesn't need CSRF, but test cookie-based CSRF)
try {
    $r = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $lBody -ContentType "application/json" -UseBasicParsing
    info_log "29.5 CSRF check" "Login with only body (no Origin check) - Status $($r.StatusCode)"
} catch { info_log "29.5 CSRF" "$(status_code $_)" }

# Header injection
try {
    $injH = @{"Authorization"="Bearer $TOKEN"; "X-School-Id"=$SCHOOL_ID; "X-Forwarded-For"="127.0.0.1\r\nX-Injected: evil"; "Host"="evil.com"}
    $r = api_get "/students" $injH
    info_log "29.6 Header injection" "Status $($r.StatusCode)"
} catch { pass_log "29.6 Header injection blocked" "$(status_code $_)" }

# Mass assignment on profile update
try {
    $r = api_patch "/auth/me" $H @{ is_super_admin=$false; username="hacked_admin"; school_id="00000000-0000-0000-0000-000000000000" }
    $me2 = (jsc $r).data
    if ($me2 -and $me2.is_super_admin -eq $false) { bug_log "29.7 Mass assignment profile" "is_super_admin changed to false!" "CRITICAL" }
    elseif ($me2 -and $me2.username -eq "hacked_admin") { bug_log "29.7 Mass assignment username" "username changed to hacked_admin!" "MEDIUM" }
    else { pass_log "29.7 Mass assignment ignored" "Protected fields not changed" }
} catch { pass_log "29.7 Mass assignment blocked" "$(status_code $_)" }

# Accessing school admin endpoint as super admin (school-specific data - should work with X-School-Id)
try {
    $r = api_get "/schools/$SCHOOL_ID" $H
    pass_log "29.8 Get school details" "Status $($r.StatusCode)"
} catch { bug_log "29.8 Get school details" "$(status_code $_)" "MEDIUM" }

# =============================================
Write-Host "`n--- [30] IMPERSONATION ---" -ForegroundColor Magenta

# List impersonation logs
try { $r=api_get "/superadmin/impersonate" $H; $imp=jsc $r; info_log "30.1 Impersonation logs" "Count: $(if($imp.Count){$imp.Count}else{'n/a'})" }
catch { info_log "30.1 Impersonation logs" "$(status_code $_)" }

# Impersonate non-existent user
try {
    $r = api_post "/superadmin/impersonate" $H @{ school_id=$SCHOOL_ID; user_id="00000000-0000-0000-0000-000000000000" }
    $imp = jsc $r; $IMP_LOG_ID = $imp.id
    if ($IMP_LOG_ID) { pass_log "30.2 Create impersonation log" "Log ID=$IMP_LOG_ID" }
    else { bug_log "30.2 Impersonation" "Created but no ID returned: $($r.Content.Substring(0,100))" "MEDIUM" }
} catch {
    if ((status_code $_) -eq 404) { pass_log "30.2 Impersonate fake user 404" "Correct" }
    else { info_log "30.2 Impersonation" "Got $(status_code $_)" }
}

if ($IMP_LOG_ID) {
    try { api_patch "/superadmin/impersonate/$IMP_LOG_ID/end" $H | Out-Null; pass_log "30.3 End impersonation" "Successfully ended" }
    catch { bug_log "30.3 End impersonation" "$(status_code $_)" "MEDIUM" }
}

# =============================================
# FINAL SUMMARY
# =============================================
Write-Host ""
Write-Host "" 
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  FINAL TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ("  TOTAL PASS : " + $script:PASSES.Count) -ForegroundColor Green
Write-Host ("  TOTAL BUGS : " + $script:BUGS.Count) -ForegroundColor Red
Write-Host ("  TOTAL INFO : " + $script:INFOS.Count) -ForegroundColor Yellow
Write-Host ""

Write-Host "BUGS FOUND:" -ForegroundColor Red
Write-Host "===========" -ForegroundColor Red
$script:BUGS | Sort-Object Sev | Format-Table Test, Sev, Detail -AutoSize -Wrap | Out-Host

Write-Host "INFO / OBSERVATIONS:" -ForegroundColor Yellow
Write-Host "====================" -ForegroundColor Yellow  
$script:INFOS | Format-Table Test, Detail -AutoSize -Wrap | Out-Host

Write-Host "PASSED TESTS:" -ForegroundColor Green
Write-Host "=============" -ForegroundColor Green
$script:PASSES | Format-Table Test, Detail -AutoSize -Wrap | Out-Host
