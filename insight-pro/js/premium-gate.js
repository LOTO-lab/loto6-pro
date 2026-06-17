import { premiumConfig } from './premium-config.js';

const rootId = 'premium-gate-root';
let services = null;
let currentUser = null;
let subscriptionUnsubscribe = null;
let firebaseApi = null;
let authApi = null;
let billingApi = null;
let premiumCheckApi = null;
let premiumReturnStatus = null;

function validateFirebaseConfig(config) {
  const requiredKeys = ['apiKey', 'authDomain', 'projectId', 'appId'];
  return requiredKeys.every(key => typeof config?.[key] === 'string' && config[key].trim());
}

function setBodyState(state) {
  document.body.classList.remove(
    'premium-gate-active',
    'premium-gate-unlocked',
    'premium-gate-disabled',
    'premium-gate-error'
  );
  if (state === 'premium-gate-unlocked' || state === 'premium-gate-disabled') {
    document.body.classList.remove('premium-boot-lock');
  } else {
    document.body.classList.add('premium-boot-lock');
  }
  document.body.classList.add(state);
}

function isGatewayPage() {
  return document.body.dataset.premiumMode === 'gateway';
}

function getPremiumAppUrl() {
  return new URL('app.html', window.location.href).toString();
}

function getRoot() {
  let root = document.getElementById(rootId);
  if (!root) {
    root = document.createElement('div');
    root.id = rootId;
    root.className = 'premium-gate-shell';
    root.setAttribute('aria-live', 'polite');
    document.body.insertBefore(root, document.body.firstChild);
  }
  return root;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function cleanPremiumReturnParam() {
  const params = new URLSearchParams(window.location.search);
  if (!params.has('premium')) return;
  params.delete('premium');
  const url = `${window.location.origin}${window.location.pathname}${params.toString() ? `?${params}` : ''}${window.location.hash}`;
  window.history.replaceState({}, document.title, url);
}

function capturePremiumReturnParam() {
  const params = new URLSearchParams(window.location.search);
  const value = params.get('premium');
  if (value !== 'success' && value !== 'cancel') return;
  premiumReturnStatus = value;
  cleanPremiumReturnParam();
}

function getReturnNotice() {
  if (premiumReturnStatus === 'success') {
    return '<div class="premium-gate-notice success">申込みが完了しました。購読状態を確認しています。反映まで少し時間がかかる場合があります。</div>';
  }
  if (premiumReturnStatus === 'cancel') {
    return '<div class="premium-gate-notice">決済がキャンセルされました。必要なタイミングで再開できます。</div>';
  }
  return '';
}

function renderShell(content) {
  const root = getRoot();
  root.innerHTML = `
    <div class="premium-gate-card">
      <div class="premium-gate-brand">
        <span class="premium-gate-logo" aria-hidden="true">
          <span></span><span></span><span></span>
        </span>
        <div>
          <p class="premium-gate-kicker">PREMIUM ACCESS</p>
          <h1>${escapeHtml(premiumConfig.labels.productName)}</h1>
        </div>
      </div>
      ${content}
      <div class="premium-gate-footer">
        <a href="${escapeHtml(premiumConfig.urls.freeSiteUrl)}">無料版へ戻る</a>
        <span>予想・分析結果は当選を保証するものではありません。</span>
      </div>
    </div>
  `;
}

function renderLoading(message = '認証状態を確認しています...') {
  setBodyState('premium-gate-active');
  renderShell(`
    ${getReturnNotice()}
    <div class="premium-gate-loading">
      <span class="premium-gate-spinner" aria-hidden="true"></span>
      <p>${escapeHtml(message)}</p>
    </div>
  `);
}

function renderConfigError() {
  setBodyState('premium-gate-error');
  renderShell(`
    <div class="premium-gate-status error">設定が未完了です</div>
    <p class="premium-gate-lead">
      有料ゲートは有効ですが、Firebase設定が未入力です。管理者は
      <code>public/js/premium-config.js</code> にFirebase設定とStripe価格IDを設定してください。
    </p>
  `);
}

function renderLogin(errorMessage = '') {
  setBodyState('premium-gate-active');
  renderShell(`
    ${getReturnNotice()}
    ${errorMessage ? `<div class="premium-gate-notice error">${escapeHtml(errorMessage)}</div>` : ''}
    <div class="premium-gate-status">ログインが必要です</div>
    <p class="premium-gate-lead">
      統合予測分析エンジンは有料メンバー向け機能です。Googleアカウントでログイン後、購読状態を確認します。
    </p>
    <div class="premium-gate-features">
      <span>AI分析 TOP10</span>
      <span>過去AIスコア傾向</span>
      <span>AI分析結果ログ</span>
      <span>個人予想検証ログ</span>
    </div>
    <div class="premium-gate-cautions">
      <p>本サービスは過去データをもとに条件検索・傾向分析を行うツールです。</p>
      <p>当選を保証するものではありません。宝くじの購入は自己判断で行ってください。</p>
    </div>
    <button id="premium-login-btn" class="premium-gate-primary" type="button">Googleでログイン</button>
  `);

  document.getElementById('premium-login-btn')?.addEventListener('click', async () => {
      renderLoading('Googleログインを開始しています...');
    try {
      await authApi.signInWithGoogle(services);
    } catch (error) {
      renderLogin(error.message || 'ログインに失敗しました。');
    }
  });
}

function renderPurchase(user, errorMessage = '') {
  const isCheckoutPending = premiumReturnStatus === 'success' && !errorMessage;
  setBodyState('premium-gate-active');
  renderShell(`
    ${getReturnNotice()}
    ${errorMessage ? `<div class="premium-gate-notice error">${escapeHtml(errorMessage)}</div>` : ''}
    <div class="premium-gate-status">${isCheckoutPending ? '購読状態を反映中です' : '購読が必要です'}</div>
    <p class="premium-gate-lead">
      ${isCheckoutPending
        ? `${escapeHtml(user.email || 'ログイン中のアカウント')} の申込みは完了しています。確認後に有料機能が自動で開きます。`
        : `${escapeHtml(user.email || 'ログイン中のアカウント')} は現在、有料プランが確認できません。
      Stripeの決済ページで購読を開始すると、確認後に有料機能が開きます。`}
    </p>
    <div class="premium-gate-plan">
      <span>${escapeHtml(premiumConfig.labels.planName)}</span>
      <strong>${escapeHtml(premiumConfig.labels.priceText)}</strong>
    </div>
    <div class="premium-gate-promo">
      <strong>${escapeHtml(premiumConfig.labels.promoText)}</strong>
      <span>対象アカウントにはStripe決済ページで自動適用されます。再契約時は通常価格になります。</span>
    </div>
    <div class="premium-gate-cautions">
      <p>本サービスは過去データをもとに条件検索・傾向分析を行うツールです。</p>
      <p>当選を保証するものではありません。宝くじの購入は自己判断で行ってください。</p>
      <p>購入時にログインしたGoogleアカウントにプレミアム権限が付与されます。次回以降も同じGoogleアカウントでログインしてください。</p>
      <p>別のアカウントでログインした場合、購入情報は引き継がれません。</p>
    </div>
    <div class="premium-gate-actions">
      <button id="premium-checkout-btn" class="premium-gate-primary" type="button" ${isCheckoutPending ? 'disabled' : ''}>
        ${isCheckoutPending ? '購読状態を確認中' : '有料版を開始する'}
      </button>
      <button id="premium-logout-btn" class="premium-gate-secondary" type="button">ログアウト</button>
    </div>
  `);

  document.getElementById('premium-checkout-btn')?.addEventListener('click', async () => {
    if (isCheckoutPending) return;
    renderLoading('決済ページを準備しています...');
    try {
      const url = await billingApi.createCheckoutSession(services, premiumConfig, user);
      window.location.assign(url);
    } catch (error) {
      renderPurchase(user, error.message || '決済ページの準備に失敗しました。');
    }
  });

  document.getElementById('premium-logout-btn')?.addEventListener('click', () => {
    authApi.signOutPremium(services);
  });
}

function unlockPremium(user) {
  if (isGatewayPage()) {
    window.location.replace(getPremiumAppUrl());
    return;
  }
  setBodyState('premium-gate-unlocked');
  getRoot().innerHTML = '';
  renderAccountChip(user);
}

function renderAccountChip(user) {
  const headerMeta = document.querySelector('.header-meta');
  if (!headerMeta) return;

  let chip = document.getElementById('premium-account-chip');
  if (!chip) {
    chip = document.createElement('div');
    chip.id = 'premium-account-chip';
    chip.className = 'premium-account-chip';
    headerMeta.appendChild(chip);
  }

  chip.innerHTML = `
    <span class="premium-account-status">有料版</span>
    <span class="premium-account-email">${escapeHtml(user.email || 'ログイン中')}</span>
    <button id="premium-portal-btn" type="button">支払い管理</button>
    <button id="premium-chip-logout-btn" type="button">ログアウト</button>
  `;

  document.getElementById('premium-portal-btn')?.addEventListener('click', async () => {
    try {
      const url = await billingApi.createPortalSession(services, premiumConfig, user);
      window.location.assign(url);
    } catch (error) {
      window.alert(error.message || '支払い管理ページを開けませんでした。');
    }
  });

  document.getElementById('premium-chip-logout-btn')?.addEventListener('click', () => {
    authApi.signOutPremium(services);
  });
}

function handleUser(user) {
  currentUser = user;
  subscriptionUnsubscribe?.();
  subscriptionUnsubscribe = null;

  if (!user) {
    document.getElementById('premium-account-chip')?.remove();
    renderLogin();
    return;
  }

  renderLoading('購読状態を確認しています...');
  subscriptionUnsubscribe = premiumCheckApi.watchPremiumSubscription(
    services,
    premiumConfig,
    user.uid,
    state => {
      if (state.subscribed) {
        unlockPremium(user);
      } else {
        renderPurchase(user);
      }
    },
    error => {
      renderPurchase(user, error.message || '購読状態の確認に失敗しました。');
    }
  );
}

async function loadPremiumModules() {
  if (firebaseApi && authApi && billingApi && premiumCheckApi) return;
  [firebaseApi, authApi, billingApi, premiumCheckApi] = await Promise.all([
    import('./firebase-init.js'),
    import('./auth.js'),
    import('./billing.js'),
    import('./premium-check.js'),
  ]);
}

async function initPremiumGate() {
  if (!premiumConfig.enabled) {
    setBodyState('premium-gate-disabled');
    return;
  }

  capturePremiumReturnParam();

  if (!validateFirebaseConfig(premiumConfig.firebase)) {
    renderConfigError();
    return;
  }

  renderLoading();
  try {
    await loadPremiumModules();
  } catch (error) {
    renderLogin(error.message || 'Firebaseモジュールの読み込みに失敗しました。');
    return;
  }

  services = firebaseApi.getFirebaseServices(premiumConfig.firebase);
  services.onAuthStateChanged(services.auth, handleUser, error => {
    renderLogin(error.message || '認証状態の確認に失敗しました。');
  });
}

document.addEventListener('DOMContentLoaded', initPremiumGate);
