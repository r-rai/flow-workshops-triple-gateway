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

If local Docker fails, use a secured presenter endpoint with distinct identities
and isolated seeded data. Initially allow at most two concurrent fallback runs
pending load testing; queue additional users or use presenter demonstration.
Fallback uses labelled model replay, and participant provider keys remain local.

## Model Access and Preparation

Participants bring their own hosted-model credentials for live local inference.
All exercises must also work with labelled deterministic model replay. Download
prebuilt images and run preflight before the session; do not build or install
dependencies during the timed exercise.

See the [delivery plan](../workshops/delivery-plan.md) and
[VPS setup guide](vps-setup-guide.md).
