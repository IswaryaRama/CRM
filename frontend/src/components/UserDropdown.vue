<template>
  <div class="flex flex-col w-full">
    <div
      class="flex items-center justify-center duration-300 ease-in-out select-none"
      :class="
        isCollapsed
          ? 'h-10 px-0 mb-2'
          : 'h-10 px-2 mb-3 mt-1'
      "
    >
      <BrandLogo v-model="brand" :isCollapsed="isCollapsed" class="h-8 w-auto max-w-full" />
    </div>

    <!-- Clickable Dropdown Trigger -->
    <Dropdown :options="dropdownItems" class="w-full" v-bind="$attrs">
      <template #default="{ open }">
        <button
          class="flex flex-col h-auto items-start rounded-lg transition-all duration-200 ease-in-out border border-gray-100/80 bg-white"
          :class="
            isCollapsed
              ? 'w-10 h-10 p-0 justify-center items-center hover:bg-gray-50 hover:border-gray-200'
              : open
                ? 'w-full px-3 py-2 bg-gray-50/60 border-gray-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.02)]'
                : 'w-full px-3 py-2 hover:bg-gray-50/50 hover:border-gray-200/60 shadow-[0_1px_2px_rgba(0,0,0,0.02)]'
          "
        >
          <!-- Expanded State -->
          <div v-if="!isCollapsed" class="flex items-center w-full">
            <div class="flex flex-1 flex-col text-left truncate">
              <div class="text-sm font-semibold leading-none text-gray-900 truncate">
                {{ __(brand.name || 'CRM') }}
              </div>
              <div class="mt-1.5 text-xs font-normal leading-none text-gray-500 truncate">
                {{ user.full_name }}
              </div>
            </div>
            <div class="ml-2 transition-transform duration-200" :class="{ 'rotate-180': open }">
              <FeatherIcon
                name="chevron-down"
                class="size-3.5 text-gray-400"
                aria-hidden="true"
              />
            </div>
          </div>

          <!-- Collapsed State: Show User Avatar -->
          <div v-else class="flex items-center justify-center w-full h-full">
            <UserAvatar v-if="user && user.name" :user="user.name" class="size-7 rounded-md shadow-sm" />
          </div>
        </button>
      </template>
    </Dropdown>
  </div>
</template>

<script setup>
import BrandLogo from '@/components/BrandLogo.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import FrappeCloudIcon from '@/components/Icons/FrappeCloudIcon.vue'
import Apps from '@/components/Apps.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import { showSettings, isMobileView } from '@/composables/settings'
import { showAboutModal } from '@/composables/modals'
import { confirmLoginToFrappeCloud } from '@/composables/frappecloud'
import { Dropdown } from 'frappe-ui'
import { computed, h, markRaw } from 'vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const { settings, brand } = getSettings()
const { logout } = sessionStore()
const { getUser } = usersStore()

const user = computed(() => getUser() || {})

const dropdownItems = computed(() => {
  if (!settings.value?.dropdown_items) return []

  let items = settings.value.dropdown_items

  let _dropdownItems = [
    {
      group: 'Dropdown Items',
      hideLabel: true,
      items: [],
    },
  ]

  items.forEach((item) => {
    if (item.hidden) return
    if (item.type !== 'Separator') {
      _dropdownItems[_dropdownItems.length - 1].items.push(
        dropdownItemObj(item),
      )
    } else {
      _dropdownItems.push({
        group: '',
        hideLabel: true,
        items: [],
      })
    }
  })

  return _dropdownItems
})

function dropdownItemObj(item) {
  let _item = JSON.parse(JSON.stringify(item))
  let icon = _item.icon || 'external-link'
  if (typeof icon === 'string' && icon.startsWith('<svg')) {
    icon = markRaw(h('div', { innerHTML: icon }))
  }
  _item.icon = icon

  if (_item.is_standard) {
    return getStandardItem(_item)
  }

  return {
    icon: _item.icon,
    label: __(_item.label),
    onClick: () =>
      window.open(_item.route, _item.open_in_new_window ? '_blank' : ''),
  }
}

function getStandardItem(item) {
  switch (item.name1) {
    case 'app_selector':
      return {
        component: markRaw(Apps),
      }
    case 'settings':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showSettings.value = true),
        condition: () => true,
      }
    case 'login_to_fc':
      return {
        icon: h(FrappeCloudIcon),
        label: __(item.label),
        onClick: () => confirmLoginToFrappeCloud(),
        condition: () => !isMobileView.value && window.is_fc_site,
      }
    case 'about':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showAboutModal.value = true),
      }
    case 'logout':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => logout.submit(),
      }
  }
}
</script>
