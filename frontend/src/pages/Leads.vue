<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Leads" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="leadsListView?.customListActions"
        :actions="leadsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showLeadModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="leads"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Lead"
    :filters="{ converted: 0 }"
    :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
      hideFilterButton: false,
      hideSortButton: true,
    }"
  />

  <KanbanView
    v-if="route.params.viewType == 'kanban'"
    v-model="leads"
    :options="{
      getRoute: (row) => ({
        name: 'Lead',
        params: { leadId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      onNewClick: (column) => onNewClick(column),
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #title="{ titleField, itemName }">
      <div class="flex items-center gap-2">
        <div v-if="titleField === 'status'">
          <IndicatorIcon :class="getRow(itemName, titleField).color" />
        </div>
        <div
          v-else-if="
            titleField === 'organization' && getRow(itemName, titleField).label
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, titleField).logo"
            :label="getRow(itemName, titleField).label"
            size="sm"
          />
        </div>
        <div
          v-else-if="
            titleField === 'lead_name' && getRow(itemName, titleField).label
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, titleField).image"
            :label="getRow(itemName, titleField).image_label"
            size="sm"
          />
        </div>
        <div
          v-else-if="
            titleField === 'lead_owner' &&
            getRow(itemName, titleField).full_name
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, titleField).user_image"
            :label="getRow(itemName, titleField).full_name"
            size="sm"
          />
        </div>
        <div v-else-if="titleField === 'mobile_no'">
          <PhoneIcon class="h-4 w-4" />
        </div>
        <div
          v-if="
            [
              'modified',
              'creation',
              'first_response_time',
              'first_responded_on',
              'response_by',
            ].includes(titleField)
          "
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, titleField).label">
            <div>{{ getRow(itemName, titleField).timeAgo }}</div>
          </Tooltip>
        </div>
        <div v-else-if="titleField === 'sla_status'" class="truncate text-base">
          <Badge
            v-if="getRow(itemName, titleField).value"
            :variant="'subtle'"
            :theme="getRow(itemName, titleField).color"
            size="md"
            :label="getRow(itemName, titleField).value"
          />
        </div>
        <div
          v-else-if="getRow(itemName, titleField).label"
          class="truncate text-base"
        >
          {{ getRow(itemName, titleField).label }}
        </div>
        <div v-else class="text-ink-gray-4">{{ __('No Title') }}</div>
      </div>
    </template>
    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
      >
        <div v-if="fieldName === 'status'">
          <IndicatorIcon :class="getRow(itemName, fieldName).color" />
        </div>
        <div
          v-else-if="
            fieldName === 'organization' && getRow(itemName, fieldName).label
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, fieldName).logo"
            :label="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else-if="fieldName === 'lead_name'">
          <Avatar
            v-if="getRow(itemName, fieldName).label"
            class="flex items-center"
            :image="getRow(itemName, fieldName).image"
            :label="getRow(itemName, fieldName).image_label"
            size="xs"
          />
        </div>
        <div v-else-if="fieldName === 'lead_owner'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="xs"
          />
        </div>
        <div
          v-if="
            [
              'modified',
              'creation',
              'first_response_time',
              'first_responded_on',
              'response_by',
            ].includes(fieldName)
          "
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <div v-else-if="fieldName === 'sla_status'" class="truncate text-base">
          <Badge
            v-if="getRow(itemName, fieldName).value"
            :variant="'subtle'"
            :theme="getRow(itemName, fieldName).color"
            size="md"
            :label="getRow(itemName, fieldName).value"
          />
        </div>
        <div
          v-else-if="fieldName === '_assign'"
          class="flex items-center truncate"
        >
          <MultipleAvatar
            :avatars="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else class="truncate text-base">
          {{ getRow(itemName, fieldName).label }}
        </div>
      </div>
    </template>
    <template #actions="{ itemName }">
      <div class="flex gap-2 items-center justify-between">
        <div class="text-ink-gray-5 flex items-center gap-1.5">
          <EmailAtIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_email_count').label">
            {{ getRow(itemName, '_email_count').label }}
          </span>
          <span class="text-3xl leading-[0]"> &middot; </span>
          <NoteIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_note_count').label">
            {{ getRow(itemName, '_note_count').label }}
          </span>
          <span class="text-3xl leading-[0]"> &middot; </span>
          <TaskIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_task_count').label">
            {{ getRow(itemName, '_task_count').label }}
          </span>
          <span class="text-3xl leading-[0]"> &middot; </span>
          <CommentIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_comment_count').label">
            {{ getRow(itemName, '_comment_count').label }}
          </span>
        </div>
        <Dropdown
          class="flex items-center gap-2"
          :options="actions(itemName)"
          variant="ghost"
          @click.stop.prevent
        >
          <Button icon="plus" variant="ghost" />
        </Dropdown>
      </div>
    </template>
  </KanbanView>
  <LeadsListView
    v-else-if="leads.data && rows.length"
    ref="leadsListView"
    v-model="leads.data.page_length_count"
    v-model:list="leads"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: leads.data.row_count,
      totalCount: leads.data.total_count,
    }"
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
    v-else-if="leads.data && !rows.length"
    name="Leads"
    :icon="LeadsIcon"
  />
  <LeadModal
    v-if="showLeadModal"
    v-model="showLeadModal"
    :defaults="defaults"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import AscendingIcon from '@/components/Icons/AscendingIcon.vue'
import DesendingIcon from '@/components/Icons/DesendingIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import LeadModal from '@/components/Modals/LeadModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import { useBroadcast } from '@/composables/useBroadcast'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Avatar, Tooltip, Dropdown, createResource } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, computed, reactive, h, onMounted, onBeforeUnmount } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Lead')
const { makeCall, $socket } = globalStore()
const { getUser } = usersStore()
const { getLeadStatus } = statusesStore()
const { on } = useBroadcast()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()
const { showModal } = useDoctypeModal()

const route = useRoute()

const leadsListView = ref(null)
const showLeadModal = ref(false)

on('trigger_lead_create', (data) => {
  showLeadModal.value = Boolean(data)
})

const defaults = reactive({})

// leads data is loaded in the ViewControls component
const leads = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

onMounted(() => {
  if ($socket) {
    $socket.on('crm_lead_update', () => {
      if (leads.value && typeof leads.value.reload === 'function') {
        leads.value.reload()
      }
    })
  }
})

onBeforeUnmount(() => {
  if ($socket) {
    $socket.off('crm_lead_update')
  }
})

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

// Rows
const rows = computed(() => {
  if (!leads.value?.data?.data) return []
  if (leads.value.data.view_type === 'group_by') {
    if (!leads.value?.data.group_by_field?.fieldname) return []
    return getGroupedByRows(
      leads.value?.data.data,
      leads.value?.data.group_by_field,
      leads.value.data.columns,
    )
  } else if (leads.value.data.view_type === 'kanban') {
    return getKanbanRows(leads.value.data.data, leads.value.data.fields)
  } else {
    return parseRows(leads.value?.data.data, leads.value.data.columns)
  }
})

const columns = computed(() => {
  let _columns = leads.value?.data?.columns || []

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

function getGroupedByRows(listRows, groupByField, columns) {
  let groupedRows = []

  groupByField.options?.forEach((option) => {
    let filteredRows

    if (!option) {
      filteredRows = listRows.filter((row) => !row[groupByField.fieldname])
    } else {
      filteredRows = listRows.filter(
        (row) => row[groupByField.fieldname] == option,
      )
    }

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows, columns),
    }
    if (groupByField.fieldname == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getLeadStatus(option)?.color,
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = leads.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((lead) => {
    let _rows = {}
    leads.value?.data.rows.forEach((row) => {
      try {
        _rows[row] = lead[row]

        let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
          type
        ]

        if (
          fieldType &&
          ['Date', 'Datetime', 'Time'].includes(fieldType) &&
          !['modified', 'creation'].includes(row)
        ) {
          try {
            _rows[row] = lead[row] ? formatDate(lead[row], '', fieldType !== 'Time', fieldType !== 'Date') : ''
          } catch (e) {
            _rows[row] = lead[row] || ''
          }
        }

        if (fieldType && fieldType == 'Currency') {
          _rows[row] = getFormattedCurrency(row, lead)
        }

        if (fieldType && fieldType == 'Float') {
          _rows[row] = getFormattedFloat(row, lead)
        }

        if (fieldType && fieldType == 'Percent') {
          _rows[row] = getFormattedPercent(row, lead)
        }

        if (row == 'lead_name') {
          _rows[row] = {
            label: lead.lead_name,
            image: lead.image,
            image_label: lead.first_name,
          }
        } else if (row == 'organization') {
          _rows[row] = lead.organization
        } else if (row === 'website') {
          _rows[row] = website(lead.website)
        } else if (row == 'status') {
          _rows[row] = {
            label: lead.status,
            color: getLeadStatus(lead.status)?.color,
          }
        } else if (row == 'sla_status') {
          let value = lead.sla_status
          let tooltipText = value
          let color =
            lead.sla_status == 'Failed'
              ? 'red'
              : lead.sla_status == 'Fulfilled'
                ? 'green'
                : 'orange'
          if (value == 'First Response Due' || value == 'Rolling Response Due') {
            try {
              value = __(timeAgo(lead.response_by))
              tooltipText = formatDate(lead.response_by)
            } catch (e) {
              value = lead.response_by || ''
              tooltipText = lead.response_by || ''
            }
            if (lead.response_by && new Date(lead.response_by) < new Date()) {
              color = 'red'
            }
          }
          _rows[row] = {
            label: tooltipText,
            value: value,
            color: color,
          }
        } else if (row == 'lead_owner') {
          _rows[row] = {
            label: lead.lead_owner && getUser(lead.lead_owner).full_name,
            ...(lead.lead_owner && getUser(lead.lead_owner)),
          }
        } else if (row == '_assign') {
          let assignees = JSON.parse(lead._assign || '[]')
          _rows[row] = assignees.map((user) => ({
            name: user,
            image: getUser(user).user_image,
            label: getUser(user).full_name,
          }))
        } else if (['modified', 'creation'].includes(row)) {
          try {
            _rows[row] = {
              label: lead[row] ? formatDate(lead[row]) : '',
              timeAgo: lead[row] ? __(timeAgo(lead[row])) : '',
            }
          } catch (e) {
            _rows[row] = { label: lead[row] || '', timeAgo: '' }
          }
        } else if (
          ['first_response_time', 'first_responded_on', 'response_by'].includes(
            row,
          )
        ) {
          let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
          try {
            _rows[row] = {
              label: lead[field] ? formatDate(lead[field]) : '',
              timeAgo: lead[row]
                ? row == 'first_response_time'
                  ? formatTime(lead[row])
                  : __(timeAgo(lead[row]))
                : '',
            }
          } catch (e) {
            _rows[row] = { label: lead[field] || '', timeAgo: '' }
          }
        }
      } catch (e) {
        // Fallback: use raw value if any formatting fails
        _rows[row] = _rows[row] || lead[row] || ''
      }
    })
    _rows['_email_count'] = lead._email_count
    _rows['_note_count'] = lead._note_count
    _rows['_task_count'] = lead._task_count
    _rows['_comment_count'] = lead._comment_count
    return _rows
  })
}

function onNewClick(column) {
  let column_field = leads.value.params.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showLeadModal.value = true
}

function actions(itemName) {
  let mobile_no = getRow(itemName, 'mobile_no')?.label || ''
  let actions = [
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(mobile_no),
      condition: () => mobile_no && callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => showTask(itemName),
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
}

function showNote(name) {
  showModal({
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: 'CRM Lead',
      reference_docname: name,
    },
    callbacks: {
      afterInsert: (d) => after(d, true),
      afterUpdate: after,
    },
  })
}

function showTask(name) {
  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: {
      reference_doctype: 'CRM Lead',
      reference_docname: name,
    },
    callbacks: {
      afterInsert: (d) => after(d, true),
      afterUpdate: after,
    },
  })
}

function after(d, isNew = false) {
  let a = d.doctype == 'FCRM Note' ? 'note' : 'task'
  if (isNew) {
    updateOnboardingStep('create_first_' + a)
    capture(a + '_created')
  } else {
    capture(a + '_updated')
  }
}

// Quick Filters and Sorts logic
const uniqueFlagsResource = createResource({
  url: 'crm.api.doc.get_unique_flags',
  auto: true,
})
const uniqueFlags = computed(() => uniqueFlagsResource.data || [])

const activeDirection = computed(() => {
  return leads.value?.params?.filters?.direction || 'all'
})

function setDirectionFilter(dir) {
  let currentFilters = { ...leads.value.params.filters }
  if (dir && dir !== 'all') {
    currentFilters.direction = dir
  } else {
    delete currentFilters.direction
  }
  viewControls.value.updateFilter(currentFilters)
}

const activeFlag = computed(() => {
  return leads.value?.params?.filters?.call_flag || ''
})

function setFlagFilter(flag) {
  let currentFilters = { ...leads.value.params.filters }
  if (flag) {
    currentFilters.call_flag = flag
  } else {
    delete currentFilters.call_flag
  }
  viewControls.value.updateFilter(currentFilters)
}

const activeSortField = computed(() => {
  const orderBy = leads.value?.params?.order_by || ''
  if (orderBy.includes('lead_name')) return 'lead_name'
  if (orderBy.includes('call_date')) return 'call_date'
  return ''
})

const activeSortDirection = computed(() => {
  const orderBy = leads.value?.params?.order_by || ''
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
