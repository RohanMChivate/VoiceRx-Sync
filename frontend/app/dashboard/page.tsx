"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { ClipboardList, Calendar, CheckCircle, Pill, TrendingUp, Building2, ChevronDown, Save, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { getAnalytics, listConsultations, getProfile, updateProfile } from "@/lib/api";
import toast from "react-hot-toast";

const PERIODS = [
  { key: "today", label: "Today" },
  { key: "week",  label: "7 Days" },
  { key: "month", label: "30 Days" },
  { key: "year",  label: "Year" },
  { key: "all",   label: "All Time" },
];
const PIE_COLORS = ["#6366f1","#8b5cf6","#a855f7","#c084fc","#e879f9"];
const TT_STYLE = {
  contentStyle: {
    background:"#0f1a2e", border:"1px solid rgba(99,102,241,0.2)",
    borderRadius:"12px", fontSize:"12px", color:"#94a3b8",
  },
  cursor:{ fill:"rgba(99,102,241,0.06)" },
};

function KPICard({ icon: Icon, value, label, from, to, border, text }:
  { icon: React.ElementType; value: string; label: string;
    from:string; to:string; border:string; text:string }) {
  return (
    <motion.div whileHover={{ y:-3 }} transition={{ type:"spring", stiffness:300 }}
      className={`glass rounded-2xl p-5 bg-gradient-to-br ${from} ${to} ${border} border relative overflow-hidden`}>
      <div className="absolute top-0 inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-current to-transparent opacity-40" />
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 bg-current/10 ${text}`}>
        <Icon size={20} />
      </div>
      <p className="text-3xl font-extrabold text-white leading-none mb-1">{value}</p>
      <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider">{label}</p>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [period, setPeriod] = useState("month");
  const [analytics, setAnalytics] = useState<Record<string,unknown>>({});
  const [consultations, setConsults] = useState<Record<string,unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  // Clinic profile state
  const PROFILE_DEFAULTS = { hospital_name:"", hospital_address:"", hospital_city:"", hospital_phone:"", qualification:"", registration_no:"" };
  const [profileOpen,  setProfileOpen]  = useState(false);
  const [profile,      setProfile]      = useState(PROFILE_DEFAULTS);
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    Promise.all([getAnalytics(user.email, period), listConsultations(user.email)])
      .then(([a, c]) => { setAnalytics(a); setConsults(c); })
      .finally(() => setLoading(false));
  }, [user, period]);

  // Fetch clinic profile once
  useEffect(() => {
    getProfile().then(setProfile).catch(() => {});
  }, []);

  const saveProfile = async () => {
    setProfileSaving(true);
    try {
      await updateProfile(profile);
      toast.success("Clinic profile saved! PDF will use these details.");
    } catch {
      toast.error("Failed to save profile.");
    } finally {
      setProfileSaving(false);
    }
  };

  const timeline = (analytics.timeline as {date:string;count:number}[]) || [];
  const topMeds  = (analytics.top_medicines as {_id:string;count:number}[]) || [];
  const diagDist = (analytics.diagnosis_distribution as {_id:string;count:number}[]) || [];
  const recent   = consultations.slice(0, 8);

  return (
    <div className="space-y-6 fade-up">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Good {new Date().getHours() < 12 ? "morning" : "afternoon"}, Dr. {user?.name.split(" ")[0]} 👋
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {new Date().toLocaleDateString("en-IN",{weekday:"long",day:"numeric",month:"long",year:"numeric"})}
          </p>
        </div>
        <div className="flex gap-1 glass rounded-xl p-1">
          {PERIODS.map(p => (
            <button key={p.key} onClick={() => setPeriod(p.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all
                ${period===p.key ? "bg-indigo-500/25 text-indigo-300" : "text-slate-500 hover:text-slate-300"}`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Clinic Profile (set once, used in every PDF) ── */}
      <div className="glass rounded-2xl overflow-hidden">
        <button onClick={() => setProfileOpen(o => !o)}
          className="w-full flex items-center gap-3 px-5 py-4 hover:bg-white/[0.02] transition-colors">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center justify-center">
            <Building2 size={16} className="text-indigo-400"/>
          </div>
          <div className="text-left flex-1">
            <p className="text-white text-sm font-semibold">Clinic / Hospital Profile</p>
            <p className="text-slate-500 text-xs mt-0.5">
              {profile.hospital_name ? profile.hospital_name : "Set your clinic details — used in every generated PDF"}
            </p>
          </div>
          <ChevronDown size={16} className={`text-slate-500 transition-transform ${profileOpen ? "rotate-180" : ""}`}/>
        </button>

        <AnimatePresence>
          {profileOpen && (
            <motion.div initial={{height:0,opacity:0}} animate={{height:"auto",opacity:1}} exit={{height:0,opacity:0}}
              className="overflow-hidden border-t border-white/[0.06]">
              <div className="p-5 grid grid-cols-2 gap-4">
                {([
                  { key:"hospital_name",    label:"Hospital / Clinic Name",  placeholder:"e.g. City Care Hospital" },
                  { key:"hospital_address", label:"Address",                  placeholder:"e.g. 12 MG Road, Pune" },
                  { key:"hospital_city",    label:"City",                     placeholder:"e.g. Mumbai" },
                  { key:"hospital_phone",   label:"Phone",                    placeholder:"e.g. +91 98765 43210" },
                  { key:"qualification",    label:"Doctor Qualification",     placeholder:"e.g. MBBS, MD (Medicine)" },
                  { key:"registration_no",  label:"Registration Number",      placeholder:"e.g. MH-12345" },
                ] as {key:string; label:string; placeholder:string}[]).map(f => (
                  <div key={f.key}>
                    <label className="text-slate-500 text-xs font-semibold uppercase tracking-wider block mb-1.5">{f.label}</label>
                    <input
                      value={profile[f.key as keyof typeof profile]}
                      onChange={e => setProfile(p => ({...p, [f.key]: e.target.value}))}
                      placeholder={f.placeholder}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5
                                 text-slate-200 text-sm placeholder:text-slate-600
                                 focus:outline-none focus:border-indigo-500/50 focus:ring-2
                                 focus:ring-indigo-500/10 transition-all"
                    />
                  </div>
                ))}
                <div className="col-span-2 flex justify-end pt-1">
                  <motion.button whileHover={{scale:1.02}} whileTap={{scale:0.98}}
                    onClick={saveProfile} disabled={profileSaving}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold
                               bg-gradient-to-r from-indigo-500 to-violet-600 text-white
                               shadow-lg shadow-indigo-500/20 disabled:opacity-50">
                    {profileSaving ? <Loader2 size={14} className="animate-spin"/> : <Save size={14}/>}
                    {profileSaving ? "Saving…" : "Save Profile"}
                  </motion.button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KPICard icon={ClipboardList} value={String(analytics.total_all??0)} label="Total Consultations"
          from="from-indigo-500/10" to="to-indigo-600/5" border="border-indigo-500/15" text="text-indigo-400"/>
        <KPICard icon={Calendar} value={String(analytics.today_count??0)} label="Today"
          from="from-violet-500/10" to="to-violet-600/5" border="border-violet-500/15" text="text-violet-400"/>
        <KPICard icon={CheckCircle} value={`${analytics.approval_rate??0}%`} label="Approval Rate"
          from="from-emerald-500/10" to="to-emerald-600/5" border="border-emerald-500/15" text="text-emerald-400"/>
        <KPICard icon={Pill} value={String(analytics.most_prescribed??"—")} label="Top Medicine"
          from="from-amber-500/10" to="to-amber-600/5" border="border-amber-500/15" text="text-amber-400"/>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7 glass rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-indigo-400"/>
            <p className="text-slate-300 text-sm font-semibold">Consultations Over Time</p>
          </div>
          {loading ? (
            <div className="h-52 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"/>
            </div>
          ) : timeline.length ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)"/>
                <XAxis dataKey="date" tick={{fill:"#475569",fontSize:11}} axisLine={false} tickLine={false}/>
                <YAxis tick={{fill:"#475569",fontSize:11}} axisLine={false} tickLine={false}/>
                <Tooltip {...TT_STYLE}/>
                <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2.5}
                  dot={{fill:"#8b5cf6",r:4}} activeDot={{r:6}}/>
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-slate-600 text-sm">No data for this period</div>
          )}
        </div>

        <div className="col-span-5 glass rounded-2xl p-5">
          <p className="text-slate-300 text-sm font-semibold mb-4">Diagnosis Distribution</p>
          {diagDist.length ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={diagDist} dataKey="count" nameKey="_id" cx="50%" cy="50%"
                  innerRadius={50} outerRadius={75} paddingAngle={3}>
                  {diagDist.map((_,i) => <Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>)}
                </Pie>
                <Tooltip {...TT_STYLE}/>
                <Legend iconType="circle" iconSize={8}
                  formatter={v=><span style={{color:"#94a3b8",fontSize:"11px"}}>{v}</span>}/>
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-slate-600 text-sm">No data yet</div>
          )}
        </div>
      </div>

      {topMeds.length > 0 && (
        <div className="glass rounded-2xl p-5">
          <p className="text-slate-300 text-sm font-semibold mb-4">Top Prescribed Medicines</p>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={topMeds} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false}/>
              <XAxis type="number" tick={{fill:"#475569",fontSize:11}} axisLine={false} tickLine={false}/>
              <YAxis type="category" dataKey="_id" width={120} tick={{fill:"#94a3b8",fontSize:11}} axisLine={false} tickLine={false}/>
              <Tooltip {...TT_STYLE}/>
              <Bar dataKey="count" fill="#6366f1" radius={[0,6,6,0]}/>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="text-slate-300 text-sm font-semibold">Recent Consultations</p>
          <a href="/consultations" className="text-indigo-400 text-xs hover:text-indigo-300 transition-colors">View all →</a>
        </div>
        {loading ? (
          <div className="glass rounded-2xl p-8 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"/>
          </div>
        ) : recent.length === 0 ? (
          <div className="glass rounded-2xl p-10 text-center text-slate-600 text-sm">
            No consultations yet.{" "}
            <a href="/consultation/new" className="text-indigo-400 hover:underline">Start your first one →</a>
          </div>
        ) : (
          <div className="glass rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.06] text-slate-600 text-xs uppercase tracking-wider">
                  {["Patient","Diagnosis","Age","Date","Status"].map(h=>(
                    <th key={h} className="text-left px-5 py-3 font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map((c,i) => {
                  const approved = c.doctor_approved as boolean;
                  const dateStr = c.created_at
                    ? new Date(c.created_at as string).toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"})
                    : "—";
                  return (
                    <tr key={i} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3.5 text-slate-200 font-medium">{(c.patient_name as string)||"Unknown"}</td>
                      <td className="px-5 py-3.5 text-slate-400">{(c.diagnosis as string)||"—"}</td>
                      <td className="px-5 py-3.5 text-slate-400">{(c.age as number)||"—"}</td>
                      <td className="px-5 py-3.5 text-slate-500 text-xs">{dateStr}</td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold
                          ${approved
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${approved?"bg-emerald-400":"bg-amber-400"}`}/>
                          {approved?"Approved":"Pending"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
