<template>
  <common-page :show-header="false">
    <n-tabs v-model:value="activeTab" mb-12 @update:value="onTabChange">
      <n-tab-pane name="all" tab="全部文件" />
      <n-tab-pane name="common" tab="普通文件" />
      <n-tab-pane name="test_case" tab="用例附件" />
      <n-tab-pane name="defect" tab="缺陷附件" />
      <n-tab-pane name="template" tab="模板文件" />
    </n-tabs>

    <crud-table
      ref="$table"
      :columns="columns"
      :get-data="fetchFiles"
      :extra-params="{
        project_id: currentProjectId,
        category: activeTab === 'all' ? '' : activeTab,
      }"
    >
      <template #queryBar>
        <project-selector style="width: 200px" @change="onProjectChange" />
      </template>

      <template #actions>
        <n-upload :custom-request="handleUpload" :show-file-list="false" accept="*">
          <n-button type="primary">
            <template #icon><the-icon icon="material-symbols:cloud-upload" :size="18" /></template>
            上传文件
          </n-button>
        </n-upload>
      </template>
    </crud-table>
  </common-page>
</template>

<script setup>
import { NButton } from 'naive-ui'
import CrudTable from '@/components/table/CrudTable.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'

const projectStore = useProjectStore()
const currentProjectId = computed(() => projectStore.currentProjectId)
const $table = ref(null)
const activeTab = ref('all')

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '文件名', key: 'name', ellipsis: { tooltip: true } },
  { title: '大小', key: 'size', width: 100, render: (row) => formatSize(row.size) },
  { title: '类型', key: 'file_type', width: 100 },
  { title: '分类', key: 'category', width: 100 },
  { title: '上传时间', key: 'created_at', width: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row) =>
      h('div', [
        h(NButton, { size: 'tiny', onClick: () => handleDownload(row) }, { default: () => '下载' }),
        h(
          NButton,
          {
            size: 'tiny',
            type: 'error',
            style: 'margin-left: 4px',
            onClick: () => handleDelete(row),
          },
          { default: () => '删除' }
        ),
      ]),
  },
]

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

async function handleUpload({ file }) {
  const formData = new FormData()
  formData.append('file', file.file)
  formData.append('category', activeTab.value === 'all' ? 'common' : activeTab.value)
  formData.append('project_id', currentProjectId.value || '')
  await api.uploadFile(formData)
  $message.success('上传成功')
  $table.value?.handleSearch()
}

function handleDownload(row) {
  window.open(`/api/v1/file/download?file_id=${row.id}`, '_blank')
}

async function handleDelete(row) {
  await api.deleteFile({ file_id: row.id })
  $message.success('删除成功')
  $table.value?.handleSearch()
}

async function fetchFiles(params) {
  params.project_id = currentProjectId.value
  if (activeTab.value !== 'all') params.category = activeTab.value
  const res = await api.getFileList(params)
  return { data: res.data, total: res.total }
}

function onProjectChange(val) {
  if (val) $table.value?.handleSearch()
}

function onTabChange() {
  $table.value?.handleSearch()
}
</script>
