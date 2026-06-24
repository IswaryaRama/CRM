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
