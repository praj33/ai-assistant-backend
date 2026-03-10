"""
Compatibility shim for Raj's enforcement engine imports.

`app/external/enforcement/enforcement_engine.py` imports `EnforcementVerdict`
from `enforcement_verdict`. The canonical verdict type lives in
`app.external.enforcement.enforcement_verdict`.
"""

from app.external.enforcement.enforcement_verdict import EnforcementVerdict

