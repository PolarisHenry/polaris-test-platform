<template>
  <!-- Case Edit View -->
  <case-edit
    v-if="editCaseId"
    :case-id="editCaseId"
    :project-id="currentProjectId"
    :module-tree="moduleTreeRaw"
    :user-options="userOpts"
    :initial-module-id="initialModuleForCaseEdit"
    @back="goBackToList"
    @saved="onCaseSaved"
  />

  <!-- Main View: Tabs + Sidebar + Table -->
  <n-layout v-else has-sider style="height: calc(100vh - 140px)">
    <n-layout-sider
      width="260"
      bordered
      collapsible
      collapse-mode="transform"
      :collapsed-width="0"
      show-trigger="arrow-circle"
      :native-scrollbar="false"
    >
      <div class="sidebar">
        <div class="sidebar-header">
          <div flex items-center gap-8 style="cursor: pointer" @click="onSelectAll">
            <the-icon
              icon="material-symbols:folder-outline"
              :size="16"
              style="color: var(--primary-color)"
            />
            <span font-500>全部用例 ({{ totalCaseCount }})</span>
          </div>
          <div flex items-center gap-4>
            <n-button
              size="tiny"
              text
              :title="treeExpanded ? '收起' : '展开'"
              @click="toggleExpand"
            >
              <template #icon
                ><the-icon
                  :icon="
                    treeExpanded ? 'material-symbols:expand-less' : 'material-symbols:expand-more'
                  "
                  :size="16"
              /></template>
            </n-button>
            <n-button size="tiny" text title="新建模块" @click="openCreateModule()">
              <template #icon><the-icon icon="material-symbols:add" :size="16" /></template>
            </n-button>
          </div>
        </div>
        <n-input
          v-model:value="moduleSearch"
          placeholder="搜索模块..."
          size="small"
          clearable
          class="sidebar-search"
        />
        <div class="tree-area">
          <n-tree
            :data="moduleTreeData"
            :node-props="nodeProps"
            :expanded-keys="expandedKeys"
            key-field="id"
            label-field="name"
            children-field="children"
            block-line
            selectable
            draggable
            :render-prefix="renderPrefixFn"
            :render-label="renderLabelFn"
            :render-suffix="renderSuffixFn"
            @update:expanded-keys="onExpandedKeysChange"
            @update:selected-keys="onTreeSelect"
            @drop="handleTreeDrop"
          />
        </div>
        <div class="sidebar-footer">
          <div
            class="recycle-item"
            :class="{ active: selectedModuleId === -1 }"
            @click="onTreeSelect(['recycle'])"
          >
            <the-icon
              icon="material-symbols:delete-outline"
              :size="14"
              style="color: var(--text-color-3)"
            />
            <span>回收站 ({{ recycleCount }})</span>
          </div>
        </div>
      </div>
    </n-layout-sider>

    <n-layout-content>
      <!-- 回收站视图 -->
      <common-page v-if="selectedModuleId === -1" :show-header="false">
        <n-alert type="warning" mb-12 size="small" :bordered="false">
          回收站中的用例可恢复或彻底删除。彻底删除后数据不可恢复。
        </n-alert>
        <div flex justify-between mb-12>
          <div>
            <n-button type="primary" :disabled="recycleChecked.length === 0" @click="onRestoreCases"
              >恢复选中</n-button
            >
            <n-button
              ml-8
              type="error"
              :disabled="recycleChecked.length === 0"
              @click="onHardDeleteCases"
              >彻底删除</n-button
            >
          </div>
          <n-button @click="loadRecycleBin">刷新</n-button>
        </div>
        <n-data-table
          :columns="recycleColumns"
          :data="recycleItems"
          :pagination="false"
          size="small"
          :row-key="(row) => row.id"
          :checked-row-keys="recycleChecked"
          @update:checked-row-keys="onRecycleChecked"
        />
        <n-empty v-if="recycleItems.length === 0" description="回收站为空" mt-32 />
      </common-page>

      <common-page v-else :show-header="false">
        <n-tabs v-model:value="activeTab" @update:value="onTabChange">
          <!-- ========== 用例 Tab ========== -->
          <n-tab-pane name="cases" tab="用例">
            <crud-table
              v-if="viewMode === 'list'"
              ref="$casesTable"
              v-model:query-items="casesQuery"
              :columns="casesColumns"
              :get-data="fetchCases"
              :extra-params="{ project_id: currentProjectId, module_id: selectedModuleId }"
              @on-checked="onChecked"
            >
              <template #actions>
                <n-button
                  v-permission="'post/api/v1/testcase/create'"
                  type="primary"
                  @click="handleAdd"
                >
                  <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
                  新建用例
                </n-button>
                <n-button ml-8 @click="openImportModal">
                  <template #icon><the-icon icon="material-symbols:upload" :size="18" /></template>
                  导入
                </n-button>
                <n-dropdown trigger="hover" :options="batchOptions" ml-8 @select="onBatchSelect">
                  <n-button>批量操作</n-button>
                </n-dropdown>
              </template>
              <template #queryBar>
                <project-selector style="width: 200px" @change="onProjectChange" />
                <n-input
                  v-model:value="casesQuery.name"
                  placeholder="通过 ID/名称/标签搜索"
                  clearable
                  style="width: 260px"
                />
                <n-select
                  v-model:value="casesQuery.level"
                  placeholder="用例等级"
                  clearable
                  :options="levelOptions"
                  style="width: 120px"
                />
                <n-select
                  v-model:value="casesQuery.status"
                  placeholder="状态"
                  clearable
                  :options="statusOptions"
                  style="width: 120px"
                />
                <n-radio-group v-model:value="viewMode" size="small" ml-auto>
                  <n-radio-button value="list">
                    <the-icon icon="material-symbols:list" :size="16" />
                  </n-radio-button>
                  <n-radio-button value="mindmap">
                    <the-icon icon="material-symbols:account-tree" :size="16" />
                  </n-radio-button>
                </n-radio-group>
              </template>
            </crud-table>
            <div v-else class="mindmap-wrapper">
              <mind-map
                ref="mindMapRef"
                :editable="true"
                :project-id="currentProjectId"
                :module-tree="mindMapTree"
                @save="onMindMapSave"
                @refresh="onMindMapRefresh"
                @update:view-mode="(mode) => (viewMode = mode)"
              />
            </div>
          </n-tab-pane>

          <!-- ========== 评审 Tab ========== -->
          <n-tab-pane name="review" tab="评审">
            <crud-table
              ref="$reviewTable"
              v-model:query-items="reviewQuery"
              :columns="reviewColumns"
              :get-data="fetchReviewCases"
              :extra-params="{ project_id: currentProjectId, module_id: selectedModuleId }"
            >
              <template #queryBar>
                <project-selector style="width: 200px" @change="onProjectChange" />
                <n-input
                  v-model:value="reviewQuery.name"
                  placeholder="通过 ID/名称/标签搜索"
                  clearable
                  style="width: 260px"
                />
                <n-select
                  v-model:value="reviewQuery.review_result"
                  placeholder="评审状态"
                  clearable
                  :options="reviewStatusOptions"
                  style="width: 130px"
                />
                <n-select
                  v-model:value="reviewQuery.level"
                  placeholder="用例等级"
                  clearable
                  :options="levelOptions"
                  style="width: 120px"
                />
              </template>
            </crud-table>
          </n-tab-pane>
        </n-tabs>

        <!-- Shared Modals -->
        <crud-modal
          v-model:visible="modalVisible"
          :title="modalTitle"
          :loading="modalLoading"
          width="800px"
          @save="handleSave"
        >
          <case-form ref="caseFormRef" :module-tree="moduleTreeRaw" :user-options="userOpts" />
        </crud-modal>

        <n-modal
          v-model:show="moduleModalVisible"
          :title="moduleModalTitle"
          preset="card"
          style="width: 400px"
          :mask-closable="false"
        >
          <n-form
            ref="moduleFormRef"
            :model="moduleForm"
            :rules="moduleRules"
            label-placement="left"
            label-width="80"
          >
            <n-form-item label="模块名称" path="name">
              <n-input v-model:value="moduleForm.name" placeholder="请输入模块名称" />
            </n-form-item>
            <n-form-item v-if="!editingModule" label="父模块">
              <n-tree-select
                v-model:value="moduleForm.parent_id"
                :options="moduleTreeRaw"
                placeholder="默认根模块"
                clearable
                key-field="id"
                label-field="name"
                children-field="children"
              />
            </n-form-item>
          </n-form>
          <template #footer>
            <n-button @click="moduleModalVisible = false">取消</n-button>
            <n-button ml-12 type="primary" :loading="moduleModalLoading" @click="doSaveModule"
              >保存</n-button
            >
          </template>
        </n-modal>

        <n-modal
          v-model:show="batchModuleVisible"
          title="批量修改模块"
          preset="card"
          style="width: 400px"
          :mask-closable="false"
        >
          <n-form label-placement="left" label-width="80">
            <n-form-item label="目标模块">
              <n-tree-select
                v-model:value="batchModuleId"
                :options="moduleTreeRaw"
                placeholder="请选择目标模块"
                clearable
                key-field="id"
                label-field="name"
                children-field="children"
              />
            </n-form-item>
          </n-form>
          <template #footer>
            <n-button @click="batchModuleVisible = false">取消</n-button>
            <n-button ml-12 type="primary" @click="doBatchUpdateModule">确定</n-button>
          </template>
        </n-modal>

        <n-modal
          v-model:show="importVisible"
          title="导入用例"
          preset="card"
          style="width: 520px"
          :mask-closable="false"
        >
          <n-alert type="info" size="small" :bordered="false" mb-12>
            支持 CSV / XLSX /
            XMind。表格首行可使用：用例名称、用例等级、前置条件、步骤描述、预期结果、标签。
          </n-alert>
          <n-space vertical :size="12">
            <n-switch v-model:value="importOverwrite">
              <template #checked>覆盖同名用例</template>
              <template #unchecked>不覆盖同名用例</template>
            </n-switch>
            <n-upload
              :custom-request="handleCaseImport"
              :show-file-list="false"
              accept=".csv,.xlsx,.xls,.xmind"
            >
              <n-upload-dragger>
                <div style="margin-bottom: 8px">
                  <the-icon icon="material-symbols:upload-file-outline" :size="36" />
                </div>
                <n-text>点击或拖拽文件到此处上传</n-text>
                <n-p depth="3" style="margin: 8px 0 0">导入完成后会自动刷新列表与模块统计。</n-p>
              </n-upload-dragger>
            </n-upload>
          </n-space>
        </n-modal>
      </common-page>
    </n-layout-content>
  </n-layout>

  <!-- Review Modal -->
  <review-detail v-model:case-id="reviewModalCaseId" @reviewed="onReviewed" />
</template>

<script setup>
import { NButton, NTag, NDropdown, NInput, NSelect, NPopconfirm } from 'naive-ui'
import { useCRUD } from '@/composables'
import CrudTable from '@/components/table/CrudTable.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'
import CaseForm from './components/CaseForm.vue'
import CaseEdit from './components/CaseEdit.vue'
import MindMap from './components/MindMap.vue'
import ReviewDetail from './components/ReviewDetail.vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'
import TheIcon from '@/components/icon/TheIcon.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const currentProjectId = computed(() => projectStore.currentProjectId)
const selectedModuleId = ref(null)

/** 新建用例时默认所属模块（与左侧树选中一致；回收站不预填） */
const initialModuleForCaseEdit = computed(() => {
  const sid = selectedModuleId.value
  if (sid === null || sid === undefined || sid === -1) return null
  return sid
})
const $casesTable = ref(null)
const $reviewTable = ref(null)
const caseFormRef = ref(null)
const mindMapRef = ref(null)
const moduleSearch = ref('')
const moduleTreeData = ref([])
const expandedKeys = ref([])
const checkedRowKeys = ref([])
const casesQuery = ref({})
const reviewQuery = ref({})
const userOpts = ref([])
const totalCaseCount = ref(0)
const recycleCount = ref(0)

// -- tabs, views & edit --
const activeTab = ref('cases')
const viewMode = ref('list')
const editCaseId = ref(null)
const reviewModalCaseId = ref(null)

// -- inline editing --
const editingNameId = ref(null)
const editingNameValue = ref('')
const editingLevelId = ref(null)

const levelColorMap = { P0: 'error', P1: 'warning', P2: 'info', P3: 'default' }
const reviewColorMap = { pass: 'success', fail: 'error', resubmit: 'warning', suggest: 'info' }
const execColorMap = {
  success: 'success',
  fail: 'error',
  pending: 'default',
  blocked: 'warning',
  skipped: 'default',
}
const reviewLabelMap = {
  pass: '已通过',
  fail: '不通过',
  resubmit: '重新提交',
  suggest: '建议',
}
const execLabelMap = {
  success: '成功',
  fail: '失败',
  pending: '待执行',
  blocked: '阻塞',
  skipped: '跳过',
}
const statusLabelMap = { draft: '草稿', published: '已发布', archived: '已归档' }

const levelOptions = [
  { label: 'P0', value: 'P0' },
  { label: 'P1', value: 'P1' },
  { label: 'P2', value: 'P2' },
  { label: 'P3', value: 'P3' },
]
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已归档', value: 'archived' },
]
const reviewStatusOptions = [
  { label: '待评审', value: '' },
  { label: '已通过', value: 'pass' },
  { label: '不通过', value: 'fail' },
  { label: '重新提交', value: 'resubmit' },
  { label: '建议', value: 'suggest' },
]
// -- inline edit handlers --
function startEditName(row) {
  editingNameId.value = row.id
  editingNameValue.value = row.name
  nextTick(() => {
    const el = document.querySelector('.inline-name-input input')
    if (el) el.focus()
  })
}

async function saveInlineName(row) {
  const newName = editingNameValue.value.trim()
  editingNameId.value = null
  if (newName && newName !== row.name) {
    try {
      await api.updateTestCase({ id: row.id, name: newName, project_id: row.project_id })
      row.name = newName
      $message.success('名称已更新')
    } catch {
      $message.error('更新失败')
    }
  }
}

function startEditLevel(row) {
  editingLevelId.value = row.id
}

async function saveInlineLevel(row, newLevel) {
  editingLevelId.value = null
  if (newLevel !== row.level) {
    try {
      await api.updateTestCase({
        id: row.id,
        name: row.name,
        project_id: row.project_id,
        level: newLevel,
      })
      row.level = newLevel
      $message.success('等级已更新')
      $casesTable.value?.handleSearch()
    } catch {
      $message.error('更新失败')
    }
  }
}

// -- cases columns --
const casesColumns = [
  { type: 'selection', width: 40 },
  { title: 'ID', key: 'id', width: 80 },
  {
    title: '用例名称',
    key: 'name',
    ellipsis: { tooltip: true },
    render(row) {
      if (editingNameId.value === row.id) {
        return [
          h(NInput, {
            class: 'inline-name-input',
            size: 'tiny',
            value: editingNameValue.value,
            style: 'width: 100%',
            onUpdateValue: (v) => {
              editingNameValue.value = v
            },
            onBlur: () => saveInlineName(row),
            onKeyup: (e) => {
              if (e.key === 'Enter') saveInlineName(row)
              if (e.key === 'Escape') editingNameId.value = null
            },
          }),
        ]
      }
      return h(
        'span',
        {
          style: 'cursor: pointer',
          onDblclick: () => startEditName(row),
        },
        row.name
      )
    },
  },
  {
    title: '用例等级',
    key: 'level',
    width: 90,
    render(row) {
      if (editingLevelId.value === row.id) {
        return h(NSelect, {
          size: 'tiny',
          value: row.level,
          options: levelOptions,
          style: 'width: 80px',
          onUpdateValue: (v) => saveInlineLevel(row, v),
          onBlur: () => {
            editingLevelId.value = null
          },
        })
      }
      return h(
        NTag,
        {
          type: levelColorMap[row.level] || 'default',
          size: 'small',
          bordered: false,
          style: 'cursor: pointer',
          onClick: () => startEditLevel(row),
        },
        { default: () => row.level }
      )
    },
  },
  {
    title: '评审结果',
    key: 'review_result',
    width: 100,
    render: (row) =>
      row.review_result
        ? h(
            NTag,
            {
              type: reviewColorMap[row.review_result] || 'default',
              size: 'small',
              bordered: false,
            },
            { default: () => reviewLabelMap[row.review_result] || row.review_result }
          )
        : h('span', { style: 'color: var(--text-color-3)' }, '-'),
  },
  {
    title: '执行结果',
    key: 'exec_result',
    width: 100,
    render: (row) =>
      h(
        NTag,
        { type: execColorMap[row.exec_result] || 'default', size: 'small', bordered: false },
        { default: () => execLabelMap[row.exec_result] || row.exec_result }
      ),
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) =>
      h(
        NTag,
        {
          type:
            row.status === 'published' ? 'success' : row.status === 'draft' ? 'default' : 'warning',
          size: 'small',
          bordered: false,
        },
        { default: () => statusLabelMap[row.status] || row.status }
      ),
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: (row) =>
      h('span', { style: 'display: flex; align-items: center; gap: 4px;' }, [
        h(
          NButton,
          { size: 'tiny', text: true, type: 'primary', onClick: () => handleEdit(row) },
          { default: () => '编辑' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        h(
          NButton,
          { size: 'tiny', text: true, type: 'primary', onClick: () => handleCopy(row) },
          { default: () => '复制' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        h(
          NDropdown,
          {
            trigger: 'click',
            options: [{ label: '删除', key: 'delete' }],
            onSelect: () => {
              window.$dialog?.warning({
                title: '确认删除',
                content: `确定要删除用例 "${row.name}" 吗？`,
                positiveText: '删除',
                negativeText: '取消',
                onPositiveClick: () => handleDelete({ case_id: row.id }),
              })
            },
          },
          {
            default: () => h(NButton, { size: 'tiny', text: true }, { default: () => '···' }),
          }
        ),
      ]),
  },
]

// -- review columns --
const reviewColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    render(row) {
      return h(
        NButton,
        {
          text: true,
          type: 'primary',
          size: 'tiny',
          onClick: () => openReviewDetail(row.id),
        },
        { default: () => String(row.id) }
      )
    },
  },
  { title: '用例名称', key: 'name', ellipsis: { tooltip: true } },
  {
    title: '用例等级',
    key: 'level',
    width: 80,
    render: (row) =>
      h(
        NTag,
        { type: levelColorMap[row.level] || 'default', size: 'small', bordered: false },
        { default: () => row.level }
      ),
  },
  {
    title: '评审结果',
    key: 'review_result',
    width: 100,
    render: (row) =>
      row.review_result
        ? h(
            NTag,
            {
              type: reviewColorMap[row.review_result] || 'default',
              size: 'small',
              bordered: false,
            },
            { default: () => reviewLabelMap[row.review_result] || row.review_result }
          )
        : h(NTag, { type: 'default', size: 'small', bordered: false }, { default: () => '待评审' }),
  },
  {
    title: '评审人',
    key: 'reviewer',
    width: 100,
    render: (row) =>
      row.reviewer?.username || h('span', { style: 'color: var(--text-color-3)' }, '-'),
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) =>
      h(
        NTag,
        {
          type:
            row.status === 'published' ? 'success' : row.status === 'draft' ? 'default' : 'warning',
          size: 'small',
          bordered: false,
        },
        { default: () => statusLabelMap[row.status] || row.status }
      ),
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row) =>
      h(
        NButton,
        {
          size: 'tiny',
          type: 'primary',
          onClick: () => openReviewDetail(row.id),
        },
        { default: () => '评审' }
      ),
  },
]

// -- CRUD --
const {
  modalVisible,
  modalTitle,
  modalLoading,
  modalFormRef,
  handleDelete,
  handleSave: _handleSave,
  modalForm,
} = useCRUD({
  name: '用例',
  initForm: {},
  doCreate: (data) =>
    api.createTestCase({
      ...data,
      project_id: currentProjectId.value,
      module_id: selectedModuleId.value || data.module_id,
    }),
  doUpdate: (data) => api.updateTestCase(data),
  doDelete: (params) => api.deleteTestCase(params),
  refresh: () => $casesTable.value?.handleSearch(),
})

function handleAdd() {
  if (!currentProjectId.value) {
    $message.warning('请先选择项目')
    return
  }
  editCaseId.value = 'new'
  router.replace({ query: { ...route.query, case_id: 'new' } })
}

function handleEdit(row) {
  editCaseId.value = row.id
  router.replace({ query: { ...route.query, case_id: String(row.id) } })
}

function handleCopy(row) {
  const copyData = { ...row, name: (row.name || '') + ' (副本)', id: undefined }
  modalForm.value = copyData
  modalVisible.value = true
  modalTitle.value = '复制用例'
  nextTick(() => {
    caseFormRef.value?.setForm(modalForm.value)
    modalFormRef.value = caseFormRef.value?.formRef
  })
}

async function handleSave() {
  const data = caseFormRef.value?.getForm()
  if (data) {
    Object.assign(modalForm.value, data)
  }
  await _handleSave()
}

async function fetchCases(params) {
  params.project_id = currentProjectId.value
  if (selectedModuleId.value) params.module_id = selectedModuleId.value
  const res = await api.getTestCaseList(params)
  return { data: res.data, total: res.total }
}

async function fetchReviewCases(params) {
  params.project_id = currentProjectId.value
  if (selectedModuleId.value) params.module_id = selectedModuleId.value
  const res = await api.getTestCaseList(params)
  return { data: res.data, total: res.total }
}

function onTreeSelect(keys) {
  if (keys[0] === 'unplanned') {
    selectedModuleId.value = 0
  } else if (keys[0] === 'recycle') {
    selectedModuleId.value = -1
  } else {
    selectedModuleId.value = keys[0]
  }
  refreshCurrentTable()
}

function refreshCurrentTable() {
  if (activeTab.value === 'review') {
    $reviewTable.value?.handleSearch()
  } else {
    $casesTable.value?.handleSearch()
  }
}

const nodeProps = () => ({})

// -- tree render props (n-tree uses render props, not slots) --
function renderPrefixFn({ option }) {
  if (option.isNewNode) return null
  if (option.id === 'recycle') {
    return h(TheIcon, {
      icon: 'material-symbols:delete-outline',
      size: 14,
      style: 'color: var(--text-color-3); margin-right: 4px',
    })
  }
  if (option.id !== 'unplanned') {
    return h(TheIcon, {
      icon: 'material-symbols:folder-outline',
      size: 14,
      style: 'color: var(--warning-color); margin-right: 4px',
    })
  }
  return null
}

function renderLabelFn({ option }) {
  if (option.isNewNode) {
    return h(NInput, {
      class: 'new-module-input',
      value: newNodeName.value,
      placeholder: '输入子模块名称',
      size: 'tiny',
      style: 'width: 160px',
      onUpdateValue: (v) => {
        newNodeName.value = v
      },
      onKeyup: (e) => {
        if (e.key === 'Enter') confirmNewNode()
        if (e.key === 'Escape') cancelNewNode()
      },
      onBlur: () => onNewNodeBlur(),
    })
  }
  const children = [h('span', null, option.name)]
  if (option.caseCount !== undefined) {
    children.push(
      h(
        'span',
        { style: 'color: var(--text-color-3); margin-left: 4px; font-size: 12px' },
        `(${option.caseCount})`
      )
    )
  }
  return children
}

function renderSuffixFn({ option }) {
  if (option.isNewNode || option.id === 'unplanned' || option.id === 'recycle') return null
  return [
    h(
      'span',
      {
        class: 'tree-suffix-btn',
        onClick: (e) => {
          e.stopPropagation()
          startInlineCreate(option)
        },
      },
      '+'
    ),
    h(
      NDropdown,
      {
        trigger: 'click',
        options: [
          { label: '新建用例', key: 'newCase' },
          { label: '重命名', key: 'rename' },
          { label: '删除', key: 'delete' },
        ],
        onSelect: (key) => {
          if (key === 'newCase') {
            selectedModuleId.value = option.id
            handleAdd()
          } else if (key === 'rename') openRenameModule(option)
          else if (key === 'delete') handleModuleDelete(option)
        },
      },
      {
        default: () =>
          h(
            'span',
            {
              class: 'tree-suffix-btn',
              style: 'margin-left: 2px',
              onClick: (e) => e.stopPropagation(),
            },
            '···'
          ),
      }
    ),
  ]
}

// -- tabs, edit & review --
function onTabChange(val) {
  router.replace({ query: { ...route.query, tab: val } })
  nextTick(() => refreshCurrentTable())
}

function openReviewDetail(caseId) {
  reviewModalCaseId.value = caseId
}

function goBackToList() {
  editCaseId.value = null
  const q = { ...route.query }
  delete q.case_id
  router.replace({ query: q })
  refreshCurrentTable()
  loadModuleTree()
}

function onCaseSaved() {
  refreshCurrentTable()
  loadModuleTree()
}

function onReviewed() {
  reviewModalCaseId.value = null
  $reviewTable.value?.handleSearch()
}

// -- mind map --
const mindMapTree = ref([])

async function loadMindMapData() {
  if (!currentProjectId.value) return
  // Load all modules and their cases for the mind map
  const res = await api.getModuleTree({ project_id: currentProjectId.value })
  const tree = JSON.parse(JSON.stringify(res.data || []))

  async function loadCasesForNodes(nodes) {
    for (const node of nodes) {
      const casesRes = await api.getTestCaseList({
        project_id: currentProjectId.value,
        module_id: node.id,
        page_size: 9999,
      })
      node.cases = casesRes.data || []
      if (node.children?.length) {
        await loadCasesForNodes(node.children)
      }
    }
  }
  await loadCasesForNodes(tree)
  mindMapTree.value = tree
  nextTick(() => mindMapRef.value?.open(tree))
}

watch(viewMode, (mode) => {
  if (mode === 'mindmap') loadMindMapData()
})

async function onMindMapSave(data) {
  if (!data?.cases?.length) return
  let created = 0
  for (const c of data.cases) {
    if (!c.isNew) continue
    if (!c.module_id) continue
    try {
      await api.createTestCase({
        name: c.name || '未命名用例',
        module_id: c.module_id,
        project_id: currentProjectId.value,
        level: c.level || 'P2',
        steps: c.steps || [],
      })
      created++
    } catch {
      /* skip failed */
    }
  }
  $message.success(`思维导图已保存，创建了 ${created} 个新用例`)
  $casesTable.value?.handleSearch()
  loadModuleTree()
}

function onMindMapRefresh() {
  $casesTable.value?.handleSearch()
  loadModuleTree()
}

// -- inline module create --
const newNodeParentId = ref(null)
const newNodeName = ref('')

function startInlineCreate(option) {
  cancelNewNode()
  const tempNode = { id: '__new__', name: '', isNewNode: true }
  function findAndAdd(nodes) {
    for (const node of nodes) {
      if (node.id === option.id) {
        if (!node.children) node.children = []
        node.children.push(tempNode)
        if (!expandedKeys.value.includes(node.id)) {
          expandedKeys.value = [...expandedKeys.value, node.id]
        }
        return true
      }
      if (node.children?.length && findAndAdd(node.children)) return true
    }
    return false
  }
  findAndAdd(moduleTreeData.value)
  newNodeParentId.value = option.id
  newNodeName.value = ''
  // Deep clone to force n-tree complete re-render
  moduleTreeData.value = JSON.parse(JSON.stringify(moduleTreeData.value))
  setTimeout(() => {
    const el = document.querySelector('.new-module-input input')
    if (el) el.focus()
  }, 100)
}

function cancelNewNode() {
  if (newNodeBlurTimer) {
    clearTimeout(newNodeBlurTimer)
    newNodeBlurTimer = null
  }
  function removeTempNode(nodes) {
    for (let i = nodes.length - 1; i >= 0; i--) {
      if (nodes[i].isNewNode) {
        nodes.splice(i, 1)
      } else if (nodes[i].children?.length) {
        removeTempNode(nodes[i].children)
      }
    }
  }
  removeTempNode(moduleTreeData.value)
  newNodeParentId.value = null
  newNodeName.value = ''
  moduleTreeData.value = JSON.parse(JSON.stringify(moduleTreeData.value))
}

let newNodeBlurTimer = null

function onNewNodeBlur() {
  newNodeBlurTimer = setTimeout(() => {
    if (newNodeName.value.trim()) {
      confirmNewNode()
    } else {
      cancelNewNode()
    }
  }, 200)
}

async function confirmNewNode() {
  if (newNodeBlurTimer) {
    clearTimeout(newNodeBlurTimer)
    newNodeBlurTimer = null
  }
  if (!newNodeName.value.trim()) {
    cancelNewNode()
    return
  }
  await api.createModule({
    project_id: currentProjectId.value,
    name: newNodeName.value.trim(),
    parent_id: newNodeParentId.value,
  })
  $message.success('模块创建成功')
  cancelNewNode()
  await loadModuleTree()
}

function onExpandedKeysChange(keys) {
  expandedKeys.value = keys
}

function onSelectAll() {
  selectedModuleId.value = null
  refreshCurrentTable()
}

function onChecked(rowKeys) {
  checkedRowKeys.value = rowKeys
}

const batchOptions = [
  {
    label: '批量评审',
    key: 'review',
    children: [
      { label: '标记为通过', key: 'review_pass' },
      { label: '标记为不通过', key: 'review_fail' },
      { label: '标记为建议', key: 'review_suggest' },
      { label: '标记为重新提交', key: 'review_resubmit' },
    ],
  },
  { label: '批量修改模块', key: 'module' },
  { label: '批量删除', key: 'delete' },
]

function onBatchSelect(key) {
  if (key === 'review_pass') doBatchReview('pass')
  else if (key === 'review_fail') doBatchReview('fail')
  else if (key === 'review_suggest') doBatchReview('suggest')
  else if (key === 'review_resubmit') doBatchReview('resubmit')
  else if (key === 'module') handleBatchModule()
  else if (key === 'delete') handleBatchDelete()
}

const importVisible = ref(false)
const importOverwrite = ref(false)

function openImportModal() {
  if (!currentProjectId.value) {
    $message.warning('请先选择项目')
    return
  }
  importVisible.value = true
}

async function handleCaseImport({ file, onFinish, onError }) {
  try {
    const formData = new FormData()
    formData.append('file', file.file)
    formData.append('project_id', currentProjectId.value)
    if (selectedModuleId.value && selectedModuleId.value !== -1) {
      formData.append('module_id', selectedModuleId.value)
    }
    formData.append('overwrite', importOverwrite.value ? 'true' : 'false')
    const res = await api.importTestCases(formData)
    const data = res.data || {}
    $message.success(
      `导入完成：新增 ${data.created || 0}，更新 ${data.updated || 0}，跳过 ${data.skipped || 0}`
    )
    importVisible.value = false
    onFinish?.()
    $casesTable.value?.handleSearch()
    loadModuleTree()
  } catch {
    onError?.()
  }
}

function handleBatchDelete() {
  if (!checkedRowKeys.value.length) {
    $message.warning('请先勾选用例')
    return
  }
  api.batchDeleteTestCases({ ids: checkedRowKeys.value }).then(() => {
    $message.success('批量删除成功')
    $casesTable.value?.handleSearch()
  })
}

function doBatchReview(review_result) {
  if (!checkedRowKeys.value.length) {
    $message.warning('请先勾选用例')
    return
  }
  api.batchReviewTestCases({ ids: checkedRowKeys.value, review_result }).then(() => {
    $message.success('批量评审已更新')
    $casesTable.value?.handleSearch()
    $reviewTable.value?.handleSearch()
  })
}

const batchModuleVisible = ref(false)
const batchModuleId = ref(null)

function handleBatchModule() {
  if (!checkedRowKeys.value.length) {
    $message.warning('请先勾选用例')
    return
  }
  batchModuleId.value = null
  batchModuleVisible.value = true
}

async function doBatchUpdateModule() {
  if (!batchModuleId.value) {
    $message.warning('请选择目标模块')
    return
  }
  await api.batchUpdateModuleCases({ ids: checkedRowKeys.value, module_id: batchModuleId.value })
  $message.success('批量修改模块成功')
  batchModuleVisible.value = false
  $casesTable.value?.handleSearch()
  loadModuleTree()
}

async function handleTreeDrop({ node, dragNode, dropPosition }) {
  if (dragNode.id === 'unplanned' || dragNode.id === 'recycle') return
  if (dropPosition === 'inner' && node.id === 'unplanned') {
    $message.warning('不能将模块拖放到此位置')
    return
  }
  try {
    if (dropPosition === 'inner') {
      await api.updateModule({
        id: dragNode.id,
        parent_id: node.id,
        name: dragNode.name,
        project_id: currentProjectId.value,
        desc: '',
        order: 0,
      })
    } else {
      const targetParentId = node.id === 'unplanned' ? 0 : node.parent_id || 0
      await api.updateModule({
        id: dragNode.id,
        parent_id: targetParentId,
        name: dragNode.name,
        project_id: currentProjectId.value,
        desc: '',
        order: 0,
      })
    }
    $message.success('模块已移动')
    await loadModuleTree()
  } catch {
    $message.error('移动失败')
  }
}

async function loadUsers() {
  const res = await api.getUserList({ page: 1, page_size: 9999 })
  userOpts.value = (res.data || []).map((u) => ({ label: u.username, value: u.id }))
}

function onProjectChange(val) {
  if (val) {
    loadModuleTree()
    loadUsers()
    loadRecycleBin()
    refreshCurrentTable()
  }
}

// -- module CRUD --
const moduleModalVisible = ref(false)
const moduleModalLoading = ref(false)
const moduleModalTitle = ref('新建模块')
const moduleFormRef = ref(null)
const moduleForm = ref({ name: '', parent_id: null })
const editingModule = ref(null)
const moduleRules = { name: [{ required: true, message: '请输入模块名称', trigger: 'blur' }] }
const moduleTreeRaw = ref([])

function openCreateModule(parentId = null) {
  if (!currentProjectId.value) {
    $message.warning('请先选择项目')
    return
  }
  editingModule.value = null
  moduleModalTitle.value = '新建模块'
  moduleForm.value = { name: '', parent_id: parentId }
  moduleModalVisible.value = true
}

function openRenameModule(module) {
  editingModule.value = module
  moduleModalTitle.value = '重命名模块'
  moduleForm.value = { name: module.name, parent_id: module.parent_id }
  moduleModalVisible.value = true
}

async function handleModuleDelete(module) {
  window.$dialog?.warning({
    title: '确认删除',
    content: `确定要删除模块 "${module.name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await api.deleteModule({ module_id: module.id })
      $message.success('模块已删除')
      loadModuleTree()
    },
  })
}

async function doSaveModule() {
  if (!currentProjectId.value) {
    $message.warning('请先选择项目')
    return
  }
  const valid = await moduleFormRef.value?.validate().catch(() => false)
  if (!valid) return
  moduleModalLoading.value = true
  try {
    if (editingModule.value) {
      await api.updateModule({
        id: editingModule.value.id,
        name: moduleForm.value.name,
        project_id: currentProjectId.value,
      })
      $message.success('模块已重命名')
    } else {
      await api.createModule({
        project_id: currentProjectId.value,
        name: moduleForm.value.name,
        parent_id: moduleForm.value.parent_id || 0,
      })
      $message.success('模块创建成功')
    }
    moduleModalVisible.value = false
    await loadModuleTree()
  } finally {
    moduleModalLoading.value = false
  }
}

// -- tree expand/collapse --
const treeExpanded = ref(false)

function collectNodeIds(nodes, ids) {
  for (const node of nodes) {
    ids.push(node.id)
    if (node.children?.length) collectNodeIds(node.children, ids)
  }
}

function toggleExpand() {
  if (treeExpanded.value) {
    expandedKeys.value = []
    treeExpanded.value = false
  } else {
    const ids = []
    collectNodeIds(moduleTreeData.value, ids)
    expandedKeys.value = ids
    treeExpanded.value = true
  }
}

function mergeCaseCounts(treeNodes, statsList) {
  const statMap = {}
  for (const s of statsList) {
    statMap[s.id] = s.case_count || 0
  }
  let total = 0
  function walk(nodes) {
    for (const node of nodes) {
      node.caseCount = statMap[node.id] || 0
      total += node.caseCount
      if (node.children?.length) walk(node.children)
    }
  }
  walk(treeNodes)
  return total
}

function removeEmptyChildren(nodes) {
  for (const node of nodes) {
    if (node.children && node.children.length === 0) {
      delete node.children
    } else if (node.children?.length) {
      removeEmptyChildren(node.children)
    }
  }
}

async function loadModuleTree() {
  if (!currentProjectId.value) return
  const res = await api.getModuleTree({ project_id: currentProjectId.value })
  moduleTreeRaw.value = res.data || []
  removeEmptyChildren(moduleTreeRaw.value)
  const statsRes = await api.getModuleStats({ project_id: currentProjectId.value })
  const statsData = statsRes.data || {}
  let statsList, unplannedCount
  if (Array.isArray(statsData)) {
    statsList = statsData
    unplannedCount = 0
  } else {
    statsList = statsData.modules || []
    unplannedCount = statsData.unplanned_count || 0
  }
  const total = mergeCaseCounts(moduleTreeRaw.value, statsList)
  totalCaseCount.value = total + unplannedCount
  recycleCount.value = 0
  moduleTreeData.value = [
    { id: 'unplanned', name: '未规划用例', caseCount: unplannedCount },
    ...moduleTreeRaw.value,
  ]
}

// -- recycle bin --
const recycleItems = ref([])
const recycleChecked = ref([])
const recycleColumns = [
  { type: 'selection', width: 40 },
  { title: 'ID', key: 'id', width: 80 },
  { title: '用例名称', key: 'name', ellipsis: { tooltip: true } },
  { title: '所属模块', key: 'module_name', width: 120, render: (row) => row.module_name || '-' },
  { title: '等级', key: 'level', width: 60 },
  {
    title: '删除时间',
    key: 'deleted_at',
    width: 160,
    render: (row) => (row.deleted_at ? new Date(row.deleted_at).toLocaleString() : '-'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row) =>
      h('span', { style: 'display: flex; gap: 4px' }, [
        h(
          NButton,
          { size: 'tiny', text: true, type: 'primary', onClick: () => onRestoreRow(row) },
          { default: () => '恢复' }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => onHardDeleteRow(row) },
          {
            trigger: () =>
              h(
                NButton,
                { size: 'tiny', text: true, type: 'error' },
                { default: () => '彻底删除' }
              ),
            default: () => '确认彻底删除？不可恢复！',
          }
        ),
      ]),
  },
]

async function loadRecycleBin() {
  if (!currentProjectId.value) return
  const res = await api.getRecycleBin({ project_id: currentProjectId.value })
  recycleItems.value = res.data || []
  recycleCount.value = recycleItems.value.length
  recycleChecked.value = []
}

function onRecycleChecked(keys) {
  recycleChecked.value = keys
}

async function onRestoreCases() {
  if (!recycleChecked.value.length) return
  await api.restoreTestCases({ ids: recycleChecked.value })
  $message.success('已恢复')
  loadRecycleBin()
  loadModuleTree()
  refreshCurrentTable()
}

async function onHardDeleteCases() {
  if (!recycleChecked.value.length) return
  window.$dialog?.warning({
    title: '确认彻底删除',
    content: `确定要彻底删除选中的 ${recycleChecked.value.length} 个用例吗？此操作不可恢复！`,
    positiveText: '彻底删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await api.hardDeleteTestCases({ ids: recycleChecked.value })
      $message.success('已彻底删除')
      loadRecycleBin()
    },
  })
}

async function onRestoreRow(row) {
  await api.restoreTestCases({ ids: [row.id] })
  $message.success('已恢复')
  loadRecycleBin()
  loadModuleTree()
  refreshCurrentTable()
}

async function onHardDeleteRow(row) {
  await api.hardDeleteTestCases({ ids: [row.id] })
  $message.success('已彻底删除')
  loadRecycleBin()
}

// init
onMounted(() => {
  if (route.query.tab === 'review') {
    activeTab.value = 'review'
  }
  if (route.query.case_id) {
    editCaseId.value = route.query.case_id
  }
  if (currentProjectId.value) {
    loadModuleTree()
    loadUsers()
    loadRecycleBin()
    nextTick(() => refreshCurrentTable())
  }
})

// Watch route changes
watch(
  () => route.query.case_id,
  (val) => {
    if (val) {
      editCaseId.value = val
    } else if (editCaseId.value) {
      editCaseId.value = null
    }
  }
)
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 8px;
}
.sidebar-search {
  margin: 0 12px 8px;
}
.tree-area {
  flex: 1;
  overflow-y: auto;
  padding: 0 4px;
}
.sidebar-footer {
  padding: 8px 12px 12px;
  border-top: 1px solid var(--n-border-color);
}
.recycle-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-color-2);
  transition: background 0.2s;
}
.recycle-item:hover {
  background: var(--n-color-hover);
}
.recycle-item.active {
  background: var(--n-color-selected);
  color: var(--primary-color);
}
:deep(.n-tree-node-content) {
  overflow: visible;
}
:deep(.n-tree) {
  overflow-x: visible !important;
}
:global(.tree-suffix-btn) {
  cursor: pointer;
  color: var(--n-text-color-3);
  font-size: 14px;
  margin-left: 4px;
  padding: 0 4px;
  border-radius: 2px;
  opacity: 0;
  transition: background 0.15s, color 0.15s, opacity 0.15s;
  white-space: nowrap;
}
:deep(.n-tree-node-content:hover .tree-suffix-btn) {
  opacity: 1;
}
:global(.tree-suffix-btn:hover) {
  color: var(--primary-color);
  background: var(--n-color-hover);
  opacity: 1;
}
.mindmap-wrapper {
  height: 100%;
  min-height: 500px;
}
</style>
