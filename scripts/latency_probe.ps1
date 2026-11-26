# latency_probe.ps1 - send one routing-sized request to Ollama and show where the time went.
# Usage: .\scripts\latency_probe.ps1 -Model qwen3:8b [-OllamaHost 192.168.1.240:11434]
param(
    [string]$Model = "qwen3:8b",
    [string]$OllamaHost = "192.168.1.240:11434"
)

# ~600-token system prompt, similar in size to the router's
$system = ("You route requests for a personal AI team. Pick exactly one agent. " * 40)
$body = @{
    model    = $Model
    stream   = $false
    think    = $false
    format   = @{ type = "object"; properties = @{ agent = @{ type = "string" } }; required = @("agent") }
    messages = @(
        @{ role = "system"; content = $system },
        @{ role = "user"; content = "i have like 12 things open, what should i work on first" }
    )
} | ConvertTo-Json -Depth 6

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$r = Invoke-RestMethod "http://$OllamaHost/api/chat" -Method Post -Body $body -ContentType "application/json"
$sw.Stop()

$ns = 1e9
$prefillTps = if ($r.prompt_eval_duration) { $r.prompt_eval_count / ($r.prompt_eval_duration / $ns) } else { 0 }
$decodeTps  = if ($r.eval_duration) { $r.eval_count / ($r.eval_duration / $ns) } else { 0 }

[pscustomobject]@{
    model           = $Model
    client_seconds  = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    total_seconds   = [math]::Round($r.total_duration / $ns, 2)
    load_seconds    = [math]::Round($r.load_duration / $ns, 2)
    prompt_tokens   = $r.prompt_eval_count
    prefill_seconds = [math]::Round($r.prompt_eval_duration / $ns, 2)
    prefill_tok_s   = [math]::Round($prefillTps, 1)
    output_tokens   = $r.eval_count
    decode_seconds  = [math]::Round($r.eval_duration / $ns, 2)
    decode_tok_s    = [math]::Round($decodeTps, 1)
    answer          = $r.message.content
} | Format-List
