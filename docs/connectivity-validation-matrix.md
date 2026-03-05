# Connectivity Validation Matrix

## Targets

- Same LAN: >= 95% connect success
- One public endpoint: >= 85% connect success
- Both home NAT: capture distribution + classified failure reasons

## Scenario Set

- `C-LAN-01`: same subnet, low packet loss
- `C-LAN-02`: same subnet, intermittent packet loss
- `C-PUB-01`: one side public IP, other NAT
- `C-PUB-02`: one side public IP with reconnect storms
- `C-NAT-01`: both side consumer NAT
- `C-NAT-02`: both side consumer NAT with intermittent route changes

## Evidence Requirements

For each scenario, collect:

- Attempt count
- Success count
- Median connect latency
- Failure reason buckets (timeout/refused/path-unreachable/handshake-fail)

## Reporting Format

- Report as JSON artifact per scenario:
  - `scenario_id`
  - `attempts`
  - `successes`
  - `success_rate`
  - `latency_ms_p50`
  - `failure_breakdown`
