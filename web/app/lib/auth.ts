import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function readAuthCookie(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get("fas_token")?.value;
}

export async function requireSession() {
  const token = await readAuthCookie();
  if (!token) {
    redirect("/login");
  }
  return { token };
}
