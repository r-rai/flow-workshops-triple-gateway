# Workshop 1 fallback evidence

**RECORDED · 2026-10-04 · not a fresh run**

Source: `workshops/w1/evidence/rehearsal-evidence.json`. Response timestamps show 06:08:47 UTC. These extracts were copied into the private package while authoring; the shared evidence file was not modified. The saved denial was made through the broad `/mcp` endpoint. It supports the same configured Gate 3 authentication concept, but is not a recorded curated-endpoint denial.

## Broad versus curated discovery

The historical broad catalog had **23** tools, including account reads, case reads, payment execution, approval, administrative reset, incident, and A2A operations. The curated catalog had exactly **get_account** and **get_case**. Current runtime discovery may differ.

Reveal only after audience votes. Say: “In this recorded run, the generator exposed 23 operations. Our prepared support contract selected these two.”

## Successful curated account read

```json
{
  "name": "Acme Retail Checking",
  "status": "active",
  "id": "acc-101",
  "balance": 1500000,
  "currency": "INR"
}
```

The response describes Acme Retail Checking. `1500000` INR minor units = ₹15,000. This is not Maya’s UI balance.

## Successful curated case read

```json
{
  "issue_type": "disputed_transaction",
  "status": "open",
  "customer_id": "cust-8801",
  "id": "case-501",
  "priority": "medium",
  "description": "Customer claims unapproved charge of 45000 INR on checking account."
}
```

This is a separate customer fixture. The record does not establish an account relationship or authorize settlement. Report its status as open; avoid converting the free-text claimed charge into a structured payment amount.

## Excluded operation rejected at invocation

Known broad tool: `list_payments_api_v1_payments_get`.

```json
{
  "result": {
    "isError": true,
    "content": [
      {
        "type": "text",
        "text": "MCP error -32602: Tool list_payments_api_v1_payments_get not found"
      }
    ]
  },
  "jsonrpc": "2.0",
  "id": 24
}
```

This demonstrates rejection at `/mcp/curated`, not removal from every endpoint. Do not replace it with a successful mutation clip.

## Invalid API credential

Recorded MCP transport HTTP status: **200**. Inside the tool’s text result, downstream status: **401**, message: **Invalid API key in request**.

This is a historical broad-endpoint invocation, not the new curated command’s fresh output. Say: “The recorded MCP exchange completed, but the banking API request was denied. We have to inspect the tool outcome.”

## Routing fallback

Use the actual `docker/apisix/apisix-w1.yaml` as static configuration evidence. It configures both MCP endpoints to use the gateway base URL and forwards the incoming lab key. `/api/v1/*` uses key-auth before the banking upstream. Configuration plus recorded responses illustrate the intended path; they are not a full distributed trace or proof of today’s deployment state.

## Presenter recovery line

> “This is recorded evidence from an earlier run. Let’s inspect the outcome we expected and the boundary responsible.”

Fallback to these extracts after 60 seconds of troubleshooting. The machine-readable source extracts are in `recorded-evidence.json`. Capture any future rehearsal into the private live-evidence folder with its own date and mode label.
