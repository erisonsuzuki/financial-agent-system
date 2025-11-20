# Implementation Blueprint: Password Hash Generator Make Target

## Overview
Create a new `make generate_password password=...` target that runs inside the existing `api` container and uses `app.security.get_password_hash` to output a bcrypt hash suitable for seeding user accounts.

## Implementation Phases

### Phase 1: Makefile Target Definition
**Objective**: Add a Makefile target that validates input and executes the hashing helper inside the `api` container.
**Code Proposal**:
```makefile
generate_password:
	@if [ -z "$(password)" ]; then \
		echo "Usage: make generate_password password=YourPlaintext"; \
		exit 1; \
	fi
	@PASSWORD_INPUT="$(password)" docker compose exec api python - <<'PY'
from app.security import get_password_hash
import os
password = os.environ["PASSWORD_INPUT"]
print(get_password_hash(password))
PY
```
The command sets `PASSWORD_INPUT` in-line before starting Python so the script receives the plaintext securely.
**Tests**:
- Run `make generate_password password=TempPass123!` and confirm it prints a bcrypt hash.
- Provide no password (`make generate_password`) to verify the usage message appears and exits non-zero.

### Phase 2: Usage Documentation
**Objective**: Document the new command in `README.md` (Common Commands) so developers know how to generate hashes.
**Code Proposal**:
```markdown
- `make generate_password password=MySecret` — prints a bcrypt hash using the app’s security helper.
```
**Tests**:
- `rg "generate_password" README.md` to confirm the entry exists.
- Follow the README instructions to ensure the command works exactly as documented.

## Consolidated Checklist
- [ ] Add `generate_password` target to `Makefile` with parameter validation and container execution.
- [ ] Document the new command inside `README.md` under Common Commands.

## Notes
- Keep the plaintext password out of logs except for the explicit usage message; the command should only echo the resulting hash.
- The inline Python must import `app.security` from within the container to ensure consistent hashing parameters (bcrypt rounds, etc.).
