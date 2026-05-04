<template>
  <n-modal
    v-model:show="visible"
    preset="card"
    title="用例评审"
    style="width: 95vw; max-width: 1000px"
    :mask-closable="false"
  >
    <n-spin :show="loading">
      <template v-if="detail">
        <n-alert type="info" mb-16 size="small" :bordered="false">
          评审结果：通过、不通过（失败）、建议；与《功能细节交互》2.5
          列表评审一致。连续评审可在列表中逐条打开。
        </n-alert>
        <n-descriptions bordered :column="2" label-placement="left" size="small">
          <n-descriptions-item label="用例名称">
            <span font-medium>{{ detail.name }}</span>
          </n-descriptions-item>
          <n-descriptions-item label="所属模块">
            {{ detail.module?.name || '未规划' }}
          </n-descriptions-item>
          <n-descriptions-item label="用例等级">
            <n-tag :type="levelColorMap[detail.level] || 'default'" size="small" bordered="false">{{
              detail.level
            }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="评审人">
            {{ detail.reviewer?.username || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="创建人">
            {{ detail.creator?.username || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ detail.created_at ? new Date(detail.created_at).toLocaleString() : '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="标签" :span="2">
            <n-tag v-for="tag in detail.tags" :key="tag" size="small" mr-4>{{ tag }}</n-tag>
            <span v-if="!detail.tags?.length" style="color: var(--text-color-3)">-</span>
          </n-descriptions-item>
        </n-descriptions>

        <n-divider />
        <h4 mb-8>前置条件</h4>
        <div v-if="detail.precondition" class="precondition-content" v-html="detail.precondition" />
        <span v-else style="color: var(--text-color-3)">无</span>

        <n-divider />
        <h4 mb-8>测试步骤（步骤描述 / 预期结果）</h4>
        <div v-if="detail.steps?.length">
          <div v-for="step in detail.steps" :key="step.id" class="step-row">
            <n-tag size="small" type="info" mr-8>{{ step.step_number }}</n-tag>
            <div class="step-content">
              <div><span font-500>操作：</span>{{ step.action }}</div>
              <div mt-4><span font-500>预期结果：</span>{{ step.expected_result }}</div>
            </div>
          </div>
        </div>
        <span v-else style="color: var(--text-color-3)">无测试步骤</span>

        <n-divider />
        <h4 mb-8>评审操作</h4>
        <n-space justify="center" size="large" wrap mt-16>
          <n-button type="success" size="large" :loading="submitting" @click="doReview('pass')">
            <template #icon><the-icon icon="material-symbols:check-circle" :size="20" /></template>
            通过
          </n-button>
          <n-button type="error" size="large" :loading="submitting" @click="doReview('fail')">
            <template #icon><the-icon icon="material-symbols:cancel" :size="20" /></template>
            不通过
          </n-button>
          <n-button type="info" size="large" :loading="submitting" @click="doReview('suggest')">
            <template #icon>
              <the-icon icon="material-symbols:lightbulb-outline" :size="20" />
            </template>
            建议
          </n-button>
          <n-button type="warning" size="large" :loading="submitting" @click="doReview('resubmit')">
            <template #icon><the-icon icon="material-symbols:refresh" :size="20" /></template>
            重新提交
          </n-button>
        </n-space>
      </template>
    </n-spin>
  </n-modal>
</template>

<script setup>
import api from '@/api'

const props = defineProps({
  caseId: { type: [Number, String], default: null },
})

const emit = defineEmits(['update:caseId', 'reviewed'])

const visible = computed({
  get: () => !!props.caseId,
  set: (v) => {
    if (!v) emit('update:caseId', null)
  },
})

const loading = ref(false)
const submitting = ref(false)
const detail = ref(null)

const levelColorMap = { P0: 'error', P1: 'warning', P2: 'info', P3: 'default' }

watch(
  () => props.caseId,
  (id) => {
    if (id) fetchDetail(id)
  }
)

async function fetchDetail(id) {
  loading.value = true
  try {
    const res = await api.getTestCase({ case_id: id })
    detail.value = res.data
  } finally {
    loading.value = false
  }
}

async function doReview(result) {
  submitting.value = true
  try {
    await api.updateTestCase({
      id: detail.value.id,
      name: detail.value.name,
      module_id: detail.value.module_id,
      project_id: detail.value.project_id,
      level: detail.value.level,
      precondition: detail.value.precondition || '',
      tags: detail.value.tags || [],
      steps: (detail.value.steps || []).map((s) => ({
        step_number: s.step_number,
        action: s.action,
        expected_result: s.expected_result,
        sort_order: s.sort_order,
      })),
      reviewer_id: detail.value.reviewer_id,
      review_result: result,
    })
    detail.value.review_result = result
    $message.success('评审完成')
    emit('reviewed')
    emit('update:caseId', null)
  } catch {
    $message.error('评审操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.precondition-content {
  padding: 12px;
  background: var(--n-color-embedded);
  border-radius: 4px;
  min-height: 40px;
}
.step-row {
  display: flex;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid var(--n-border-color);
}
.step-row:last-child {
  border-bottom: none;
}
.step-content {
  flex: 1;
  font-size: 13px;
}
</style>
