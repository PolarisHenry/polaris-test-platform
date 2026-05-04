<template>
  <div class="steps-editor">
    <div class="steps-grid steps-head">
      <div />
      <div class="steps-col-index">序号</div>
      <div>用例步骤</div>
      <div>预期结果</div>
      <div class="steps-col-action">操作</div>
    </div>

    <div
      v-for="(step, index) in steps"
      :key="step._key"
      class="steps-grid steps-row"
      :class="{ 'is-drag-over': dragOverIndex === index }"
      draggable="true"
      @dragstart="onDragStart($event, index)"
      @dragend="onDragEnd"
      @dragover.prevent="onDragOver($event, index)"
      @dragleave="onDragLeave(index)"
      @drop.prevent="onDrop(index)"
    >
      <div class="drag-cell">
        <the-icon
          icon="material-symbols:drag-indicator"
          :size="16"
          class="drag-icon"
          title="拖拽排序"
        />
      </div>
      <div class="index-cell">
        <span class="step-index">{{ index + 1 }}</span>
      </div>
      <div class="step-cell">
        <n-input
          v-model:value="step.action"
          type="textarea"
          autosize
          placeholder="请输入步骤"
          class="ghost-input"
          @update:value="emitUpdate"
        />
      </div>
      <div class="step-cell">
        <n-input
          v-model:value="step.expected_result"
          type="textarea"
          autosize
          placeholder="请输入预期"
          class="ghost-input"
          @update:value="emitUpdate"
        />
      </div>
      <div class="action-cell">
        <n-dropdown
          trigger="click"
          :options="rowActionOptions"
          @select="(key) => onRowAction(key, index)"
        >
          <n-button text size="tiny" class="more-btn">...</n-button>
        </n-dropdown>
      </div>
    </div>

    <n-button text type="primary" class="add-step-btn" @click="addStep">
      <template #icon><the-icon icon="material-symbols:add" :size="16" /></template>
      添加步骤
    </n-button>
  </div>
</template>

<script setup>
import TheIcon from '@/components/icon/TheIcon.vue'

let keySeq = 0
function nextKey() {
  keySeq += 1
  return `s-${keySeq}`
}

function normalizeRows(arr) {
  const list = Array.isArray(arr) ? arr : []
  return list.map((s, i) => ({
    _key: nextKey(),
    step_number: s.step_number || i + 1,
    action: s.action || '',
    expected_result: s.expected_result || '',
    sort_order: s.sort_order ?? i,
  }))
}

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

const steps = ref(normalizeRows(props.modelValue))

const dragFromIndex = ref(null)
const dragOverIndex = ref(null)

const rowActionOptions = [
  { label: '向下添加步骤', key: 'insertAfter' },
  { label: '复制当前步骤', key: 'duplicate' },
  { label: '删除步骤', key: 'delete' },
]

watch(
  () => props.modelValue,
  (val) => {
    const incoming = JSON.stringify(
      (val || []).map((s, i) => ({
        step_number: s?.step_number ?? i + 1,
        action: s?.action ?? '',
        expected_result: s?.expected_result ?? '',
        sort_order: s?.sort_order ?? i,
      }))
    )
    const current = JSON.stringify(
      steps.value.map((s, i) => ({
        step_number: i + 1,
        action: s.action,
        expected_result: s.expected_result,
        sort_order: i,
      }))
    )
    if (incoming !== current) {
      keySeq = 0
      steps.value = normalizeRows(val)
    }
  },
  { deep: true }
)

function stripEmit(rows) {
  return rows.map((s, i) => ({
    step_number: i + 1,
    action: s.action || '',
    expected_result: s.expected_result || '',
    sort_order: i,
  }))
}

function emitUpdate() {
  emit('update:modelValue', stripEmit(steps.value))
}

function onDragStart(e, index) {
  dragFromIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

function onDragEnd() {
  dragFromIndex.value = null
  dragOverIndex.value = null
}

function onDragOver(_e, index) {
  if (dragFromIndex.value === null) return
  dragOverIndex.value = index
}

function onDragLeave(index) {
  if (dragOverIndex.value === index) dragOverIndex.value = null
}

function onDrop(toIndex) {
  const from = dragFromIndex.value
  dragOverIndex.value = null
  if (from === null || from === toIndex) return
  const arr = steps.value.slice()
  const [row] = arr.splice(from, 1)
  arr.splice(toIndex, 0, row)
  steps.value = arr
  dragFromIndex.value = null
  emitUpdate()
}

function addStep() {
  steps.value.push({
    _key: nextKey(),
    step_number: steps.value.length + 1,
    action: '',
    expected_result: '',
    sort_order: steps.value.length,
  })
  emitUpdate()
}

function insertStepAfter(index, source = {}) {
  steps.value.splice(index + 1, 0, {
    _key: nextKey(),
    step_number: index + 2,
    action: source.action || '',
    expected_result: source.expected_result || '',
    sort_order: index + 1,
  })
  emitUpdate()
}

function removeStep(index) {
  if (steps.value.length <= 1) {
    steps.value = normalizeRows([
      { step_number: 1, action: '', expected_result: '', sort_order: 0 },
    ])
    emitUpdate()
    return
  }
  steps.value.splice(index, 1)
  emitUpdate()
}

function onRowAction(key, index) {
  if (key === 'insertAfter') {
    insertStepAfter(index)
  } else if (key === 'duplicate') {
    insertStepAfter(index, steps.value[index])
  } else if (key === 'delete') {
    removeStep(index)
  }
}
</script>

<style scoped>
.steps-editor {
  width: 100%;
  border: 1px solid #eee;
  border-bottom: 0;
  background: #fff;
  border-radius: 6px;
  overflow: hidden;
}
.steps-grid {
  display: grid;
  grid-template-columns: 32px 72px minmax(220px, 1fr) minmax(220px, 1fr) 96px;
  align-items: stretch;
}
.steps-head {
  height: 40px;
  align-items: center;
  color: #666;
  font-size: 13px;
  background: #fafafa;
  border-bottom: 1px solid #eee;
}
.steps-row {
  min-height: 48px;
  border-bottom: 1px solid #eee;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}
.steps-row:hover {
  background: #fff7f0;
}
.steps-row.is-drag-over {
  position: relative;
  background: #fff7f0;
  box-shadow: inset 0 0 0 1px #e88024;
}
.steps-col-index,
.steps-col-action {
  text-align: center;
}
.drag-cell,
.index-cell,
.step-cell,
.action-cell {
  display: flex;
  align-items: center;
  min-width: 0;
}
.drag-cell,
.index-cell,
.action-cell {
  justify-content: center;
}
.drag-icon {
  color: #999;
  cursor: grab;
}
.step-index {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  line-height: 18px;
  text-align: center;
  font-size: 12px;
  color: #666;
  background: #f5f6fb;
}
.ghost-input {
  width: 100%;
}
.ghost-input :deep(.n-input) {
  background: transparent;
}
.ghost-input :deep(.n-input-wrapper) {
  padding: 8px 12px;
}
.ghost-input :deep(.n-input__border),
.ghost-input :deep(.n-input__state-border) {
  display: none;
}
.ghost-input :deep(textarea) {
  min-height: 24px;
  line-height: 22px;
}
.more-btn {
  color: #666;
  letter-spacing: 1px;
}
.add-step-btn {
  margin: 12px 0 14px 12px;
  color: #e88024;
}
</style>
