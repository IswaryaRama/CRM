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
  },
  {
    file: 'node_modules/frappe-ui/src/utils/frappeRequest.js',
    find: 'let data = await response.json()',
    replace: 'let data\\n        try {\\n          data = await response.json()\\n        } catch (e) {\\n          let err = new Error(`Failed to parse JSON for \${url}: \${e.message}`)\\n          options.onError && options.onError(err)\\n          throw err\\n        }',
  },
  {
    file: 'node_modules/frappe-ui/src/utils/call.js',
    find: 'const data = await res.json()',
    replace: `let data;
    try {
      data = await res.json();
    } catch (e) {
      let err = new Error(\`Failed to parse JSON for \${path}: \${e.message}\`);
      if (options.onError) {
        options.onError({ response: res, status: res.status, error: err });
      }
      throw err;
    }`,
  },
  {
    file: 'node_modules/frappe-ui/src/utils/call.js',
    find: "let errorParts = [\\n      [method, error.exc_type, error._error_message].filter(Boolean).join(' '),\\n    ]\\n    if (error.exc) {\\n      exception = error.exc\\n      try {\\n        exception = JSON.parse(exception)[0]\\n        console.log(exception)\\n        // eslint-disable-next-line no-empty\\n      } catch (e) {}\\n    }\\n    let e = new Error(errorParts.join('\\\\n'))\\n    e.exc_type = error.exc_type\\n    e.exc = exception\\n    e.status = res.status\\n    e.messages = error._server_messages\\n      ? JSON.parse(error._server_messages)\\n      : []\\n    e.messages = e.messages.concat(error.message)\\n    e.messages = e.messages.map((m) => {\\n      try {\\n        return JSON.parse(m).message\\n      } catch (error) {\\n        return m\\n      }\\n    })\\n    e.messages = e.messages.filter(Boolean)\\n    if (!e.messages.length) {\\n      e.messages = error._error_message\\n        ? [error._error_message]\\n        : ['Internal Server Error']\\n    }",
    replace: "let errorParts = [\\n      [method, error?.exc_type, error?._error_message].filter(Boolean).join(' '),\\n    ]\\n    if (!errorParts.filter(Boolean).length) {\\n      errorParts = [\`Request failed for \${method}: \${response.substring(0, 100)}...\` ]\\n    }\\n    if (error?.exc) {\\n      exception = error.exc\\n      try {\\n        exception = JSON.parse(exception)[0]\\n        console.log(exception)\\n        // eslint-disable-next-line no-empty\\n      } catch (e) {}\\n    }\\n    let e = new Error(errorParts.join('\\\\n'))\\n    e.exc_type = error?.exc_type\\n    e.exc = exception\\n    e.status = res.status\\n    e.messages = error?._server_messages\\n      ? JSON.parse(error._server_messages)\\n      : []\\n    if (error?.message) {\\n      e.messages = e.messages.concat(error.message)\\n    }\\n    e.messages = e.messages.map((m) => {\\n      try {\\n        return JSON.parse(m).message\\n      } catch (error) {\\n        return m\\n      }\\n    })\\n    e.messages = e.messages.filter(Boolean)\\n    if (!e.messages.length) {\\n      e.messages = error?._error_message\\n        ? [error._error_message]\\n        : ['Internal Server Error']\\n    }"
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
