<template>
  <common-page :show-header="false">
    <crud-table
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="fetchPlans"
      :extra-params="{ project_id: currentProjectId }"
    >
      <template #queryBar>
        <project-selector style="width: 200px" @change="onProjectChange" />
        <n-input
          v-model:value="queryItems.name"
          placeholder="通过 ID/名称搜索"
          clearable
          style="width: 220px"
        />
        <n-select
          v-model:value="queryItems.status"
          placeholder="状态"
          clearable
          :options="statusOptions"
          style="width: 130px"
        />
      </template>

      <template #actions>
        <n-button v-permission="'post/api/v1/testplan/create'" type="primary" @click="handleAdd">
          <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
          新建计划
        </n-button>
      </template>
    </crud-table>

    <crud-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      width="700px"
      @save="doSave"
    >
      <n-form
        ref="modalFormRef"
        :model="planForm"
        :rules="planRules"
        label-placement="left"
        label-width="100"
      >
        <n-alert type="info" mb-16 size="small" :bordered="false">
          创建后可在「执行」中逐条记录功能用例步骤结果；通过率 = 已通过用例数 /
          关联用例总数（见《功能细节交互》3.3、3.5）。
        </n-alert>
        <n-form-item label="计划名称" path="name">
          <n-input v-model:value="planForm.name" placeholder="请输入计划名称" />
        </n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-grid-item>
            <n-form-item label="开始时间">
              <n-date-picker v-model:value="planForm.start_time" type="datetime" clearable />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="结束时间">
              <n-date-picker v-model:value="planForm.end_time" type="datetime" clearable />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-form-item label="关联用例">
          <n-space vertical :size="8" style="width: 100%">
            <n-transfer v-model:value="planForm.case_ids" :options="caseTransferOptions" />
            <n-text depth="3" style="font-size: 12px">
              支持多选关联；与《功能细节交互》3.2 中「按模块树、用例 ID、名称筛选并批量选择」一致。
            </n-text>
          </n-space>
        </n-form-item>
        <n-form-item label="计划描述">
          <n-input v-model:value="planForm.desc" type="textarea" placeholder="请输入计划描述" />
        </n-form-item>
      </n-form>
    </crud-modal>

    <!-- 执行结果列表 -->
    <n-modal
      v-model:show="execVisible"
      title="执行结果"
      preset="card"
      style="width: 950px"
      :mask-closable="false"
    >
      <n-alert type="warning" mb-12 size="small" :bordered="false">
        点击用例名称进入逐步执行模式；步骤执行失败时可点击「创建缺陷」快速登记。
      </n-alert>
      <div v-if="execData.progress" mb-16>
        <n-progress
          type="line"
          :percentage="execData.progress.percent"
          :indicator-text="`${
            execData.progress.success +
            execData.progress.fail +
            execData.progress.blocked +
            (execData.progress.skipped || 0)
          }/${execData.progress.total}`"
          :height="24"
          :color="execData.progress.percent === 100 ? '#18a058' : '#2080f0'"
        />
        <div mt-8 flex justify-center gap-24>
          <span style="color: #18a058">通过 {{ execData.progress.success }}</span>
          <span style="color: #d03050">失败 {{ execData.progress.fail }}</span>
          <span style="color: #f0a020">阻塞 {{ execData.progress.blocked }}</span>
          <span style="color: #909399">跳过 {{ execData.progress.skipped || 0 }}</span>
          <span style="color: #999">待执行 {{ execData.progress.pending }}</span>
        </div>
      </div>

      <n-table mt-16>
        <thead>
          <tr>
            <th style="width: 42px">
              <n-checkbox
                :checked="allExecChecked"
                :indeterminate="execChecked.length > 0 && !allExecChecked"
                @update:checked="toggleAllExecChecked"
              />
            </th>
            <th>用例名称</th>
            <th style="width: 120px">执行结果</th>
            <th style="width: 160px">执行时间</th>
            <th style="width: 180px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in execData.cases" :key="item.id">
            <td>
              <n-checkbox
                :checked="execChecked.includes(item.id)"
                @update:checked="(checked) => toggleExecChecked(item.id, checked)"
              />
            </td>
            <td>
              <n-button text type="primary" @click="openManualExec(item)">{{
                item.case_name
              }}</n-button>
            </td>
            <td>
              <n-select
                :value="item.exec_result"
                size="small"
                :options="execResultOptions"
                @update:value="(v) => onUpdateResult(item.id, v)"
              />
            </td>
            <td>{{ item.executed_at ? new Date(item.executed_at).toLocaleString() : '-' }}</td>
            <td>
              <n-space>
                <n-button
                  v-if="item.exec_result === 'fail'"
                  size="tiny"
                  type="error"
                  @click="onCreateDefect(item)"
                  >创建缺陷</n-button
                >
                <n-button size="tiny" @click="openManualExec(item)">逐步执行</n-button>
              </n-space>
            </td>
          </tr>
        </tbody>
      </n-table>

      <template #footer>
        <div flex justify-between>
          <div>
            <n-button
              :disabled="execChecked.length === 0"
              type="primary"
              secondary
              @click="onBatchExecuteCases"
            >
              批量执行
            </n-button>
            <n-popconfirm @positive-click="onBatchUnlinkCases">
              <template #trigger>
                <n-button ml-8 :disabled="execChecked.length === 0" type="error" secondary>
                  批量取消关联
                </n-button>
              </template>
              确认从当前计划中移除选中的用例吗？
            </n-popconfirm>
            <n-select
              v-model:value="batchExecutorId"
              :disabled="execChecked.length === 0"
              :options="userOptions"
              clearable
              filterable
              size="small"
              placeholder="批量更换执行人"
              style="width: 160px; margin-left: 8px"
              @update:value="onBatchChangeExecutor"
            />
            <n-button
              v-if="currentExecPlanStatus === 'in_progress'"
              ml-8
              type="success"
              @click="onCompletePlan"
              >标记完成</n-button
            >
            <n-button
              v-if="currentExecPlanStatus === 'in_progress'"
              ml-8
              type="warning"
              @click="onCancelPlan"
              >取消计划</n-button
            >
            <n-button ml-8 @click="openReport">查看报告</n-button>
          </div>
          <n-button @click="execVisible = false">关闭</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 手动逐步执行 -->
    <n-modal
      v-model:show="manualExecVisible"
      title="手动执行"
      preset="card"
      style="width: 800px"
      :mask-closable="false"
    >
      <n-descriptions v-if="manualExecCase" label-placement="left" :column="2" bordered mb-16>
        <n-descriptions-item label="用例名称">{{ manualExecCase.case_name }}</n-descriptions-item>
        <n-descriptions-item label="用例等级">{{ manualExecCase.level }}</n-descriptions-item>
        <n-descriptions-item label="前置条件" :span="2">{{
          manualExecCase.precondition || '-'
        }}</n-descriptions-item>
      </n-descriptions>

      <n-alert v-if="manualExecSteps.length === 0" type="info" mb-12
        >该用例无测试步骤，可直接设置执行结果。</n-alert
      >

      <n-table v-if="manualExecSteps.length > 0">
        <thead>
          <tr>
            <th style="width: 50px">#</th>
            <th>测试步骤</th>
            <th>预期结果</th>
            <th style="width: 160px">实际结果</th>
            <th style="width: 100px">步骤结果</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="step in manualExecSteps" :key="step.step_number">
            <td>{{ step.step_number }}</td>
            <td>{{ step.action }}</td>
            <td>{{ step.expected_result }}</td>
            <td>
              <n-input
                v-model:value="step.actual_result"
                size="small"
                type="textarea"
                placeholder="输入实际结果"
              />
            </td>
            <td>
              <n-select
                v-model:value="step.step_exec_result"
                size="small"
                :options="stepResultOptions"
              />
            </td>
          </tr>
        </tbody>
      </n-table>

      <n-form-item label="整体执行结果" mt-16>
        <n-select
          v-model:value="manualExecResult"
          :options="execResultOptions"
          style="width: 160px"
        />
      </n-form-item>
      <n-form-item label="备注">
        <n-input
          v-model:value="manualExecComment"
          type="textarea"
          placeholder="执行备注或缺陷说明"
        />
      </n-form-item>

      <template #footer>
        <div flex justify-between>
          <n-button type="error" size="small" @click="onCreateDefectFromManualExec"
            >创建缺陷</n-button
          >
          <div>
            <n-button @click="manualExecVisible = false">取消</n-button>
            <n-button
              ml-12
              type="primary"
              :loading="manualExecSubmitting"
              @click="doSubmitManualExec"
              >提交结果</n-button
            >
          </div>
        </div>
      </template>
    </n-modal>

    <!-- 测试报告 -->
    <n-modal
      v-model:show="reportVisible"
      title="测试报告"
      preset="card"
      style="width: 900px"
      :mask-closable="false"
    >
      <div v-if="reportData">
        <n-descriptions label-placement="left" :column="3" bordered mb-16>
          <n-descriptions-item label="计划名称">{{ reportData.plan_name }}</n-descriptions-item>
          <n-descriptions-item label="通过率">{{ reportData.pass_rate }}%</n-descriptions-item>
          <n-descriptions-item label="完成率"
            >{{ reportData.completion_rate }}%</n-descriptions-item
          >
          <n-descriptions-item label="总用例">{{ reportData.total_cases }}</n-descriptions-item>
          <n-descriptions-item label="通过">{{ reportData.passed }}</n-descriptions-item>
          <n-descriptions-item label="失败">{{ reportData.failed }}</n-descriptions-item>
          <n-descriptions-item label="阻塞">{{ reportData.blocked }}</n-descriptions-item>
          <n-descriptions-item label="跳过">{{ reportData.skipped || 0 }}</n-descriptions-item>
          <n-descriptions-item label="待执行">{{ reportData.pending }}</n-descriptions-item>
          <n-descriptions-item label="缺陷数">{{ reportData.defect_count }}</n-descriptions-item>
        </n-descriptions>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="exportReportHtml">导出 HTML</n-button>
          <n-button @click="copyReportShareLink">分享链接</n-button>
          <n-button @click="reportVisible = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="defectVisible"
      title="创建缺陷"
      preset="card"
      style="width: 500px"
      :mask-closable="false"
    >
      <n-form
        ref="defectFormRef"
        :model="defectForm"
        :rules="defectRules"
        label-placement="left"
        label-width="100"
      >
        <n-form-item label="缺陷名称" path="name">
          <n-input v-model:value="defectForm.name" placeholder="请输入缺陷名称" />
        </n-form-item>
        <n-form-item label="严重程度">
          <n-select v-model:value="defectForm.severity" :options="severityOpts" />
        </n-form-item>
        <n-form-item label="关联用例">
          <n-input :value="defectForm.case_name" disabled />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end>
          <n-button @click="defectVisible = false">取消</n-button>
          <n-button ml-12 type="primary" :loading="defectSubmitting" @click="doCreateDefect"
            >创建</n-button
          >
        </div>
      </template>
    </n-modal>
  </common-page>
</template>

<script setup>
import { NButton, NTag, NPopconfirm, NProgress } from 'naive-ui'
import { useCRUD } from '@/composables'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const currentProjectId = computed(() => projectStore.currentProjectId)
const $table = ref(null)
const queryItems = ref({})
const caseTransferOptions = ref([])
const userOptions = ref([])
const planForm = ref({ name: '', start_time: null, end_time: null, desc: '', case_ids: [] })

const planStatusColorMap = {
  draft: 'default',
  in_progress: 'info',
  completed: 'success',
  cancelled: 'warning',
}
const planStatusLabelMap = {
  draft: '草稿',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

const execResultOptions = [
  { label: '待执行', value: 'pending' },
  { label: '通过', value: 'success' },
  { label: '失败', value: 'fail' },
  { label: '阻塞', value: 'blocked' },
  { label: '跳过', value: 'skipped' },
]

const severityOpts = [
  { label: '提示', value: 'trivial' },
  { label: '次要', value: 'minor' },
  { label: '严重', value: 'major' },
  { label: '致命', value: 'critical' },
]

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '计划名称', key: 'name', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: (row) =>
      h(
        NTag,
        { type: planStatusColorMap[row.status] || 'default', size: 'small', bordered: false },
        { default: () => planStatusLabelMap[row.status] || row.status }
      ),
  },
  {
    title: '进度',
    key: 'progress',
    width: 180,
    render: (row) =>
      h(NProgress, {
        type: 'line',
        percentage: row.progress?.completion_rate || 0,
        height: 12,
        indicatorPlacement: 'inside',
        processing: row.status === 'in_progress',
      }),
  },
  {
    title: '通过率',
    key: 'pass_rate',
    width: 90,
    render: (row) => `${row.progress?.pass_rate ?? 0}%`,
  },
  {
    title: '创建人',
    key: 'creator_name',
    width: 100,
    render: (row) => row.creator_name || row.creator_id,
  },
  { title: '开始时间', key: 'start_time', width: 150 },
  { title: '结束时间', key: 'end_time', width: 150 },
  {
    title: '操作',
    key: 'actions',
    width: 200,
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
          { size: 'tiny', text: true, type: 'info', onClick: () => handleExecute(row) },
          { default: () => '执行' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        h(
          NButton,
          { size: 'tiny', text: true, onClick: () => openExecResults(row) },
          { default: () => '结果' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete({ plan_id: row.id }) },
          {
            trigger: () =>
              h(NButton, { size: 'tiny', text: true, type: 'error' }, { default: () => '删除' }),
            default: () => '确认删除?',
          }
        ),
      ]),
  },
]

const planRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  modalForm,
  modalFormRef,
  handleAdd: _handleAdd,
  handleEdit: _handleEdit,
  handleDelete,
  handleSave,
} = useCRUD({
  name: '计划',
  initForm: {},
  doCreate: (data) => api.createTestPlan({ ...data, project_id: currentProjectId.value }),
  doUpdate: (data) => api.updateTestPlan(data),
  doDelete: (params) => api.deleteTestPlan(params),
  refresh: () => $table.value?.handleSearch(),
})

function handleEdit(row) {
  _handleEdit(row)
  nextTick(() => {
    planForm.value = {
      name: modalForm.value.name || '',
      start_time: modalForm.value.start_time
        ? new Date(modalForm.value.start_time).getTime()
        : null,
      end_time: modalForm.value.end_time ? new Date(modalForm.value.end_time).getTime() : null,
      desc: modalForm.value.desc || '',
      case_ids: modalForm.value.case_ids || [],
    }
  })
}
function handleAdd() {
  _handleAdd()
  nextTick(() => {
    planForm.value = { name: '', start_time: null, end_time: null, desc: '', case_ids: [] }
  })
}

async function doSave() {
  Object.assign(modalForm.value, {
    name: planForm.value.name,
    start_time: planForm.value.start_time
      ? new Date(planForm.value.start_time).toISOString()
      : null,
    end_time: planForm.value.end_time ? new Date(planForm.value.end_time).toISOString() : null,
    desc: planForm.value.desc,
    case_ids: planForm.value.case_ids,
  })
  await handleSave()
}

async function handleExecute(row) {
  await api.executeTestPlan({ plan_id: row.id })
  $message.success('计划已开始执行')
  $table.value?.handleSearch()
}

async function fetchPlans(params) {
  params.project_id = currentProjectId.value
  const res = await api.getTestPlanList(params)
  return { data: res.data, total: res.total }
}

function onProjectChange(val) {
  if (val) {
    $table.value?.handleSearch()
    loadCaseOptions()
    loadUserOptions()
  }
}

async function loadCaseOptions() {
  const res = await api.getTestCaseList({ project_id: currentProjectId.value, page_size: 9999 })
  caseTransferOptions.value = (res.data || []).map((c) => ({
    label: `[${c.level}] ${c.name}`,
    value: c.id,
  }))
}

async function loadUserOptions() {
  const res = await api.getUserList({ page: 1, page_size: 9999 })
  userOptions.value = (res.data || []).map((u) => ({ label: u.username || u.email, value: u.id }))
}

onMounted(() => {
  if (currentProjectId.value) {
    loadCaseOptions()
    loadUserOptions()
    nextTick(() => $table.value?.handleSearch())
  }
  if (route.query.report_plan_id) {
    openReportById(route.query.report_plan_id)
  }
})

// -- execution results --
const execVisible = ref(false)
const execData = ref({ cases: [], progress: null })
const currentExecPlanId = ref(null)
const currentExecPlanStatus = ref('')
const execChecked = ref([])
const batchExecutorId = ref(null)
const allExecChecked = computed(
  () => execData.value.cases.length > 0 && execChecked.value.length === execData.value.cases.length
)

async function openExecResults(row) {
  currentExecPlanId.value = row.id
  currentExecPlanStatus.value = row.status
  const res = await api.getPlanCaseResults({ plan_id: row.id })
  execData.value = res.data || { cases: [], progress: null }
  execChecked.value = []
  execVisible.value = true
}

function toggleExecChecked(id, checked) {
  if (checked) {
    execChecked.value = Array.from(new Set([...execChecked.value, id]))
  } else {
    execChecked.value = execChecked.value.filter((item) => item !== id)
  }
}

function toggleAllExecChecked(checked) {
  execChecked.value = checked ? execData.value.cases.map((item) => item.id) : []
}

async function onUpdateResult(planCaseId, result) {
  await api.updatePlanCaseResult({ plan_case_id: planCaseId, exec_result: result })
  const item = execData.value.cases.find((c) => c.id === planCaseId)
  if (item) {
    item.exec_result = result
    if (!item.executed_at) item.executed_at = new Date().toISOString()
  }
  $message.success('执行结果已更新')
}

async function onCompletePlan() {
  await api.completeTestPlan({ plan_id: currentExecPlanId.value })
  $message.success('计划已完成')
  currentExecPlanStatus.value = 'completed'
  execVisible.value = false
  $table.value?.handleSearch()
}

async function onCancelPlan() {
  await api.cancelTestPlan({ plan_id: currentExecPlanId.value })
  $message.success('计划已取消')
  currentExecPlanStatus.value = 'cancelled'
  execVisible.value = false
  $table.value?.handleSearch()
}

async function refreshExecResults() {
  const res = await api.getPlanCaseResults({ plan_id: currentExecPlanId.value })
  execData.value = res.data || { cases: [], progress: null }
  execChecked.value = execChecked.value.filter((id) =>
    execData.value.cases.some((item) => item.id === id)
  )
}

async function onBatchExecuteCases() {
  if (!execChecked.value.length) return
  await api.batchExecutePlan({ ids: execChecked.value })
  $message.success('已触发批量执行')
  await refreshExecResults()
}

async function onBatchUnlinkCases() {
  if (!execChecked.value.length) return
  await api.batchUnlinkPlanCases({ plan_id: currentExecPlanId.value, ids: execChecked.value })
  $message.success('已取消关联')
  await refreshExecResults()
}

async function onBatchChangeExecutor(executorId) {
  if (!executorId || !execChecked.value.length) return
  await api.batchChangeExecutor({ ids: execChecked.value, executor_id: executorId })
  $message.success('执行人已更新')
  batchExecutorId.value = null
  await refreshExecResults()
}

// -- quick create defect --
const defectVisible = ref(false)
const defectSubmitting = ref(false)
const defectFormRef = ref(null)
const defectForm = ref({ name: '', severity: 'major', case_id: null, case_name: '', plan_id: null })
const defectRules = { name: [{ required: true, message: '请输入缺陷名称', trigger: 'blur' }] }

function onCreateDefect(item) {
  defectForm.value = {
    name: `[执行失败] ${item.case_name || ''}`,
    severity: 'major',
    case_id: item.case_id,
    case_name: item.case_name || '',
    plan_id: currentExecPlanId.value,
  }
  defectVisible.value = true
}

async function doCreateDefect() {
  const valid = await defectFormRef.value?.validate().catch(() => false)
  if (!valid) return
  defectSubmitting.value = true
  try {
    await api.createDefectFromFailure({
      plan_id: defectForm.value.plan_id,
      case_id: defectForm.value.case_id,
      name: defectForm.value.name,
    })
    $message.success('缺陷已创建')
    defectVisible.value = false
  } finally {
    defectSubmitting.value = false
  }
}

// -- 手动逐步执行 --
const manualExecVisible = ref(false)
const manualExecSubmitting = ref(false)
const manualExecCase = ref(null)
const manualExecSteps = ref([])
const manualExecResult = ref('pending')
const manualExecComment = ref('')
const manualExecPlanCaseId = ref(null)
const stepResultOptions = [
  { label: '待执行', value: 'pending' },
  { label: '通过', value: 'success' },
  { label: '失败', value: 'fail' },
  { label: '跳过', value: 'skipped' },
]

async function openManualExec(item) {
  manualExecPlanCaseId.value = item.id
  manualExecResult.value = item.exec_result || 'pending'
  manualExecComment.value = ''
  const res = await api.getTestCase({ case_id: item.case_id })
  manualExecCase.value = { ...res.data, case_name: item.case_name, level: res.data.level }
  manualExecSteps.value = (res.data.steps || []).map((s) => ({
    step_number: s.step_number,
    action: s.action,
    expected_result: s.expected_result,
    actual_result: '',
    step_exec_result: 'pending',
  }))
  // Try loading existing step results
  try {
    const detail = await api.getExecutionDetail({ plan_case_id: item.id })
    if (detail.data?.step_results?.length) {
      detail.data.step_results.forEach((sr) => {
        const step = manualExecSteps.value.find((s) => s.step_number === sr.step_number)
        if (step) {
          step.actual_result = sr.actual_result
          step.step_exec_result = sr.step_exec_result
        }
      })
    }
  } catch {
    // Existing step results are optional; keep the execution dialog usable if this endpoint is unavailable.
  }
  manualExecVisible.value = true
}

async function doSubmitManualExec() {
  manualExecSubmitting.value = true
  try {
    await api.submitManualExec({
      plan_case_id: manualExecPlanCaseId.value,
      exec_result: manualExecResult.value,
      step_results: manualExecSteps.value.map((s) => ({
        step_number: s.step_number,
        actual_result: s.actual_result,
        step_exec_result: s.step_exec_result,
      })),
      comment: manualExecComment.value,
    })
    $message.success('执行结果已提交')
    manualExecVisible.value = false
    // Refresh results if visible
    if (execVisible.value) {
      const res = await api.getPlanCaseResults({ plan_id: currentExecPlanId.value })
      execData.value = res.data || { cases: [], progress: null }
    }
  } finally {
    manualExecSubmitting.value = false
  }
}

function onCreateDefectFromManualExec() {
  defectForm.value = {
    name: `[执行失败] ${manualExecCase.value?.case_name || ''}`,
    severity: 'major',
    case_id: manualExecCase.value?.id || defectForm.value.case_id,
    case_name: manualExecCase.value?.case_name || '',
    plan_id: currentExecPlanId.value,
  }
  defectVisible.value = true
}

// -- 测试报告 --
const reportVisible = ref(false)
const reportData = ref(null)

async function openReport() {
  const res = await api.getTestReport({ plan_id: currentExecPlanId.value })
  reportData.value = res.data
  reportVisible.value = true
}

async function openReportById(planId) {
  currentExecPlanId.value = planId
  const res = await api.getTestReport({ plan_id: planId })
  reportData.value = res.data
  reportVisible.value = true
}

function exportReportHtml() {
  if (!reportData.value) return
  const html = `<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>${reportData.value.plan_name} - 测试报告</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:32px;color:#1f2329}table{border-collapse:collapse;width:100%;margin-top:16px}td,th{border:1px solid #e5e7eb;padding:8px;text-align:left}.metric{display:inline-block;margin:0 16px 12px 0}</style>
</head>
<body>
<h1>${reportData.value.plan_name} - 测试报告</h1>
<div class="metric">通过率：${reportData.value.pass_rate}%</div>
<div class="metric">完成率：${reportData.value.completion_rate}%</div>
<div class="metric">总用例：${reportData.value.total_cases}</div>
<div class="metric">缺陷数：${reportData.value.defect_count}</div>
<table><thead><tr><th>用例</th><th>结果</th><th>执行时间</th></tr></thead><tbody>
${(reportData.value.case_details || [])
  .map(
    (item) =>
      `<tr><td>${item.case_name || '-'}</td><td>${item.exec_result}</td><td>${
        item.executed_at || '-'
      }</td></tr>`
  )
  .join('')}
</tbody></table>
</body></html>`
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${reportData.value.plan_name || '测试报告'}.html`
  link.click()
  URL.revokeObjectURL(url)
}

async function copyReportShareLink() {
  if (!reportData.value) return
  const href = router.resolve({
    path: '/testplatform/testplan',
    query: { report_plan_id: reportData.value.plan_id },
  }).href
  await navigator.clipboard?.writeText(`${window.location.origin}${href}`)
  $message.success('报告分享链接已复制')
}
</script>
