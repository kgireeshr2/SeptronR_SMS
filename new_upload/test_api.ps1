# SMS Application - Comprehensive API Test Script
# Run as: .\test_api.ps1

$BASE = "http://localhost:8000/api/v1"
$RESULTS = @()

function Test-API {
    param($Name, $Method, $Url, $Body, $Headers, $ExpectedStatus, $Note)
    $result = [PSCustomObject]@{
        Test = $Name
        Method = $Method
        URL = $Url
        Expected = $ExpectedStatus
        Actual = "N/A"
        Status = "UNKNOWN"
        Note = $Note
        Response = ""
    }
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            UseBasicParsing = $true
            ErrorAction = "Stop"
        }
        if ($Headers) { $params.Headers = $Headers }
        if ($Body) { $params.Body = $Body; $params.ContentType = "application/json" }
        $r = Invoke-WebRequest @params
        $result.Actual = [int]$r.StatusCode
        $result.Response = $r.Content.Substring(0, [Math]::Min(200, $r.Content.Length))
        if ([int]$r.StatusCode -eq $ExpectedStatus) { $result.Status = "PASS" }
        else { $result.Status = "FAIL" }
    } catch {
        $sc = [int]$_.Exception.Response.StatusCode
        if ($sc -eq 0) { $sc = 500 }
        $result.Actual = $sc
        if ($sc -eq $ExpectedStatus) { $result.Status = "PASS" }
        else { $result.Status = "FAIL" }
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $result.Response = $reader.ReadToEnd().Substring(0, [Math]::Min(200, $reader.ReadToEnd().Length))
        } catch {}
    }
    return $result
}

# =============================================
# STEP 1: LOGIN & GET TOKEN
# =============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SMS APPLICATION - COMPREHENSIVE TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Authenticating..." -ForegroundColor Yellow
$loginBody = '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}'
$loginResp = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing | ConvertFrom-Json
$TOKEN = $loginResp.data.access_token
$H = @{"Authorization" = "Bearer $TOKEN"}
Write-Host "Token obtained: $($TOKEN.Substring(0,30))..." -ForegroundColor Green

# =============================================
# SECTION 1: AUTHENTICATION TESTS
# =============================================
Write-Host "`n[1] AUTHENTICATION TESTS" -ForegroundColor Magenta

$tests = @()

# 1.1 Get current user profile
$r = Invoke-WebRequest -Uri "$BASE/auth/me" -Headers $H -UseBasicParsing
$u = ($r.Content | ConvertFrom-Json).data
$tests += [PSCustomObject]@{ Test="1.1 GET /auth/me"; Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"}; Detail="User: $($u.email), SuperAdmin: $($u.is_super_admin)" }

# 1.2 Login with wrong password
try { Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{"identifier":"superadmin@sms.com","password":"WRONG"}' -ContentType "application/json" -UseBasicParsing; $tests += [PSCustomObject]@{Test="1.2 Wrong password";Status="FAIL";Detail="Should have returned 401"} }
catch { $tests += [PSCustomObject]@{Test="1.2 Wrong password";Status=if($_.Exception.Response.StatusCode -eq "Unauthorized"){"PASS"}else{"FAIL"};Detail="Correctly blocked: 401"} }

# 1.3 Access protected route without token
try { Invoke-WebRequest -Uri "$BASE/auth/me" -UseBasicParsing; $tests += [PSCustomObject]@{Test="1.3 No token";Status="FAIL";Detail="Should have returned 401"} }
catch { $tests += [PSCustomObject]@{Test="1.3 No token";Status=if($_.Exception.Response.StatusCode -eq "Unauthorized"){"PASS"}else{"FAIL"};Detail="Correctly blocked: 401"} }

# 1.4 Invalid token
try { Invoke-WebRequest -Uri "$BASE/auth/me" -Headers @{"Authorization"="Bearer invalid_token_xyz"} -UseBasicParsing; $tests += [PSCustomObject]@{Test="1.4 Invalid token";Status="FAIL";Detail="Should return 401"} }
catch { $tests += [PSCustomObject]@{Test="1.4 Invalid token";Status=if($_.Exception.Response.StatusCode -eq "Unauthorized"){"PASS"}else{"FAIL"};Detail="Correctly blocked: 401"} }

# 1.5 Empty credentials
try { Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{"identifier":"","password":""}' -ContentType "application/json" -UseBasicParsing; $tests += [PSCustomObject]@{Test="1.5 Empty creds";Status="WARN";Detail="Accepted empty credentials"} }
catch { $tests += [PSCustomObject]@{Test="1.5 Empty creds";Status="PASS";Detail="Blocked empty credentials: $([int]$_.Exception.Response.StatusCode)"} }

$tests | Format-Table -AutoSize

# =============================================
# SECTION 2: SUPER ADMIN - SCHOOLS
# =============================================
Write-Host "`n[2] SUPER ADMIN - SCHOOLS" -ForegroundColor Magenta
$sat = @()

# 2.1 List all schools
$r = Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers $H -UseBasicParsing
$schools = ($r.Content | ConvertFrom-Json)
$sat += [PSCustomObject]@{Test="2.1 List schools";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($schools.Count)"}
Write-Host "Schools found: $($schools.Count)" -ForegroundColor Yellow
if ($schools.Count -gt 0) {
    $schools | Select-Object -First 3 | Select-Object name, is_active, @{N="id";E={$_.id.ToString().Substring(0,8)+"..."}} | Format-Table
    $SCHOOL_ID = $schools[0].id
}

# 2.2 Non-super-admin cannot access super admin routes
$r2 = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -Body '{"identifier":"superadmin@sms.com","password":"SuperAdmin@123"}' -ContentType "application/json" -UseBasicParsing
# No non-admin user exists yet, so we test with expired/wrong token
try { Invoke-WebRequest -Uri "$BASE/superadmin/schools" -Headers @{"Authorization"="Bearer bad"} -UseBasicParsing; $sat += [PSCustomObject]@{Test="2.2 Unauthorized superadmin";Status="FAIL";Detail="Should block"} }
catch { $sat += [PSCustomObject]@{Test="2.2 Unauthorized superadmin";Status="PASS";Detail="Blocked: $([int]$_.Exception.Response.StatusCode)"} }

$sat | Format-Table -AutoSize

# =============================================
# SECTION 3: SUBSCRIPTION PLANS
# =============================================
Write-Host "`n[3] SUBSCRIPTION PLANS" -ForegroundColor Magenta
$pt = @()

# 3.1 List plans
$r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Headers $H -UseBasicParsing
$plans = ($r.Content | ConvertFrom-Json)
$pt += [PSCustomObject]@{Test="3.1 List plans";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($plans.Count)"}

# 3.2 Create a plan
$planBody = '{"name":"Test Plan","description":"Testing plan","price":999.99,"max_students":500,"max_staff":50,"features":{"attendance":true,"fees":true},"duration_days":365}'
try {
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Method POST -Headers $H -Body $planBody -ContentType "application/json" -UseBasicParsing
    $newPlan = ($r.Content | ConvertFrom-Json)
    $PLAN_ID = $newPlan.id
    $pt += [PSCustomObject]@{Test="3.2 Create plan";Status=if($r.StatusCode -eq 201){"PASS"}else{"FAIL"};Detail="Created: $($newPlan.name)"}
}
catch { $pt += [PSCustomObject]@{Test="3.2 Create plan";Status="FAIL";Detail="Error: $($_)"} }

# 3.3 Create plan with missing required fields
try {
    $r = Invoke-WebRequest -Uri "$BASE/superadmin/plans" -Method POST -Headers $H -Body '{"name":""}' -ContentType "application/json" -UseBasicParsing
    $pt += [PSCustomObject]@{Test="3.3 Create plan (invalid)";Status="WARN";Detail="Accepted invalid data - status $($r.StatusCode)"}
}
catch { $pt += [PSCustomObject]@{Test="3.3 Create plan (invalid)";Status="PASS";Detail="Rejected invalid: $([int]$_.Exception.Response.StatusCode)"} }

$pt | Format-Table -AutoSize

# =============================================
# SECTION 4: FEATURE FLAGS
# =============================================
Write-Host "`n[4] FEATURE FLAGS" -ForegroundColor Magenta
$ff = @()

if ($SCHOOL_ID) {
    # 4.1 Get feature flags for school
    try {
        $r = Invoke-WebRequest -Uri "$BASE/superadmin/schools/$SCHOOL_ID/features" -Headers $H -UseBasicParsing
        $ff += [PSCustomObject]@{Test="4.1 Get feature flags";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail=$r.Content.Substring(0,100)}
    }
    catch { $ff += [PSCustomObject]@{Test="4.1 Get feature flags";Status="FAIL";Detail="$($_)"} }

    # 4.2 Set feature flags
    $flagBody = '{"flags":{"library":true,"transport":false,"inventory":true}}'
    try {
        $r = Invoke-WebRequest -Uri "$BASE/superadmin/schools/$SCHOOL_ID/features" -Method POST -Headers $H -Body $flagBody -ContentType "application/json" -UseBasicParsing
        $ff += [PSCustomObject]@{Test="4.2 Set feature flags";Status=if($r.StatusCode -in @(200,201)){"PASS"}else{"FAIL"};Detail=$r.Content.Substring(0,100)}
    }
    catch { $ff += [PSCustomObject]@{Test="4.2 Set feature flags";Status="FAIL";Detail="$($_)"} }
} else {
    $ff += [PSCustomObject]@{Test="4.x Feature flags";Status="SKIP";Detail="No school found"}
}

$ff | Format-Table -AutoSize

# =============================================
# SECTION 5: ACADEMIC YEARS
# =============================================
Write-Host "`n[5] ACADEMIC YEARS" -ForegroundColor Magenta
$ayt = @()

# 5.1 List academic years (need school context - try without school)
try {
    $r = Invoke-WebRequest -Uri "$BASE/academic-years" -Headers $H -UseBasicParsing
    $years = ($r.Content | ConvertFrom-Json)
    $ayt += [PSCustomObject]@{Test="5.1 List academic years";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($years.data.Count)" }
    if ($years.data.Count -gt 0) { $YEAR_ID = $years.data[0].id }
}
catch { $ayt += [PSCustomObject]@{Test="5.1 List academic years";Status="FAIL";Detail="$($_)"} }

# 5.2 Create academic year (missing school context - will fail gracefully)
$yearBody = '{"name":"2026-2027","start_date":"2026-04-01","end_date":"2027-03-31","is_active":true}'
try {
    $r = Invoke-WebRequest -Uri "$BASE/academic-years" -Method POST -Headers $H -Body $yearBody -ContentType "application/json" -UseBasicParsing
    $newYear = ($r.Content | ConvertFrom-Json)
    $ayt += [PSCustomObject]@{Test="5.2 Create academic year";Status=if($r.StatusCode -in @(200,201)){"PASS"}else{"FAIL"};Detail="Created OK"}
}
catch { $ayt += [PSCustomObject]@{Test="5.2 Create academic year";Status="FAIL/403";Detail="$([int]$_.Exception.Response.StatusCode) - SuperAdmin has no school context"} }

$ayt | Format-Table -AutoSize

# =============================================
# SECTION 6: STUDENTS
# =============================================
Write-Host "`n[6] STUDENTS" -ForegroundColor Magenta
$st = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/students" -Headers $H -UseBasicParsing
    $studs = ($r.Content | ConvertFrom-Json)
    $st += [PSCustomObject]@{Test="6.1 List students";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($studs.data.Count)"}
    if ($studs.data -and $studs.data.Count -gt 0) { $STUDENT_ID = $studs.data[0].id }
}
catch { $st += [PSCustomObject]@{Test="6.1 List students";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 6.2 Get student with invalid ID
try {
    Invoke-WebRequest -Uri "$BASE/students/00000000-0000-0000-0000-000000000000" -Headers $H -UseBasicParsing
    $st += [PSCustomObject]@{Test="6.2 Invalid student ID";Status="FAIL";Detail="Should return 404"}
}
catch { $st += [PSCustomObject]@{Test="6.2 Invalid student ID";Status=if($_.Exception.Response.StatusCode -eq "NotFound"){"PASS"}else{"PASS-ish"};Detail="Got: $([int]$_.Exception.Response.StatusCode)"} }

# 6.3 Create student with missing required fields
try {
    $r = Invoke-WebRequest -Uri "$BASE/students" -Method POST -Headers $H -Body '{"first_name":""}' -ContentType "application/json" -UseBasicParsing
    $st += [PSCustomObject]@{Test="6.3 Create student (invalid)";Status="WARN";Detail="Accepted invalid data"}
}
catch { $st += [PSCustomObject]@{Test="6.3 Create student (invalid)";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$st | Format-Table -AutoSize

# =============================================
# SECTION 7: STAFF
# =============================================
Write-Host "`n[7] STAFF" -ForegroundColor Magenta
$stft = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/staff" -Headers $H -UseBasicParsing
    $staff = ($r.Content | ConvertFrom-Json)
    $stft += [PSCustomObject]@{Test="7.1 List staff";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($staff.data.Count)"}
}
catch { $stft += [PSCustomObject]@{Test="7.1 List staff";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 7.2 XSS in staff name
try {
    $xssBody = '{"first_name":"<script>alert(1)</script>","last_name":"Test","email":"xss@test.com","role":"teacher"}'
    $r = Invoke-WebRequest -Uri "$BASE/staff" -Method POST -Headers $H -Body $xssBody -ContentType "application/json" -UseBasicParsing
    $stft += [PSCustomObject]@{Test="7.2 XSS in staff name";Status="WARN";Detail="Accepted XSS payload - check if sanitized in response"}
}
catch { $stft += [PSCustomObject]@{Test="7.2 XSS attempt";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$stft | Format-Table -AutoSize

# =============================================
# SECTION 8: FEES
# =============================================
Write-Host "`n[8] FEES" -ForegroundColor Magenta
$ft = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/fees/structures" -Headers $H -UseBasicParsing
    $fees = ($r.Content | ConvertFrom-Json)
    $ft += [PSCustomObject]@{Test="8.1 List fee structures";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($fees.data.Count)"}
}
catch { $ft += [PSCustomObject]@{Test="8.1 List fee structures";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 8.2 Negative fee amount
try {
    $feeBody = '{"name":"Test Fee","amount":-500,"fee_type":"tuition","academic_year_id":"00000000-0000-0000-0000-000000000000"}'
    $r = Invoke-WebRequest -Uri "$BASE/fees/structures" -Method POST -Headers $H -Body $feeBody -ContentType "application/json" -UseBasicParsing
    $ft += [PSCustomObject]@{Test="8.2 Negative fee amount";Status="FAIL";Detail="Accepted negative amount!"}
}
catch { $ft += [PSCustomObject]@{Test="8.2 Negative fee amount";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$ft | Format-Table -AutoSize

# =============================================
# SECTION 9: ATTENDANCE
# =============================================
Write-Host "`n[9] ATTENDANCE" -ForegroundColor Magenta
$att = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/attendance" -Headers $H -UseBasicParsing
    $atts = ($r.Content | ConvertFrom-Json)
    $att += [PSCustomObject]@{Test="9.1 List attendance";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response received"}
}
catch { $att += [PSCustomObject]@{Test="9.1 List attendance";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 9.2 Future date attendance (should be allowed or warned)
try {
    $attBody = '{"date":"2099-12-31","class_id":"00000000-0000-0000-0000-000000000000","records":[]}'
    $r = Invoke-WebRequest -Uri "$BASE/attendance" -Method POST -Headers $H -Body $attBody -ContentType "application/json" -UseBasicParsing
    $att += [PSCustomObject]@{Test="9.2 Future date attendance";Status="WARN";Detail="Accepted far-future date"}
}
catch { $att += [PSCustomObject]@{Test="9.2 Future date attendance";Status="PASS";Detail="Rejected/constrained: $([int]$_.Exception.Response.StatusCode)"} }

$att | Format-Table -AutoSize

# =============================================
# SECTION 10: EXAMS
# =============================================
Write-Host "`n[10] EXAMS" -ForegroundColor Magenta
$et = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/exams" -Headers $H -UseBasicParsing
    $exams = ($r.Content | ConvertFrom-Json)
    $et += [PSCustomObject]@{Test="10.1 List exams";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($exams.data.Count)"}
}
catch { $et += [PSCustomObject]@{Test="10.1 List exams";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 10.2 Results out of valid range (0-100)
try {
    $resultBody = '{"student_id":"00000000-0000-0000-0000-000000000000","exam_id":"00000000-0000-0000-0000-000000000000","marks_obtained":150,"max_marks":100}'
    $r = Invoke-WebRequest -Uri "$BASE/exams/results" -Method POST -Headers $H -Body $resultBody -ContentType "application/json" -UseBasicParsing
    $et += [PSCustomObject]@{Test="10.2 Marks > max_marks";Status="WARN";Detail="Accepted marks > max!"}
}
catch { $et += [PSCustomObject]@{Test="10.2 Marks > max_marks";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$et | Format-Table -AutoSize

# =============================================
# SECTION 11: TRANSPORT
# =============================================
Write-Host "`n[11] TRANSPORT" -ForegroundColor Magenta
$tt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/transport/routes" -Headers $H -UseBasicParsing
    $routes = ($r.Content | ConvertFrom-Json)
    $tt += [PSCustomObject]@{Test="11.1 List routes";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($routes.data.Count)"}
}
catch { $tt += [PSCustomObject]@{Test="11.1 List routes";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/transport/vehicles" -Headers $H -UseBasicParsing
    $vehicles = ($r.Content | ConvertFrom-Json)
    $tt += [PSCustomObject]@{Test="11.2 List vehicles";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($vehicles.data.Count)"}
}
catch { $tt += [PSCustomObject]@{Test="11.2 List vehicles";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$tt | Format-Table -AutoSize

# =============================================
# SECTION 12: LIBRARY
# =============================================
Write-Host "`n[12] LIBRARY" -ForegroundColor Magenta
$lt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/library/books" -Headers $H -UseBasicParsing
    $books = ($r.Content | ConvertFrom-Json)
    $lt += [PSCustomObject]@{Test="12.1 List books";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($books.data.Count)"}
}
catch { $lt += [PSCustomObject]@{Test="12.1 List books";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 12.2 Borrow non-existent book
try {
    $borrowBody = '{"book_id":"00000000-0000-0000-0000-000000000000","student_id":"00000000-0000-0000-0000-000000000000","due_date":"2026-05-01"}'
    $r = Invoke-WebRequest -Uri "$BASE/library/issue" -Method POST -Headers $H -Body $borrowBody -ContentType "application/json" -UseBasicParsing
    $lt += [PSCustomObject]@{Test="12.2 Borrow non-existent book";Status="FAIL";Detail="Should return 404"}
}
catch { $lt += [PSCustomObject]@{Test="12.2 Borrow non-existent book";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$lt | Format-Table -AutoSize

# =============================================
# SECTION 13: INVENTORY
# =============================================
Write-Host "`n[13] INVENTORY" -ForegroundColor Magenta
$it = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/inventory/items" -Headers $H -UseBasicParsing
    $items = ($r.Content | ConvertFrom-Json)
    $it += [PSCustomObject]@{Test="13.1 List inventory items";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($items.data.Count)"}
}
catch { $it += [PSCustomObject]@{Test="13.1 List inventory";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 13.2 Negative stock quantity
try {
    $invBody = '{"name":"Test Item","quantity":-10,"unit_price":100,"category":"stationery"}'
    $r = Invoke-WebRequest -Uri "$BASE/inventory/items" -Method POST -Headers $H -Body $invBody -ContentType "application/json" -UseBasicParsing
    $it += [PSCustomObject]@{Test="13.2 Negative quantity";Status="FAIL";Detail="Accepted negative stock!"}
}
catch { $it += [PSCustomObject]@{Test="13.2 Negative quantity";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$it | Format-Table -AutoSize

# =============================================
# SECTION 14: COMMUNICATION
# =============================================
Write-Host "`n[14] COMMUNICATION" -ForegroundColor Magenta
$ct = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/communications" -Headers $H -UseBasicParsing
    $comms = ($r.Content | ConvertFrom-Json)
    $ct += [PSCustomObject]@{Test="14.1 List communications";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $ct += [PSCustomObject]@{Test="14.1 List comms";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 14.2 Send message with empty body
try {
    $msgBody = '{"title":"","body":"","recipients":[],"type":"announcement"}'
    $r = Invoke-WebRequest -Uri "$BASE/communications" -Method POST -Headers $H -Body $msgBody -ContentType "application/json" -UseBasicParsing
    $ct += [PSCustomObject]@{Test="14.2 Empty message";Status="WARN";Detail="Accepted empty message body"}
}
catch { $ct += [PSCustomObject]@{Test="14.2 Empty message";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$ct | Format-Table -AutoSize

# =============================================
# SECTION 15: CALENDAR
# =============================================
Write-Host "`n[15] CALENDAR & HOLIDAYS" -ForegroundColor Magenta
$calt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/calendar/events" -Headers $H -UseBasicParsing
    $events = ($r.Content | ConvertFrom-Json)
    $calt += [PSCustomObject]@{Test="15.1 List calendar events";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $calt += [PSCustomObject]@{Test="15.1 Calendar events";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/holidays" -Headers $H -UseBasicParsing
    $holidays = ($r.Content | ConvertFrom-Json)
    $calt += [PSCustomObject]@{Test="15.2 List holidays";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $calt += [PSCustomObject]@{Test="15.2 Holidays";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 15.3 Event with end before start
try {
    $evBody = '{"title":"Bad Event","start_date":"2026-12-31","end_date":"2026-01-01","type":"event"}'
    $r = Invoke-WebRequest -Uri "$BASE/calendar/events" -Method POST -Headers $H -Body $evBody -ContentType "application/json" -UseBasicParsing
    $calt += [PSCustomObject]@{Test="15.3 End before start";Status="FAIL";Detail="Accepted invalid date range!"}
}
catch { $calt += [PSCustomObject]@{Test="15.3 End before start";Status="PASS";Detail="Rejected: $([int]$_.Exception.Response.StatusCode)"} }

$calt | Format-Table -AutoSize

# =============================================
# SECTION 16: REPORTS
# =============================================
Write-Host "`n[16] REPORTS" -ForegroundColor Magenta
$rt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/reports" -Headers $H -UseBasicParsing
    $rt += [PSCustomObject]@{Test="16.1 Reports endpoint";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $rt += [PSCustomObject]@{Test="16.1 Reports";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$rt | Format-Table -AutoSize

# =============================================
# SECTION 17: ROLES AND SETTINGS
# =============================================
Write-Host "`n[17] ROLES & SETTINGS" -ForegroundColor Magenta
$rst = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/roles" -Headers $H -UseBasicParsing
    $roles = ($r.Content | ConvertFrom-Json)
    $rst += [PSCustomObject]@{Test="17.1 List roles";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($roles.data.Count)"}
}
catch { $rst += [PSCustomObject]@{Test="17.1 List roles";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/settings" -Headers $H -UseBasicParsing
    $rst += [PSCustomObject]@{Test="17.2 Get settings";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $rst += [PSCustomObject]@{Test="17.2 Settings";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

# 17.3 Delete a system role (should be protected)
try {
    Invoke-WebRequest -Uri "$BASE/roles/00000000-0000-0000-0000-000000000001" -Method DELETE -Headers $H -UseBasicParsing
    $rst += [PSCustomObject]@{Test="17.3 Delete built-in role";Status="WARN";Detail="Allowed delete of built-in role"}
}
catch { $rst += [PSCustomObject]@{Test="17.3 Delete built-in role";Status="PASS";Detail="Blocked: $([int]$_.Exception.Response.StatusCode)"} }

$rst | Format-Table -AutoSize

# =============================================
# SECTION 18: AUDIT LOGS
# =============================================
Write-Host "`n[18] AUDIT LOGS" -ForegroundColor Magenta
$ault = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/audit-logs" -Headers $H -UseBasicParsing
    $auditlogs = ($r.Content | ConvertFrom-Json)
    $ault += [PSCustomObject]@{Test="18.1 List audit logs";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK - logs tracked"}
}
catch { $ault += [PSCustomObject]@{Test="18.1 Audit logs";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$ault | Format-Table -AutoSize

# =============================================
# SECTION 19: DASHBOARD
# =============================================
Write-Host "`n[19] DASHBOARD" -ForegroundColor Magenta
$dt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/dashboard/stats" -Headers $H -UseBasicParsing
    $dt += [PSCustomObject]@{Test="19.1 Dashboard stats";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $dt += [PSCustomObject]@{Test="19.1 Dashboard";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/dashboard/summary" -Headers $H -UseBasicParsing
    $dt += [PSCustomObject]@{Test="19.2 Dashboard summary";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $dt += [PSCustomObject]@{Test="19.2 Dashboard summary";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$dt | Format-Table -AutoSize

# =============================================
# SECTION 20: SECURITY - IDOR / MASS ASSIGNMENT / RATE LIMITING
# =============================================
Write-Host "`n[20] SECURITY TESTS" -ForegroundColor Magenta
$sect = @()

# 20.1 IDOR - Try to access another school's data via super_admin manipulating school_id in headers
try {
    $r = Invoke-WebRequest -Uri "$BASE/students?school_id=00000000-0000-0000-0000-000000000000" -Headers $H -UseBasicParsing
    $sect += [PSCustomObject]@{Test="20.1 IDOR via query param";Status="INFO";Detail="Response: $($r.StatusCode) - check data isolation"}
}
catch { $sect += [PSCustomObject]@{Test="20.1 IDOR attempt";Status="INFO";Detail="$([int]$_.Exception.Response.StatusCode)"} }

# 20.2 Mass assignment - try to set is_super_admin via update profile
try {
    $body = '{"is_super_admin":true,"email":"attacker@evil.com"}'
    $r = Invoke-WebRequest -Uri "$BASE/auth/me" -Method PUT -Headers $H -Body $body -ContentType "application/json" -UseBasicParsing
    $sect += [PSCustomObject]@{Test="20.2 Mass assignment";Status="WARN";Detail="Check if is_super_admin can be set"}
}
catch { $sect += [PSCustomObject]@{Test="20.2 Mass assignment";Status="PASS";Detail="Blocked: $([int]$_.Exception.Response.StatusCode)"} }

# 20.3 Path traversal in file params
try {
    $r = Invoke-WebRequest -Uri "$BASE/students/../../../etc/passwd" -Headers $H -UseBasicParsing
    $sect += [PSCustomObject]@{Test="20.3 Path traversal";Status="FAIL";Detail="Returned 200 - check response"}
}
catch { $sect += [PSCustomObject]@{Test="20.3 Path traversal";Status="PASS";Detail="Blocked: $([int]$_.Exception.Response.StatusCode)"} }

# 20.4 HTTP Method override
try {
    $r = Invoke-WebRequest -Uri "$BASE/auth/me" -Method GET -Headers ($H + @{"X-HTTP-Method-Override"="DELETE"}) -UseBasicParsing
    $sect += [PSCustomObject]@{Test="20.4 HTTP Method override";Status="INFO";Detail="Status: $($r.StatusCode)"}
}
catch { $sect += [PSCustomObject]@{Test="20.4 HTTP Method override";Status="INFO";Detail="$([int]$_.Exception.Response.StatusCode)"} }

$sect | Format-Table -AutoSize

# =============================================
# SECTION 21: ADMISSIONS
# =============================================
Write-Host "`n[21] ADMISSIONS" -ForegroundColor Magenta
$admt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/admissions" -Headers $H -UseBasicParsing
    $adms = ($r.Content | ConvertFrom-Json)
    $admt += [PSCustomObject]@{Test="21.1 List admissions";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($adms.data.Count)"}
}
catch { $admt += [PSCustomObject]@{Test="21.1 Admissions";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$admt | Format-Table -AutoSize

# =============================================
# SECTION 22: TIMETABLE & SUBJECTS
# =============================================
Write-Host "`n[22] TIMETABLE & SUBJECTS" -ForegroundColor Magenta
$tmt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/subjects" -Headers $H -UseBasicParsing
    $subs = ($r.Content | ConvertFrom-Json)
    $tmt += [PSCustomObject]@{Test="22.1 List subjects";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Count: $($subs.data.Count)"}
}
catch { $tmt += [PSCustomObject]@{Test="22.1 Subjects";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/timetable" -Headers $H -UseBasicParsing
    $tmt += [PSCustomObject]@{Test="22.2 Timetable";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $tmt += [PSCustomObject]@{Test="22.2 Timetable";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$tmt | Format-Table -AutoSize

# =============================================
# SECTION 23: ACCOUNTING / PAYROLL
# =============================================
Write-Host "`n[23] ACCOUNTING & PAYROLL" -ForegroundColor Magenta
$act = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/accounting/transactions" -Headers $H -UseBasicParsing
    $act += [PSCustomObject]@{Test="23.1 Accounting transactions";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $act += [PSCustomObject]@{Test="23.1 Accounting";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/payroll" -Headers $H -UseBasicParsing
    $act += [PSCustomObject]@{Test="23.2 Payroll";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $act += [PSCustomObject]@{Test="23.2 Payroll";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$act | Format-Table -AutoSize

# =============================================
# SECTION 24: HOMEWORK & PTM
# =============================================
Write-Host "`n[24] HOMEWORK & PTM" -ForegroundColor Magenta
$hwt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/homework" -Headers $H -UseBasicParsing
    $hwt += [PSCustomObject]@{Test="24.1 List homework";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $hwt += [PSCustomObject]@{Test="24.1 Homework";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

try {
    $r = Invoke-WebRequest -Uri "$BASE/ptm/meetings" -Headers $H -UseBasicParsing
    $hwt += [PSCustomObject]@{Test="24.2 PTM meetings";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $hwt += [PSCustomObject]@{Test="24.2 PTM";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$hwt | Format-Table -AutoSize

# =============================================
# SECTION 25: DOCUMENT TEMPLATES
# =============================================
Write-Host "`n[25] DOCUMENT TEMPLATES" -ForegroundColor Magenta
$dtt = @()

try {
    $r = Invoke-WebRequest -Uri "$BASE/document-templates" -Headers $H -UseBasicParsing
    $dtt += [PSCustomObject]@{Test="25.1 List templates";Status=if($r.StatusCode -eq 200){"PASS"}else{"FAIL"};Detail="Response OK"}
}
catch { $dtt += [PSCustomObject]@{Test="25.1 Templates";Status="FAIL";Detail="$($_.Exception.Response.StatusCode)"} }

$dtt | Format-Table -AutoSize

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "  ALL TESTS COMPLETED" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan
