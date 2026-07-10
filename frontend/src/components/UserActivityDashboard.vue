<template>
  <div v-if="user" class="mb-8 space-y-6">
    <!-- Period Selector Bar -->
    <div class="flex flex-wrap items-center justify-between gap-4 bg-surface-white border border-outline-gray-modals rounded-xl p-3 shadow-sm">
      <div class="flex items-center gap-2">
        <span class="text-base font-bold text-ink-gray-9 px-2">{{ __('Activity Dashboard') }}</span>
      </div>
      <div class="flex items-center gap-1 bg-surface-gray-2 p-1 rounded-lg">
        <button
          v-for="p in periods"
          :key="p"
          @click="selectedPeriod = p"
          class="px-3 py-1.5 rounded-md text-xs font-medium transition cursor-pointer"
          :class="selectedPeriod === p ? 'bg-surface-white text-ink-gray-9 shadow-sm font-bold' : 'text-ink-gray-6 hover:text-ink-gray-8'"
        >
          {{ __(p) }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="summary.loading" class="flex items-center justify-center py-12 bg-surface-gray-1 border border-outline-gray-modals rounded-xl">
      <LoadingIndicator class="size-6 animate-spin text-ink-gray-5 mr-2" />
      <span class="text-sm text-ink-gray-6">{{ __('Calculating real-time activity metrics...') }}</span>
    </div>

    <!-- Summary Content -->
    <div v-else-if="summary.data" class="space-y-6">
      <!-- Stat Cards Row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <!-- Card 1: Total Activity -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-4 shadow-sm hover:shadow transition flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase text-ink-gray-5 tracking-wider">{{ __('Total Activities') }}</span>
            <div class="p-2 rounded-lg bg-blue-50 text-blue-600">
              <LucideActivity class="size-5" />
            </div>
          </div>
          <div>
            <div class="text-3xl font-extrabold text-ink-gray-9">{{ summary.data.activities?.total || 0 }}</div>
            <div class="text-xs text-ink-gray-5 mt-1.5">{{ __('Actions performed in selected period') }}</div>
          </div>
        </div>

        <!-- Card 2: Call Logs -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-4 shadow-sm hover:shadow transition flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase text-ink-gray-5 tracking-wider">{{ __('Total Calls') }}</span>
            <div class="p-2 rounded-lg bg-purple-50 text-purple-600">
              <LucidePhoneCall class="size-5" />
            </div>
          </div>
          <div>
            <div class="text-3xl font-extrabold text-ink-gray-9">{{ summary.data.calls?.total || 0 }}</div>
            <div class="flex items-center gap-2 mt-1.5 text-xs font-semibold">
              <span class="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">
                {{ summary.data.calls?.outbound || 0 }} Out
              </span>
              <span class="px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">
                {{ summary.data.calls?.inbound || 0 }} In
              </span>
            </div>
          </div>
        </div>

        <!-- Card 3: Call Duration -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-4 shadow-sm hover:shadow transition flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase text-ink-gray-5 tracking-wider">{{ __('Talk Time') }}</span>
            <div class="p-2 rounded-lg bg-amber-50 text-amber-600">
              <LucideClock class="size-5" />
            </div>
          </div>
          <div>
            <div class="text-3xl font-extrabold text-ink-gray-9">{{ formatDuration(summary.data.calls?.duration || 0) }}</div>
            <div class="text-xs text-ink-gray-5 mt-1.5">
              {{ __('Avg per call:') }} <span class="font-bold text-ink-gray-8">{{ formatDuration(summary.data.calls?.avg_duration || 0) }}</span>
            </div>
          </div>
        </div>

        <!-- Card 4: Lead Pipeline -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-4 shadow-sm hover:shadow transition flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase text-ink-gray-5 tracking-wider">{{ __('Active Leads') }}</span>
            <div class="p-2 rounded-lg bg-green-50 text-green-600">
              <LucideUsers class="size-5" />
            </div>
          </div>
          <div>
            <div class="text-3xl font-extrabold text-ink-gray-9">{{ summary.data.leads?.total || 0 }}</div>
            <div class="flex items-center gap-2 mt-1.5 text-xs font-semibold">
              <span class="px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                {{ summary.data.leads?.converted || 0 }} Converted
              </span>
              <span class="text-ink-gray-5 font-normal">
                ({{ summary.data.leads?.status_changes || 0 }} status updates)
              </span>
            </div>
          </div>
        </div>

        <!-- Card 5: Deal Pipeline -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-4 shadow-sm hover:shadow transition flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase text-ink-gray-5 tracking-wider">{{ __('Active Deals') }}</span>
            <div class="p-2 rounded-lg bg-orange-50 text-orange-600">
              <LucideBriefcase class="size-5" />
            </div>
          </div>
          <div>
            <div class="text-3xl font-extrabold text-ink-gray-9">{{ summary.data.deals?.total || 0 }}</div>
            <div class="flex items-center gap-2 mt-1.5 text-xs font-semibold">
              <span class="px-2 py-0.5 rounded-full bg-orange-100 text-orange-800">
                {{ summary.data.deals?.won || 0 }} Won
              </span>
              <span class="text-ink-gray-5 font-normal">
                ({{ summary.data.deals?.status_changes || 0 }} status updates)
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: Call Performance Breakdown -->
      <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-5 shadow-sm">
        <h3 class="text-sm font-bold text-ink-gray-9 mb-4 flex items-center gap-2">
          <LucidePhoneCall class="size-4 text-ink-gray-5" />
          {{ __('Call Status Breakdown') }}
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Answered/Completed -->
          <div class="border rounded-xl p-4 bg-surface-gray-1 flex flex-col justify-between">
            <div class="flex items-center justify-between text-xs font-bold text-green-700 mb-2">
              <span>{{ __('Completed / Answered') }}</span>
              <span>{{ getPercentage(summary.data.calls?.completed, summary.data.calls?.total) }}%</span>
            </div>
            <div class="text-2xl font-extrabold text-ink-gray-9 mb-2">{{ summary.data.calls?.completed || 0 }}</div>
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div class="bg-green-500 h-2 rounded-full transition-all duration-500" :style="`width: ${getPercentage(summary.data.calls?.completed, summary.data.calls?.total)}%`"></div>
            </div>
          </div>

          <!-- Busy -->
          <div class="border rounded-xl p-4 bg-surface-gray-1 flex flex-col justify-between">
            <div class="flex items-center justify-between text-xs font-bold text-amber-700 mb-2">
              <span>{{ __('Busy') }}</span>
              <span>{{ getPercentage(summary.data.calls?.busy, summary.data.calls?.total) }}%</span>
            </div>
            <div class="text-2xl font-extrabold text-ink-gray-9 mb-2">{{ summary.data.calls?.busy || 0 }}</div>
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div class="bg-amber-500 h-2 rounded-full transition-all duration-500" :style="`width: ${getPercentage(summary.data.calls?.busy, summary.data.calls?.total)}%`"></div>
            </div>
          </div>

          <!-- Declined/Failed -->
          <div class="border rounded-xl p-4 bg-surface-gray-1 flex flex-col justify-between">
            <div class="flex items-center justify-between text-xs font-bold text-red-700 mb-2">
              <span>{{ __('Declined / Failed') }}</span>
              <span>{{ getPercentage(summary.data.calls?.declined, summary.data.calls?.total) }}%</span>
            </div>
            <div class="text-2xl font-extrabold text-ink-gray-9 mb-2">{{ summary.data.calls?.declined || 0 }}</div>
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div class="bg-red-500 h-2 rounded-full transition-all duration-500" :style="`width: ${getPercentage(summary.data.calls?.declined, summary.data.calls?.total)}%`"></div>
            </div>
          </div>

          <!-- Missed / No Answer -->
          <div class="border rounded-xl p-4 bg-surface-gray-1 flex flex-col justify-between">
            <div class="flex items-center justify-between text-xs font-bold text-purple-700 mb-2">
              <span>{{ __('Missed / No Answer') }}</span>
              <span>{{ getPercentage(summary.data.calls?.no_answer, summary.data.calls?.total) }}%</span>
            </div>
            <div class="text-2xl font-extrabold text-ink-gray-9 mb-2">{{ summary.data.calls?.no_answer || 0 }}</div>
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div class="bg-purple-500 h-2 rounded-full transition-all duration-500" :style="`width: ${getPercentage(summary.data.calls?.no_answer, summary.data.calls?.total)}%`"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 3: 3-Column Grid (Lead Funnel, Deal Funnel & Activity Breakdown) -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left: Lead Pipeline Distribution -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-5 shadow-sm flex flex-col">
          <h3 class="text-sm font-bold text-ink-gray-9 mb-4 flex items-center gap-2">
            <LucideUsers class="size-4 text-ink-gray-5" />
            {{ __('Lead Pipeline by Status') }}
          </h3>
          <div v-if="!summary.data.leads?.by_status?.length" class="text-sm text-ink-gray-5 py-8 text-center italic">
            {{ __('No leads currently assigned to this user.') }}
          </div>
          <div v-else class="space-y-4 flex-1">
            <div
              v-for="(item, idx) in summary.data.leads.by_status"
              :key="item.status"
              class="flex flex-col gap-1.5"
            >
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-ink-gray-8 flex items-center gap-2">
                  <span class="size-2.5 rounded-full" :class="getDotColor(idx)"></span>
                  {{ item.status }}
                </span>
                <span class="text-ink-gray-7 font-bold">{{ item.count }} <span class="text-ink-gray-5 font-normal">({{ getPercentage(item.count, summary.data.leads.total) }}%)</span></span>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                <div class="h-2.5 rounded-full transition-all duration-500" :class="getBarColor(idx)" :style="`width: ${getPercentage(item.count, summary.data.leads.total)}%`"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Middle: Deal Pipeline Distribution -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-5 shadow-sm flex flex-col">
          <h3 class="text-sm font-bold text-ink-gray-9 mb-4 flex items-center gap-2">
            <LucideBriefcase class="size-4 text-ink-gray-5" />
            {{ __('Deal Pipeline by Status') }}
          </h3>
          <div v-if="!summary.data.deals?.by_status?.length" class="text-sm text-ink-gray-5 py-8 text-center italic">
            {{ __('No deals currently assigned to this user.') }}
          </div>
          <div v-else class="space-y-4 flex-1">
            <div
              v-for="(item, idx) in summary.data.deals.by_status"
              :key="item.status"
              class="flex flex-col gap-1.5"
            >
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-ink-gray-8 flex items-center gap-2">
                  <span class="size-2.5 rounded-full" :class="getDotColor(idx + 4)"></span>
                  {{ item.status }}
                </span>
                <span class="text-ink-gray-7 font-bold">{{ item.count }} <span class="text-ink-gray-5 font-normal">({{ getPercentage(item.count, summary.data.deals.total) }}%)</span></span>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                <div class="h-2.5 rounded-full transition-all duration-500" :class="getBarColor(idx + 4)" :style="`width: ${getPercentage(item.count, summary.data.deals.total)}%`"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Activity Breakdown Grid -->
        <div class="bg-surface-white border border-outline-gray-modals rounded-xl p-5 shadow-sm flex flex-col">
          <h3 class="text-sm font-bold text-ink-gray-9 mb-4 flex items-center gap-2">
            <LucideActivity class="size-4 text-ink-gray-5" />
            {{ __('Activity Mix (Selected Period)') }}
          </h3>
          <div class="flex flex-col gap-2.5 flex-1 justify-center">
            <div class="flex items-center justify-between p-2 px-3 rounded-xl border bg-surface-gray-1">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-blue-100 text-blue-700 shadow-sm">
                  <LucidePhoneCall class="size-4" />
                </div>
                <span class="text-xs font-semibold text-ink-gray-7">{{ __('Calls') }}</span>
              </div>
              <span class="text-sm font-bold text-ink-gray-9">{{ summary.data.calls?.total || 0 }}</span>
            </div>

            <div class="flex items-center justify-between p-2 px-3 rounded-xl border bg-surface-gray-1">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-emerald-100 text-emerald-700 shadow-sm">
                  <LucideMessageSquare class="size-4" />
                </div>
                <span class="text-xs font-semibold text-ink-gray-7">{{ __('WhatsApp') }}</span>
              </div>
              <span class="text-sm font-bold text-ink-gray-9">{{ summary.data.activities?.whatsapp || 0 }}</span>
            </div>

            <div class="flex items-center justify-between p-2 px-3 rounded-xl border bg-surface-gray-1">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-teal-100 text-teal-700 shadow-sm">
                  <LucideMail class="size-4" />
                </div>
                <span class="text-xs font-semibold text-ink-gray-7">{{ __('Emails') }}</span>
              </div>
              <span class="text-sm font-bold text-ink-gray-9">{{ summary.data.activities?.emails || 0 }}</span>
            </div>

            <div class="flex items-center justify-between p-2 px-3 rounded-xl border bg-surface-gray-1">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-amber-100 text-amber-700 shadow-sm">
                  <LucideFileText class="size-4" />
                </div>
                <span class="text-xs font-semibold text-ink-gray-7">{{ __('Notes Added') }}</span>
              </div>
              <span class="text-sm font-bold text-ink-gray-9">{{ summary.data.activities?.notes || 0 }}</span>
            </div>

            <div class="flex items-center justify-between p-2 px-3 rounded-xl border bg-surface-gray-1">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-sky-100 text-sky-700 shadow-sm">
                  <LucideCheckSquare class="size-4" />
                </div>
                <span class="text-xs font-semibold text-ink-gray-7">{{ __('Tasks Completed') }}</span>
              </div>
              <span class="text-sm font-bold text-ink-gray-9">
                {{ summary.data.activities?.tasks_completed || 0 }}
                <span class="text-xs font-normal text-ink-gray-5">/ {{ summary.data.activities?.tasks_total || 0 }}</span>
              </span>
            </div>

            <div class="flex items-center justify-between p-2 px-3 rounded-xl border bg-surface-gray-1">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-yellow-100 text-yellow-700 shadow-sm">
                  <LucideEdit3 class="size-4" />
                </div>
                <span class="text-xs font-semibold text-ink-gray-7">{{ __('Field Edits') }}</span>
              </div>
              <span class="text-sm font-bold text-ink-gray-9">{{ summary.data.activities?.edits || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import LucideActivity from '~icons/lucide/activity'
import LucidePhoneCall from '~icons/lucide/phone-call'
import LucideClock from '~icons/lucide/clock'
import LucideUsers from '~icons/lucide/users'
import LucideBriefcase from '~icons/lucide/briefcase'
import LucideMessageSquare from '~icons/lucide/message-square'
import LucideMail from '~icons/lucide/mail'
import LucideFileText from '~icons/lucide/file-text'
import LucideCheckSquare from '~icons/lucide/check-square'
import LucideEdit3 from '~icons/lucide/edit-3'

const props = defineProps({
  user: {
    type: String,
    required: false,
    default: null
  }
})

const periods = ['All Time', 'Today', 'Last 7 Days', 'Last 30 Days', 'This Month']
const selectedPeriod = ref('Last 30 Days')

const summary = createResource({
  url: 'crm.api.activities.get_user_activity_summary',
  makeParams() {
    return {
      user: props.user,
      period: selectedPeriod.value === 'All Time' ? null : selectedPeriod.value
    }
  },
  auto: false
})

watch(() => [props.user, selectedPeriod.value], ([newUser]) => {
  if (newUser) {
    summary.fetch()
  } else {
    summary.data = null
  }
}, { immediate: true })

function getPercentage(val, total) {
  if (!total || total === 0 || !val) return 0
  return Math.round((val / total) * 100)
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0s'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s > 0 ? s + 's' : ''}`
  return `${s}s`
}

const dotColors = [
  'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-amber-500', 
  'bg-teal-500', 'bg-indigo-500', 'bg-rose-500', 'bg-gray-500'
]
const barColors = [
  'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-amber-500', 
  'bg-teal-500', 'bg-indigo-500', 'bg-rose-500', 'bg-gray-500'
]

function getDotColor(idx) {
  return dotColors[idx % dotColors.length]
}

function getBarColor(idx) {
  return barColors[idx % barColors.length]
}

defineExpose({ reload: () => summary.reload() })
</script>
