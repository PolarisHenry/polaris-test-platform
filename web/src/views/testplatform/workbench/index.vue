<template>
  <common-page>
    <template #action>
      <n-space align="center">
        <n-radio-group v-model:value="timeRange" size="small" @update:value="loadData">
          <n-radio-button value="3d">近 3 天</n-radio-button>
          <n-radio-button value="7d">近 7 天</n-radio-button>
          <n-radio-button value="custom">自定义</n-radio-button>
        </n-radio-group>
        <project-selector style="width: 240px" @change="onProjectChange" />
      </n-space>
    </template>

    <div v-if="!projectId" class="empty-hint">
      <n-empty description="请先选择一个项目" />
    </div>

    <template v-else>
      <n-alert type="info" mb-16 size="small" :bordered="false" title="工作台说明">
        聚合当前项目下的用例、评审、计划与缺陷概况；与《功能细节交互》第五章「仪表盘 / 我的待办 /
        我创建的」一致。第三方集成与「我关注的」后续扩展。
      </n-alert>
      <n-grid :cols="4" :x-gap="16" mb-16>
        <n-grid-item>
          <n-card size="small" hoverable>
            <n-statistic label="功能用例数" :value="stats.case_count" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small" hoverable>
            <n-statistic label="已产生评审结果的用例数" :value="stats.review_count" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small" hoverable>
            <n-statistic label="测试计划数" :value="stats.plan_count" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small" hoverable>
            <n-statistic label="缺陷数" :value="stats.defect_count" />
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid :cols="2" :x-gap="16" mb-16>
        <n-grid-item>
          <n-card title="用例等级分布" size="small">
            <v-chart :option="caseLevelOption" style="height: 280px" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card title="缺陷严重程度分布" size="small">
            <v-chart :option="defectSeverityOption" style="height: 280px" />
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-card :title="`${timeRangeLabel}用例增长趋势`" size="small" mb-16>
        <v-chart :option="caseTrendOption" style="height: 260px" />
      </n-card>

      <n-card title="个人资产" size="small">
        <n-tabs v-model:value="activeTab" @update:value="onMyTabChange">
          <n-tab-pane name="created" tab="我创建的" />
          <n-tab-pane name="todos" tab="我的待办" />
          <n-tab-pane name="starred" tab="我关注的" />
        </n-tabs>
        <n-data-table
          :columns="activeTab === 'starred' ? followedColumns : myItemColumns"
          :data="myItems"
          :pagination="false"
          size="small"
        />
      </n-card>
    </template>
  </common-page>
</template>

<script setup>
import { computed, h, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { NButton } from 'naive-ui'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'

use([
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
])

const projectStore = useProjectStore()
const router = useRouter()
const projectId = computed(() => projectStore.currentProjectId)
const stats = ref({ case_count: 0, review_count: 0, plan_count: 0, defect_count: 0 })
const charts = ref({
  case_by_level: [],
  defect_by_status: [],
  case_by_week: [],
  defect_by_severity: [],
})
const activeTab = ref('created')
const myItems = ref([])
const timeRange = ref('7d')

const timeRangeLabelMap = {
  '3d': '近3天',
  '7d': '近7天',
  custom: '自定义时间',
}
const timeRangeLabel = computed(() => timeRangeLabelMap[timeRange.value] || '近7天')

const typeLabelMap = {
  plan: '测试计划',
  defect: '缺陷',
  case: '功能用例',
  case_review: '待评审用例',
}
const targetTypeLabel = {
  testcase: '功能用例',
  defect: '缺陷',
  plan: '测试计划',
  review_plan: '用例评审',
}

const myItemColumns = [
  { title: 'ID', key: 'id', width: 80 },
  {
    title: '名称',
    key: 'name',
    ellipsis: { tooltip: true },
    render: (row) =>
      h(
        NButton,
        { text: true, type: 'primary', onClick: () => openWorkbenchItem(row) },
        { default: () => row.name }
      ),
  },
  { title: '类型', key: 'type', width: 110, render: (row) => typeLabelMap[row.type] || row.type },
  { title: '状态', key: 'status', width: 120 },
]

const followedColumns = [
  { title: 'ID', key: 'target_id', width: 80 },
  {
    title: '名称',
    key: 'name',
    ellipsis: { tooltip: true },
    render: (row) =>
      h(
        NButton,
        { text: true, type: 'primary', onClick: () => openWorkbenchItem(row) },
        { default: () => row.name || '-' }
      ),
  },
  {
    title: '类型',
    key: 'target_type',
    width: 110,
    render: (row) => targetTypeLabel[row.target_type] || row.target_type,
  },
  { title: '状态', key: 'status', width: 120 },
  {
    title: '关注时间',
    key: 'created_at',
    width: 160,
    render: (row) => (row.created_at ? new Date(row.created_at).toLocaleString() : '-'),
  },
]

const caseLevelOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: charts.value.case_by_level.map((i) => i.label) },
  yAxis: { type: 'value' },
  series: [
    {
      data: charts.value.case_by_level.map((i) => i.value),
      type: 'bar',
      itemStyle: { color: '#2080f0' },
    },
  ],
}))

const defectSeverityOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      data: charts.value.defect_by_severity.map((i) => ({ name: i.label, value: i.value })),
    },
  ],
}))

const caseTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: charts.value.case_by_week.map((i) => i.label) },
  yAxis: { type: 'value' },
  series: [{ data: charts.value.case_by_week.map((i) => i.value), type: 'line', smooth: true }],
}))

async function loadData() {
  if (!projectId.value) return
  const [statsRes, chartsRes] = await Promise.all([
    api.getWorkbenchStats({ project_id: projectId.value }),
    api.getWorkbenchCharts({ project_id: projectId.value, time_range: timeRange.value }),
  ])
  stats.value = statsRes.data
  charts.value = chartsRes.data
  loadMyItems()
}

async function loadMyItems() {
  if (activeTab.value === 'starred') {
    const res = await api.getMyFollowed()
    myItems.value = res.data || []
    return
  }
  const res = await api.getMyItems({ project_id: projectId.value, tab: activeTab.value })
  myItems.value = res.data || []
}

function onMyTabChange() {
  loadMyItems()
}

function onProjectChange(val) {
  if (val) loadData()
}

function openWorkbenchItem(row) {
  const path =
    row.target_path ||
    {
      plan: '/testplatform/testplan',
      defect: '/testplatform/defect',
      case: `/testplatform/testcase?case_id=${row.id}`,
      case_review: `/testplatform/testcase?tab=review&case_id=${row.id}`,
      testcase: `/testplatform/testcase?case_id=${row.target_id}`,
      review_plan: '/testplatform/testcase?tab=review',
    }[row.type || row.target_type]
  if (path) router.push(path)
}

onMounted(() => {
  if (projectId.value) loadData()
})
</script>

<style scoped>
.empty-hint {
  padding: 60px 0;
}
</style>
