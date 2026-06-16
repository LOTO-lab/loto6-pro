function getSubscriptionsCollection(services, config, uid) {
  return services.collection(
    services.db,
    config.firestore.customersCollection,
    uid,
    config.firestore.subscriptionsCollection
  );
}

export function watchPremiumSubscription(services, config, uid, callback, onError) {
  const subscriptionsRef = getSubscriptionsCollection(services, config, uid);

  return services.onSnapshot(
    subscriptionsRef,
    snapshot => {
      const subscriptions = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      const activeSubscription = subscriptions.find(subscription => {
        const status = String(subscription.status || '').toLowerCase();
        return status === 'active' || status === 'trialing';
      });

      callback({
        subscribed: Boolean(activeSubscription),
        subscription: activeSubscription || null,
        subscriptions,
      });
    },
    error => {
      onError?.(error);
    }
  );
}
