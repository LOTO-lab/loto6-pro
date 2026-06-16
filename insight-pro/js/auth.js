export async function signInWithGoogle(services) {
  try {
    await services.signInWithPopup(services.auth, services.googleProvider);
  } catch (error) {
    if (error?.code === 'auth/popup-blocked' || error?.code === 'auth/popup-closed-by-user') {
      await services.signInWithRedirect(services.auth, services.googleProvider);
      return;
    }
    throw error;
  }
}

export function signOutPremium(services) {
  return services.signOut(services.auth);
}
