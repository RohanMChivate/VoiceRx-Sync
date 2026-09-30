"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { onAuthStateChanged, signInWithPopup, signOut, User } from "firebase/auth";
import { auth, provider } from "@/lib/firebase";
import { verifyFirebaseToken } from "@/lib/api";

interface Doctor { email: string; name: string; picture: string; }
interface AuthCtx {
  user:    Doctor | null;
  loading: boolean;
  login:   () => Promise<void>;
  logout:  () => Promise<void>;
}

const Ctx = createContext<AuthCtx>({ user: null, loading: true, login: async () => {}, logout: async () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<Doctor | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Restore session from localStorage
    const stored = localStorage.getItem("voicerx_doctor");
    if (stored) setUser(JSON.parse(stored));
    setLoading(false);
  }, []);

  const login = async () => {
    setLoading(true);
    try {
      const result  = await signInWithPopup(auth, provider);
      const idToken = await result.user.getIdToken();
      const data    = await verifyFirebaseToken(idToken);
      localStorage.setItem("voicerx_token",  data.token);
      localStorage.setItem("voicerx_doctor", JSON.stringify(data.doctor));
      setUser(data.doctor);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await signOut(auth);
    localStorage.removeItem("voicerx_token");
    localStorage.removeItem("voicerx_doctor");
    setUser(null);
  };

  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
