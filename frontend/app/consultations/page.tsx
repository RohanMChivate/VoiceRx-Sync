"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Filter, X, ChevronDown } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { listConsultations } from "@/lib/api";

type Consult = Record<string, unknown>;

function StatusBadge({ approved }: { approved: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold
      ${approved
        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
        : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${approved ? "bg-emerald-400" : "bg-amber-400"}`} />
      {approved ? "Approved" : "Pending"}
    </span>
  );
}

export default function AllConsultationsPage() {
  const { user } = useAuth();
  const [all, setAll]           = useState<Consult[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [status, setStatus]     = useState("All");
  const [sort, setSort]         = useState("newest");
  const [selected, setSelected] = useState<Consult | null>(null);
  const [tab, setTab]           = useState<"medical"|"fhir">("medical");

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    listConsultations(user.email)
      .then(setAll)
      .finally(() => setLoading(false));
  }, [user]);

  const filtered = all
    .filter(c => {
      if (status === "Approved" && !c.doctor_approved) return false;
      if (status === "Pending"  &&  c.doctor_approved) return false;
      const q = search.toLowerCase();
      return !q ||
        (c.patient_name as string || "").toLowerCase().includes(q) ||
        (c.diagnosis as string || "").toLowerCase().includes(q);
    })
    .sort((a, b) => {
      const da = new Date(a.created_at as string).getTime();
      const db = new Date(b.created_at as string).getTime();
      return sort === "newest" ? db - da : da - db;
    });

  const fmtDate = (d: unknown) =>
    d ? new Date(d as string).toLocaleDateString("en-IN",
        { day:"2-digit", month:"short", year:"numeric" }) : "—";

  return (
    <div className="fade-up space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-white">📋 All Consultations</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          {all.length} total · scoped to your account
        </p>
      </div>

      {/* Search + filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-600"/>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search patient or diagnosis…"
            className="w-full pl-9 pr-4 py-2.5 glass border border-white/10 rounded-xl
                       text-slate-200 text-sm focus:outline-none focus:border-indigo-500/40
                       focus:ring-2 focus:ring-indigo-500/10 transition-all bg-transparent"/>
        </div>

        <div className="relative">
          <select value={status} onChange={e => setStatus(e.target.value)}
            className="appearance-none pl-4 pr-8 py-2.5 glass border border-white/10 rounded-xl
                       text-slate-300 text-sm focus:outline-none focus:border-indigo-500/40
                       bg-transparent cursor-pointer">
            {["All","Approved","Pending"].map(s => <option key={s} value={s} className="bg-slate-900">{s}</option>)}
          </select>
          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-600 pointer-events-none"/>
        </div>

        <div className="relative">
          <select value={sort} onChange={e => setSort(e.target.value)}
            className="appearance-none pl-4 pr-8 py-2.5 glass border border-white/10 rounded-xl
                       text-slate-300 text-sm focus:outline-none focus:border-indigo-500/40
                       bg-transparent cursor-pointer">
            <option value="newest" className="bg-slate-900">Newest First</option>
            <option value="oldest" className="bg-slate-900">Oldest First</option>
          </select>
          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-600 pointer-events-none"/>
        </div>
      </div>

      <p className="text-slate-600 text-xs">{filtered.length} result(s)</p>

      {/* Two-col layout */}
      <div className="flex gap-5 min-h-[600px]">
        {/* List */}
        <div className={`flex-shrink-0 space-y-2 overflow-y-auto pr-1
                         ${selected ? "w-80" : "w-full"}`}>
          {loading ? (
            Array.from({length:5}).map((_,i) => (
              <div key={i} className="glass rounded-xl h-20 animate-pulse opacity-40"/>
            ))
          ) : filtered.length === 0 ? (
            <div className="glass rounded-2xl p-10 text-center text-slate-600 text-sm">
              No consultations found.
            </div>
          ) : filtered.map((c, i) => {
            const isActive = selected && selected._id === c._id;
            return (
              <motion.div key={String(c._id)} layout
                whileHover={{ x: 2 }} transition={{ type:"spring", stiffness:300 }}
                onClick={() => { setSelected(c); setTab("medical"); }}
                className={`glass rounded-xl p-4 cursor-pointer transition-all
                  ${isActive
                    ? "border-indigo-500/40 bg-indigo-500/8"
                    : "border-white/8 hover:border-indigo-500/20"}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="overflow-hidden">
                    <p className="text-slate-200 font-semibold text-sm truncate">
                      👤 {(c.patient_name as string) || "Unknown"}
                    </p>
                    <p className="text-slate-500 text-xs mt-0.5 truncate">
                      {(c.diagnosis as string) || "No diagnosis"} · Age {(c.age as number) || "?"}
                    </p>
                    <p className="text-slate-700 text-xs mt-1">{fmtDate(c.created_at)}</p>
                  </div>
                  <StatusBadge approved={!!c.doctor_approved}/>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Detail panel */}
        <AnimatePresence>
          {selected && (
            <motion.div key="detail"
              initial={{ opacity:0, x:24 }} animate={{ opacity:1, x:0 }} exit={{ opacity:0, x:24 }}
              className="flex-1 glass rounded-2xl p-6 overflow-y-auto self-start sticky top-0">
              {/* Close */}
              <button onClick={() => setSelected(null)}
                className="absolute top-4 right-4 w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10
                           flex items-center justify-center transition-all text-slate-500 hover:text-slate-300">
                <X size={14}/>
              </button>

              {/* Header */}
              <div className="flex items-start justify-between mb-4 pr-8">
                <div>
                  <h2 className="text-white font-bold text-lg">
                    {(selected.patient_name as string) || "Unknown Patient"}
                  </h2>
                  <p className="text-slate-500 text-xs mt-0.5">
                    {fmtDate(selected.created_at)} · Dr. {(selected.doctor_name as string) || user?.name}
                  </p>
                </div>
                <StatusBadge approved={!!selected.doctor_approved}/>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 mb-5">
                {[
                  { label:"Age",       value: String(selected.age || "—") },
                  { label:"Diagnosis", value: (selected.diagnosis as string) || "—" },
                  { label:"Medicines", value: String((selected.medicines as unknown[])?.length || 0) },
                ].map(m => (
                  <div key={m.label} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3 text-center">
                    <p className="text-white font-bold text-lg leading-none">{m.value}</p>
                    <p className="text-slate-600 text-xs mt-1">{m.label}</p>
                  </div>
                ))}
              </div>

              {/* Symptoms */}
              {(selected.symptoms as string[])?.length > 0 && (
                <div className="mb-4">
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Symptoms</p>
                  <div className="flex flex-wrap gap-1.5">
                    {(selected.symptoms as string[]).map(s => (
                      <span key={s} className="px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/20
                                               rounded-full text-indigo-300 text-xs">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Medicines */}
              {(selected.medicines as Record<string,string>[])?.length > 0 && (
                <div className="mb-5">
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Medicines</p>
                  <div className="space-y-2">
                    {(selected.medicines as Record<string,string>[]).map((m, i) => (
                      <div key={i} className="bg-white/[0.02] border border-white/[0.06] rounded-lg px-3 py-2.5
                                              flex items-center justify-between">
                        <div>
                          <p className="text-slate-200 text-sm font-medium">{m.name}</p>
                          <p className="text-slate-500 text-xs">{m.dosage} · {m.frequency} · {m.duration}</p>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${m.warning==="Validated"
                          ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                          {m.warning==="Validated" ? "✅" : "⚠️"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* JSON tabs */}
              <div className="flex gap-1 glass rounded-xl p-1 mb-3">
                {(["medical","fhir"] as const).map(t => (
                  <button key={t} onClick={() => setTab(t)}
                    className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all
                      ${tab===t ? "bg-indigo-500/20 text-indigo-300" : "text-slate-600 hover:text-slate-400"}`}>
                    {t==="medical" ? "📄 Medical JSON" : "🏥 FHIR JSON"}
                  </button>
                ))}
              </div>
              <pre className="bg-black/30 border border-white/[0.06] rounded-xl p-4 text-xs
                              text-slate-400 overflow-auto max-h-52 leading-relaxed">
                {JSON.stringify(
                  tab==="medical" ? selected.medical_json : selected.fhir_json,
                  null, 2
                )}
              </pre>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
