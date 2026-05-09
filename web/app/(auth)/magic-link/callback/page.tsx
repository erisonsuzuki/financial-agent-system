import { Suspense } from "react";
import MagicLinkCallbackClient from "./MagicLinkCallbackClient";

function MagicLinkCallbackFallback() {
  return (
    <div className="max-w-md mx-auto mt-24">
      <div className="card">
        <h1 className="text-2xl font-semibold mb-4">Checking your link</h1>
        <p className="text-sm text-slate-300">Please wait...</p>
      </div>
    </div>
  );
}

export default function MagicLinkCallbackPage() {
  return (
    <Suspense fallback={<MagicLinkCallbackFallback />}>
      <MagicLinkCallbackClient />
    </Suspense>
  );
}
