import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "VoiceRx Sync — Clinical AI Platform",
  description: "AI-powered voice-to-prescription system for doctors",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-[#080d1a] text-slate-200 antialiased">
        <AuthProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#0f1a2e",
                color: "#e2e8f0",
                border: "1px solid rgba(99,102,241,0.2)",
                borderRadius: "12px",
                fontSize: "0.875rem",
              },
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
