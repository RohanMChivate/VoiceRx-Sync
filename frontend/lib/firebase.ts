// Firebase client configuration
import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey:            process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain:        process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId:         process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
  storageBucket:     process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "",
  appId:             process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
};

// Safe initialization (avoids crash during static prerender if env vars are being injected at runtime)
const app = getApps().length === 0
  ? initializeApp(firebaseConfig.apiKey ? firebaseConfig : {
      apiKey: "dummy-key-for-build",
      authDomain: "dummy.firebaseapp.com",
      projectId: "dummy-project",
      storageBucket: "dummy.firebasestorage.app",
      messagingSenderId: "1234567890",
      appId: "1:1234567890:web:dummy"
    })
  : getApps()[0];

export const auth     = getAuth(app);
export const provider = new GoogleAuthProvider();
