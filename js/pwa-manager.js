/**
 * PWA Manager for Flow Metrics Dashboard
 * 
 * Handles service worker registration, push notifications, offline capabilities,
 * app installation prompts, and background sync management.
 */

class PWAManager {
    constructor() {
        this.serviceWorker = null;
        this.installPrompt = null;
        this.pushSubscription = null;
        this.isOnline = navigator.onLine;
        this.syncQueue = new Map();
        
        // PWA status
        this.isInstalled = false;
        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                           window.navigator.standalone === true;
        
        // Notification permission
        this.notificationPermission = 'default';
        
        // Background sync support
        this.backgroundSyncSupported = 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype;
        
        // Push notification support  
        this.pushSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        
        console.log('PWA Manager initialized', {
            isStandalone: this.isStandalone,
            backgroundSync: this.backgroundSyncSupported,
            pushSupported: this.pushSupported
        });
    }

    /**
     * Initialize PWA features
     */
    async init() {
        try {
            // Register service worker
            await this.registerServiceWorker();
            
            // Setup online/offline detection
            this.setupNetworkDetection();
            
            // Setup install prompt handling
            this.setupInstallPrompt();
            
            // Load notification permission
            this.loadNotificationPermission();
            
            // Setup message handling
            this.setupMessageHandling();
            
            // Check for updates
            this.checkForUpdates();
            
            console.log('PWA Manager ready');
            
            // Notify UI of PWA readiness
            this.dispatchPWAEvent('pwa-ready', {
                isInstalled: this.isInstalled,
                isStandalone: this.isStandalone,
                canInstall: this.installPrompt !== null,
                notificationPermission: this.notificationPermission
            });
            
        } catch (error) {
            console.error('PWA Manager initialization failed:', error);
        }
    }

    /**
     * Register service worker
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('Service Worker not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            });

            this.serviceWorker = registration;
            
            console.log('Service Worker registered:', registration.scope);

            // Handle updates
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                console.log('New Service Worker available');
                
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.showUpdateAvailable();
                    }
                });
            });

            // Handle controller change
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                console.log('Service Worker controller changed');
                window.location.reload();
            });

        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }

    /**
     * Setup network status detection
     */
    setupNetworkDetection() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log('Network: Online');
            this.handleOnlineStatus();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log('Network: Offline');
            this.handleOfflineStatus();
        });

        // Initial status
        this.isOnline = navigator.onLine;
        console.log('Network status:', this.isOnline ? 'Online' : 'Offline');
    }

    /**
     * Setup app installation prompt
     */
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (event) => {
            console.log('Install prompt available');
            event.preventDefault();
            this.installPrompt = event;
            
            this.dispatchPWAEvent('install-available', {
                canInstall: true
            });
        });

        window.addEventListener('appinstalled', () => {
            console.log('App installed');
            this.isInstalled = true;
            this.installPrompt = null;
            
            this.dispatchPWAEvent('app-installed', {
                isInstalled: true
            });
        });
    }

    /**
     * Setup message handling with service worker
     */
    setupMessageHandling() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                console.log('Message from Service Worker:', event.data);
                
                switch (event.data.type) {
                    case 'METRICS_SYNCED':
                        this.handleMetricsSynced(event.data.data);
                        break;
                    case 'EXPORT_SYNCED':
                        this.handleExportSynced(event.data.data);
                        break;
                    case 'CACHE_UPDATED':
                        this.handleCacheUpdated(event.data.data);
                        break;
                    default:
                        console.log('Unknown message type:', event.data.type);
                }
            });
        }
    }

    /**
     * Load notification permission status
     */
    loadNotificationPermission() {
        if ('Notification' in window) {
            this.notificationPermission = Notification.permission;
            console.log('Notification permission:', this.notificationPermission);
        }
    }

    /**
     * Show app install prompt
     */
    async showInstallPrompt() {
        if (!this.installPrompt) {
            console.warn('No install prompt available');
            return false;
        }

        try {
            const result = await this.installPrompt.prompt();
            console.log('Install prompt result:', result.outcome);
            
            if (result.outcome === 'accepted') {
                this.installPrompt = null;
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Install prompt failed:', error);
            return false;
        }
    }

    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.warn('Notifications not supported');
            return 'not-supported';
        }

        if (this.notificationPermission === 'granted') {
            return 'granted';
        }

        try {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            console.log('Notification permission:', permission);
            
            this.dispatchPWAEvent('notification-permission-changed', {
                permission: permission
            });
            
            return permission;
        } catch (error) {
            console.error('Notification permission request failed:', error);
            return 'denied';
        }
    }

    /**
     * Setup push notifications
     */
    async setupPushNotifications() {
        if (!this.pushSupported) {
            console.warn('Push notifications not supported');
            return false;
        }

        if (!this.serviceWorker) {
            console.warn('Service Worker not available for push notifications');
            return false;
        }

        try {
            // Check if already subscribed
            const existingSubscription = await this.serviceWorker.pushManager.getSubscription();
            if (existingSubscription) {
                this.pushSubscription = existingSubscription;
                console.log('Existing push subscription found');
                return true;
            }

            // Request notification permission
            const permission = await this.requestNotificationPermission();
            if (permission !== 'granted') {
                console.warn('Notification permission denied');
                return false;
            }

            // Subscribe to push notifications
            const subscription = await this.serviceWorker.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.getVAPIDPublicKey())
            });

            this.pushSubscription = subscription;
            console.log('Push notification subscription created');

            // Send subscription to server (in real implementation)
            await this.sendSubscriptionToServer(subscription);

            this.dispatchPWAEvent('push-subscription-created', {
                subscription: subscription
            });

            return true;
        } catch (error) {
            console.error('Push notification setup failed:', error);
            return false;
        }
    }

    /**
     * Cache data for offline access
     */
    async cacheData(key, data) {
        if (!this.serviceWorker) {
            console.warn('Service Worker not available for caching');
            return;
        }

        try {
            // Send data to service worker for caching
            this.sendMessageToServiceWorker({
                type: 'CACHE_METRICS_DATA',
                data: data
            });

            console.log('Data cached for offline access:', key);
        } catch (error) {
            console.error('Data caching failed:', error);
        }
    }

    /**
     * Queue operation for background sync
     */
    async queueForBackgroundSync(operation, data) {
        if (!this.backgroundSyncSupported) {
            console.warn('Background sync not supported');
            return;
        }

        try {
            // Add to local queue
            const queueId = Date.now().toString();
            this.syncQueue.set(queueId, { operation, data, timestamp: new Date() });

            // Register background sync
            if (this.serviceWorker) {
                await this.serviceWorker.sync.register(`background-sync-${operation}`);
                console.log('Background sync registered:', operation);
            }

            // Send to service worker
            this.sendMessageToServiceWorker({
                type: `QUEUE_${operation.toUpperCase()}`,
                [operation === 'export' ? 'exportData' : 'filterData']: data
            });

        } catch (error) {
            console.error('Background sync queuing failed:', error);
        }
    }

    /**
     * Handle online status
     */
    handleOnlineStatus() {
        this.dispatchPWAEvent('network-status-changed', {
            isOnline: true
        });

        // Trigger background sync for queued operations
        if (this.syncQueue.size > 0) {
            console.log('Triggering background sync for queued operations');
            this.triggerBackgroundSync();
        }
    }

    /**
     * Handle offline status
     */
    handleOfflineStatus() {
        this.dispatchPWAEvent('network-status-changed', {
            isOnline: false
        });

        // Show offline indicator
        this.showOfflineNotification();
    }

    /**
     * Show offline notification
     */
    showOfflineNotification() {
        const notification = document.createElement('div');
        notification.id = 'offline-notification';
        notification.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
        `;
        notification.innerHTML = `
            <i class="fas fa-wifi-slash me-2"></i>
            <strong>Offline Mode</strong><br>
            <small>You're currently offline. Changes will sync when connection is restored.</small>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 10000);
    }

    /**
     * Show update available notification
     */
    showUpdateAvailable() {
        const notification = document.createElement('div');
        notification.id = 'update-notification';
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.cssText = `
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            max-width: 400px;
        `;
        notification.innerHTML = `
            <i class="fas fa-download me-2"></i>
            <strong>Update Available</strong><br>
            <small>A new version of the app is available.</small>
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-primary me-2" onclick="updateApp()">
                    Update Now
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-dismiss="alert">
                    Later
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Make update function globally available
        window.updateApp = () => {
            this.updateServiceWorker();
            notification.remove();
        };
    }

    /**
     * Update service worker
     */
    updateServiceWorker() {
        if (this.serviceWorker && this.serviceWorker.waiting) {
            this.sendMessageToServiceWorker({ type: 'SKIP_WAITING' });
        }
    }

    /**
     * Send message to service worker
     */
    sendMessageToServiceWorker(message) {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage(message);
        }
    }

    /**
     * Check for service worker updates
     */
    async checkForUpdates() {
        if (!this.serviceWorker) {
            return;
        }

        try {
            await this.serviceWorker.update();
            console.log('Checked for Service Worker updates');
        } catch (error) {
            console.error('Update check failed:', error);
        }
    }

    /**
     * Trigger background sync manually
     */
    async triggerBackgroundSync() {
        if (!this.backgroundSyncSupported || !this.serviceWorker) {
            return;
        }

        try {
            // Register sync for different types
            await this.serviceWorker.sync.register('background-sync-metrics');
            await this.serviceWorker.sync.register('background-sync-exports');
            await this.serviceWorker.sync.register('background-sync-filters');
            
            console.log('Background sync triggered');
        } catch (error) {
            console.error('Background sync trigger failed:', error);
        }
    }

    /**
     * Get PWA installation status
     */
    getInstallationStatus() {
        return {
            isInstalled: this.isInstalled,
            isStandalone: this.isStandalone,
            canInstall: this.installPrompt !== null,
            notificationPermission: this.notificationPermission,
            pushSubscription: this.pushSubscription !== null,
            isOnline: this.isOnline
        };
    }

    /**
     * Get VAPID public key (would be from server config)
     */
    getVAPIDPublicKey() {
        // This would typically come from your server configuration
        return 'BEl62iUYgUivxIkv69yViEuiBIa40HI8YlOU2cGEkFI7L9DJTGGH-wvJRZdnJ-pjJH-EIhxv1RVTZFAqBl-XP3w';
    }

    /**
     * Convert VAPID key to Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    /**
     * Send subscription to server (placeholder)
     */
    async sendSubscriptionToServer(subscription) {
        // In a real implementation, this would send the subscription to your server
        console.log('Subscription to send to server:', subscription.toJSON());
        
        try {
            // const response = await fetch('/api/push-subscription', {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify(subscription.toJSON())
            // });
            
            console.log('Push subscription sent to server');
        } catch (error) {
            console.error('Failed to send subscription to server:', error);
        }
    }

    /**
     * Handle metrics sync completion
     */
    handleMetricsSynced(data) {
        console.log('Metrics synced:', data);
        this.dispatchPWAEvent('metrics-synced', { data });
    }

    /**
     * Handle export sync completion
     */
    handleExportSynced(data) {
        console.log('Export synced:', data);
        this.dispatchPWAEvent('export-synced', { data });
    }

    /**
     * Handle cache update
     */
    handleCacheUpdated(data) {
        console.log('Cache updated:', data);
        this.dispatchPWAEvent('cache-updated', { data });
    }

    /**
     * Dispatch PWA events
     */
    dispatchPWAEvent(type, detail) {
        const event = new CustomEvent(`pwa-${type}`, { detail });
        window.dispatchEvent(event);
    }

    /**
     * Show notification (when app is in focus)
     */
    showNotification(title, options = {}) {
        if (this.notificationPermission !== 'granted') {
            console.warn('Cannot show notification: permission not granted');
            return;
        }

        const defaultOptions = {
            icon: '/icons/icon-192x192.png',
            badge: '/icons/badge-72x72.png',
            tag: 'flow-metrics',
            requireInteraction: false
        };

        const notificationOptions = { ...defaultOptions, ...options };

        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            // Show notification via service worker (works when app is in background)
            navigator.serviceWorker.controller.postMessage({
                type: 'SHOW_NOTIFICATION',
                title,
                options: notificationOptions
            });
        } else {
            // Show notification directly (when app is in focus)
            new Notification(title, notificationOptions);
        }
    }

    /**
     * Clean up resources
     */
    destroy() {
        // Remove event listeners
        window.removeEventListener('online', this.handleOnlineStatus);
        window.removeEventListener('offline', this.handleOfflineStatus);
        
        // Clear queues
        this.syncQueue.clear();
        
        console.log('PWA Manager destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}