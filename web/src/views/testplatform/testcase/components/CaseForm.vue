<template>
  <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="100">
    <n-form-item label="用例名称" path="name">
      <n-input v-model:value="form.name" placeholder="请输入用例名称" />
    </n-form-item>
    <n-form-item label="所属模块" path="module_id">
      <n-tree-select
        v-model:value="form.module_id"
        :options="moduleTree"
        placeholder="选择模块"
        clearable
        key-field="id"
        label-field="name"
        children-field="children"
      />
    </n-form-item>
    <n-form-item label="用例等级" path="level">
      <n-select v-model:value="form.level" :options="levelOptions" placeholder="选择等级" />
    </n-form-item>
    <n-form-item label="评审人">
      <n-select
        v-model:value="form.reviewer_id"
        :options="userOptions"
        placeholder="选择评审人"
        clearable
        filterable
      />
    </n-form-item>
    <n-form-item label="标签">
      <n-dynamic-tags v-model:value="form.tags" />
    </n-form-item>
    <n-form-item label="前置条件">
      <rich-text-editor v-model="form.precondition" placeholder="请输入前置条件..." />
    </n-form-item>
    <n-form-item label="测试步骤">
      <dynamic-steps v-model="form.steps" />
    </n-form-item>
  </n-form>
</template>

<script setup>
import RichTextEditor from '@/components/editor/RichTextEditor.vue'
import DynamicSteps from './DynamicSteps.vue'

const props = defineProps({
  moduleTree: { type: Array, default: () => [] },
  userOptions: { type: Array, default: () => [] },
})

const formRef = ref(null)
const form = ref({
  name: '',
  module_id: null,
  level: 'P2',
  reviewer_id: null,
  tags: [],
  precondition: '',
  steps: [],
})

const levelOptions = [
  { label: 'P0', value: 'P0' },
  { label: 'P1', value: 'P1' },
  { label: 'P2', value: 'P2' },
  { label: 'P3', value: 'P3' },
]

const rules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  level: [{ required: true, message: '请选择用例等级', trigger: 'change' }],
}

function setForm(data) {
  form.value = {
    name: data.name || '',
    module_id: data.module_id || null,
    level: data.level || 'P2',
    reviewer_id: data.reviewer_id || null,
    tags: data.tags || [],
    precondition: data.precondition || '',
    steps: (data.steps || []).map((s) => ({ ...s })),
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
