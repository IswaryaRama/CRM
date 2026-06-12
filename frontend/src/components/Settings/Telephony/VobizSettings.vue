<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Vobiz Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="isEnabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="isEnabled && !vobiz.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="vobiz.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="vobiz.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="vobiz.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
      <div v-else-if="vobiz.doc" class="h-full">
        <div v-if="isEnabled" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="vobiz.doc.auth_id"
              :label="__('Auth ID')"
              type="text"
              placeholder="MA_XXXXXXXXXX"
              required
              autocomplete="off"
            />
            <Password
              v-model="vobiz.doc.api_password"
              :label="__('API Password')"
              placeholder="************"
              required
            />
          </div>
          <div class="h-px border-t border-outline-gray-modals" />
          <div class="flex items-center justify-between">
            <div class="flex flex-col">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ __('Record Outgoing Calls') }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{
                  __('Enable call recording for outbound calls made from the browser')
                }}
              </div>
            </div>
            <div>
              <Switch v-model="recordCalls" size="sm" />
            </div>
          </div>
          <div class="h-px border-t border-outline-gray-modals" />
          <!-- Webhook Configuration -->
          <div class="space-y-4">
            <h3 class="text-md font-semibold text-ink-gray-8">
              {{ __('Webhook Configuration (Answer URL)') }}
            </h3>
            
            <div class="p-3 bg-gray-50 border border-outline-gray rounded-md space-y-2">
              <div class="flex justify-between items-center gap-4">
                <div class="flex-1 min-w-0">
                  <span class="text-p-sm font-medium text-ink-gray-5">
                    {{ __('Your Answer URL (Webhook)') }}
                  </span>
                  <div class="font-mono text-p-base text-ink-gray-8 truncate bg-white p-2 border border-outline-gray rounded mt-1 select-all select-text">
                    {{ webhookUrl || __('Loading...') }}
                  </div>
                </div>
                <Button
                  v-if="webhookUrl"
                  :label="copied ? __('Copied') : __('Copy')"
                  variant="subtle"
                  class="mt-6"
                  @click="copyWebhook"
                />
              </div>
              <p class="text-p-sm text-ink-gray-5">
                {{ __('Configure this URL as the Answer URL in your Vobiz Application settings.') }}
                <span class="text-orange-600 font-medium">
                  {{ __('Must be publicly accessible (e.g. via ngrok for local development).') }}
                </span>
              </p>
            </div>
            <Alert
              v-if="isLocalhost"
              :title="__('Local Environment Detected')"
              theme="orange"
              variant="subtle"
              class="mt-2"
            >
              {{ __('Your site is running locally. Vobiz servers must be able to reach your site to handle calls. Please configure a public tunnel (e.g. ngrok) and configure your site hostname.') }}
            </Alert>

            <div class="p-3 bg-gray-50 border border-outline-gray rounded-md space-y-4">
              <FormControl
                v-model="vobiz.doc.webhook_url_override"
                :label="__('Webhook URL Override')"
                type="text"
                placeholder="https://your-tunnel.ngrok-free.app"
                :description="__('Paste a custom public tunnel URL here to override the default site URL for webhooks.')"
              />
              <FormControl
                v-model="vobiz.doc.websocket_url_override"
                :label="__('WebSocket URL Override')"
                type="text"
                placeholder="wss://your-sip-server.com:5063"
                :description="__('Paste a custom WebSocket server URL here to override the default Vobiz WebSocket registrar URL.')"
              />
            </div>

            <!-- Programmatic Registration -->
            <div v-if="vobiz.originalDoc?.auth_id" class="space-y-3">
              <div class="flex justify-between items-center">
                <div class="flex flex-col">
                  <span class="text-p-base font-medium text-ink-gray-7">
                    {{ __('Auto-configure Vobiz Application') }}
                  </span>
                  <span class="text-p-sm text-ink-gray-5">
                    {{ __('Select a Vobiz Application to register the Answer URL webhook automatically.') }}
                  </span>
                </div>
                <Button
                  :label="vobizApps.length > 0 ? __('Refresh Apps') : __('Fetch Vobiz Apps')"
                  variant="subtle"
                  :loading="fetchVobizAppsResource.loading"
                  @click="fetchApps"
                />
              </div>

              <div v-if="vobizApps.length > 0" class="flex gap-4 items-end">
                <FormControl
                  v-model="vobiz.doc.app_id"
                  :label="__('Vobiz Application')"
                  type="select"
                  class="w-64 animate-fade-in"
                  :options="vobizApps"
                  required
                />
                <Button
                  v-if="vobiz.doc.app_id"
                  :label="__('Register Webhook')"
                  variant="solid"
                  :loading="registerWebhookResource.loading"
                  @click="registerWebhook"
                />
              </div>

              <div v-if="vobiz.doc.registered_webhook_url" class="text-p-sm text-green-600 flex items-center gap-1.5 mt-2 bg-green-50 p-2.5 rounded border border-green-200">
                <svg class="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {{ __('Webhook successfully registered on: {0}', [vobiz.doc.registered_webhook_url]) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <!-- Disabled State -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg font-medium text-ink-gray-8">
                {{ __('Vobiz Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Vobiz integration to make and receive calls directly from your browser in the CRM',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import { setEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import { Switch, Badge, Button, FormControl, LoadingIndicator, toast, createResource } from 'frappe-ui'
import { computed, ref, onMounted, watch } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: vobiz } = useDocument(
  'CRM Vobiz Settings',
  'CRM Vobiz Settings',
)

const fetchVobizAppsResource = createResource({
  url: 'run_doc_method',
  makeParams() {
    return {
      dt: 'CRM Vobiz Settings',
      dn: 'CRM Vobiz Settings',
      method: 'fetch_applications',
    }
  },
  transform(data) {
    return data.message
  }
})

const registerWebhookResource = createResource({
  url: 'run_doc_method',
  makeParams(values) {
    return {
      dt: 'CRM Vobiz Settings',
      dn: 'CRM Vobiz Settings',
      method: 'register_webhook',
      args: values,
    }
  },
  transform(data) {
    return data.message
  }
})

const getWebhookUrlResource = createResource({
  url: 'run_doc_method',
  makeParams() {
    return {
      dt: 'CRM Vobiz Settings',
      dn: 'CRM Vobiz Settings',
      method: 'get_webhook_url',
    }
  },
  transform(data) {
    return data.message
  }
})

const webhookUrl = ref('')
const copied = ref(false)
const vobizApps = ref([])
const isEnabled = ref(false)

const recordCalls = computed({
  get() {
    return Boolean(vobiz.doc?.record_calls)
  },
  set(val) {
    if (vobiz.doc) {
      vobiz.doc.record_calls = val ? 1 : 0
    }
  }
})

async function fetchWebhookUrl() {
  try {
    const url = await getWebhookUrlResource.submit()
    if (url) {
      webhookUrl.value = url
    }
  } catch (err) {
    console.error('Failed to get webhook url:', err)
  }
}

async function fetchApps() {
  try {
    const res = await fetchVobizAppsResource.submit()
    let apps = []
    if (res && Array.isArray(res)) {
      apps = res
    } else if (res && res.objects && Array.isArray(res.objects)) {
      apps = res.objects
    }

    if (apps.length > 0) {
      vobizApps.value = apps.map((app) => ({
        label: app.app_name || app.name || app.friendly_name || app.app_id || app.id,
        value: app.app_id || app.id,
      }))
    } else {
      toast.error(__('No applications found in Vobiz account.'))
    }
  } catch (err) {
    toast.error(err.message || __('Failed to fetch applications.'))
  }
}

async function registerWebhook() {
  if (!vobiz.doc.app_id) return
  try {
    const res = await registerWebhookResource.submit({ app_id: vobiz.doc.app_id })
    if (res && res.status === 'success') {
      vobiz.doc.registered_webhook_url = res.webhook_url
      toast.success(__('Webhook registered successfully!'))
    }
  } catch (err) {
    toast.error(err.message || __('Failed to register webhook.'))
  }
}

async function copyWebhook() {
  if (!webhookUrl.value) return
  try {
    await navigator.clipboard.writeText(webhookUrl.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    toast.error(__('Failed to copy webhook URL.'))
  }
}

watch(() => vobiz.doc?.enabled, (val) => {
  isEnabled.value = Boolean(val)
  if (val) {
    fetchWebhookUrl()
  }
}, { immediate: true })

function enable() {
  if (vobiz.doc) {
    vobiz.doc.enabled = 1
    isEnabled.value = true
  }
}

function disable() {
  if (vobiz.doc) {
    vobiz.doc.enabled = 0
    isEnabled.value = false
    update()
  }
}

function update() {
  vobiz.save.submit(null, {
    onSuccess: async () => {
      await vobiz.reload()
      setEnabled('vobiz', vobiz.doc.enabled)
      toast.success(__('Vobiz settings updated successfully'))
      fetchWebhookUrl()
    },
    onError: (err) => {
      toast.error(err.message || __('Failed to update settings'))
    }
  })
}

const isDirty = computed(() => {
  return (
    vobiz.doc &&
    vobiz.originalDoc &&
    JSON.stringify(vobiz.doc) !== JSON.stringify(vobiz.originalDoc)
  )
})

const isLocalhost = computed(() => {
  if (!webhookUrl.value) return false
  return (
    webhookUrl.value.includes('localhost') ||
    webhookUrl.value.includes('127.0.0.1') ||
    webhookUrl.value.includes('0.0.0.0') ||
    webhookUrl.value.includes('.local')
  )
})
</script>
