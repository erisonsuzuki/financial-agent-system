import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Financial Agent Console",
  description: "Chat with your financial agents via a web UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100">
        <Providers>
          <div className="min-h-screen p-6">
            <header className="flex items-center justify-end mb-6">
              {/* Reserved for login modal trigger in dashboard */}
            </header>
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
