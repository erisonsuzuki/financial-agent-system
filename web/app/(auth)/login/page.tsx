import { redirect } from "next/navigation";
import { readAuthCookie } from "@/app/lib/auth";
import LoginForm from "./LoginForm";

export default async function LoginPage() {
  if (await readAuthCookie()) {
    redirect("/dashboard");
  }

  return (
    <div className="max-w-md mx-auto mt-24">
      <div className="card">
        <h1 className="text-2xl font-semibold mb-6">Sign in</h1>
        <LoginForm />
      </div>
    </div>
  );
}
