<template>
  <div class="mindmap-wrap">
    <div class="mindmap-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">{{ currentModule || '全部用例' }}</span>
        <span class="toolbar-count">({{ totalCases }})</span>
        <n-tooltip trigger="hover">
          <template #trigger>
            <the-icon
              icon="material-symbols:help-outline"
              :size="16"
              style="margin-left: 8px; color: var(--n-text-color-3); cursor: help"
            />
          </template>
          脑图：在模块下添加子节点可表示用例；子节点可表示步骤与预期。《功能细节交互》1.2：文本/前置/备注富文本与空格快捷编辑能力逐步对齐。
        </n-tooltip>
      </div>
      <div class="toolbar-center">
        <n-button-group size="tiny">
          <n-button @click="zoomOut">
            <template #icon><the-icon icon="material-symbols:zoom-out" :size="16" /></template>
          </n-button>
          <n-button @click="zoomIn">
            <template #icon><the-icon icon="material-symbols:zoom-in" :size="16" /></template>
          </n-button>
          <n-button @click="fitScreen">
            <template #icon><the-icon icon="material-symbols:fit-screen" :size="16" /></template>
          </n-button>
        </n-button-group>
        <n-slider
          v-model:value="zoomPercent"
          :min="30"
          :max="200"
          style="width: 100px"
          @update:value="onZoomSlide"
        />
      </div>
      <div class="toolbar-right">
        <n-radio-group :value="viewMode" size="tiny" @update:value="onViewChange">
          <n-radio-button value="list">
            <the-icon icon="material-symbols:list" :size="14" />
          </n-radio-button>
          <n-radio-button value="mindmap">
            <the-icon icon="material-symbols:account-tree" :size="14" />
          </n-radio-button>
        </n-radio-group>
        <n-button
          v-if="editable"
          size="tiny"
          type="primary"
          :loading="saving"
          style="margin-left: 8px"
          @click="onSave"
        >
          <template #icon><the-icon icon="material-symbols:save" :size="16" /></template>
          保存
        </n-button>
      </div>
    </div>
    <div class="mindmap-body">
      <div ref="mapContainer" class="mindmap-canvas" @contextmenu.prevent></div>
      <transition name="slide-right">
        <div v-if="selectedNode" class="mindmap-detail">
          <div class="detail-header">
            <span font-500>{{ detailTab === 'basic' ? '基本信息' : '测试步骤' }}</span>
            <n-button text size="tiny" @click="selectedNode = null">
              <template #icon><the-icon icon="material-symbols:close" :size="16" /></template>
            </n-button>
          </div>
          <n-tabs v-model:value="detailTab" size="small" justify-content="space-evenly">
            <n-tab-pane name="basic" tab="基本信息" />
            <n-tab-pane v-if="selectedNodeType === 'case'" name="steps" tab="测试步骤" />
          </n-tabs>
          <div class="detail-body">
            <template v-if="detailTab === 'basic'">
              <n-form label-placement="top" size="small">
                <n-form-item label="名称">
                  <n-input v-model:value="editForm.name" size="small" />
                </n-form-item>
                <n-form-item v-if="selectedNodeType === 'case'" label="用例等级">
                  <n-select v-model:value="editForm.level" :options="levelOpts" size="small" />
                </n-form-item>
                <n-form-item v-if="selectedNodeType === 'case'" label="所属模块">
                  <n-tree-select
                    v-model:value="editForm.module_id"
                    :options="moduleTree"
                    placeholder="选择模块"
                    clearable
                    size="small"
                    key-field="id"
                    label-field="name"
                    children-field="children"
                  />
                </n-form-item>
                <n-form-item v-if="selectedNodeType === 'case'" label="标签">
                  <n-dynamic-tags v-model:value="editForm.tags" />
                </n-form-item>
              </n-form>
            </template>
            <template v-if="detailTab === 'steps' && selectedNodeType === 'case'">
              <div v-for="(step, i) in editForm.steps" :key="i" class="detail-step-row">
                <n-tag size="tiny" style="min-width: 22px; text-align: center">{{ i + 1 }}</n-tag>
                <n-input v-model:value="step.action" size="small" placeholder="步骤" />
                <n-input v-model:value="step.expected_result" size="small" placeholder="预期" />
                <n-button text size="tiny" type="error" @click="editForm.steps.splice(i, 1)">
                  <template #icon><the-icon icon="material-symbols:close" :size="14" /></template>
                </n-button>
              </div>
              <n-button
                dashed
                size="small"
                block
                @click="editForm.steps.push({ action: '', expected_result: '' })"
              >
                + 添加步骤
              </n-button>
            </template>
            <div mt-12 flex gap-8>
              <n-button size="small" type="primary" @click="saveNodeDetail">确定</n-button>
              <n-button size="small" @click="selectedNode = null">取消</n-button>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import MindElixir from 'mind-elixir'
import TheIcon from '@/components/icon/TheIcon.vue'

const props = defineProps({
  editable: { type: Boolean, default: false },
  projectId: { type: Number, default: null },
  moduleTree: { type: Array, default: () => [] },
})

const emit = defineEmits(['save', 'refresh', 'update:viewMode'])
const viewMode = ref('mindmap')

function onViewChange(mode) {
  viewMode.value = mode
  emit('update:viewMode', mode)
}

const mapContainer = ref(null)
const saving = ref(false)
const currentModule = ref('')
const totalCases = ref(0)
const zoomPercent = ref(100)
const selectedNode = ref(null)
const selectedNodeType = ref('')
const detailTab = ref('basic')
const editForm = ref({ name: '', level: 'P2', module_id: null, tags: [], steps: [] })

let mind = null
let mindData = null

const levelOpts = [
  { label: 'P0', value: 'P0' },
  { label: 'P1', value: 'P1' },
  { label: 'P2', value: 'P2' },
  { label: 'P3', value: 'P3' },
]

async function open(caseTreeData) {
  await nextTick()
  if (mind) {
    try {
      mind.destroy()
    } catch (e) {
      /* ignore */
    }
    mind = null
  }
  const data = buildMindData(caseTreeData)
  mindData = JSON.parse(JSON.stringify(data))
  try {
    mind = new MindElixir({
      el: mapContainer.value,
      direction: 1,
      draggable: props.editable,
      contextMenu: props.editable,
      toolBar: props.editable,
      nodeMenu: props.editable,
      keypress: props.editable,
      before: props.editable
        ? {
            clickNode: onNodeClick,
          }
        : undefined,
    })
    mind.init(mindData)
    mind.toCenter()
  } catch (e) {
    console.error('MindElixir init error:', e)
  }
}

function buildMindData(tree) {
  let caseCount = 0
  const root = {
    id: 'root',
    topic: '测试用例',
    children: [],
  }
  function buildModuleNode(mod, parentChildren) {
    const modNode = {
      id: `module-${mod.id}`,
      topic: mod.name,
      direction: 2,
      expanded: true,
      children: [],
    }
    if (mod.cases) {
      for (const tc of mod.cases) {
        caseCount++
        const caseNode = {
          id: `case-${tc.id}`,
          topic: `[${tc.level}] ${tc.name}`,
          children: [],
        }
        if (tc.steps) {
          for (const step of tc.steps) {
            caseNode.children.push({
              id: `step-${step.id}`,
              topic: `${step.step_number}. ${step.action} → ${step.expected_result}`,
            })
          }
        }
        modNode.children.push(caseNode)
      }
    }
    // Handle nested child modules
    if (mod.children?.length) {
      for (const childMod of mod.children) {
        buildModuleNode(childMod, modNode.children)
      }
    }
    parentChildren.push(modNode)
  }
  for (const mod of tree) {
    buildModuleNode(mod, root.children)
  }
  totalCases.value = caseCount
  return { nodeData: root }
}

function onNodeClick(node) {
  if (!node || !node.id) return
  let nodeType = ''
  const form = { name: '', level: 'P2', module_id: null, tags: [], steps: [] }

  if (node.id.startsWith('case-')) {
    nodeType = 'case'
    const caseId = parseInt(node.id.replace('case-', ''))
    form.name = (node.topic || '').replace(/^\[P[0-3]\]\s*/, '')
    const levelMatch = (node.topic || '').match(/^\[(P[0-3])\]/)
    form.level = levelMatch ? levelMatch[1] : 'P2'
    form.module_id = findModuleForCase(caseId)
    form.steps = (node.children || []).map((s, i) => ({
      step_number: i + 1,
      action: (s.topic || '').split(' → ')[0] || s.topic || '',
      expected_result: (s.topic || '').split(' → ')[1] || '',
    }))
  } else if (node.id.startsWith('module-')) {
    nodeType = 'module'
    form.name = node.topic || ''
  } else {
    return
  }
  selectedNodeType.value = nodeType
  editForm.value = form
  detailTab.value = 'basic'
  selectedNode.value = node
}

function findModuleForCase(caseId) {
  if (!mindData) return null
  const root = mindData.nodeData
  for (const mod of root.children || []) {
    for (const c of mod.children || []) {
      if (c.id === `case-${caseId}`) {
        const moduleId = mod.id.replace('module-', '')
        return parseInt(moduleId) || null
      }
    }
  }
  return null
}

function saveNodeDetail() {
  if (!selectedNode.value || !mind) return
  const node = selectedNode.value
  if (selectedNodeType.value === 'case') {
    const topic = `[${editForm.value.level}] ${editForm.value.name}`
    mind.updateNodeTopic(node, topic)
    // Update steps: clear children, rebuild
    const newChildren = editForm.value.steps.map((s, i) => ({
      id: node.children?.[i]?.id || `step-new-${Date.now()}-${i}`,
      topic: `${i + 1}. ${s.action} → ${s.expected_result}`,
    }))
    // Replace children by removing old and adding new - use mind API
    const existing = node.children || []
    for (const child of existing) {
      mind.removeNode(child)
    }
    for (const child of newChildren) {
      mind.addChild(node, child)
    }
  } else if (selectedNodeType.value === 'module') {
    mind.updateNodeTopic(node, editForm.value.name)
  }
  $message.success('节点已更新')
  selectedNode.value = null
}

function onSave() {
  if (!mind) return
  saving.value = true
  const data = mind.getAllData()
  // Parse mind map data and emit
  const result = parseMindData(data)
  emit('save', result)
  saving.value = false
}

function parseMindData(data) {
  const root = data.nodeData || data
  const modules = []
  const cases = []

  function parseNode(node, parentModuleId) {
    if (!node || !node.id) return
    if (node.id.startsWith('module-')) {
      const moduleId = parseInt(node.id.replace('module-', '')) || null
      modules.push({ id: moduleId, name: node.topic })
      for (const child of node.children || []) {
        parseNode(child, moduleId)
      }
    } else if (node.id.startsWith('case-') || !node.id.startsWith('module-')) {
      const isNew = !node.id || !node.id.startsWith('case-')
      let caseId = null
      if (!isNew) caseId = parseInt(node.id.replace('case-', ''))
      const levelMatch = (node.topic || '').match(/^\[(P[0-3])\]\s*(.+)/)
      const caseName = levelMatch ? levelMatch[2] : node.topic || ''
      const level = levelMatch ? levelMatch[1] : 'P2'
      const steps = (node.children || []).map((stepNode, i) => ({
        step_number: i + 1,
        action: (stepNode.topic || '').split(' → ')[0] || stepNode.topic || '',
        expected_result: (stepNode.topic || '').split(' → ')[1] || '',
        sort_order: i,
      }))
      cases.push({
        id: caseId,
        isNew,
        name: caseName,
        level,
        module_id: parentModuleId,
        project_id: props.projectId,
        steps,
      })
    }
  }

  for (const node of root.children || []) {
    parseNode(node, null)
  }
  return { modules, cases }
}

function zoomOut() {
  zoomPercent.value = Math.max(30, zoomPercent.value - 20)
  applyZoom()
}
function zoomIn() {
  zoomPercent.value = Math.min(200, zoomPercent.value + 20)
  applyZoom()
}
function onZoomSlide(val) {
  zoomPercent.value = val
  applyZoom()
}
function applyZoom() {
  if (!mapContainer.value) return
  const scale = zoomPercent.value / 100
  mapContainer.value.style.transform = `scale(${scale})`
  mapContainer.value.style.transformOrigin = 'center center'
}
function fitScreen() {
  zoomPercent.value = 100
  applyZoom()
  if (mind) mind.toCenter()
}

function close() {
  if (mind) {
    mind.destroy()
    mind = null
  }
}

defineExpose({ open, close })
</script>

<style scoped>
.mindmap-wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.mindmap-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color);
  flex-shrink: 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}
.toolbar-label {
  font-weight: 500;
}
.toolbar-count {
  color: var(--n-text-color-3);
}
.toolbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.mindmap-body {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}
.mindmap-canvas {
  flex: 1;
  overflow: auto;
  min-height: 400px;
  transition: transform 0.15s;
}
.mindmap-detail {
  width: 300px;
  border-left: 1px solid var(--n-border-color);
  background: var(--n-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px 4px;
}
.detail-body {
  padding: 8px 12px 12px;
  flex: 1;
  overflow-y: auto;
}
.detail-step-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.detail-step-row .n-input {
  flex: 1;
}
.slide-right-enter-active,
.slide-right-leave-active {
  transition: width 0.2s, opacity 0.2s;
}
.slide-right-enter-from,
.slide-right-leave-to {
  width: 0;
  opacity: 0;
}
</style>
