"use client";
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Upload, Loader2, CheckCircle, ChevronRight, Save, CloudUpload } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "@/lib/auth";
import { processAudio, saveConsultation, getPdfUrl } from "@/lib/api";

type Step = 0 | 1 | 2 | 3;

const STEPS = ["Record Voice","AI Extract","Review & Edit","Sync & Export"];

interface Medicine { name:string|null; dosage:string|null; frequency:string|null; duration:string|null; warning:string; }
interface Prescription {
  patient_id:   string | null;  // encrypted Fernet token — never plaintext
  age:          number | null;
  diagnosis:    string | null;
  symptoms:     string[];
  medicines:    Medicine[];
  safety_warnings: string[];
}

export default function NewConsultationPage() {
  const { user } = useAuth();
  const [step, setStep]       = useState<Step>(0);
  const [recording, setRec]   = useState(false);
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [rx, setRx]           = useState<Prescription | null>(null);
  const [form, setForm]        = useState<Prescription | null>(null);
  const [approved, setApproved] = useState(false);
  const [savedId, setSavedId]   = useState<string | null>(null);

  const mediaRef  = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  /* ── Recording ── */
  const startRec = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    const mr = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];
    mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    mr.start(250);
    mediaRef.current = mr;
    setRec(true);
  };


  const stopRec = () => {
    const mr = mediaRef.current;
    if (!mr) return;
    setRec(false);
    setLoading(true);
    setStep(1);

    mr.onstop = async () => {
      mr.stream.getTracks().forEach((t) => t.stop());

      const blob = new Blob(chunksRef.current, { type: mr.mimeType || "audio/webm" });
      const fd = new FormData();
      fd.append("file", blob, "recording.webm");
      // patient_id is extracted from the transcript on the backend
      try {
        const data = await processAudio(fd);
        setTranscript(data.transcript);
        setRx(data.prescription);
        setForm(data.prescription);
        setStep(2);
        toast.success("Prescription extracted!");
      } catch (err: unknown) {
        // Show backend's specific error message if available (e.g. patient ID not found)
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        toast.error(detail || "Processing failed. Check your Groq API key.", { duration: 6000 });
        setStep(0);
      } finally {
        setLoading(false);

      }
    };

    mr.stop();
  };


  /* ── Save ── */
  const handleSave = async () => {
    if (!form || !user) return;
    setLoading(true);
    try {
      const res = await saveConsultation({
        ...form, doctor_approved: approved,
        doctor_email: user.email, doctor_name: user.name, doctor_picture: user.picture,
      });
      setSavedId(res.id);
      setStep(3);
      toast.success("Saved to MongoDB!");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Save failed — check server logs.", { duration: 8000 });
    } finally {
      setLoading(false);
    }
  };

  const updateMed = (i: number, field: keyof Medicine, val: string) => {
    if (!form) return;
    const meds = [...form.medicines];
    meds[i] = { ...meds[i], [field]: val };
    setForm({ ...form, medicines: meds });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🎙️ New Consultation</h1>
        <p className="text-slate-500 text-sm mt-0.5">Record → AI extract → Review → Sync to MongoDB</p>
      </div>

      {/* Stepper */}
      <div className="glass rounded-2xl p-1 flex">
        {STEPS.map((s, i) => {
          const done   = i < step;
          const active = i === step;
          return (
            <div key={s} className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl
              text-xs font-semibold transition-all
              ${active ? "bg-indigo-500/20 text-indigo-300" :
                done   ? "text-emerald-400" : "text-slate-600"}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold
                ${active ? "bg-indigo-500/40 text-indigo-200" :
                  done   ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5"}`}>
                {done ? "✓" : i + 1}
              </span>
              {s}
              {i < STEPS.length - 1 && <ChevronRight size={12} className="text-slate-700 ml-1"/>}
            </div>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        {/* ── Step 0: Record ── */}
        {step === 0 && (
          <motion.div key="s0" initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-16}}
            className="glass rounded-2xl p-8 text-center space-y-6">
            <div>
              <h2 className="text-white font-semibold text-lg">Record Your Voice Note</h2>
              <p className="text-slate-500 text-sm mt-1">
                Start with <span className="text-indigo-300 font-mono">&quot;Patient ID P1234&quot;</span>, then speak symptoms, medicines and dosage
              </p>
            </div>

            <div className="flex justify-center">
              {!recording ? (
                <motion.button whileHover={{ scale:1.05 }} whileTap={{ scale:0.95 }}
                  onClick={startRec} disabled={loading}
                  className="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600
                             flex items-center justify-center shadow-xl shadow-indigo-500/30
                             pulse-ring disabled:opacity-50">
                  {loading ? <Loader2 size={32} className="text-white animate-spin"/> : <Mic size={32} className="text-white"/>}
                </motion.button>

              ) : (
                <motion.button whileHover={{ scale:1.05 }} whileTap={{ scale:0.95 }}
                  onClick={stopRec}
                  className="w-24 h-24 rounded-full bg-red-500 flex items-center justify-center
                             shadow-xl shadow-red-500/30 animate-pulse">
                  <Square size={28} className="text-white"/>
                </motion.button>
              )}
            </div>

            <p className="text-center text-slate-600 text-sm">
              {recording ? "🔴 Recording… tap to stop" : loading ? "Processing…" : "Tap the mic to start"}
            </p>
          </motion.div>
        )}

        {/* ── Step 1: AI thinking ── */}
        {step === 1 && (
          <motion.div key="s1" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
            className="glass rounded-2xl p-12 flex flex-col items-center gap-4">
            <Loader2 size={40} className="text-indigo-400 animate-spin"/>
            <p className="text-slate-300 font-medium">AI is extracting prescription data…</p>
            <p className="text-slate-600 text-sm">Groq Whisper + LLaMA 3.3 70B</p>
          </motion.div>
        )}

        {/* ── Step 2: Review form ── */}
        {step === 2 && form && (
          <motion.div key="s2" initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-16}}
            className="space-y-4">
            {/* Transcript */}
            {transcript && (
              <div className="glass rounded-2xl p-4">
                <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Transcript</p>
                <p className="text-slate-300 text-sm leading-relaxed">{transcript}</p>
              </div>
            )}

            {/* Form */}
            <div className="glass rounded-2xl p-6 space-y-4">
              <p className="text-white font-semibold">Review & Edit Prescription</p>

              {/* Patient ID — read-only encrypted badge */}
              <div className="flex items-center gap-3 bg-indigo-500/5 border border-indigo-500/20 rounded-xl px-4 py-3">
                <span className="text-indigo-400 text-lg">🔒</span>
                <div className="min-w-0">
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Patient ID (Encrypted)</p>
                  <p className="text-indigo-300 text-xs font-mono mt-0.5 truncate">{form.patient_id ?? "—"}</p>
                </div>
                <span className="ml-auto text-xs bg-indigo-500/15 text-indigo-400 px-2 py-0.5 rounded-full font-semibold shrink-0">Secured</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-slate-500 text-xs font-semibold uppercase tracking-wider block mb-1.5">Age</label>
                  <input type="number" value={form.age ?? ""} onChange={e=>setForm({...form,age:+e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5
                               text-slate-200 text-sm focus:outline-none focus:border-indigo-500/50
                               focus:ring-2 focus:ring-indigo-500/10 transition-all"/>
                </div>
              </div>

              <div>
                <label className="text-slate-500 text-xs font-semibold uppercase tracking-wider block mb-1.5">Diagnosis</label>
                <input value={form.diagnosis ?? ""} onChange={e=>setForm({...form,diagnosis:e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5
                             text-slate-200 text-sm focus:outline-none focus:border-indigo-500/50
                             focus:ring-2 focus:ring-indigo-500/10 transition-all"/>
              </div>

              <div>
                <label className="text-slate-500 text-xs font-semibold uppercase tracking-wider block mb-1.5">Symptoms</label>
                <input value={(form.symptoms ?? []).join(", ")}
                  onChange={e=>setForm({...form,symptoms:e.target.value.split(",").map(s=>s.trim())})}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5
                             text-slate-200 text-sm focus:outline-none focus:border-indigo-500/50
                             focus:ring-2 focus:ring-indigo-500/10 transition-all"/>
              </div>

              {/* Medicines */}
              <div>
                <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-3">Medicines</p>
                <div className="space-y-3">
                  {form.medicines.map((med, i) => (
                    <div key={i} className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-slate-400 text-xs font-semibold">Medicine {i+1}</p>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold
                          ${med.warning==="Validated"
                            ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                          {med.warning==="Validated" ? "✅ Validated" : `⚠️ ${med.warning}`}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {(["name","dosage","frequency","duration"] as (keyof Medicine)[]).map(f => (
                          <div key={f}>
                            <label className="text-slate-600 text-xs capitalize block mb-1">{f}</label>
                            <input value={med[f] ?? ""} onChange={e=>updateMed(i,f,e.target.value)}
                              className="w-full bg-white/5 border border-white/8 rounded-lg px-3 py-2
                                         text-slate-200 text-sm focus:outline-none focus:border-indigo-500/40 transition-all"/>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Approve + Save */}
              <div className="flex items-center gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}
                    className="w-4 h-4 rounded accent-indigo-500"/>
                  <span className="text-slate-400 text-sm">I approve this prescription</span>
                </label>
                <motion.button whileHover={{ scale:1.02 }} whileTap={{ scale:0.98 }}
                  onClick={handleSave} disabled={!approved || loading}
                  className="ml-auto flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm
                             bg-gradient-to-r from-indigo-500 to-violet-600 text-white
                             shadow-lg shadow-indigo-500/25 disabled:opacity-40 transition-all">
                  {loading ? <Loader2 size={16} className="animate-spin"/> : <Save size={16}/>}
                  {loading ? "Saving…" : "Save & Sync"}
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Step 3: Done ── */}
        {step === 3 && savedId && (
          <motion.div key="s3" initial={{opacity:0,scale:0.95}} animate={{opacity:1,scale:1}}
            className="glass rounded-2xl p-12 text-center space-y-5">
            <motion.div initial={{scale:0}} animate={{scale:1}} transition={{type:"spring",stiffness:200,delay:0.1}}
              className="w-20 h-20 rounded-full bg-emerald-500/15 border border-emerald-500/30
                         flex items-center justify-center mx-auto">
              <CheckCircle size={40} className="text-emerald-400"/>
            </motion.div>
            <div>
              <h2 className="text-white font-bold text-xl">Consultation Saved!</h2>
              <p className="text-slate-500 text-sm mt-1">Stored in MongoDB with FHIR payload</p>
            </div>
            <div className="flex gap-3 justify-center">
              <a href={getPdfUrl(savedId)} target="_blank"
                className="flex items-center gap-2 px-5 py-2.5 glass border border-white/10 rounded-xl
                           text-slate-300 text-sm hover:text-white transition-all">
                <CloudUpload size={16}/> Download PDF
              </a>
              <a href="/consultations"
                className="flex items-center gap-2 px-5 py-2.5 bg-indigo-500/20 border border-indigo-500/30
                           rounded-xl text-indigo-300 text-sm hover:bg-indigo-500/30 transition-all">
                View All Consultations
              </a>
              <button onClick={() => { setStep(0); setRx(null); setForm(null); setSavedId(null); setApproved(false); }}
                className="px-5 py-2.5 glass border border-white/10 rounded-xl text-slate-300 text-sm hover:text-white transition-all">
                New Consultation
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
