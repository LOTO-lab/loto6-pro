function makeReturnUrl(param) {
  const url = new URL(window.location.href);
  url.search = param || '';
  return url.toString();
}

function getCustomerCollection(services, config, uid, subcollectionName) {
  return services.collection(
    services.db,
    config.firestore.customersCollection,
    uid,
    subcollectionName
  );
}

export function watchSubscription(services, config, uid, callback, onError) {
  const subscriptionsRef = getCustomerCollection(
    services,
    config,
    uid,
    config.firestore.subscriptionsCollection
  );

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

export async function createCheckoutSession(services, config, user) {
  if (!config.stripe.priceId) {
    throw new Error('Stripe priceId が未設定です。public/js/premium-config.js を設定してください。');
  }

  const checkoutSessionsRef = getCustomerCollection(
    services,
    config,
    user.uid,
    config.firestore.checkoutSessionsCollection
  );

  const docRef = await services.addDoc(checkoutSessionsRef, {
    price: config.stripe.priceId,
    allow_promotion_codes: Boolean(config.stripe.allowPromotionCodes),
    success_url: makeReturnUrl(config.urls.successParam),
    cancel_url: makeReturnUrl(config.urls.cancelParam),
    metadata: {
      product: 'loto6-pro-insight',
    },
  });

  return new Promise((resolve, reject) => {
    const unsubscribe = services.onSnapshot(
      docRef,
      snapshot => {
        const data = snapshot.data() || {};
        if (data.error) {
          unsubscribe();
          reject(new Error(data.error.message || 'Checkout セッション作成に失敗しました。'));
          return;
        }
        if (data.url) {
          unsubscribe();
          resolve(data.url);
        }
      },
      error => {
        unsubscribe();
        reject(error);
      }
    );
  });
}

export async function createPortalSession(services, config, user) {
  const portalSessionsRef = getCustomerCollection(
    services,
    config,
    user.uid,
    config.firestore.portalSessionsCollection
  );

  const docRef = await services.addDoc(portalSessionsRef, {
    return_url: makeReturnUrl(''),
  });

  return new Promise((resolve, reject) => {
    const unsubscribe = services.onSnapshot(
      docRef,
      snapshot => {
        const data = snapshot.data() || {};
        if (data.error) {
          unsubscribe();
          reject(new Error(data.error.message || '支払い管理ページの作成に失敗しました。'));
          return;
        }
        if (data.url) {
          unsubscribe();
          resolve(data.url);
        }
      },
      error => {
        unsubscribe();
        reject(error);
      }
    );
  });
}
