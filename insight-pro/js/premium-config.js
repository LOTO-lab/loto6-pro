export const premiumConfig = {
  enabled: false,
  firebaseVersion: '10.12.5',
  firebase: {
    apiKey: '',
    authDomain: '',
    projectId: '',
    appId: '',
  },
  stripe: {
    priceId: '',
    allowPromotionCodes: true,
  },
  firestore: {
    customersCollection: 'customers',
    subscriptionsCollection: 'subscriptions',
    checkoutSessionsCollection: 'checkout_sessions',
    portalSessionsCollection: 'portal_sessions',
  },
  urls: {
    freeSiteUrl: '../',
    successParam: 'premium=success',
    cancelParam: 'premium=cancel',
  },
  labels: {
    productName: 'LOTO6 PRO 統合予測分析エンジン',
    planName: '月額プラン',
    priceText: '初回680円 / 2か月目以降980円',
  },
};
