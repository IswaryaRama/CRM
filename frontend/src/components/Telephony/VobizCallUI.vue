<template>
  <div v-show="showCallPopup" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 text-ink-gray-2 shadow-2xl"
      :style="style"
      @click.stop
    >
      <div class="flex flex-row-reverse items-center gap-1">
        <MinimizeIcon
          class="h-4 w-4 cursor-pointer"
          @click="toggleCallWindow"
        />
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <div
          class="relative flex h-24 w-24 items-center justify-center rounded-full bg-surface-gray-6"
          :class="onCall || calling ? '' : 'pulse'"
        >
          <Avatar
            v-if="contact?.image"
            :image="contact.image"
            :label="contact.full_name"
            class="!h-24 !w-24 [&>div]:text-[30px]"
          />
          <AvatarIcon v-else class="h-12 w-12 text-ink-gray-4" />
        </div>
        <div class="flex flex-col items-center justify-center gap-1">
          <div class="text-xl font-medium text-ink-white truncate max-w-[200px]">
            {{ contact?.full_name ?? __('Unknown') }}
          </div>
          <div class="text-sm text-ink-gray-4">{{ contact?.mobile_no || phoneNumber }}</div>
        </div>
        <CountUpTimer ref="counterUp">
          <div v-if="onCall" class="my-1 text-base text-ink-white">
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall" class="my-1 text-base text-ink-white">
          {{
            callStatus == 'initiating'
              ? __('Initiating call...')
              : callStatus == 'ringing'
                ? __('Ringing...')
                : calling
                  ? __('Calling...')
                  : __('Incoming call...')
          }}
        </div>

        <div v-if="onCall" class="flex gap-2">
          <Button
            :icon="muted ? 'mic-off' : 'mic'"
            class="rounded-full bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            @click="toggleMute"
          />
          <Button
            class="cursor-pointer rounded-full bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            :tooltip="__('Add a Note')"
            :icon="NoteIcon"
            @click="openNoteModal"
          />
          <Button
            class="rounded-full bg-surface-red-5 hover:bg-surface-red-6 rotate-[135deg] text-ink-white"
            :tooltip="__('Hang Up')"
            :icon="PhoneIcon"
            @click="hangUpCall"
          />
        </div>
        <div v-else-if="calling || callStatus == 'initiating'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Cancel')"
            class="rounded-lg text-ink-white"
            @click="cancelCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
        <div v-else class="flex gap-2">
          <Button
            size="md"
            variant="solid"
            theme="green"
            :label="__('Accept')"
            class="rounded-lg text-ink-white"
            :iconLeft="PhoneIcon"
            @click="acceptIncomingCall"
          />
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Reject')"
            class="rounded-lg text-ink-white"
            @click="rejectIncomingCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>

  <div
    v-show="showSmallCallWindow"
    class="ml-2 flex cursor-pointer select-none items-center justify-between gap-3 rounded-lg bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
    v-bind="$attrs"
    @click="toggleCallWindow"
  >
    <div class="flex items-center gap-2">
      <Avatar
        v-if="contact?.image"
        :image="contact.image"
        :label="contact.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <div class="max-w-[120px] truncate text-ink-white">
        {{ contact?.full_name ?? __('Unknown') }}
      </div>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center text-ink-white">
        {{ counterUp?.updatedTime }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-white"
        :icon="PhoneIcon"
        @click.stop="hangUpCall"
      />
    </div>
    <div v-else-if="calling" class="flex items-center gap-3">
      <div class="my-1 text-ink-white">
        {{ callStatus == 'ringing' ? __('Ringing...') : __('Calling...') }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-white"
        :icon="PhoneIcon"
        @click.stop="cancelCall"
      />
    </div>
    <div v-else class="flex items-center gap-2">
      <Button
        variant="solid"
        theme="green"
        class="pulse relative !h-6 !w-6 rounded-full animate-pulse text-ink-white"
        :tooltip="__('Accept Call')"
        :icon="PhoneIcon"
        @click.stop="acceptIncomingCall"
      />
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-white"
        :tooltip="__('Reject Call')"
        :icon="PhoneIcon"
        @click.stop="rejectIncomingCall"
      />
    </div>
  </div>

  <!-- Audio Element for Remote Stream -->
  <audio ref="remoteAudio" autoplay playsinline style="display:none"></audio>
</template>

<script setup>
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import AvatarIcon from '@/components/Icons/AvatarIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { globalStore } from '@/stores/global'
import { Avatar, Button, call, createResource, toast } from 'frappe-ui'
import { ref, watch, onBeforeUnmount } from 'vue'

let vobiz = null
let currentCallSid = null
let loginPromise = null
let loginSucceeded = false

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let calling = ref(false)
let muted = ref(false)
let callPopup = ref(null)
let remoteAudio = ref(null)
let counterUp = ref(null)
let callStatus = ref('')

const phoneNumber = ref('')
const pendingOutboundNumber = ref('')

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  cache: ['contact', phoneNumber.value],
  onSuccess(data) {
    contact.value = data
  },
})

const { showModal } = useDoctypeModal()
const note = ref({
  name: '',
  title: '',
  content: '',
})

function openNoteModal() {
  if (!currentCallSid) return
  showModal({
    name: note.value.name || null,
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: (n) => updateNote(n, true),
      afterUpdate: updateNote,
    },
  })
}

async function updateNote(_note, isInsert = false) {
  note.value = _note
  if (isInsert && _note.name && currentCallSid) {
    await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: currentCallSid,
      note: _note,
    })
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  preventDefault: true,
})

function destroyVobizClient() {
  if (vobiz) {
    try {
      vobiz.client.hangup()
    } catch (e) { /* no active call */ }
    try {
      vobiz.client.logout()
    } catch (e) { /* not logged in */ }
  }
  vobiz = null
  loginPromise = null
  loginSucceeded = false
}

async function startupClient() {
  // If previously logged in successfully, reuse
  if (vobiz && loginSucceeded) return loginPromise

  // If SDK exists but login failed/timed out, destroy and start fresh
  if (vobiz && !loginSucceeded) {
    console.warn('[Vobiz] Previous login failed, destroying old client and re-initializing...')
    destroyVobizClient()
  }

  try {
    const creds = await call('crm.integrations.vobiz.api.get_vobiz_credentials')

    // Debug: log credential shape to diagnose Authentication Error
    console.log('[Vobiz Debug] Credentials received:', {
      username: creds.username,
      passwordLength: creds.password?.length ?? 0,
      passwordEmpty: !creds.password,
      hasAppId: !!creds.appId,
      hasAppSecret: !!creds.appSecret,
      wsUrlOverride: creds.websocketUrlOverride || '(none — will use /vobiz-ws default)',
    })

    if (!creds.username || !creds.password) {
      console.warn('[Vobiz] Credentials not set for user — username or password is empty. Check CRM Telephony Agent record.')
      return
    }

    if (!window.Vobiz) {
      console.error('Vobiz SDK is not loaded')
      return
    }

    console.log('[Vobiz] Initializing SDK and logging in as:', creds.username)

    // Initialize Vobiz SDK
    vobiz = new window.Vobiz({
      debug: 'ALL',
      permOnClick: true,
      enableTracking: false,
      closeProtection: false,
      maxAverageBitrate: 48000,
      appId: creds.appId || null,
      appSecret: creds.appSecret || null,
      registrationDomainSocket: (() => {
        let wsOverride = creds.websocketUrlOverride || '/vobiz-ws'
        if (wsOverride) {
          if (wsOverride.startsWith('/')) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            wsOverride = `${protocol}//${window.location.host}${wsOverride}`
          } else if (wsOverride.includes('/vobiz-ws')) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            wsOverride = `${protocol}//${window.location.host}/vobiz-ws`
          }
        }
        return wsOverride
      })(),
    })

    // Create a promise that resolves when SIP registration completes
    loginPromise = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        loginSucceeded = false
        reject(new Error('Vobiz login timed out after 15s'))
      }, 15000)

      vobiz.client.on('onLogin', () => {
        clearTimeout(timeout)
        loginSucceeded = true
        console.log('[Vobiz] Successfully registered!')
        resolve()
      })

      vobiz.client.on('onLoginFailed', (reason) => {
        clearTimeout(timeout)
        loginSucceeded = false
        console.error('[Vobiz] Login failed:', reason)
        reject(new Error(`Vobiz login failed: ${reason}`))
      })
    })

    addVobizListeners()
    listenForServerCallEvents()

    // Login WebRTC endpoint
    vobiz.client.login(creds.username, creds.password)
    return loginPromise
  } catch (err) {
    console.error('[Vobiz] Error starting up client:', err)
    // Reset so next attempt starts fresh
    destroyVobizClient()
  }
}

function addVobizListeners() {
  // onLogin and onLoginFailed are handled by the loginPromise in startupClient

  vobiz.client.on('onCallRemoteRinging', (callInfo) => {
    callStatus.value = 'ringing'
  })

  vobiz.client.on('onCallAnswered', (callInfo) => {
    onCall.value = true
    calling.value = false
    callStatus.value = 'in-progress'
    if (callInfo?.callUUID) {
      currentCallSid = callInfo.callUUID
    }
    counterUp.value.start()
    attachAudioStream()
    updateBackendStatus('In Progress')
  })

  vobiz.client.on('onCallTerminated', (event, callInfo) => {
    // Extract callUUID before ending UI in case it was updated
    if (callInfo?.callUUID && !currentCallSid) {
      currentCallSid = callInfo.callUUID
    }
    const callSidForUpdate = currentCallSid
    // Capture duration BEFORE endCallUI resets the timer
    const durationSec = counterUp.value ? counterUp.value.totalSeconds || 0 : 0
    endCallUI()
    if (callSidForUpdate) {
      call('crm.integrations.vobiz.api.update_vobiz_call_status', {
        call_sid: callSidForUpdate,
        status: 'Completed',
        duration: durationSec,
      }).catch((err) => console.warn('Could not update call status on termination:', err))
    }
  })

  vobiz.client.on('onCallFailed', (cause, callInfo) => {
    if (callInfo?.callUUID && !currentCallSid) {
      currentCallSid = callInfo.callUUID
    }
    const callSidForUpdate = currentCallSid
    endCallUI()
    if (callSidForUpdate) {
      let backendStatus = 'Failed'
      if (cause === 'Busy') {
        backendStatus = 'Busy'
      } else if (cause === 'No Answer') {
        backendStatus = 'No Answer'
      } else if (cause === 'Canceled') {
        backendStatus = 'Canceled'
      }
      call('crm.integrations.vobiz.api.update_vobiz_call_status', {
        call_sid: callSidForUpdate,
        status: backendStatus,
        duration: 0,
      }).catch((err) => console.warn('Could not update call status on failure:', err))
    }
  })

  vobiz.client.on('onIncomingCall', (callerName, extraHeaders) => {
    phoneNumber.value = callerName
    showCallPopup.value = true
    callStatus.value = 'incoming'
  })
}

function listenForServerCallEvents() {
  // Listen for the server-side call log creation event to capture the real call_sid
  const { $socket } = globalStore()
  $socket.on('vobiz_call', (data) => {
    // Match outbound calls by phone number when we don't have a call_sid yet
    if (
      data.Direction === 'outbound-api' &&
      pendingOutboundNumber.value &&
      data.CallSid
    ) {
      const normalizedTo = (data.To || '').replace(/[^\d+]/g, '')
      const normalizedPending = pendingOutboundNumber.value.replace(
        /[^\d+]/g,
        '',
      )
      if (
        normalizedTo === normalizedPending ||
        normalizedTo.endsWith(normalizedPending) ||
        normalizedPending.endsWith(normalizedTo)
      ) {
        currentCallSid = data.CallSid
        pendingOutboundNumber.value = ''
      }
    }
  })
}

function attachAudioStream() {
  setTimeout(() => {
    let stream = null
    if (vobiz && vobiz.client && vobiz.client.remoteView) {
      stream = vobiz.client.remoteView.srcObject
    }

    if (!stream && vobiz && vobiz.client) {
      try {
        const pc = vobiz.client.getPeerConnection().pc
        if (pc) {
          const receivers = pc.getReceivers()
          const audioReceiver = receivers.find((r) => r.track && r.track.kind === 'audio')
          if (audioReceiver && audioReceiver.track) {
            stream = new MediaStream([audioReceiver.track])
          }
        }
      } catch (e) {
        console.warn('Could not retrieve peer connection stream:', e)
      }
    }

    if (stream && remoteAudio.value) {
      remoteAudio.value.srcObject = stream
      remoteAudio.value.play().catch((e) => console.error('Audio play error:', e))
    }
  }, 1000)
}

function updateBackendStatus(status) {
  if (!currentCallSid) {
    console.warn('Vobiz: No call_sid available to update status to', status)
    return
  }
  const durationSec = counterUp.value ? counterUp.value.totalSeconds || 0 : 0
  call('crm.integrations.vobiz.api.update_vobiz_call_status', {
    call_sid: currentCallSid,
    status: status,
    duration: durationSec,
  }).catch((err) =>
    console.warn('Vobiz: Could not update call status:', err),
  )
}

function forceCleanupSdk() {
  if (!vobiz) return
  try {
    vobiz.client.hangup()
  } catch (e) {
    // Ignore errors if no active call to hang up
  }
  try {
    vobiz.client.reject()
  } catch (e) {
    // Ignore errors if no incoming call to reject
  }
}

function endCallUI() {
  forceCleanupSdk()
  onCall.value = false
  calling.value = false
  showCallPopup.value = false
  showSmallCallWindow.value = false
  callStatus.value = ''
  muted.value = false
  pendingOutboundNumber.value = ''
  currentCallSid = null
  if (counterUp.value) counterUp.value.stop()
  note.value = {
    name: '',
    title: '',
    content: '',
  }
}

function toggleMute() {
  if (!vobiz) return
  if (muted.value) {
    vobiz.client.unmute()
    muted.value = false
  } else {
    vobiz.client.mute()
    muted.value = true
  }
}

async function acceptIncomingCall() {
  if (vobiz) {
    vobiz.client.answer()
  }
}

function rejectIncomingCall() {
  if (vobiz) {
    vobiz.client.reject()
  }
  endCallUI()
}

function hangUpCall() {
  if (vobiz) {
    vobiz.client.hangup()
  }
  endCallUI()
}

function cancelCall() {
  hangUpCall()
}

async function makeOutgoingCall(number) {
  phoneNumber.value = number
  pendingOutboundNumber.value = number
  showCallPopup.value = true
  callStatus.value = 'initiating'
  calling.value = true
  currentCallSid = null

  // Ensure client is set up and SIP registration is complete
  try {
    await startupClient()
  } catch (err) {
    console.error('[Vobiz] startup/login failed:', err)
    toast.error(__('Vobiz login failed. Please check your credentials.'))
    endCallUI()
    return
  }

  if (!vobiz) {
    toast.error(__('Vobiz integration not configured or registered.'))
    endCallUI()
    return
  }

  // Force cleanup any stale call session before placing a new call
  forceCleanupSdk()
  // Small delay to let the SDK settle after cleanup
  await new Promise((resolve) => setTimeout(resolve, 500))

  // Clean phone number for dialing: keep only digits and '+'
  let cleanNumber = number.replace(/[^\d+]/g, '')
  if (cleanNumber && !cleanNumber.startsWith('+') && /^\d+$/.test(cleanNumber)) {
    // Strip leading zero for local 10-digit calls
    if (cleanNumber.startsWith('0') && cleanNumber.length === 11) {
      cleanNumber = cleanNumber.substring(1)
    }
    // Prepend +91 if it's a 10-digit Indian mobile number (starts with 6-9)
    if (cleanNumber.length === 10 && /^[6-9]/.test(cleanNumber)) {
      cleanNumber = '+91' + cleanNumber
    } else {
      cleanNumber = '+' + cleanNumber
    }
  }

  console.log('[Vobiz] Placing call to:', cleanNumber)
  vobiz.client.call(cleanNumber)
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallWindow.value = !showSmallCallWindow.value
}

function handleUnload() {
  if (vobiz) {
    vobiz.client.logout()
  }
}

window.addEventListener('beforeunload', handleUnload)

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleUnload)
  handleUnload()
})


defineExpose({ makeOutgoingCall, setup: startupClient })
</script>

<style scoped>
.pulse::before {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}
</style>
