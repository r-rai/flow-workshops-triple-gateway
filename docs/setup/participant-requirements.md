# Participant Requirements

## Target

-   Windows 11
-   16 GB RAM
-   4+ CPU cores
-   SSD
-   Docker Desktop / WSL2
-   Git
-   browser
-   VS Code or equivalent

## Memory

Do not assume 16 GB is available to Docker. A useful lab-test
configuration is:

``` ini
[wsl2]
memory=5GB
swap=2GB
processors=4
```

Corporate-managed devices may restrict these settings. Changing
`.wslconfig` requires WSL restart.

## Pre-Workshop Validation

Provide a script that checks Docker, Compose, required ports, image
availability, workshop network startup, memory and LLM credentials where
applicable.

## Pre-Pull

Do not depend on conference Wi-Fi. Participants should pull all required
images before workshop day.

## Fallback

If local Docker fails, allow the participant client to point to the
presenter APISIX/MCP endpoint. The presenter VPS is a failsafe, not a
multi-tenant agent runtime.
