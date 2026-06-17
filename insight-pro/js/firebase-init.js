import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js';
import {
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signInWithRedirect,
  signOut,
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js';
import {
  addDoc,
  collection,
  getDocs,
  getFirestore,
  onSnapshot,
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

let firebaseServices = null;

export function validateFirebaseConfig(config) {
  const requiredKeys = ['apiKey', 'authDomain', 'projectId', 'appId'];
  return requiredKeys.every(key => typeof config?.[key] === 'string' && config[key].trim());
}

export function getFirebaseServices(firebaseConfig) {
  if (firebaseServices) {
    return firebaseServices;
  }

  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const db = getFirestore(app);
  const googleProvider = new GoogleAuthProvider();
  googleProvider.setCustomParameters({ prompt: 'select_account' });

  firebaseServices = {
    app,
    auth,
    db,
    googleProvider,
    onAuthStateChanged,
    signInWithPopup,
    signInWithRedirect,
    signOut,
    addDoc,
    collection,
    getDocs,
    onSnapshot,
  };

  return firebaseServices;
}
