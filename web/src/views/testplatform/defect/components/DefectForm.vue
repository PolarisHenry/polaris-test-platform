<template>
  <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="100">
    <n-form-item label="缺陷名称" path="name">
      <n-input v-model:value="form.name" placeholder="请输入缺陷名称" />
    </n-form-item>
    <n-grid :cols="2" :x-gap="12">
      <n-grid-item>
        <n-form-item label="严重程度" path="severity">
          <n-select
            v-model:value="form.severity"
            :options="severityOptions"
            placeholder="选择严重程度"
          />
        </n-form-item>
      </n-grid-item>
      <n-grid-item>
        <n-form-item label="状态" path="status">
          <n-select v-model:value="form.status" :options="statusOptions" placeholder="选择状态" />
        </n-form-item>
      </n-grid-item>
    </n-grid>
    <n-form-item label="处理人">
      <n-select
        v-model:value="form.handler_id"
        :options="userOptions"
        placeholder="选择处理人"
        clearable
        filterable
        label-field="label"
        value-field="value"
      />
    </n-form-item>
    <n-form-item label="关联用例">
      <n-select
        v-model:value="form.related_case_ids"
        :options="caseOptions"
        placeholder="选择关联用例"
        multiple
        filterable
        label-field="label"
        value-field="value"
      />
    </n-form-item>
    <n-form-item label="缺陷内容">
      <rich-text-editor v-model="form.content" placeholder="请输入缺陷详细描述..." />
    </n-form-item>
  </n-form>
</template>

<script setup>
import RichTextEditor from '@/components/editor/RichTextEditor.vue'

const props = defineProps({
  userOptions: { type: Array, default: () => [] },
  caseOptions: { type: Array, default: () => [] },
})

const formRef = ref(null)
const form = ref({
  name: '',
  severity: 'minor',
  status: 'new',
  handler_id: null,
  related_case_ids: [],
  content: '',
})

const severityOptions = [
  { label: '提示', value: 'trivial' },
  { label: '次要', value: 'minor' },
  { label: '严重', value: 'major' },
  { label: '致命', value: 'critical' },
]
const statusOptions = [
  { label: '新建', value: 'new' },
  { label: '处理中', value: 'processing' },
  { label: '已解决', value: 'resolved' },
  { label: '已关闭', value: 'closed' },
]

const rules = {
  name: [{ required: true, message: '请输入缺陷名称', trigger: 'blur' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }],
}

function setForm(data) {
  form.value = {
    name: data.name || '',
    severity: data.severity || 'minor',
    status: data.status || 'new',
    handler_id: data.handler_id || data.handler?.id || null,
    related_case_ids: data.related_case_ids || [],
    content: data.content || '',
  }
}

function getForm() {
  return { ...form.value }
}

async function validate() {
  return formRef.value?.validate()
}

defineExpose({ setForm, getForm, validate, formRef })
</script>
