$researchJson = Get-Content "E:\PythonChimera\Chimera\research\loop4\Tool_Scanner_Model\parameters.json" -Raw

$gradeBody = @{
    model = "qwen3.6-35b-a3b-mtp@iq2_m"
    messages = @(@{
        role = "user"
        content = @"
Grade this research summary for feature: Tool_Scanner_Model

Research:
$researchJson

Grading Criteria:
A (4.0): Complete research with specific technical parameters (exact numbers, not ranges), real-world references (actual URLs, not generic names), and clear implementation path (specific MCP tools and steps).
B (3.0): Good research but missing some specific parameters or references.
C (2.0): Basic research with vague parameters, no real references.
F (0.0): Inadequate or missing research.

Output EXACTLY this format with no other text:
Grade: [A/B/C/F]
Score: [0-100]
Reasoning: [one sentence explaining the grade based on the criteria]
"@
    })
    temperature = 0.0
    max_tokens = 1024
} | ConvertTo-Json -Depth 3

try {
    $gradeResponse = Invoke-RestMethod -Uri "http://localhost:1234/v1/chat/completions" -Method Post -Body $gradeBody -ContentType "application/json" -TimeoutSec 60
    $gradeText = $gradeResponse.choices[0].message.content
    
    # If content is empty, check reasoning_content field
    if (-not $gradeText) {
        $gradeText = $gradeResponse.choices[0].message.reasoning_content
    }
    
    Write-Output "Professor Response:"
    Write-Output $gradeText
} catch {
    Write-Output "ERROR: LM Studio request failed: $_"
    Write-Output "Retrying once..."
    Start-Sleep -Seconds 5
    try {
        $gradeResponse = Invoke-RestMethod -Uri "http://localhost:1234/v1/chat/completions" -Method Post -Body $gradeBody -ContentType "application/json" -TimeoutSec 60
        $gradeText = $gradeResponse.choices[0].message.content
        if (-not $gradeText) {
            $gradeText = $gradeResponse.choices[0].message.reasoning_content
        }
    } catch {
        Write-Output "FATAL: LM Studio unavailable. Cannot proceed with Professor review."
        Write-Output "Grade set to C (default). Proceeding with caution."
        $gradeText = "Grade: C`nScore: 70`nReasoning: LM Studio unavailable, default grade assigned."
    }
}