# Implementation Blueprint: Phase 17 Read-only Dashboard

## Overview
Allow unauthenticated users to view a limited dashboard: show the assets list without amounts/average price, disable question submission (blocked send), and surface a top-right login button opening a modal for authentication. Authenticated users retain full functionality.

## Implementation Phases

### Phase 1: Auth Detection and Read-only Gate
**Objective**: Detect auth state client-side (reuse cookie logic) and gate chat/actions for unauthenticated users while allowing assets list rendering.
**Code Proposal**:
```tsx
// web/app/dashboard/ClientChat.tsx
import { useAuthToken } from "@/app/hooks/useAuthToken"; // client hook wrapping cookie detection (uses existing cookie logic)

const isAuthenticated = useAuthToken();

// pass isAuthenticated to child components for gating
const handleSubmit = (value: string) => {
  if (!isAuthenticated) return;
  mutation.mutate(value);
};
<ChatInput onSubmit={handleSubmit} loading={mutation.isPending} isDisabled={!isAuthenticated} />
<AssetSidebar assets={assets} loading={assetsLoading} error={assetsError ?? null} hideAmounts={!isAuthenticated} />
```
**Tests**:
- Unit test `useAuthToken` for detecting presence/absence of `fas_token` (mock cookies); ensure it shares logic with `readAuthCookie`.
- Component test: unauthenticated render shows disabled send button and no amounts; authenticated render shows enabled send + amounts.
- Integration: `handleSubmit` is a no-op when unauthenticated even if the button is re-enabled by the browser.

### Phase 2: Asset List Redaction When Unauthenticated
**Objective**: Render assets list but omit amounts/average price when not authenticated.
**Code Proposal**:
```tsx
// web/app/components/AssetSidebar.tsx
export default function AssetSidebar({ assets, loading, error, hideAmounts = false }: Props) {
  ...
  {assets.map((asset) => (
    <li ...>
      <div className="min-w-0">
        <p className="font-semibold text-slate-100 truncate">{asset.name}</p>
        {!hideAmounts && <p className="text-xs text-slate-400">{asset.units} units</p>}
      </div>
      {!hideAmounts && <p className="text-emerald-300 font-mono text-sm">${asset.averagePrice.toFixed(2)}</p>}
    </li>
  ))}
}
```
**Tests**:
- Component test asserting amounts are hidden when `hideAmounts=true` and present otherwise.

### Phase 3: Chat Input Disable State
**Objective**: Prevent question submission when unauthenticated; present “Login to ask” cue.
**Code Proposal**:
```tsx
// web/app/components/ChatInput.tsx
export default function ChatInput({ onSubmit, loading, isDisabled = false }: ChatInputProps) {
  ...
  <textarea disabled={isDisabled} ... />
  <button type="submit" disabled={loading || isDisabled}>
    {isDisabled ? "Login to ask" : loading ? "Sending..." : "Send"}
  </button>
}
```
**Tests**:
- Component test verifying textarea/button are disabled and label changes when `isDisabled=true`.

### Phase 4: Login Button + Modal
**Objective**: Add a top-right login button that opens the existing login flow in a modal (client-side; reuse existing auth endpoints and `LoginForm`).
**Code Proposal**:
```tsx
// web/app/layout.tsx or a navbar component
const [showLogin, setShowLogin] = useState(false);
<button className="..." onClick={() => setShowLogin(true)}>Login</button>
{showLogin && (
  <LoginModal onClose={() => setShowLogin(false)}>
    <LoginForm /> {/* reuse existing form from (auth)/login/LoginForm.tsx */}
  </LoginModal>
)}
```
If a login modal component doesn’t exist, create `web/app/components/LoginModal.tsx` with the existing login form.
**Tests**:
- Component test to ensure clicking the login button toggles modal visibility.
- Manual QA: login via modal sets `fas_token` and reenables chat + amounts.

## Consolidated Checklist
- [x] Add auth token detection hook and gate chat/assets display based on authentication.
- [x] Hide asset amounts/average price when unauthenticated.
- [x] Disable chat submission (textarea/button) when unauthenticated with clear CTA text.
- [x] Add top-right login button that opens a login modal leveraging existing auth flow.

## Notes
- Single-user dev environments may already have a token; ensure gating falls back to cookie presence. If API calls error 401, handle gracefully in hooks to avoid crash loops.
- Maintain existing Tailwind styling; keep responsive layout intact.
- If a shared layout/header exists, add the login button there to appear on the dashboard. Otherwise, add to the dashboard page container.
