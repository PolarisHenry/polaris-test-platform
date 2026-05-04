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
          placeholder="通过名称搜索"
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
        <n-select
          v-model:value="queryItems.filter"
          placeholder="视图筛选"
          clearable
          :options="filterOptions"
          style="width: 150px"
          @update:value="onFilterChange"
        />
      </template>

      <template #actions>
        <n-button v-permission="'post/api/v1/review/create'" type="primary" @click="handleAdd">
          <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
          创建用例评审
        </n-button>
      </template>
    </crud-table>

    <!-- 创建/编辑评审计划弹窗 -->
    <n-modal
      v-model:show="modalVisible"
      :title="modalTitle"
      preset="card"
      style="width: 800px"
      :mask-closable="false"
    >
      <n-form
        ref="modalFormRef"
        :model="planForm"
        :rules="planRules"
        label-placement="left"
        label-width="100"
      >
        <n-form-item label="评审名称" path="name">
          <n-input v-model:value="planForm.name" placeholder="如: v1.0 版本用例评审" />
        </n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-grid-item>
            <n-form-item label="评审模式" path="review_mode">
              <n-select v-model:value="planForm.review_mode" :options="reviewModeOptions" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="评审周期(起)">
              <n-date-picker v-model:value="planForm.start_time" type="datetime" clearable />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-grid :cols="2" :x-gap="12">
          <n-grid-item>
            <n-form-item label="评审人" path="reviewer_ids">
              <n-select
                v-model:value="planForm.reviewer_ids"
                multiple
                :options="userOptions"
                placeholder="选择参与评审的成员"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="评审周期(止)">
              <n-date-picker v-model:value="planForm.end_time" type="datetime" clearable />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="planForm.tags" />
        </n-form-item>
        <n-form-item label="关联用例">
          <n-space vertical :size="8" style="width: 100%">
            <n-transfer v-model:value="planForm.case_ids" :options="caseTransferOptions" />
          </n-space>
        </n-form-item>
        <n-form-item label="评审描述">
          <n-input v-model:value="planForm.desc" type="textarea" placeholder="评审计划说明" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div flex justify-end>
          <n-button @click="modalVisible = false">取消</n-button
          ><n-button ml-12 type="primary" :loading="modalLoading" @click="doSave">提交</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 评审执行弹窗 -->
    <n-modal
      v-model:show="reviewVisible"
      title="评审执行"
      preset="card"
      style="width: 1000px"
      :mask-closable="false"
    >
      <div v-if="reviewData.progress" mb-16>
        <n-progress
          type="line"
          :percentage="reviewData.progress.percent"
          :indicator-text="`${
            reviewData.progress.pass_count +
            reviewData.progress.unpass_count +
            reviewData.progress.suggest +
            reviewData.progress.resubmit
          }/${reviewData.progress.total}`"
          :height="24"
          :color="reviewData.progress.percent === 100 ? '#18a058' : '#2080f0'"
        />
        <div mt-8 flex justify-center gap-24>
          <span style="color: #18a058">通过 {{ reviewData.progress.pass_count }}</span>
          <span style="color: #d03050">不通过 {{ reviewData.progress.unpass_count }}</span>
          <span style="color: #f0a020">建议 {{ reviewData.progress.suggest }}</span>
          <span style="color: #999">未评审 {{ reviewData.progress.unreviewed }}</span>
        </div>
      </div>

      <n-table>
        <thead>
          <tr>
            <th>用例名称</th>
            <th style="width: 150px">评审结果</th>
            <th style="width: 120px">评审人</th>
            <th style="width: 160px">评审时间</th>
            <th style="width: 100px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in reviewData.cases" :key="item.id">
            <td>
              <n-button text type="primary" @click="openCaseDetail(item)">{{
                item.case_name
              }}</n-button>
            </td>
            <td>
              <n-select
                :value="item.review_result"
                size="small"
                :options="reviewResultOptions"
                @update:value="(v) => onSubmitReview(item.id, v)"
              />
            </td>
            <td>{{ item.reviewer_name || '-' }}</td>
            <td>{{ item.reviewed_at ? new Date(item.reviewed_at).toLocaleString() : '-' }}</td>
            <td>
              <n-checkbox
                v-if="reviewData.cases.indexOf(item) < reviewData.cases.length - 1"
                v-model:checked="autoNext"
                >自动下一条</n-checkbox
              >
            </td>
          </tr>
        </tbody>
      </n-table>

      <template #footer>
        <div flex justify-between>
          <div>
            <n-button
              v-if="currentReviewPlanStatus === 'in_progress'"
              type="success"
              @click="onCompleteReview"
              >标记完成</n-button
            >
            <n-button
              v-if="currentReviewPlanStatus === 'in_progress'"
              ml-8
              type="warning"
              @click="onCancelReview"
              >取消评审</n-button
            >
          </div>
          <n-button @click="reviewVisible = false">关闭</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 用例详情预览 -->
    <n-modal v-model:show="caseDetailVisible" title="用例详情" preset="card" style="width: 700px">
      <div v-if="caseDetail">
        <n-descriptions label-placement="left" :column="2" bordered>
          <n-descriptions-item label="用例名称">{{ caseDetail.name }}</n-descriptions-item>
          <n-descriptions-item label="用例等级">{{ caseDetail.level }}</n-descriptions-item>
          <n-descriptions-item label="前置条件" :span="2">{{
            caseDetail.precondition || '-'
          }}</n-descriptions-item>
          <n-descriptions-item label="标签" :span="2">
            <n-tag v-for="t in caseDetail.tags || []" :key="t" size="small" ml-4>{{ t }}</n-tag>
          </n-descriptions-item>
        </n-descriptions>
        <n-divider>测试步骤</n-divider>
        <n-table>
          <thead>
            <tr>
              <th>#</th>
              <th>步骤描述</th>
              <th>预期结果</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="step in caseDetail.steps || []" :key="step.id">
              <td>{{ step.step_number }}</td>
              <td>{{ step.action }}</td>
              <td>{{ step.expected_result }}</td>
            </tr>
          </tbody>
        </n-table>
      </div>
      <template #footer><n-button @click="caseDetailVisible = false">关闭</n-button></template>
    </n-modal>
  </common-page>
</template>

<script setup>
import { h } from 'vue'
import { NButton, NTag, NPopconfirm, NCheckbox } from 'naive-ui'
import CrudTable from '@/components/table/CrudTable.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'

const projectStore = useProjectStore()
const currentProjectId = computed(() => projectStore.currentProjectId)
const $table = ref(null)
const queryItems = ref({})

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
const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '我创建的', value: 'my_create' },
  { label: '我评审的', value: 'my_review' },
]
const reviewModeOptions = [
  { label: '单人评审', value: 'single' },
  { label: '多人评审', value: 'multi' },
]
const reviewResultOptions = [
  { label: '未评审', value: null },
  { label: '通过', value: 'pass' },
  { label: '不通过', value: 'fail' },
  { label: '建议', value: 'suggest' },
  { label: '重新提审', value: 'resubmit' },
]

const columns = [
  { title: 'ID', key: 'id', width: 70 },
  { title: '评审名称', key: 'name', ellipsis: { tooltip: true } },
  {
    title: '评审模式',
    key: 'review_mode',
    width: 90,
    render: (row) => (row.review_mode === 'multi' ? '多人' : '单人'),
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) =>
      h(
        NTag,
        { type: planStatusColorMap[row.status] || 'default', size: 'small', bordered: false },
        { default: () => planStatusLabelMap[row.status] || row.status }
      ),
  },
  { title: '创建人', key: 'creator_id', width: 80 },
  { title: '开始时间', key: 'start_time', width: 150 },
  { title: '结束时间', key: 'end_time', width: 150 },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    render: (row) =>
      h('span', { style: 'display: flex; align-items: center; gap: 2px;' }, [
        h(
          NButton,
          { size: 'tiny', text: true, type: 'primary', onClick: () => handleEdit(row) },
          { default: () => '编辑' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        h(
          NButton,
          { size: 'tiny', text: true, type: 'info', onClick: () => openReviewExecution(row) },
          { default: () => '评审' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        h(
          NButton,
          { size: 'tiny', text: true, type: 'success', onClick: () => onCopyPlan(row) },
          { default: () => '复制' }
        ),
        h('span', { style: 'color: var(--n-text-color-3)' }, '|'),
        row.status === 'draft'
          ? h(
              NButton,
              { size: 'tiny', text: true, type: 'info', onClick: () => onStartPlan(row) },
              { default: () => '开始' }
            )
          : row.status === 'in_progress'
          ? h(
              NButton,
              {
                size: 'tiny',
                text: true,
                type: 'success',
                onClick: () => onCompletePlanDirect(row),
              },
              { default: () => '完成' }
            )
          : null,
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

const planRules = { name: [{ required: true, message: '请输入评审名称', trigger: 'blur' }] }

const modalVisible = ref(false)
const modalTitle = ref('创建用例评审')
const modalLoading = ref(false)
const modalFormRef = ref(null)
const planForm = ref({
  name: '',
  review_mode: 'single',
  reviewer_ids: [],
  case_ids: [],
  tags: [],
  desc: '',
  start_time: null,
  end_time: null,
})
const editId = ref(null)
const caseTransferOptions = ref([])
const userOptions = ref([])

async function loadCaseOptions() {
  if (!currentProjectId.value) return
  const res = await api.getTestCaseList({ project_id: currentProjectId.value, page_size: 9999 })
  caseTransferOptions.value = (res.data || []).map((c) => ({
    label: `[${c.level}] ${c.name}`,
    value: c.id,
  }))
}
async function loadUserOptions() {
  const res = await api.getUserList({ page_size: 9999 })
  userOptions.value = (res.data || []).map((u) => ({ label: u.username || u.email, value: u.id }))
}

function handleAdd() {
  editId.value = null
  modalTitle.value = '创建用例评审'
  planForm.value = {
    name: '',
    review_mode: 'single',
    reviewer_ids: [],
    case_ids: [],
    tags: [],
    desc: '',
    start_time: null,
    end_time: null,
  }
  modalVisible.value = true
}
function handleEdit(row) {
  editId.value = row.id
  modalTitle.value = '编辑用例评审'
  planForm.value = {
    name: row.name,
    review_mode: row.review_mode || 'single',
    reviewer_ids: (row.reviewers || []).map((r) => r.user_id || r.id),
    case_ids: row.case_ids || [],
    tags: row.tags || [],
    desc: row.desc || '',
    start_time: row.start_time ? new Date(row.start_time).getTime() : null,
    end_time: row.end_time ? new Date(row.end_time).getTime() : null,
  }
  modalVisible.value = true
}
async function doSave() {
  const valid = await modalFormRef.value?.validate().catch(() => false)
  if (!valid) return
  modalLoading.value = true
  try {
    const data = {
      name: planForm.value.name,
      review_mode: planForm.value.review_mode,
      project_id: currentProjectId.value,
      reviewer_ids: planForm.value.reviewer_ids,
      case_ids: planForm.value.case_ids,
      tags: planForm.value.tags,
      desc: planForm.value.desc,
      start_time: planForm.value.start_time
        ? new Date(planForm.value.start_time).toISOString()
        : null,
      end_time: planForm.value.end_time ? new Date(planForm.value.end_time).toISOString() : null,
    }
    if (editId.value) {
      await api.updateReviewPlan({ id: editId.value, ...data })
    } else {
      await api.createReviewPlan(data)
    }
    $message.success(editId.value ? '更新成功' : '创建成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    modalLoading.value = false
  }
}
async function handleDelete(params) {
  await api.deleteReviewPlan(params)
  $message.success('删除成功')
  $table.value?.handleSearch()
}
async function onStartPlan(row) {
  await api.startReview({ plan_id: row.id })
  $message.success('评审已开始')
  $table.value?.handleSearch()
}
async function onCompletePlanDirect(row) {
  await api.completeReview({ plan_id: row.id })
  $message.success('评审已完成')
  $table.value?.handleSearch()
}
async function onCopyPlan(row) {
  await api.copyReviewPlan({ plan_id: row.id })
  $message.success('已复制评审计划')
  $table.value?.handleSearch()
}

// -- 评审执行 --
const reviewVisible = ref(false)
const reviewData = ref({ cases: [], progress: null })
const currentReviewPlanId = ref(null)
const currentReviewPlanStatus = ref('')
const autoNext = ref(false)

async function openReviewExecution(row) {
  if (row.status === 'draft') {
    await api.startReview({ plan_id: row.id })
  }
  currentReviewPlanId.value = row.id
  currentReviewPlanStatus.value = row.status === 'draft' ? 'in_progress' : row.status
  const res = await api.getReviewCaseResults({ plan_id: row.id })
  reviewData.value = res.data || { cases: [], progress: null }
  reviewVisible.value = true
}
async function onSubmitReview(planCaseId, result) {
  if (!result) return
  await api.submitReviewResult({ plan_case_id: planCaseId, review_result: result })
  const item = reviewData.value.cases.find((c) => c.id === planCaseId)
  if (item) {
    item.review_result = result
    if (!item.reviewed_at) item.reviewed_at = new Date().toISOString()
  }
  // 重新加载进度
  const res = await api.getReviewCaseResults({ plan_id: currentReviewPlanId.value })
  reviewData.value = res.data || { cases: [], progress: null }
  $message.success('评审结果已提交')
  if (autoNext.value) {
    const idx = reviewData.value.cases.findIndex((c) => c.id === planCaseId)
    if (idx < reviewData.value.cases.length - 1 && !reviewData.value.cases[idx + 1].review_result) {
      // auto-next is handled by the user seeing the next row
    }
  }
}
async function onCompleteReview() {
  await api.completeReview({ plan_id: currentReviewPlanId.value })
  $message.success('评审已完成')
  reviewVisible.value = false
  $table.value?.handleSearch()
}
async function onCancelReview() {
  await api.cancelReview({ plan_id: currentReviewPlanId.value })
  $message.success('评审已取消')
  reviewVisible.value = false
  $table.value?.handleSearch()
}

// -- 用例详情 --
const caseDetailVisible = ref(false)
const caseDetail = ref(null)
async function openCaseDetail(item) {
  const res = await api.getTestCase({ case_id: item.case_id })
  caseDetail.value = res.data
  caseDetailVisible.value = true
}

async function fetchPlans(params) {
  params.project_id = currentProjectId.value
  if (queryItems.value.filter === 'my_create') {
    params.my_create = true
  } else if (queryItems.value.filter === 'my_review') {
    params.my_review = true
  }
  const res = await api.getReviewPlanList(params)
  return { data: res.data, total: res.total }
}
function onProjectChange() {
  $table.value?.handleSearch()
  loadCaseOptions()
}
function onFilterChange(val) {
  queryItems.value.my_review = val === 'my_review'
  queryItems.value.my_create = val === 'my_create'
  $table.value?.handleSearch()
}

onMounted(() => {
  if (currentProjectId.value) {
    loadCaseOptions()
    nextTick(() => $table.value?.handleSearch())
  }
  loadUserOptions()
})
</script>
