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
import {
  getFunctions,
  httpsCallable,
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-functions.js';

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
  const functions = getFunctions(app, 'us-central1');
  const googleProvider = new GoogleAuthProvider();
  googleProvider.setCustomParameters({ prompt: 'select_account' });

  firebaseServices = {
    app,
    auth,
    db,
    functions,
    googleProvider,
    onAuthStateChanged,
    signInWithPopup,
    signInWithRedirect,
    signOut,
    addDoc,
    collection,
    getDocs,
    onSnapshot,
    httpsCallable,
  };

  return firebaseServices;
}
