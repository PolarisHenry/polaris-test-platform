<template>
  <div class="case-edit">
    <div class="edit-header">
      <n-breadcrumb class="edit-breadcrumb">
        <n-breadcrumb-item @click="$emit('back')">功能用例</n-breadcrumb-item>
        <n-breadcrumb-item>{{ isEdit ? '编辑用例' : '创建用例' }}</n-breadcrumb-item>
      </n-breadcrumb>
    </div>

    <div class="edit-middle">
      <n-spin :show="loading" class="edit-spin">
        <div v-if="!loading" class="edit-shell">
          <div class="edit-title-row">{{ isEdit ? '编辑用例' : '创建用例' }}</div>

          <div class="edit-body">
            <div class="edit-main">
              <n-form
                ref="formRef"
                :model="form"
                :rules="rules"
                label-placement="top"
                :show-require-mark="false"
              >
                <n-form-item class="case-name-item" path="name">
                  <template #label>
                    <span class="field-label required">用例名称</span>
                  </template>
                  <n-input
                    ref="nameInputRef"
                    v-model:value="form.name"
                    placeholder="请输入用例名称"
                    clearable
                    :maxlength="200"
                  />
                </n-form-item>

                <n-form-item>
                  <template #label>
                    <span class="field-label">前置条件</span>
                  </template>
                  <rich-text-editor
                    v-model="form.precondition"
                    placeholder="请输入内容"
                    upload-category="test_case"
                    :project-id="projectId"
                  />
                </n-form-item>

                <section class="form-section">
                  <div class="section-title">
                    <span>步骤描述</span>
                    <n-select
                      v-model:value="changeType"
                      :options="changeTypeOptions"
                      size="tiny"
                      class="change-type-select"
                    />
                  </div>
                  <dynamic-steps :key="String(caseId)" v-model="form.steps" />
                </section>

                <n-form-item class="remark-item">
                  <template #label>
                    <span class="field-label">备注</span>
                  </template>
                  <rich-text-editor
                    v-model="form.remark"
                    placeholder="请输入内容"
                    upload-category="test_case"
                    :project-id="projectId"
                  />
                </n-form-item>

                <section class="attachment-section">
                  <div class="field-label">添加附件</div>
                  <n-upload
                    :custom-request="handleAttachmentUpload"
                    :show-file-list="false"
                    accept="*"
                  >
                    <n-button size="small" class="attachment-btn">
                      <template #icon><the-icon icon="material-symbols:add" :size="16" /></template>
                      添加附件
                    </n-button>
                  </n-upload>
                  <div v-if="attachments.length" class="attachment-list">
                    <div v-for="file in attachments" :key="file.id" class="attachment-item">
                      <the-icon icon="material-symbols:attach-file" :size="15" />
                      <n-button text size="tiny" @click="downloadAttachment(file)">
                        {{ file.name }}
                      </n-button>
                    </div>
                  </div>
                </section>
              </n-form>
            </div>

            <aside class="edit-sidebar">
              <n-form label-placement="top" size="small" :show-require-mark="false">
                <n-form-item required>
                  <template #label>
                    <span class="field-label required">所属模块</span>
                  </template>
                  <n-tree-select
                    v-model:value="form.module_id"
                    :options="moduleTree"
                    placeholder="未规划用例"
                    clearable
                    key-field="id"
                    label-field="name"
                    children-field="children"
                  />
                </n-form-item>
                <n-form-item path="level" required>
                  <template #label>
                    <span class="field-label required">用例等级</span>
                  </template>
                  <n-select
                    v-model:value="form.level"
                    :options="levelOptions"
                    placeholder="请选择"
                  />
                </n-form-item>
                <n-form-item>
                  <template #label>
                    <span class="field-label">标签</span>
                  </template>
                  <n-dynamic-tags v-model:value="form.tags" />
                </n-form-item>
              </n-form>
            </aside>
          </div>
        </div>
      </n-spin>
    </div>

    <div class="edit-footer">
      <span />
      <n-space :size="12">
        <n-button class="footer-btn" @click="$emit('back')">取消</n-button>
        <n-button type="primary" secondary :loading="saving" @click="doSave('continue')">
          保存并继续创建
        </n-button>
        <n-button type="primary" class="create-btn" :loading="saving" @click="doSave">
          {{ isEdit ? '保存' : '创建用例' }}
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup>
import RichTextEditor from '@/components/editor/RichTextEditor.vue'
import DynamicSteps from './DynamicSteps.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'

const props = defineProps({
  caseId: { type: [String, Number], default: null },
  projectId: { type: Number, default: null },
  moduleTree: { type: Array, default: () => [] },
  userOptions: { type: Array, default: () => [] },
  /** 创建用例时默认模块（来自列表页左侧树选中） */
  initialModuleId: { type: Number, default: null },
})

const emit = defineEmits(['back', 'saved'])

const formRef = ref(null)
const nameInputRef = ref(null)
const loading = ref(false)
const saving = ref(false)
const attachments = ref([])

const form = ref({
  name: '',
  module_id: null,
  level: 'P2',
  reviewer_id: null,
  tags: [],
  precondition: '',
  remark: '',
  steps: [],
})

const levelOptions = [
  { label: 'P0', value: 'P0' },
  { label: 'P1', value: 'P1' },
  { label: 'P2', value: 'P2' },
  { label: 'P3', value: 'P3' },
]
const changeType = ref('step')
const changeTypeOptions = [{ label: '更改类型', value: 'step' }]

const rules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  level: [{ required: true, message: '请选择用例等级', trigger: 'change' }],
}

const isEdit = computed(() => props.caseId && props.caseId !== 'new')

function emptyForm() {
  return {
    name: '',
    module_id: props.initialModuleId ?? null,
    level: 'P2',
    reviewer_id: null,
    tags: [],
    precondition: '',
    remark: '',
    // 与 MeterSphere 类似：新建时默认一行步骤，减少「点了添加才有第一行」的摩擦
    steps: [{ step_number: 1, action: '', expected_result: '', sort_order: 0 }],
  }
}

function focusNameIfNew() {
  if (isEdit.value) return
  nextTick(() => {
    nameInputRef.value?.focus?.()
  })
}

function nonEmptyStepsPayload() {
  return form.value.steps
    .map((s, i) => ({
      step_number: s.step_number || i + 1,
      action: (s.action || '').trim(),
      expected_result: (s.expected_result || '').trim(),
      sort_order: s.sort_order ?? i,
    }))
    .filter((s) => s.action || s.expected_result)
}

async function loadCase() {
  if (!isEdit.value) {
    form.value = emptyForm()
    nextTick(() => formRef.value?.restoreValidation?.())
    focusNameIfNew()
    return
  }
  loading.value = true
  try {
    const res = await api.getTestCase({ case_id: props.caseId })
    const d = res.data
    form.value = {
      name: d.name || '',
      module_id: d.module_id ?? null,
      level: d.level || 'P2',
      reviewer_id: d.reviewer_id || null,
      tags: d.tags || [],
      precondition: d.precondition || '',
      remark: d.remark || '',
      steps: (d.steps || []).map((s) => ({ ...s })),
    }
  } finally {
    loading.value = false
    focusNameIfNew()
  }
}

async function loadAttachments() {
  if (!props.projectId) return
  const res = await api.getFileList({
    project_id: props.projectId,
    category: 'test_case',
    page: 1,
    page_size: 20,
  })
  attachments.value = res.data || []
}

async function handleAttachmentUpload({ file, onFinish, onError }) {
  try {
    const formData = new FormData()
    formData.append('file', file.file)
    formData.append('category', 'test_case')
    formData.append('project_id', props.projectId || '')
    await api.uploadFile(formData)
    $message.success('附件上传成功')
    await loadAttachments()
    onFinish?.()
  } catch (error) {
    onError?.()
  }
}

function downloadAttachment(file) {
  window.open(`/api/v1/file/download?file_id=${file.id}`, '_blank')
}

async function doSave(mode) {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const data = {
      name: form.value.name,
      module_id: form.value.module_id,
      project_id: props.projectId,
      level: form.value.level,
      reviewer_id: form.value.reviewer_id || null,
      precondition: form.value.precondition || '',
      remark: form.value.remark || '',
      tags: form.value.tags || [],
      steps: nonEmptyStepsPayload(),
    }

    if (isEdit.value) {
      await api.updateTestCase({ id: parseInt(props.caseId), ...data })
      $message.success('用例已更新')
    } else {
      await api.createTestCase(data)
      $message.success('用例已创建')
    }

    emit('saved')
    if (mode !== 'continue') {
      emit('back')
    } else {
      const savedModuleId = form.value.module_id
      form.value = emptyForm()
      form.value.module_id = savedModuleId ?? props.initialModuleId ?? null
      nextTick(() => formRef.value?.restoreValidation?.())
    }
  } catch {
    $message.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadCase()
  loadAttachments()
})

watch(
  () => props.caseId,
  () => {
    loadCase()
  }
)
</script>

<style scoped>
.case-edit {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  color: var(--n-text-color);
  background: #f5f6fb;
  overflow: hidden;
}
.edit-middle {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.edit-spin {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.edit-spin :deep(.n-spin-container) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.edit-spin :deep(.n-spin-content) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.edit-header {
  height: 32px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  background: #f5f6fb;
  flex-shrink: 0;
}
.edit-breadcrumb {
  font-size: 12px;
}
.edit-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin: 0 12px;
  background: #fff;
  border-radius: 10px 10px 0 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.edit-title-row {
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  color: #333;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 1px solid #eee;
}
.edit-body {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.edit-main {
  flex: 1;
  min-width: 0;
  padding: 16px 18px 28px;
  border-right: 1px solid #eee;
}
.edit-sidebar {
  width: 300px;
  flex-shrink: 0;
  padding: 16px;
  background: #fff;
}
.field-label {
  color: #333;
  font-size: 13px;
  font-weight: 500;
}
.field-label.required::after {
  content: '*';
  margin-left: 2px;
  color: #d03050;
}
.case-name-item {
  margin-bottom: 10px;
}
.case-name-item :deep(.n-form-item-label) {
  padding-bottom: 6px;
}
.case-name-item :deep(.n-input) {
  --n-height: 32px;
}
.form-section {
  margin-top: 4px;
}
.section-title {
  height: 32px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1f2329;
  font-size: 13px;
  font-weight: 600;
}
.change-type-select {
  width: 96px;
}
.change-type-select :deep(.n-base-selection) {
  --n-height: 24px;
  --n-font-size: 12px;
  border: 0;
  box-shadow: none;
}
.remark-item {
  margin-top: 16px;
}
.attachment-section {
  margin-top: 12px;
}
.attachment-btn {
  margin-top: 8px;
  color: #e88024;
}
.attachment-list {
  margin-top: 8px;
}
.attachment-item {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 24px;
  color: #666;
}
.edit-main :deep(.n-form-item) {
  --n-label-height: 22px;
}
.edit-main :deep(.n-form-item-blank) {
  width: 100%;
}
.edit-sidebar :deep(.n-form-item) {
  margin-bottom: 12px;
}
.edit-sidebar :deep(.n-form-item-label) {
  padding-bottom: 6px;
}
.edit-sidebar :deep(.n-base-selection),
.edit-sidebar :deep(.n-input) {
  --n-height: 32px;
}
.edit-footer {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-top: 1px solid #eee;
  background: #fff;
  flex-shrink: 0;
  box-shadow: 0 -2px 8px rgba(31, 35, 41, 0.04);
}
.footer-btn {
  background: #f5f6fb;
}
.case-edit :deep(.n-input),
.case-edit :deep(.n-base-selection) {
  --n-border-hover: 1px solid #e88024 !important;
  --n-border-focus: 1px solid #e88024 !important;
}
.case-edit :deep(.n-form-item-feedback-wrapper) {
  min-height: 14px;
}
</style>
