# Falcon Strike-AI: Safe Sandbox Execution Engine (Phase 10)

## Overview & Operational Bounds

The Safe Sandbox Execution Engine coordinates and enforces the execution of policy-approved multi-stage adversary emulation campaigns. It serves as the primary enforcement layer bridging abstract campaign plans and observable security signals.

In accordance with PRD Requirements **FR-3.1**, **FR-3.2**, and **FR-3.3**, the Execution Engine enforces strict safety boundaries:
1. **Dry-Run by Default**: Unless explicitly configured and cryptographically approved via two-key tokens, campaigns always execute in non-destructive `DRY_RUN` mode.
2. **Approved Technique Library Only**: Arbitrary commands, user-supplied shell scripts, or raw LLM-generated commands are strictly rejected. Every executable action is mapped directly to a pre-validated contract in the `TechniqueRegistry`.
3. **No Destructive Cloud Mutations**: Emulations do not delete infrastructure, drop databases, wipe IAM configurations, or disrupt active services.
4. **Honest Runtime Transparency**: Falcon Strike-AI never silently degrades container isolation into an unisolated host subprocess while claiming container safety. If Docker is offline, the system explicitly reports runtime unviability or falls back to documented in-memory simulation.

---

## Architectural Components

```
                          ┌──────────────────────────┐
                          │   Policy-Approved Plan   │
                          │      (CampaignPlan)      │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │     ExecutionEngine      │
                          │  (dry_run default=True)  │
                          └─────────────┬────────────┘
                                        │
                ┌───────────────────────┼────────────────────────┐
                │                       │                        │
                ▼                       ▼                        ▼
       ┌──────────────────┐    ┌─────────────────┐     ┌──────────────────┐
       │ Pre-Run Baseline │    │   Kill Switch   │     │  Runner Selector │
       │ Snapshot Capture │    │ Pre-Stage Check │     │ (Docker / Memory)│
       └──────────────────┘    └─────────────────┘     └─────────┬────────┘
                                                                 │
                                        ┌────────────────────────┴────────┐
                                        ▼                                 ▼
                             ┌─────────────────────┐           ┌────────────────────┐
                             │    DockerRunner     │           │  InMemorySimulator │
                             │(Isolated Container) │           │ (Pure Python Inert)│
                             └─────────────────────┘           └────────────────────┘
```

### 1. `ExecutionEngine` (`backend/app/orchestrator/execution_engine.py`)
- Coordinates the complete campaign lifecycle using a single correlated `run_id`.
- Validates policy gate approval status before launching live emulation.
- Performs sequential stage execution with dependency satisfaction checks.
- Interrogates `EmergencyKillSwitch` before every stage to guarantee emergency abort latency under 2 seconds.
- Triggers automatic pre-run baseline capture and post-execution teardown.

### 2. `DockerRunner` (`backend/app/orchestrator/docker_runner.py`)
Implements containerized sandboxed execution for container-ready host environments.
- **Security Profile (when Docker daemon is online)**:
  - Non-root UID/GID (`user="10001:10001"`).
  - Dropped Linux capabilities (`cap_drop=["ALL"]`).
  - Read-only root filesystem (`read_only=True`).
  - Memory ceiling (`mem_limit="256m"`).
  - CPU quota capping (`cpu_quota=50000` / 0.5 cores).
  - Network isolation (`network_mode="none"` or restricted lab bridge).
- **Honest Availability Behavior (when Docker daemon is offline)**:
  - `is_available()` returns `False`.
  - When container execution is requested while unavailable, raises `DockerRuntimeUnavailableError`.
  - Rejects executing arbitrary host processes under false isolation claims.

### 3. `InMemorySimulatorRunner` (`backend/app/orchestrator/in_memory_runner.py`)
- Safe, inert, deterministic simulation fallback (FR-3.3).
- Uses `TechniqueSimulator` to evaluate technique contracts in pure Python.
- Emits realistic, benign telemetry events (CloudTrail and VPC Flow representations) and benign markers without modifying system or cloud infrastructure.
- Zero external network dependencies; 100% offline development readiness.

### 4. `StageLifecycleManager` (`backend/app/orchestrator/lifecycle.py`)
- **Pre-Stage Hook**:
  - Validates kill switch state.
  - Asserts technique ID exists in `TechniqueRegistry`.
  - Validates stage dependencies (`dependencies` subset of `completed_stage_ids`).
- **Post-Stage Hook**:
  - Records execution timing and duration.
  - Registers teardown rollback actions if `contract.teardown_required == True`.
  - Dispatches observables to `TelemetryCollector`.

---

## Execution Modes & State Machine

| Mode | Trigger Condition | Authorization Required | Actions Permitted |
| :--- | :--- | :--- | :--- |
| **`DRY_RUN`** | Default mode, or via `POST /api/v1/executions/dry-run` | Standard operator credentials | Inert behavioral emulation, synthetic telemetry emission, baseline capture. |
| **`LIVE_SIMULATION`** | Explicit flag, via `POST /api/v1/executions/live` | Cryptographic Two-Key approval (Operator + Mentor/Lead) | Bounded, reversible emulation within container or safe runner. Zero destructive actions. |

### Execution Status Progression

```
[PENDING] ──► [RUNNING] ──┬──► [COMPLETED] ──► [TEARDOWN] ──► [BASELINE_VERIFIED]
                          │
                          ├──► [FAILED] (Stage error / unmet dependency)
                          │
                          ├──► [CANCELLED] (Operator manual abort)
                          │
                          └──► [ABORTED_BY_KILL_SWITCH] (Emergency stop < 2s)
```

---

## API Endpoints

- `POST /api/v1/executions/dry-run`: Trigger dry-run of a cached campaign plan.
- `POST /api/v1/executions/live`: Trigger live emulation simulation (requires two-key tokens).
- `GET /api/v1/executions`: List all historical executions.
- `GET /api/v1/executions/{run_id}`: Retrieve detailed execution record and stage progression.
- `POST /api/v1/executions/{run_id}/cancel`: Request immediate cancellation of in-flight execution.
- `GET /api/v1/executions/{run_id}/events`: Retrieve raw simulation events emitted during the run.
- `POST /api/v1/executions/{run_id}/teardown`: Explicitly trigger or verify post-run teardown.

