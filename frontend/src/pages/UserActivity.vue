<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2 text-xl font-semibold text-ink-gray-8">
          <LucideActivity class="size-5 text-ink-gray-5" />
          <span>{{ __('User Activity History') }}</span>
        </div>
      </template>
      <template #right-header>
        <Link
          class="form-control w-64"
          variant="outline"
          :value="selectedUser && getUser(selectedUser).full_name"
          doctype="User"
          :filters="{
            name: ['in', users.data.crmUsers?.map((u) => u.name) || []],
            ignore_user_type: 1,
          }"
          :placeholder="__('Select User')"
          :hideMe="true"
          @change="(v) => selectedUser = v"
        >
          <template #prefix>
            <UserAvatar
              v-if="selectedUser"
              class="mr-2"
              :user="selectedUser"
              size="sm"
            />
          </template>
          <template #item-prefix="{ option }">
            <UserAvatar class="mr-2" :user="option.value" size="sm" />
          </template>
          <template #item-label="{ option }">
            <Tooltip :text="option.value">
              <div class="cursor-pointer">
                {{ getUser(option.value).full_name }}
              </div>
            </Tooltip>
          </template>
        </Link>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto p-5 sm:px-10">
      <div v-if="!selectedUser" class="flex flex-col items-center justify-center h-full text-ink-gray-4 gap-2">
        <LucideUser class="size-12 stroke-1" />
        <div class="text-lg font-medium">{{ __('No User Selected') }}</div>
        <div class="text-sm text-ink-gray-5">{{ __('Select a user from the dropdown above to view their activity log.') }}</div>
      </div>
      <div v-else-if="userActivities.loading" class="flex flex-col items-center justify-center h-full text-ink-gray-4 gap-2">
        <LoadingIndicator class="size-6 animate-spin" />
        <div>{{ __('Fetching activities...') }}</div>
      </div>
      <div v-else-if="!userActivities.data?.length" class="flex flex-col items-center justify-center h-full text-ink-gray-4 gap-2">
        <LucideActivity class="size-12 stroke-1" />
        <div class="text-lg font-medium">{{ __('No Activities Found') }}</div>
        <div class="text-sm text-ink-gray-5">{{ __('This user has not performed any activities in the system yet.') }}</div>
      </div>
      <div v-else class="max-w-4xl mx-auto space-y-4 pb-10">
        <div
          v-for="activity in userActivities.data"
          :key="activity.name || activity.creation"
          class="bg-surface-gray-1 border border-outline-gray-modals rounded-xl p-4 shadow-sm hover:shadow transition"
        >
          <div class="flex items-center justify-between border-b pb-2 mb-3">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-xs font-semibold uppercase" :class="getBadgeClass(activity.activity_type)">
                {{ activity.activity_type }}
              </span>
              <span class="text-sm text-ink-gray-5">on</span>
              <router-link
                v-if="activity.reference_doctype && activity.reference_docname"
                :to="getRecordRoute(activity.reference_doctype, activity.reference_docname)"
                class="font-medium text-blue-600 hover:underline"
              >
                {{ activity.reference_doctype }}: {{ activity.reference_docname }}
              </router-link>
            </div>
            <span class="text-xs text-ink-gray-5">{{ formatDate(activity.creation) }}</span>
          </div>

          <div class="text-base text-ink-gray-8">
            <div v-if="activity.activity_type === 'comment'" class="italic bg-surface-white border rounded p-3 text-sm">
              "{{ stripHtml(activity.content) }}"
            </div>
            <div v-else-if="activity.activity_type === 'creation'">
              {{ activity.data }}
            </div>
            <div v-else-if="['incoming_call', 'outgoing_call'].includes(activity.activity_type)">
              <div class="flex items-center gap-2">
                <span class="font-medium">{{ activity.activity_type === 'incoming_call' ? __('Inbound Call') : __('Outbound Call') }}</span>
                <span class="text-ink-gray-5">- Status:</span>
                <span class="font-semibold">{{ activity.data?.status }}</span>
                <span class="text-ink-gray-5">Duration:</span>
                <span>{{ activity.data?.duration }}s</span>
              </div>
            </div>
            <div v-else-if="activity.activity_type === 'note'">
              <div class="font-medium mb-1">{{ activity.title }}</div>
              <div class="text-sm text-ink-gray-6" v-html="activity.content"></div>
            </div>
            <div v-else-if="activity.activity_type === 'communication'">
              <div class="font-medium text-sm text-ink-gray-9 mb-1">{{ activity.data?.subject }}</div>
              <div class="text-sm text-ink-gray-6 bg-surface-white border rounded p-3 max-h-40 overflow-y-auto" v-html="activity.data?.content"></div>
            </div>
            <div v-else-if="activity.activity_type === 'whatsapp'">
              <div class="text-sm text-ink-gray-6 bg-green-50 border border-green-200 rounded p-3">
                <span class="font-semibold text-green-800 text-xs uppercase block mb-1">WhatsApp message ({{ activity.data?.type }})</span>
                "{{ activity.data?.message }}"
              </div>
            </div>
            <div v-else-if="activity.activity_type === 'task'">
              <div class="flex items-center justify-between">
                <div class="font-medium">{{ activity.title }}</div>
                <span class="text-xs px-2 py-0.5 rounded font-medium bg-blue-50 text-blue-800">{{ activity.status }}</span>
              </div>
              <div class="text-sm text-ink-gray-5 mt-1">{{ activity.description }}</div>
              <div v-if="activity.assigned_to" class="text-xs text-ink-gray-4 mt-2">Assigned to: {{ activity.assigned_to }}</div>
            </div>
            <div v-else-if="activity.activity_type === 'attachment_log'">
              <div class="flex items-center gap-2 text-sm">
                <LucidePaperclip class="size-4 text-ink-gray-5" />
                <span>Uploaded attachment:</span>
                <a :href="activity.data?.file_url" target="_blank" class="font-medium text-blue-600 hover:underline">
                  {{ activity.data?.file_name }}
                </a>
              </div>
            </div>
            <div v-else-if="['changed', 'added', 'removed'].includes(activity.activity_type)" class="text-sm text-ink-gray-7">
              <span class="font-medium">{{ __(activity.data?.field_label || activity.data?.field) }}</span>
              <span v-if="activity.activity_type === 'changed'">
                changed from <span class="font-medium text-ink-gray-9">{{ activity.data?.old_value }}</span> to <span class="font-medium text-ink-gray-9">{{ activity.data?.value }}</span>
              </span>
              <span v-else-if="activity.activity_type === 'added'">
                set to <span class="font-medium text-ink-gray-9">{{ activity.data?.value }}</span>
              </span>
              <span v-else-if="activity.activity_type === 'removed'">
                removed value <span class="font-medium text-ink-gray-9">{{ activity.data?.value }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import LucideActivity from '~icons/lucide/activity'
import LucideUser from '~icons/lucide/user'
import LucidePaperclip from '~icons/lucide/paperclip'
import { usersStore } from '@/stores/users'
import { createResource, Tooltip } from 'frappe-ui'
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { formatDate } from '@/utils'
import { globalStore } from '@/stores/global'

const { $socket } = globalStore()
const { users, getUser } = usersStore()
const selectedUser = ref(null)

const userActivities = createResource({
  url: 'crm.api.activities.get_user_activities',
  makeParams() {
    return {
      user: selectedUser.value,
      limit: 100
    }
  },
  auto: false
})

watch(selectedUser, (val) => {
  if (val) {
    userActivities.fetch()
  } else {
    userActivities.data = []
  }
})

onMounted(() => {
  if ($socket) {
    const reloadIfActive = () => {
      if (selectedUser.value) {
        userActivities.reload()
      }
    }
    $socket.on('crm_lead_update', reloadIfActive)
    $socket.on('crm_deal_update', reloadIfActive)
    $socket.on('vobiz_call_update', reloadIfActive)
    $socket.on('vobiz_call', reloadIfActive)
    $socket.on('exotel_call', reloadIfActive)
  }
})

onBeforeUnmount(() => {
  if ($socket) {
    $socket.off('crm_lead_update')
    $socket.off('crm_deal_update')
    $socket.off('vobiz_call_update')
    $socket.off('vobiz_call')
    $socket.off('exotel_call')
  }
})

function getBadgeClass(type) {
  switch (type) {
    case 'creation': return 'bg-green-100 text-green-800'
    case 'comment': return 'bg-blue-100 text-blue-800'
    case 'changed': return 'bg-yellow-100 text-yellow-800'
    case 'added': return 'bg-indigo-100 text-indigo-800'
    case 'removed': return 'bg-red-100 text-red-800'
    case 'incoming_call':
    case 'outgoing_call': return 'bg-purple-100 text-purple-800'
    case 'communication': return 'bg-teal-100 text-teal-800'
    case 'whatsapp': return 'bg-emerald-100 text-emerald-800'
    case 'task': return 'bg-sky-100 text-sky-800'
    case 'attachment_log': return 'bg-orange-100 text-orange-800'
    case 'note': return 'bg-amber-100 text-amber-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

function getRecordRoute(doctype, docname) {
  if (doctype === 'CRM Lead') return { name: 'Lead', params: { leadId: docname } }
  if (doctype === 'CRM Deal') return { name: 'Deal', params: { dealId: docname } }
  if (doctype === 'Contact') return { name: 'Contact', params: { contactId: docname } }
  if (doctype === 'CRM Organization') return { name: 'Organization', params: { organizationId: docname } }
  return '/'
}

function stripHtml(html) {
  if (!html) return ''
  return html.replace(/<[^>]*>/g, '')
}
</script>
