export const premiumConfig = {
  enabled: true,
  firebaseVersion: '10.12.5',
  firebase: {
    apiKey: 'AIzaSyDAl25s7TZ2-YxChmJFuJkiKzNWO84S3g4',
    authDomain: 'loto6-pro-premium.firebaseapp.com',
    projectId: 'loto6-pro-premium',
    appId: '1:709270393170:web:f4ca86eb26c46c7b856a8b',
  },
  stripe: {
    priceId: 'price_1Tj27jJ5bfMYeiGy0MFfgEdu',
    allowPromotionCodes: false,
    firstCheckoutDiscount: {
      enabled: true,
      couponId: '6Kpf5KMh',
      promotionCodeId: '',
    },
  },
  firestore: {
    customersCollection: 'customers',
    subscriptionsCollection: 'subscriptions',
    checkoutSessionsCollection: 'checkout_sessions',
    portalSessionsCollection: 'portal_sessions',
    paymentsCollection: 'payments',
  },
  urls: {
    freeSiteUrl: '../',
    successParam: 'premium=success',
    cancelParam: 'premium=cancel',
  },
  labels: {
    productName: 'LOTO6 PRO 統合予測分析エンジン',
    planName: '月額プラン',
    priceText: '月額680円',
    promoText: '初回月は自動割引で500円、2か月目以降は月額680円',
    promoCode: 'FIRST500',
  },
};
