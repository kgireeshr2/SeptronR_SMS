import { communicationsApi } from '@api/communications';

/** Convert a base64url VAPID public key to the Uint8Array the Push API expects. */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

let _attempted = false;

/**
 * Register the service worker and subscribe this browser to Web Push, then send the
 * subscription to the backend device registry. Safe to call on every authenticated load —
 * it no-ops if push is unsupported, the VAPID key is unset, or permission is denied.
 */
export async function registerWebPush(): Promise<void> {
  if (_attempted) return;
  _attempted = true;
  try {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

    const keyRes: any = await communicationsApi.getWebPushKey();
    const publicKey = (keyRes?.data ?? keyRes)?.public_key;
    if (!publicKey) return; // web push not configured server-side

    const reg = await navigator.serviceWorker.register('/sw.js');

    let permission = Notification.permission;
    if (permission === 'default') permission = await Notification.requestPermission();
    if (permission !== 'granted') return;

    const existing = await reg.pushManager.getSubscription();
    const sub = existing || (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    }));

    await communicationsApi.registerDevice({
      token: JSON.stringify(sub),
      provider: 'webpush',
      platform: 'web',
    });
  } catch {
    /* push registration is best-effort */
  }
}
