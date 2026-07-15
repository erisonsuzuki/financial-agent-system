import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Financial Agent System",
  description: "Chat with your financial agents via a web UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-surface text-on-surface">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
