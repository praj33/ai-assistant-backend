### BHIV EMS Integration Proof

- **Executor**: `ems_executor.py`
- **Gateway path**: `ExecutionService.execute_action("ems", ...)`
- **Enforcement**: Required (decision `ALLOW/REWRITE` + `gateway_auth` token)

#### Capabilities
- **Create task**: `create_task`
- **Update task**: `update_task`
- **Assign task**: `assign_task`

#### Proof Artifacts
- JSON proof: `ems_execution_proof.json`
- Certification: `universal_execution_certification.md`

The EMS proof JSON shows:
- A task being created via the gateway (simulation or EMS API depending on `EMS_API_URL/EMS_API_KEY`)
- Gated by an enforcement decision and using a gateway-issued invocation token.

