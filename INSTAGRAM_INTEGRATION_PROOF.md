### Instagram Integration Proof

- **Executor**: `instagram_executor.py`
- **Inbound**: `/webhook/instagram` (Meta webhook)
- **Gateway path**: `ExecutionService.execute_action("instagram", ...)`
- **Enforcement**: Required (decision `ALLOW/REWRITE` + `gateway_auth` token)

#### Capabilities
- **Send DM**: via Meta Graph API (`/{page_id}/messages`)
- **Receive DM webhook**: Instagram/Meta webhook → `webhook/instagram` → `handle_assistant_request`

#### Proof Artifacts
- JSON proof: `instagram_execution_proof.json`
- Certification: `universal_execution_certification.md`

These proofs demonstrate that:
- The Instagram executor is wired behind the universal execution gateway.
- Inbound messages follow the full pipeline before any outbound/side effects.

