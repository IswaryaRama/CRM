#!/usr/bin/env node
/**
 * postinstall-patch.js
 * Patches frappe-ui DataImport components to include credentials in fetch calls.
 * This runs automatically after every `npm install`.
 */

const fs = require('fs')
const path = require('path')

const patches = [
  {
    file: 'node_modules/frappe-ui/frappe/DataImport/UploadStep.vue',
    find: 'const response = await fetch(url)',
    replace: "const response = await fetch(url, { credentials: 'include' })",
  },
  {
    file: 'node_modules/frappe-ui/frappe/DataImport/TemplateModal.vue',
    find: 'const response = await fetch(url)',
    replace: "const response = await fetch(url, { credentials: 'include' })",
  },
  {
    file: 'node_modules/frappe-ui/src/utils/fileUploadHandler.ts',
    find: "xhr.open('POST', uploadEndpoint, true)",
    replace: "xhr.open('POST', uploadEndpoint, true)\\n      xhr.withCredentials = true",
  },
  {
    file: 'node_modules/frappe-ui/frappe/DataImport/UploadStep.vue',
    find: "exportFields = { [props.doctype || props.data?.reference_doctype as string]: ['name'] }",
    replace: `let defaultFields = ['name'];\\n        if (props.doctype === 'CRM Lead') {\\n            defaultFields = ['name', 'first_name', 'last_name', 'status', 'email', 'mobile_no', 'company_name', 'territory', 'source', 'campaign'];\\n        } else if (props.doctype === 'CRM Deal') {\\n            defaultFields = ['name', 'deal_name', 'status', 'amount', 'organization', 'contact'];\\n        }\\n        exportFields = { [props.doctype || props.data?.reference_doctype as string]: defaultFields }`,
  }
]

let patchedCount = 0

for (const patch of patches) {
  const filePath = path.resolve(__dirname, patch.file)
  if (!fs.existsSync(filePath)) {
    console.warn(`[patch] SKIP: ${patch.file} not found`)
    continue
  }

  let content = fs.readFileSync(filePath, 'utf-8')

  if (content.includes(patch.replace)) {
    console.log(`[patch] OK: ${patch.file} already patched`)
    patchedCount++
    continue
  }

  if (!content.includes(patch.find)) {
    console.warn(`[patch] WARN: ${patch.file} — target string not found, skipping`)
    continue
  }

  content = content.replace(patch.find, patch.replace)
  fs.writeFileSync(filePath, content, 'utf-8')
  console.log(`[patch] PATCHED: ${patch.file}`)
  patchedCount++
}

console.log(`[patch] Done. ${patchedCount}/${patches.length} patches applied.`)
