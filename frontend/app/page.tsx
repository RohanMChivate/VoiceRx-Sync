"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Stethoscope, Mic, BarChart3, FileText, Shield } from "lucide-react";
import { useAuth } from "@/lib/auth";
import toast from "react-hot-toast";

const features = [
  { icon: Mic,       label: "Voice → Prescription", desc: "Speak naturally, AI does the rest" },
  { icon: BarChart3, label: "Smart Analytics",       desc: "Track consultations over time" },
  { icon: FileText,  label: "FHIR Ready",            desc: "Standards-compliant output" },
  { icon: Shield,    label: "Secure & Private",      desc: "Scoped per doctor account" },
];

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading]);

  const handleLogin = async () => {
    try {
      await login();
      router.replace("/dashboard");
    } catch (e: unknown) {
      toast.error("Sign-in failed. Please try again.");
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* ── Left: Hero ──────────────────────────────────────────────── */}
      <div className="relative flex-1 flex flex-col justify-center px-12 py-16
                      bg-gradient-to-br from-[#0d1526] via-[#0f172a] to-[#080d1a]
                      overflow-hidden">
        {/* Glow blobs */}
        <div className="absolute top-[-80px] left-[-80px] w-72 h-72 rounded-full
                        bg-indigo-600/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-[-60px] right-[-60px] w-56 h-56 rounded-full
                        bg-violet-600/10 blur-3xl pointer-events-none" />

        <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6 }} className="max-w-lg">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600
                            flex items-center justify-center shadow-lg shadow-indigo-500/30 pulse-ring">
              <Stethoscope size={22} className="text-white" />
            </div>
            <div>
              <p className="text-white font-bold text-lg leading-none">VoiceRx Sync</p>
              <p className="text-slate-500 text-xs mt-0.5">Clinical AI Platform</p>
            </div>
          </div>

          <h1 className="text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-4">
            Voice-powered<br />
            <span className="gradient-text">prescriptions</span><br />
            for modern doctors
          </h1>
          <p className="text-slate-400 text-base leading-relaxed mb-10">
            Record your consultation, let AI extract the prescription, review it in seconds,
            and sync it to a secure cloud database — FHIR-ready.
          </p>

          {/* Features grid */}
          <div className="grid grid-cols-2 gap-3">
            {features.map(({ icon: Icon, label, desc }) => (
              <motion.div key={label}
                whileHover={{ y: -2 }}
                className="glass p-4 rounded-xl flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center
                                justify-center flex-shrink-0">
                  <Icon size={16} className="text-indigo-400" />
                </div>
                <div>
                  <p className="text-slate-200 text-sm font-semibold leading-none mb-1">{label}</p>
                  <p className="text-slate-500 text-xs">{desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* ── Right: Login card ────────────────────────────────────────── */}
      <div className="flex items-center justify-center px-8 py-16 lg:w-[480px]
                      bg-[#080d1a] border-l border-white/5">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600
                            flex items-center justify-center mx-auto mb-4
                            shadow-xl shadow-indigo-500/30">
              <Stethoscope size={28} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white">Welcome back</h2>
            <p className="text-slate-500 text-sm mt-1">Sign in to your doctor account</p>
          </div>

          <div className="glass rounded-2xl p-8">
            <button
              onClick={handleLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 bg-white hover:bg-slate-100
                         text-slate-800 font-semibold py-3.5 px-5 rounded-xl
                         transition-all duration-200 hover:shadow-lg hover:scale-[1.02]
                         active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {/* Google SVG */}
              <svg width="20" height="20" viewBox="0 0 48 48">
                <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"/>
                <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"/>
                <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"/>
                <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"/>
              </svg>
              {loading ? "Signing in…" : "Continue with Google"}
            </button>

            <div className="mt-6 pt-6 border-t border-white/5 text-center">
              <p className="text-slate-600 text-xs leading-relaxed">
                By signing in, you agree that your consultation data<br />
                is stored securely and scoped to your account only.
              </p>
            </div>
          </div>

          <p className="text-center text-slate-700 text-xs mt-6">
            VoiceRx Sync v2.0 · ABDM / ABHA Compatible
          </p>
        </motion.div>
      </div>
    </div>
  );
}
