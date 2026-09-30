"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Mic, ClipboardList,
  Stethoscope, LogOut, ChevronRight,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

const nav = [
  { href: "/dashboard",      icon: LayoutDashboard, label: "Dashboard" },
  { href: "/consultation/new", icon: Mic,           label: "New Consultation" },
  { href: "/consultations",  icon: ClipboardList,   label: "All Consultations" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 h-screen sticky top-0 flex flex-col
                      bg-gradient-to-b from-[#0d1526] to-[#080d1a]
                      border-r border-white/[0.06]">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/[0.06]">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600
                        flex items-center justify-center shadow-md shadow-indigo-500/30 flex-shrink-0">
          <Stethoscope size={18} className="text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-none">VoiceRx Sync</p>
          <p className="text-slate-600 text-[10px] mt-0.5">Clinical AI Platform</p>
        </div>
      </div>

      {/* Doctor profile */}
      {user && (
        <div className="mx-3 mt-4 mb-2 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]
                        flex items-center gap-3">
          <img src={user.picture || "/avatar.png"} alt={user.name}
               className="w-9 h-9 rounded-full border-2 border-indigo-500/40 flex-shrink-0 object-cover" />
          <div className="overflow-hidden">
            <p className="text-slate-200 text-sm font-semibold truncate leading-none">
              Dr. {user.name.split(" ")[0]}
            </p>
            <p className="text-slate-600 text-[10px] truncate mt-0.5">{user.email}</p>
          </div>
        </div>
      )}

      {/* Nav links */}
      <nav className="flex-1 px-3 py-2 space-y-0.5">
        <p className="text-slate-700 text-[10px] font-bold uppercase tracking-widest
                      px-2 py-2 mb-1">Menu</p>
        {nav.map(({ href, icon: Icon, label }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href}>
              <motion.div
                whileHover={{ x: 2 }}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm
                            font-medium transition-all cursor-pointer group
                            ${active
                              ? "bg-indigo-500/15 text-indigo-300 border border-indigo-500/20"
                              : "text-slate-500 hover:bg-white/[0.04] hover:text-slate-300"}`}
              >
                <Icon size={17} className={active ? "text-indigo-400" : "text-slate-600 group-hover:text-slate-400"} />
                <span className="flex-1">{label}</span>
                {active && <ChevronRight size={14} className="text-indigo-400/60" />}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 pb-5">
        <div className="h-px bg-white/[0.06] mb-3" />
        <button onClick={logout}
                className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm
                           font-medium text-slate-600 hover:text-red-400
                           hover:bg-red-500/8 transition-all">
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
