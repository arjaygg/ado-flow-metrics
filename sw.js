/**
 * Service Worker for Flow Metrics Dashboard PWA
 * 
 * Provides offline capability, background sync, push notifications,
 * and caching strategies for optimal performance.
 */

const CACHE_NAME = 'flow-metrics-v1.0.0';
const DYNAMIC_CACHE_NAME = 'flow-metrics-dynamic-v1.0.0';
const DATA_CACHE_NAME = 'flow-metrics-data-v1.0.0';

// Static assets to cache for offline access
const STATIC_ASSETS = [
    '/',
    '/dashboard.html',
    '/test-phase1-features.html',
    '/js/workstream_config.js',
    '/js/workstream-manager.js',
    '/js/predictive-analytics.js',
    '/js/time-series-analysis.js',
    '/js/enhanced-ux.js',
    '/js/advanced-filtering.js',
    '/js/export-collaboration.js',
    '/js/pwa-manager.js',
    '/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdn.plot.ly/plotly-latest.min.js'
];

// Data endpoints to cache
const DATA_URLS = [
    '/api/flow-metrics',
    '/api/team-metrics',
    '/api/historical-data'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && 
                            cacheName !== DYNAMIC_CACHE_NAME && 
                            cacheName !== DATA_CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const requestUrl = new URL(event.request.url);
    
    // Handle different types of requests with appropriate caching strategies
    if (event.request.method === 'GET') {
        // Static assets - Cache First strategy
        if (STATIC_ASSETS.some(asset => event.request.url.includes(asset))) {
            event.respondWith(cacheFirstStrategy(event.request));
        }
        // Data requests - Network First with cache fallback
        else if (DATA_URLS.some(url => event.request.url.includes(url))) {
            event.respondWith(networkFirstStrategy(event.request));
        }
        // CDN resources - Cache First strategy
        else if (requestUrl.hostname.includes('cdn.') || 
                 requestUrl.hostname.includes('cdnjs.') ||
                 requestUrl.hostname.includes('jsdelivr')) {
            event.respondWith(cacheFirstStrategy(event.request));
        }
        // Other requests - Network First strategy
        else {
            event.respondWith(networkFirstStrategy(event.request));
        }
    }
});

// Background sync for offline data updates
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    if (event.tag === 'background-sync-metrics') {
        event.waitUntil(syncMetricsData());
    } else if (event.tag === 'background-sync-exports') {
        event.waitUntil(syncExportQueue());
    } else if (event.tag === 'background-sync-filters') {
        event.waitUntil(syncFilterChanges());
    }
});

// Push notification handling
self.addEventListener('push', (event) => {
    console.log('Service Worker: Push notification received', event);
    
    let notificationData = {
        title: 'Flow Metrics Dashboard',
        body: 'New metrics data available',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: 'metrics-update',
        requireInteraction: false,
        actions: [
            {
                action: 'view-dashboard',
                title: 'View Dashboard',
                icon: '/icons/action-view.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/icons/action-dismiss.png'
            }
        ]
    };
    
    if (event.data) {
        try {
            const payload = event.data.json();
            notificationData = { ...notificationData, ...payload };
        } catch (error) {
            console.error('Service Worker: Error parsing push data', error);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('Service Worker: Notification clicked', event);
    
    event.notification.close();
    
    if (event.action === 'view-dashboard') {
        event.waitUntil(
            clients.openWindow('/dashboard.html')
        );
    } else if (event.action === 'dismiss') {
        // Just close the notification
        return;
    } else {
        // Default action - open dashboard
        event.waitUntil(
            clients.openWindow('/dashboard.html')
        );
    }
});

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
    console.log('Service Worker: Message received', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data.type === 'CACHE_METRICS_DATA') {
        cacheMetricsData(event.data.data);
    } else if (event.data.type === 'QUEUE_EXPORT') {
        queueExportForSync(event.data.exportData);
    } else if (event.data.type === 'QUEUE_FILTER_CHANGE') {
        queueFilterChangeForSync(event.data.filterData);
    }
});

// Caching Strategies

/**
 * Cache First Strategy - Try cache first, fallback to network
 */
async function cacheFirstStrategy(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Service Worker: Cache first strategy failed', error);
        return new Response('Offline - Resource not available', { 
            status: 503, 
            statusText: 'Service Unavailable' 
        });
    }
}

/**
 * Network First Strategy - Try network first, fallback to cache
 */
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DATA_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Service Worker: Network failed, trying cache', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page or error response
        return new Response(JSON.stringify({
            error: 'Offline - No cached data available',
            offline: true,
            timestamp: new Date().toISOString()
        }), {
            status: 503,
            statusText: 'Service Unavailable',
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
}

// Background Sync Functions

/**
 * Sync metrics data when back online
 */
async function syncMetricsData() {
    try {
        console.log('Service Worker: Syncing metrics data...');
        
        // Get queued metrics requests from IndexedDB
        const queuedRequests = await getQueuedMetricsRequests();
        
        for (const request of queuedRequests) {
            try {
                const response = await fetch(request.url, request.options);
                if (response.ok) {
                    // Cache the fresh data
                    const cache = await caches.open(DATA_CACHE_NAME);
                    cache.put(request.url, response.clone());
                    
                    // Remove from queue
                    await removeFromMetricsQueue(request.id);
                    
                    // Notify clients of fresh data
                    const clients = await self.clients.matchAll();
                    clients.forEach(client => {
                        client.postMessage({
                            type: 'METRICS_SYNCED',
                            data: request.url
                        });
                    });
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync metrics request', error);
            }
        }
        
        console.log('Service Worker: Metrics sync complete');
    } catch (error) {
        console.error('Service Worker: Metrics sync failed', error);
    }
}

/**
 * Sync export queue when back online
 */
async function syncExportQueue() {
    try {
        console.log('Service Worker: Syncing export queue...');
        
        const queuedExports = await getQueuedExports();
        
        for (const exportData of queuedExports) {
            try {
                // Process the export
                const response = await fetch('/api/exports', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(exportData.data)
                });
                
                if (response.ok) {
                    await removeFromExportQueue(exportData.id);
                    
                    // Notify client of successful export
                    const clients = await self.clients.matchAll();
                    clients.forEach(client => {
                        client.postMessage({
                            type: 'EXPORT_SYNCED',
                            data: exportData
                        });
                    });
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync export', error);
            }
        }
        
        console.log('Service Worker: Export sync complete');
    } catch (error) {
        console.error('Service Worker: Export sync failed', error);
    }
}

/**
 * Sync filter changes when back online
 */
async function syncFilterChanges() {
    try {
        console.log('Service Worker: Syncing filter changes...');
        
        const queuedFilters = await getQueuedFilterChanges();
        
        for (const filterData of queuedFilters) {
            try {
                // Sync filter preferences to server
                const response = await fetch('/api/user-preferences/filters', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(filterData.data)
                });
                
                if (response.ok) {
                    await removeFromFilterQueue(filterData.id);
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync filter change', error);
            }
        }
        
        console.log('Service Worker: Filter sync complete');
    } catch (error) {
        console.error('Service Worker: Filter sync failed', error);
    }
}

// IndexedDB Helper Functions for Background Sync

/**
 * Cache metrics data for offline access
 */
async function cacheMetricsData(data) {
    try {
        const db = await openIndexedDB();
        const transaction = db.transaction(['metrics-cache'], 'readwrite');
        const store = transaction.objectStore('metrics-cache');
        
        await store.put({
            id: 'current-metrics',
            data: data,
            timestamp: new Date().toISOString()
        });
        
        console.log('Service Worker: Metrics data cached');
    } catch (error) {
        console.error('Service Worker: Failed to cache metrics data', error);
    }
}

/**
 * Queue export for background sync
 */
async function queueExportForSync(exportData) {
    try {
        const db = await openIndexedDB();
        const transaction = db.transaction(['export-queue'], 'readwrite');
        const store = transaction.objectStore('export-queue');
        
        await store.add({
            id: Date.now(),
            data: exportData,
            timestamp: new Date().toISOString()
        });
        
        console.log('Service Worker: Export queued for sync');
    } catch (error) {
        console.error('Service Worker: Failed to queue export', error);
    }
}

/**
 * Queue filter change for background sync
 */
async function queueFilterChangeForSync(filterData) {
    try {
        const db = await openIndexedDB();
        const transaction = db.transaction(['filter-queue'], 'readwrite');
        const store = transaction.objectStore('filter-queue');
        
        await store.add({
            id: Date.now(),
            data: filterData,
            timestamp: new Date().toISOString()
        });
        
        console.log('Service Worker: Filter change queued for sync');
    } catch (error) {
        console.error('Service Worker: Failed to queue filter change', error);
    }
}

/**
 * Open IndexedDB for offline storage
 */
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FlowMetricsPWA', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create object stores
            if (!db.objectStoreNames.contains('metrics-cache')) {
                db.createObjectStore('metrics-cache', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('export-queue')) {
                db.createObjectStore('export-queue', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('filter-queue')) {
                db.createObjectStore('filter-queue', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('metrics-queue')) {
                db.createObjectStore('metrics-queue', { keyPath: 'id' });
            }
        };
    });
}

// Placeholder functions for queue management (would be implemented with IndexedDB)
async function getQueuedMetricsRequests() {
    // Implementation would retrieve from IndexedDB
    return [];
}

async function removeFromMetricsQueue(id) {
    // Implementation would remove from IndexedDB
}

async function getQueuedExports() {
    // Implementation would retrieve from IndexedDB
    return [];
}

async function removeFromExportQueue(id) {
    // Implementation would remove from IndexedDB
}

async function getQueuedFilterChanges() {
    // Implementation would retrieve from IndexedDB
    return [];
}

async function removeFromFilterQueue(id) {
    // Implementation would remove from IndexedDB
}