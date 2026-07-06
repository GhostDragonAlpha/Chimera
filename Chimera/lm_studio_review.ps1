$url = "http://localhost:1234/v1/chat/completions"

$body = @{
    model = "qwen3.6-35b-a3b-mtp@iq2_m"
    messages = @(
        @{
            role = "system"
            content = "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        },
        @{
            role = "user"
            content = "RESEARCH SUMMARY FOR LOOP 4 TOOLS FEATURES:

Loop 4 — Tools:
- Tool_Shovel_Model (geometry), Tool_Shovel_Material (material)
- Tool_Scanner_Model (geometry), Tool_Scanner_Material (material)
- Tool_Weapon_Model (geometry), Tool_Weapon_Material (material)

Research summary extracted parameters for Tool_Shovel_Model/Material, Tool_Scanner_Model/Material, Tool_Weapon_Model/Material.

Please review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    )
    temperature = 0.1
    max_tokens = 500
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
Write-Output $response.choices[0].message.content
