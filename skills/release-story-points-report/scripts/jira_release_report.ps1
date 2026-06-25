param(
    [Parameter(Mandatory = $true)]
    [string]$Release,

    [string]$TeamAlias = "",
    [string]$Token = $env:JIRA_TOKEN,
    [string]$OutDir = "",
    [switch]$Html
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Token)) {
    throw "JIRA_TOKEN is not set. Provide -Token or set `$env:JIRA_TOKEN first."
}

$jiraBase = "https://jira.ringcentral.com"
$storyPointsField = "customfield_10422"
$devEstimateField = "customfield_25757"
$qaEstimateField = "customfield_25958"
$productionField = "customfield_10570"
$teamField = "cf[17553]"

$headers = @{
    Authorization = "Bearer $Token"
    Accept = "application/json"
}

function Normalize-Release([string]$value) {
    $trimmed = $value.Trim()
    if ($trimmed -match "\d{2}\.\d\.\d{2}") {
        return $Matches[0]
    }
    return $trimmed
}

$releaseNumber = Normalize-Release $Release

function Test-Q3OrLaterRelease([string]$value) {
    if ($value -match "^(\d{2})\.(\d+)\.(\d{2})$") {
        $year = [int]$Matches[1]
        $quarter = [int]$Matches[2]
        if ($year -gt 26) {
            return $true
        }
        return ($year -eq 26 -and $quarter -ge 3)
    }
    return $false
}

$useVoipExpandedScope = Test-Q3OrLaterRelease $releaseNumber

$teamConfigs = @(
    [pscustomobject]@{ Alias = "Jupiter Titan"; Project = "FIJI"; Sprint = $releaseNumber; TeamJql = "$teamField = `"Phone-J-Titan-XMN`"" },
    [pscustomobject]@{ Alias = "Jupiter IND"; Project = "FIJI"; Sprint = $releaseNumber; TeamJql = "$teamField = `"Phone-Jupiter-IND`"" },
    [pscustomobject]@{ Alias = "EU Jupiter"; Project = "FIJI"; Sprint = $releaseNumber; TeamJql = "$teamField = `"EU-Jupiter-team`"" },
    [pscustomobject]@{ Alias = "VoIP"; Project = "FIJI,MTR"; Sprint = $releaseNumber; TeamJql = "$teamField = `"XMN-VoIP`"" },
    [pscustomobject]@{ Alias = "mThor Ping&Pong"; Project = "MTR"; Sprint = $releaseNumber; TeamJql = "$teamField in (`"Phone-M-Ping-XMN`",`"Phone-M-Pong-XMN`")" }
)

if (-not [string]::IsNullOrWhiteSpace($TeamAlias)) {
    $needle = $TeamAlias.Trim().ToLowerInvariant()
    $teamConfigs = @($teamConfigs | Where-Object {
        $_.Alias.ToLowerInvariant().Contains($needle) -or
        ($needle -eq "titan" -and $_.Alias -eq "Jupiter Titan") -or
        ($needle -eq "mthor" -and $_.Alias -eq "mThor Ping&Pong") -or
        ($needle -eq "pingpong" -and $_.Alias -eq "mThor Ping&Pong") -or
        ($needle -eq "ping&pong" -and $_.Alias -eq "mThor Ping&Pong") -or
        ($needle -eq "mthor pingpong" -and $_.Alias -eq "mThor Ping&Pong")
    })

    if ($teamConfigs.Count -eq 0) {
        throw "Unknown TeamAlias '$TeamAlias'. Known aliases: Jupiter Titan, Jupiter IND, EU Jupiter, VoIP, mThor Ping&Pong."
    }
}

function Invoke-JiraSearch([string]$jql) {
    $all = @()
    $startAt = 0
    $pageSize = 100
    do {
        $body = @{
            jql = $jql
            startAt = $startAt
            maxResults = $pageSize
            fields = @(
                "key",
                "summary",
                "issuetype",
                "project",
                "status",
                "assignee",
                "fixVersions",
                $storyPointsField,
                $devEstimateField,
                $qaEstimateField,
                $productionField
            )
        } | ConvertTo-Json -Depth 6

        $result = Invoke-RestMethod `
            -Uri "$jiraBase/rest/api/2/search" `
            -Headers ($headers + @{ "Content-Type" = "application/json" }) `
            -Method Post `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 60

        if ($result.issues) {
            $all += $result.issues
        }
        $startAt += $pageSize
        $total = [int]$result.total
    } while ($startAt -lt $total)

    return $all
}

function Number-OrZero($value) {
    if ($null -eq $value -or $value -eq "") {
        return 0.0
    }
    return [double]$value
}

function Get-OptionValue($value) {
    if ($null -eq $value) {
        return ""
    }
    if ($value -is [string]) {
        return $value
    }
    if ($value.PSObject.Properties["value"]) {
        return [string]$value.value
    }
    return [string]$value
}

function Get-TeamQueries($team) {
    if ($team.Alias -eq "VoIP") {
        $queries = @(
            [pscustomobject]@{
                Source = "FIJI/MTR VoIP sprint"
                ProjectLabel = "FIJI,MTR"
                Jql = "project in (FIJI, MTR) AND $($team.TeamJql) AND sprint = `"$($team.Sprint)`" ORDER BY key ASC"
            }
        )

        if ($useVoipExpandedScope) {
            $queries += [pscustomobject]@{
                Source = "Log Insight FV"
                ProjectLabel = "LI"
                Jql = "project = LI AND fixVersion = `"Log Insight $($team.Sprint)`" ORDER BY key ASC"
            }
            $queries += [pscustomobject]@{
                Source = "Rooms VoIP FV"
                ProjectLabel = "RCVR"
                Jql = "project = RCVR AND $($team.TeamJql) AND fixVersion = `"Rooms $($team.Sprint)`" ORDER BY key ASC"
            }
        }

        return $queries
    }

    return @(
        [pscustomobject]@{
            Source = "$($team.Project) sprint"
            ProjectLabel = $team.Project
            Jql = "project = $($team.Project) AND $($team.TeamJql) AND sprint = `"$($team.Sprint)`" ORDER BY key ASC"
        }
    )
}

$allRows = @()
$teamSummaries = @()

foreach ($team in $teamConfigs) {
    $teamQueries = @(Get-TeamQueries $team)
    $teamRows = @()

    foreach ($query in $teamQueries) {
        try {
            $issues = Invoke-JiraSearch $query.Jql
        }
        catch {
            Write-Warning "Skipped source '$($query.Source)' because Jira rejected the query: $($_.Exception.Message)"
            $issues = @()
        }

        $rows = foreach ($issue in $issues) {
            $fields = $issue.fields
            $sp = Number-OrZero $fields.$storyPointsField
            $dev = Number-OrZero $fields.$devEstimateField
            $qa = Number-OrZero $fields.$qaEstimateField
            $productionValue = Get-OptionValue $fields.$productionField
            [pscustomobject]@{
                Team = $team.Alias
                Project = if ($fields.project) { $fields.project.key } else { $query.ProjectLabel }
                Source = $query.Source
                Release = $team.Sprint
                Sprint = $team.Sprint
                Key = $issue.key
                IssueType = $fields.issuetype.name
                Status = $fields.status.name
                Assignee = if ($fields.assignee) { $fields.assignee.displayName } else { "" }
                StoryPoints = $sp
                DevEstimate = $dev
                QaEstimate = $qa
                Production = $productionValue
                IsEmbedBug = ($fields.issuetype.name -eq "Bug" -and $productionValue -eq "No")
                Summary = $fields.summary
                Url = "$jiraBase/browse/$($issue.key)"
                Jql = $query.Jql
            }
        }

        $teamRows += $rows
    }

    $allRows += $teamRows

    $deliveryRows = @($teamRows | Where-Object { $_.IssueType -in @("User Story", "Technical task", "Improvement") })
    $embedBugRows = @($teamRows | Where-Object { $_.IsEmbedBug })
    $activeRows = @($teamRows | Where-Object { $_.Status -notin @("Closed", "Done", "Resolved", "Cancelled") })
    $missingSpRows = @($teamRows | Where-Object { $_.StoryPoints -eq 0 -and $_.IssueType -in @("User Story", "Technical task", "Improvement") })
    $totalSp = (@($teamRows) | Measure-Object StoryPoints -Sum).Sum
    $bugRatio = if ($totalSp -gt 0) { [math]::Round($embedBugRows.Count / $totalSp, 4) } else { $null }

    $teamSummaries += [pscustomobject]@{
        Team = $team.Alias
        Project = $team.Project
        Release = $team.Sprint
        Sprint = $team.Sprint
        Issues = @($teamRows).Count
        TotalSP = $totalSp
        DeliverySP = ($deliveryRows | Measure-Object StoryPoints -Sum).Sum
        EmbedBugs = $embedBugRows.Count
        BugRatio = $bugRatio
        BugRatioPct = if ($null -ne $bugRatio) { [math]::Round($bugRatio * 100, 2) } else { "N/A" }
        DevEstimate = (@($teamRows) | Measure-Object DevEstimate -Sum).Sum
        QaEstimate = (@($teamRows) | Measure-Object QaEstimate -Sum).Sum
        Active = $activeRows.Count
        MissingDeliverySP = $missingSpRows.Count
        Jql = (($teamQueries | ForEach-Object { $_.Jql }) -join " ; ")
    }
}

$grand = [pscustomobject]@{
    Teams = $teamSummaries.Count
    Issues = ($teamSummaries | Measure-Object Issues -Sum).Sum
    TotalSP = ($teamSummaries | Measure-Object TotalSP -Sum).Sum
    DeliverySP = ($teamSummaries | Measure-Object DeliverySP -Sum).Sum
    EmbedBugs = ($teamSummaries | Measure-Object EmbedBugs -Sum).Sum
    DevEstimate = ($teamSummaries | Measure-Object DevEstimate -Sum).Sum
    QaEstimate = ($teamSummaries | Measure-Object QaEstimate -Sum).Sum
    Active = ($teamSummaries | Measure-Object Active -Sum).Sum
    MissingDeliverySP = ($teamSummaries | Measure-Object MissingDeliverySP -Sum).Sum
}

$grandBugRatio = if ($grand.TotalSP -gt 0) { [math]::Round($grand.EmbedBugs / $grand.TotalSP, 4) } else { $null }
$grandBugRatioPct = if ($null -ne $grandBugRatio) { [math]::Round($grandBugRatio * 100, 2) } else { "N/A" }

Write-Host ""
Write-Host "Release report: $releaseNumber"
Write-Host "Teams checked: $($grand.Teams)"
Write-Host "Issues: $($grand.Issues)"
Write-Host "Total SP: $($grand.TotalSP)"
Write-Host "Delivery SP (User Story + Technical task + Improvement): $($grand.DeliverySP)"
Write-Host "Embed Bugs: $($grand.EmbedBugs)"
Write-Host "Bug Ratio: $(if ($null -ne $grandBugRatio) { "$grandBugRatio ($grandBugRatioPct%)" } else { "N/A" })"
Write-Host "DEV Estimate: $($grand.DevEstimate)"
Write-Host "QA Estimate: $($grand.QaEstimate)"
Write-Host "Active issues: $($grand.Active)"
Write-Host "Missing delivery SP: $($grand.MissingDeliverySP)"
Write-Host ""
Write-Host "Team breakdown:"
$teamSummaries | Sort-Object Team | Format-Table Team,Issues,TotalSP,DeliverySP,EmbedBugs,BugRatioPct,DevEstimate,QaEstimate,Active,MissingDeliverySP -AutoSize

Write-Host ""
Write-Host "Story Points by issue type:"
$allRows | Group-Object IssueType | ForEach-Object {
    [pscustomobject]@{
        IssueType = $_.Name
        Count = $_.Count
        StoryPoints = ($_.Group | Measure-Object StoryPoints -Sum).Sum
    }
} | Sort-Object IssueType | Format-Table -AutoSize

Write-Host ""
Write-Host "Story Points by status:"
$allRows | Group-Object Status | ForEach-Object {
    [pscustomobject]@{
        Status = $_.Name
        Count = $_.Count
        StoryPoints = ($_.Group | Measure-Object StoryPoints -Sum).Sum
    }
} | Sort-Object Status | Format-Table -AutoSize

if ($grand.Active -gt 0) {
    Write-Host ""
    Write-Host "Active issues:"
    $allRows | Where-Object { $_.Status -notin @("Closed", "Done", "Resolved", "Cancelled") } |
        Select-Object Team,Key,IssueType,Status,StoryPoints,Production,Assignee,Summary,Url |
        Format-Table -AutoSize
}

if (-not [string]::IsNullOrWhiteSpace($OutDir)) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $safeRelease = $releaseNumber -replace "[^0-9A-Za-z.-]", "-"
    $detailPath = Join-Path $OutDir "jira-release-$safeRelease-detail.csv"
    $summaryPath = Join-Path $OutDir "jira-release-$safeRelease-summary.csv"
    $allRows | Export-Csv -LiteralPath $detailPath -NoTypeInformation -Encoding UTF8
    $teamSummaries | Export-Csv -LiteralPath $summaryPath -NoTypeInformation -Encoding UTF8
    Write-Host ""
    Write-Host "CSV detail: $detailPath"
    Write-Host "CSV summary: $summaryPath"

    if ($Html) {
        $htmlPath = Join-Path $OutDir "jira-release-$safeRelease-report.html"
        $cards = @(
            @("Issues", $grand.Issues),
            @("Total SP", $grand.TotalSP),
            @("Delivery SP", $grand.DeliverySP),
            @("Embed Bugs", $grand.EmbedBugs),
            @("Bug Ratio", $(if ($null -ne $grandBugRatio) { "$grandBugRatioPct%" } else { "N/A" })),
            @("Active", $grand.Active),
            @("Missing SP", $grand.MissingDeliverySP),
            @("DEV / QA", "$($grand.DevEstimate) / $($grand.QaEstimate)")
        )
        $cardHtml = ($cards | ForEach-Object {
            "<div class='card'><div class='label'>$($_[0])</div><div class='value'>$($_[1])</div></div>"
        }) -join "`n"

        $teamRowsHtml = ($teamSummaries | Sort-Object Team | ForEach-Object {
            $bugRatioDisplay = if ($_.BugRatioPct -eq "N/A") { "N/A" } else { "$($_.BugRatioPct)%" }
            "<tr><td>$($_.Team)</td><td>$($_.Issues)</td><td>$($_.TotalSP)</td><td>$($_.DeliverySP)</td><td>$($_.EmbedBugs)</td><td>$bugRatioDisplay</td><td>$($_.DevEstimate)</td><td>$($_.QaEstimate)</td><td>$($_.Active)</td><td>$($_.MissingDeliverySP)</td></tr>"
        }) -join "`n"

        $issueRowsHtml = ($allRows | Sort-Object Team, Key | ForEach-Object {
            "<tr><td>$($_.Team)</td><td><a href='$($_.Url)'>$($_.Key)</a></td><td>$($_.IssueType)</td><td>$($_.Status)</td><td>$($_.StoryPoints)</td><td>$($_.Production)</td><td>$($_.Assignee)</td><td>$([System.Web.HttpUtility]::HtmlEncode($_.Summary))</td></tr>"
        }) -join "`n"

        $htmlContent = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Jira Release Report - $releaseNumber</title>
<style>
body { font-family: Arial, sans-serif; margin: 28px; color: #1f2933; background: #f7f8fb; }
h1 { margin: 0 0 6px; font-size: 28px; }
.sub { color: #64748b; margin-bottom: 22px; }
.cards { display: grid; grid-template-columns: repeat(8, 1fr); gap: 12px; margin-bottom: 24px; }
.card { background: white; border: 1px solid #dde3ea; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(16,24,40,.04); }
.label { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
.value { font-size: 26px; font-weight: 700; margin-top: 7px; color: #0f172a; }
table { width: 100%; border-collapse: collapse; background: white; margin-bottom: 24px; border: 1px solid #dde3ea; }
th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid #edf1f5; font-size: 13px; vertical-align: top; }
th { background: #e8eef7; color: #0f172a; font-weight: 700; }
a { color: #1558d6; text-decoration: none; }
.section-title { font-size: 18px; font-weight: 700; margin: 20px 0 8px; }
</style>
</head>
<body>
<h1>Jira Release Report - $releaseNumber</h1>
<div class="sub">Generated from Jira current data. Team filters follow Phone/Jupiter/mThor release report mapping.</div>
<div class="cards">$cardHtml</div>
<div class="section-title">Team Breakdown</div>
<table>
<thead><tr><th>Team</th><th>Issues</th><th>Total SP</th><th>Delivery SP</th><th>Embed Bugs</th><th>Bug Ratio</th><th>DEV</th><th>QA</th><th>Active</th><th>Missing SP</th></tr></thead>
<tbody>$teamRowsHtml</tbody>
</table>
<div class="section-title">Issue Details</div>
<table>
<thead><tr><th>Team</th><th>Key</th><th>Type</th><th>Status</th><th>SP</th><th>Production</th><th>Assignee</th><th>Summary</th></tr></thead>
<tbody>$issueRowsHtml</tbody>
</table>
</body>
</html>
"@
        [System.IO.File]::WriteAllText($htmlPath, $htmlContent, [System.Text.Encoding]::UTF8)
        Write-Host "HTML report: $htmlPath"
    }
}
