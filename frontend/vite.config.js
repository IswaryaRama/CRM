import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig(async ({ mode }) => {
  const isDev = mode === 'development'

  const fs = await import('node:fs')
  let socketioPort = 9000
  try {
    const commonSiteConfig = JSON.parse(
      fs.readFileSync(path.resolve(__dirname, '../sites/common_site_config.json'), 'utf-8')
    )
    socketioPort = commonSiteConfig.socketio_port || 9000
  } catch (e) {
    // ignore
  }

  const config = {
    plugins: [
      vue(),
      vueJsx(),
      VitePWA({
        registerType: 'autoUpdate',
        devOptions: {
          enabled: true,
        },
        workbox: {
          maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
        },
        manifest: {
          display: 'standalone',
          name: 'Frappe CRM',
          short_name: 'Frappe CRM',
          start_url: '/crm',
          description:
            'Modern & 100% Open-source CRM tool to supercharge your sales operations',
          icons: [
            {
              src: '/assets/crm/manifest/manifest-icon-192.maskable.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: '/assets/crm/manifest/manifest-icon-192.maskable.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'maskable',
            },
            {
              src: '/assets/crm/manifest/manifest-icon-512.maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: '/assets/crm/manifest/manifest-icon-512.maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '../../../../sites/common_site_config.json': path.resolve(
          __dirname,
          '../sites/common_site_config.json',
        ),
      },
    },
    optimizeDeps: {
      include: [
        'feather-icons',
        'tailwind.config.js',
        'prosemirror-state',
        'prosemirror-view',
        'lowlight',
        'interactjs',
      ],
    },
    server: {
      allowedHosts: true,
      fs: {
        strict: false,
        allow: [
          path.resolve(__dirname, '..'),
          path.resolve(__dirname, 'src'),
          __dirname,
        ],
      },
      proxy: {
        '/socket.io': {
          target: `http://127.0.0.1:${socketioPort}`,
          ws: true,
          changeOrigin: true,
          configure: (proxy, _options) => {
            proxy.on('proxyReqWs', (proxyReq, req, _socket, _options, _head) => {
              const host = req.headers.host.split(':')[0]
              proxyReq.setHeader('Origin', `http://${host}:8000`)
            })
            proxy.on('proxyReq', (proxyReq, req, _res, _options) => {
              const host = req.headers.host.split(':')[0]
              proxyReq.setHeader('Origin', `http://${host}:8000`)
            })
          },
        },
        '/vobiz-ws': {
          target: 'wss://registrar.vobiz.ai:5063',
          ws: true,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/vobiz-ws/, ''),
        },
      },
    },
    appType: 'spa',
  }

  // SPA history fallback for /crm routes so Vue Router can handle them
  config.plugins.push({
    name: 'crm-spa-fallback',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (
          req.url.startsWith('/crm') &&
          !req.url.includes('.') &&
          req.headers.accept?.includes('text/html')
        ) {
          req.url = '/index.html'
        }
        next()
      })
    },
  })

  const frappeui = await importFrappeUIPlugin(isDev, config)
  config.plugins.unshift(
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: !isDev,
      buildConfig: {
        indexHtmlPath: '../crm/www/crm.html',
        emptyOutDir: true,
        sourcemap: true,
      },
    }),
  )

  return config
})

async function importFrappeUIPlugin(isDev, config) {
  if (isDev) {
    try {
      // Check if local frappe-ui has the vite plugin file
      const fs = await import('node:fs')
      const localVitePluginPath = path.resolve(__dirname, '../frappe-ui/vite')

      if (fs.existsSync(localVitePluginPath)) {
        const module = await import('../frappe-ui/vite')
        console.info('Local frappe-ui vite plugin found, using local plugin')
        config.resolve.alias = getAliases(config)
        return module.default
      } else {
        console.warn('Local frappe-ui vite plugin not found, using npm package')
      }
    } catch (error) {
      console.warn(
        'Local frappe-ui not found, falling back to npm package:',
        error.message,
      )
    }
  }
  // Fall back to npm package if local import fails
  const module = await import('frappe-ui/vite')
  return module.default
}

function getAliases(config) {
  return {
    ...config.resolve.alias,
    'frappe-ui/tailwind': path.resolve(
      __dirname,
      '../frappe-ui/tailwind/preset.js',
    ),
    'frappe-ui/style.css': path.resolve(
      __dirname,
      '../frappe-ui/src/style.css',
    ),
    'frappe-ui/frappe': path.resolve(__dirname, '../frappe-ui/frappe/index.js'),
    'frappe-ui': path.resolve(__dirname, '../frappe-ui/src/index.ts'),
  }
}
