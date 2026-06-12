<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Call Logs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="callLogsListView?.customListActions"
        :actions="callLogsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createCallLog"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="callLogs"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Call Log"
    :options="{
      hideFilterButton: true,
      hideSortButton: true,
    }"
  />

  <div class="px-5 pt-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
    <div class="flex gap-6">
      <button 
        v-for="dir in ['all', 'inbound', 'outbound']" 
        :key="dir"
        @click="setDirectionFilter(dir)"
        :class="[
          'pb-3 text-sm font-medium border-b-2 transition-colors duration-200 capitalize',
          activeDirection === dir 
            ? 'border-gray-900 text-gray-900 dark:border-white dark:text-white' 
            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
        ]"
      >
        {{ __(dir) }}
      </button>
    </div>
  </div>

  <div 
    v-if="callLogs.data"
    class="mx-5 my-4 p-4 bg-white/70 dark:bg-gray-900/70 backdrop-blur-md border border-gray-100 dark:border-gray-800 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-sm transition-all duration-300"
  >
    <!-- Left Side: Quick Filters -->
    <div class="flex flex-wrap items-center gap-6">

      <!-- Flags Filter -->
      <div class="flex flex-col gap-1.5 min-w-[160px]">
        <span class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Filter by Flag') }}</span>
        <select 
          :value="activeFlag"
          @change="setFlagFilter($event.target.value)"
          class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200"
        >
          <option value="">{{ __('All Flags') }}</option>
          <option v-for="flag in uniqueFlags" :key="flag" :value="flag">{{ flag }}</option>
        </select>
      </div>
    </div>

    <!-- Right Side: Quick Sort -->
    <div class="flex items-center gap-6">
      <!-- Sort By Field -->
      <div class="flex flex-col gap-1.5">
        <span class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Sort By') }}</span>
        <div class="flex items-center gap-2">
          <div class="flex bg-gray-100/80 dark:bg-gray-800/80 p-0.5 rounded-lg border border-gray-200/40 dark:border-gray-700/40">
            <button 
              v-for="s in [
                { label: 'Date', field: 'call_date' },
                { label: 'Name', field: 'lead_name' }
              ]" 
              :key="s.field"
              @click="setSortField(s.field)"
              :class="[
                'px-3 py-1 text-sm font-medium rounded-md transition-all duration-200',
                activeSortField === s.field 
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              ]"
            >
              {{ __(s.label) }}
            </button>
          </div>
          <button 
            @click="toggleSortDirection"
            class="p-1.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-lg border border-gray-200/40 dark:border-gray-700/40 transition-all duration-200 flex items-center justify-center"
            :title="activeSortDirection === 'asc' ? __('Ascending') : __('Descending')"
          >
            <component 
              :is="activeSortDirection === 'asc' ? AscendingIcon : DesendingIcon" 
              class="h-4 w-4 text-gray-600 dark:text-gray-400"
            />
          </button>
        </div>
      </div>
    </div>
  </div>
  <CallLogsListView
    v-if="callLogs.data && rows.length"
    ref="callLogsListView"
    v-model="callLogs.data.page_length_count"
    v-model:list="callLogs"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: callLogs.data.row_count,
      totalCount: callLogs.data.total_count,
    }"
    @showCallLog="showCallLog"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="callLogs.data && !rows.length"
    name="Call Logs"
    :icon="PhoneIcon"
  />
  <CallLogDetailModal
    v-model="showCallLogDetailModal"
    v-model:callLog="callLog"
  />
</template>

<script setup>
import AscendingIcon from '@/components/Icons/AscendingIcon.vue'
import DesendingIcon from '@/components/Icons/DesendingIcon.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getCallLogDetail } from '@/utils/callLog'
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource } from 'frappe-ui'
import { computed, ref, onMounted } from 'vue'

const callLogsListView = ref(null)

// callLogs data is loaded in the ViewControls component
const callLogs = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !callLogs.value?.data?.data ||
    !['list', 'group_by'].includes(callLogs.value.data.view_type)
  )
    return []
  return callLogs.value?.data.data.map((callLog) => {
    let _rows = {}
    callLogs.value?.data.rows.forEach((row) => {
      _rows[row] = getCallLogDetail(row, callLog, callLogs.value?.data.columns)
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = callLogs.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

const showCallLogDetailModal = ref(false)
const callLog = ref({})

function showCallLog(name) {
  showCallLogDetailModal.value = true
  callLog.value = createResource({
    url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
    params: { name },
    cache: ['call_log', name],
    auto: true,
  })
}

const { showModal } = useDoctypeModal()
const { capture } = useTelemetry()

function createCallLog() {
  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: () => {
        capture('call_log_created')
        callLogs.value.reload()
      },
    },
  })
}

const openCallLogFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const callLogName = searchParams.get('open')

  if (callLogName) {
    showCallLog(callLogName)
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}

onMounted(() => {
  openCallLogFromURL()
})

// Quick Filters and Sorts logic

const uniqueFlagsResource = createResource({
  url: 'crm.api.doc.get_unique_flags',
  auto: true,
})
const uniqueFlags = computed(() => uniqueFlagsResource.data || [])

const activeDirection = computed(() => {
  const type = callLogs.value?.params?.filters?.type
  if (type === 'Incoming') return 'inbound'
  if (type === 'Outgoing') return 'outbound'
  return 'all'
})

function setDirectionFilter(dir) {
  let currentFilters = { ...callLogs.value.params.filters }
  if (dir === 'inbound') {
    currentFilters.type = 'Incoming'
    delete currentFilters.direction
  } else if (dir === 'outbound') {
    currentFilters.type = 'Outgoing'
    delete currentFilters.direction
  } else {
    delete currentFilters.type
    delete currentFilters.direction
  }
  viewControls.value.updateFilter(currentFilters)
}

const activeFlag = computed(() => {
  return callLogs.value?.params?.filters?.call_flag || ''
})

function setFlagFilter(flag) {
  let currentFilters = { ...callLogs.value.params.filters }
  if (flag) {
    currentFilters.call_flag = flag
  } else {
    delete currentFilters.call_flag
  }
  viewControls.value.updateFilter(currentFilters)
}

const activeSortField = computed(() => {
  const orderBy = callLogs.value?.params?.order_by || ''
  if (orderBy.includes('lead_name')) return 'lead_name'
  if (orderBy.includes('call_date')) return 'call_date'
  return ''
})

const activeSortDirection = computed(() => {
  const orderBy = callLogs.value?.params?.order_by || ''
  if (orderBy.includes('asc')) return 'asc'
  return 'desc'
})

function setSortField(field) {
  let direction = activeSortDirection.value
  let orderBy = ''
  if (field === 'call_date') {
    orderBy = direction === 'asc' 
      ? 'call_date is null desc, call_date asc, call_time asc' 
      : 'call_date is null asc, call_date desc, call_time desc'
  } else if (field === 'lead_name') {
    orderBy = `lead_name ${direction}`
  }
  viewControls.value.updateSort(orderBy)
}

function toggleSortDirection() {
  let field = activeSortField.value || 'call_date'
  let nextDirection = activeSortDirection.value === 'asc' ? 'desc' : 'asc'
  let orderBy = ''
  if (field === 'call_date') {
    orderBy = nextDirection === 'asc' 
      ? 'call_date is null desc, call_date asc, call_time asc' 
      : 'call_date is null asc, call_date desc, call_time desc'
  } else if (field === 'lead_name') {
    orderBy = `lead_name ${nextDirection}`
  }
  viewControls.value.updateSort(orderBy)
}

</script>
