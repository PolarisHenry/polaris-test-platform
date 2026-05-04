<template>
  <common-page :show-header="false">
    <crud-table
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="fetchDefects"
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
          :options="statusOpts"
          style="width: 120px"
        />
        <n-select
          v-model:value="queryItems.severity"
          placeholder="严重程度"
          clearable
          :options="severityOpts"
          style="width: 130px"
        />
      </template>

      <template #actions>
        <n-button v-permission="'post/api/v1/defect/create'" type="primary" @click="handleAdd">
          <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
          创建缺陷
        </n-button>
      </template>
    </crud-table>

    <!-- 缺陷详情模态框 -->
    <n-modal
      v-model:show="detailVisible"
      title="缺陷详情"
      preset="card"
      style="width: 900px"
      :mask-closable="false"
    >
      <n-tabs v-model:value="detailTab" type="line">
        <n-tab-pane name="detail" tab="详情">
          <n-descriptions v-if="detailData" label-placement="left" :column="2" bordered>
            <n-descriptions-item label="缺陷名称" :span="2">{{
              detailData.name
            }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="statusColorMap[detailData.status]" size="small" bordered="false">{{
                statusLabelMap[detailData.status] || detailData.status
              }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="严重程度">
              <n-tag :type="severityColorMap[detailData.severity]" size="small" bordered="false">{{
                severityLabelMap[detailData.severity] || detailData.severity
              }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="处理人">{{
              detailData.handler_name || '-'
            }}</n-descriptions-item>
            <n-descriptions-item label="创建人">{{
              detailData.creator_name || '-'
            }}</n-descriptions-item>
            <n-descriptions-item label="创建时间">{{
              detailData.created_at ? new Date(detailData.created_at).toLocaleString() : '-'
            }}</n-descriptions-item>
            <n-descriptions-item label="所属平台">{{ 'Local' }}</n-descriptions-item>
            <n-descriptions-item label="缺陷内容" :span="2">
              <!-- eslint-disable-next-line vue/no-v-html -->
              <div v-html="detailData.content || '-'" />
            </n-descriptions-item>
          </n-descriptions>
          <div mt-12 flex justify-between>
            <n-button size="small" @click="toggleDefectFollow">
              <template #icon
                ><the-icon
                  :icon="defectFollowed ? 'material-symbols:star' : 'material-symbols:star-outline'"
                  :size="16"
              /></template>
              {{ defectFollowed ? '已关注' : '关注' }}
            </n-button>
            <n-button size="small" @click="copyDefectShareLink">
              <template #icon
                ><the-icon icon="material-symbols:share-outline" :size="16"
              /></template>
              分享
            </n-button>
          </div>
        </n-tab-pane>
        <n-tab-pane name="cases" tab="用例">
          <n-table v-if="detailData?.related_cases?.length">
            <thead>
              <tr>
                <th>用例ID</th>
                <th>用例名称</th>
                <th>等级</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in detailData.related_cases" :key="c.id">
                <td>{{ c.id }}</td>
                <td>{{ c.name }}</td>
                <td>{{ c.level }}</td>
              </tr>
            </tbody>
          </n-table>
          <n-empty v-else description="未关联用例" />
        </n-tab-pane>
        <n-tab-pane name="comments" tab="评论">
          <div mb-12>
            <n-input
              v-model:value="newComment"
              type="textarea"
              placeholder="添加评论..."
              :rows="2"
            />
            <n-button mt-8 size="small" type="primary" @click="doCreateComment">发表评论</n-button>
          </div>
          <n-divider />
          <div v-if="comments.length === 0"><n-empty description="暂无评论" /></div>
          <div v-for="c in comments" :key="c.id" mb-16>
            <div flex items-center gap-8>
              <span font-bold>{{ c.username }}</span>
              <span style="color: var(--n-text-color-3); font-size: 12px">{{
                c.created_at ? new Date(c.created_at).toLocaleString() : '-'
              }}</span>
              <n-button size="tiny" text type="error" @click="doDeleteComment(c.id)">删除</n-button>
            </div>
            <div ml-24 mt-4 style="white-space: pre-wrap">{{ c.content }}</div>
            <div v-if="c.replies?.length" ml-24 mt-8>
              <div
                v-for="r in c.replies"
                :key="r.id"
                mb-8
                style="background: var(--n-color-embedded); padding: 8px 12px; border-radius: 4px"
              >
                <span font-bold>{{ r.username }}</span>
                <span style="color: var(--n-text-color-3); font-size: 11px; margin-left: 8px">{{
                  r.created_at ? new Date(r.created_at).toLocaleString() : '-'
                }}</span>
                <n-button size="tiny" text type="error" ml-8 @click="doDeleteComment(r.id)"
                  >删除</n-button
                >
                <div mt-2>{{ r.content }}</div>
              </div>
            </div>
            <n-button
              v-if="c.replies?.length === 0 || !c.replies"
              size="tiny"
              text
              type="primary"
              ml-24
              @click="replyToComment(c)"
              >回复</n-button
            >
          </div>
        </n-tab-pane>
        <n-tab-pane name="history" tab="变更历史">
          <n-timeline v-if="changeHistories.length">
            <n-timeline-item
              v-for="item in changeHistories"
              :key="item.id"
              type="info"
              :title="`${item.field_name} 发生变更`"
              :time="item.changed_at ? new Date(item.changed_at).toLocaleString() : '-'"
            >
              <div class="history-content">
                <span>{{ item.changed_by_name || item.changed_by_id }}</span>
                <span>：</span>
                <span class="history-old">{{ item.old_value || '-' }}</span>
                <span> → </span>
                <span class="history-new">{{ item.new_value || '-' }}</span>
              </div>
            </n-timeline-item>
          </n-timeline>
          <n-empty v-else description="暂无变更历史" />
        </n-tab-pane>
      </n-tabs>
      <template #footer><n-button @click="detailVisible = false">关闭</n-button></template>
    </n-modal>

    <crud-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      width="800px"
      @save="doSave"
    >
      <div class="defect-form-layout">
        <div class="defect-form-main">
          <n-form ref="defectFormRef" :model="defectFormData" label-placement="top">
            <n-form-item
              label="缺陷名称"
              path="name"
              :rules="[{ required: true, message: '请输入缺陷名称' }]"
            >
              <n-input v-model:value="defectFormData.name" placeholder="请输入缺陷名称" />
            </n-form-item>
            <n-form-item label="缺陷内容">
              <rich-text-editor
                v-model="defectFormData.content"
                placeholder="请输入缺陷内容..."
                upload-category="defect"
                :project-id="currentProjectId"
              />
            </n-form-item>
            <n-form-item label="附件">
              <n-space vertical :size="8" style="width: 100%">
                <n-upload
                  :custom-request="handleDefectAttachmentUpload"
                  :show-file-list="false"
                  accept="*"
                >
                  <n-button size="small">
                    <template #icon>
                      <the-icon icon="material-symbols:add" :size="16" />
                    </template>
                    添加附件
                  </n-button>
                </n-upload>
                <div v-if="defectAttachments.length" class="attachment-list">
                  <div v-for="file in defectAttachments" :key="file.id" class="attachment-item">
                    <the-icon icon="material-symbols:attach-file" :size="15" />
                    <n-button text size="tiny" @click="downloadAttachment(file)">
                      {{ file.name }}
                    </n-button>
                  </div>
                </div>
              </n-space>
            </n-form-item>
          </n-form>
        </div>
        <div class="defect-form-sidebar">
          <n-form label-placement="top" size="small">
            <n-form-item label="严重程度">
              <n-select v-model:value="defectFormData.severity" :options="severityOpts" />
            </n-form-item>
            <n-form-item label="状态">
              <n-select v-model:value="defectFormData.status" :options="statusOpts" />
            </n-form-item>
            <n-form-item label="处理人">
              <n-select
                v-model:value="defectFormData.handler_id"
                :options="userOpts"
                placeholder="请选择"
                clearable
                filterable
              />
            </n-form-item>
            <n-form-item label="关联用例">
              <n-select
                v-model:value="defectFormData.related_case_ids"
                :options="caseOpts"
                multiple
                placeholder="选择关联用例"
                clearable
                filterable
              />
            </n-form-item>
          </n-form>
        </div>
      </div>
    </crud-modal>
  </common-page>
</template>

<script setup>
import { NButton, NTag, NPopconfirm } from 'naive-ui'
import { useCRUD } from '@/composables'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'
import RichTextEditor from '@/components/editor/RichTextEditor.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'

const projectStore = useProjectStore()
const route = useRoute()
const router = useRouter()
const currentProjectId = computed(() => projectStore.currentProjectId)
const $table = ref(null)
const queryItems = ref({})

const statusOpts = [
  { label: '新建', value: 'new' },
  { label: '处理中', value: 'processing' },
  { label: '已解决', value: 'resolved' },
  { label: '重新打开', value: 'reopened' },
  { label: '已关闭', value: 'closed' },
]
const severityOpts = [
  { label: '提示', value: 'trivial' },
  { label: '次要', value: 'minor' },
  { label: '严重', value: 'major' },
  { label: '致命', value: 'critical' },
]
const severityColorMap = { trivial: 'default', minor: 'warning', major: 'error', critical: 'error' }
const statusColorMap = {
  new: 'info',
  processing: 'warning',
  resolved: 'success',
  reopened: 'warning',
  closed: 'default',
}
const statusLabelMap = {
  new: '新建',
  processing: '处理中',
  resolved: '已解决',
  reopened: '重新打开',
  closed: '已关闭',
}
const severityLabelMap = { trivial: '提示', minor: '次要', major: '严重', critical: '致命' }
const userOpts = ref([])
const caseOpts = ref([])
const defectAttachments = ref([])

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  {
    title: '缺陷名称',
    key: 'name',
    ellipsis: { tooltip: true },
    render: (row) =>
      h(
        NButton,
        { text: true, type: 'primary', size: 'small', onClick: () => openDetail(row) },
        { default: () => row.name }
      ),
  },
  {
    title: '所属平台',
    key: 'platform',
    width: 90,
    render: () => h(NTag, { size: 'small', bordered: false }, { default: () => 'Local' }),
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: (row) =>
      h(
        NTag,
        { type: statusColorMap[row.status] || 'default', size: 'small', bordered: false },
        { default: () => statusLabelMap[row.status] || row.status }
      ),
  },
  {
    title: '严重程度',
    key: 'severity',
    width: 90,
    render: (row) =>
      h(
        NTag,
        { type: severityColorMap[row.severity] || 'default', size: 'small', bordered: false },
        { default: () => severityLabelMap[row.severity] || row.severity }
      ),
  },
  { title: '处理人', key: 'handler_id', width: 80 },
  { title: '创建人', key: 'creator_id', width: 80 },
  { title: '创建时间', key: 'created_at', width: 150 },
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
          NPopconfirm,
          { onPositiveClick: () => handleDelete({ defect_id: row.id }) },
          {
            trigger: () =>
              h(NButton, { size: 'tiny', text: true, type: 'error' }, { default: () => '删除' }),
            default: () => '确认删除?',
          }
        ),
      ]),
  },
]

const defectFormRef = ref(null)
const defectFormData = ref({
  name: '',
  status: 'new',
  severity: 'minor',
  handler_id: null,
  content: '',
  related_case_ids: [],
  plan_id: null,
})

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
  name: '缺陷',
  initForm: {},
  doCreate: (data) => api.createDefect({ ...data, project_id: currentProjectId.value }),
  doUpdate: (data) => api.updateDefect(data),
  doDelete: (params) => api.deleteDefect(params),
  refresh: () => $table.value?.handleSearch(),
})

function handleEdit(row) {
  _handleEdit(row)
  nextTick(() => {
    defectFormData.value = {
      name: modalForm.value.name || '',
      status: modalForm.value.status || 'new',
      severity: modalForm.value.severity || 'minor',
      handler_id: modalForm.value.handler_id || null,
      content: modalForm.value.content || '',
      related_case_ids: modalForm.value.related_case_ids || [],
      plan_id: modalForm.value.plan_id || null,
    }
  })
}
function handleAdd() {
  _handleAdd()
  nextTick(() => {
    defectFormData.value = {
      name: '',
      status: 'new',
      severity: 'minor',
      handler_id: null,
      content: '',
      related_case_ids: [],
      plan_id: null,
    }
  })
}

async function doSave() {
  const valid = await defectFormRef.value?.validate().catch(() => false)
  if (!valid) return
  Object.assign(modalForm.value, defectFormData.value)
  modalFormRef.value = defectFormRef.value
  await handleSave()
}

async function fetchDefects(params) {
  params.project_id = currentProjectId.value
  const res = await api.getDefectList(params)
  return { data: res.data, total: res.total }
}

function onProjectChange(val) {
  if (val) {
    $table.value?.handleSearch()
    loadOptions()
  }
}

async function loadOptions() {
  const [usersRes, casesRes] = await Promise.all([
    api.getUserList({ page: 1, page_size: 9999 }),
    api.getTestCaseList({ project_id: currentProjectId.value, page_size: 9999 }),
  ])
  userOpts.value = (usersRes.data || []).map((u) => ({ label: u.username, value: u.id }))
  caseOpts.value = (casesRes.data || []).map((c) => ({
    label: `[${c.level}] ${c.name}`,
    value: c.id,
  }))
  loadDefectAttachments()
}

async function loadDefectAttachments() {
  if (!currentProjectId.value) return
  const res = await api.getFileList({
    project_id: currentProjectId.value,
    category: 'defect',
    page: 1,
    page_size: 20,
  })
  defectAttachments.value = res.data || []
}

async function handleDefectAttachmentUpload({ file, onFinish, onError }) {
  try {
    const formData = new FormData()
    formData.append('file', file.file)
    formData.append('category', 'defect')
    formData.append('project_id', currentProjectId.value || '')
    await api.uploadFile(formData)
    $message.success('附件上传成功')
    await loadDefectAttachments()
    onFinish?.()
  } catch {
    onError?.()
  }
}

function downloadAttachment(file) {
  window.open(`/api/v1/file/download?file_id=${file.id}`, '_blank')
}

// -- 缺陷详情 --
const detailVisible = ref(false)
const detailData = ref(null)
const detailTab = ref('detail')
const defectFollowed = ref(false)
const comments = ref([])
const newComment = ref('')
const replyTargetId = ref(0)
const changeHistories = ref([])

async function openDetail(row) {
  const res = await api.getDefect({ defect_id: row.id })
  detailData.value = res.data
  detailTab.value = 'detail'
  detailVisible.value = true
  loadComments()
  loadChangeHistories()
  checkFollow()
}

async function openDetailById(defectId) {
  if (!defectId) return
  const res = await api.getDefect({ defect_id: defectId })
  detailData.value = res.data
  detailTab.value = 'detail'
  detailVisible.value = true
  loadComments()
  loadChangeHistories()
  checkFollow()
}
async function loadComments() {
  if (!detailData.value) return
  const res = await api.getDefectComments({ defect_id: detailData.value.id })
  comments.value = res.data || []
}
async function loadChangeHistories() {
  if (!detailData.value) return
  const res = await api.getChangeHistory({ target_type: 'defect', target_id: detailData.value.id })
  changeHistories.value = res.data || []
}
async function checkFollow() {
  if (!detailData.value) return
  const res = await api.checkFollowStatus({ target_type: 'defect', target_id: detailData.value.id })
  defectFollowed.value = res.data?.followed || false
}
async function toggleDefectFollow() {
  await api.toggleFollow({ target_type: 'defect', target_id: detailData.value.id })
  defectFollowed.value = !defectFollowed.value
  $message.success(defectFollowed.value ? '已关注' : '已取消关注')
}

async function copyDefectShareLink() {
  if (!detailData.value) return
  const href = router.resolve({
    path: '/testplatform/defect',
    query: { defect_id: detailData.value.id },
  }).href
  const url = `${window.location.origin}${href}`
  await navigator.clipboard?.writeText(url)
  $message.success('分享链接已复制')
}
async function doCreateComment() {
  if (!newComment.value.trim()) return
  await api.createDefectComment({
    defect_id: detailData.value.id,
    content: newComment.value,
    parent_id: replyTargetId.value,
  })
  newComment.value = ''
  replyTargetId.value = 0
  $message.success('评论已发表')
  loadComments()
}
async function doDeleteComment(commentId) {
  await api.deleteDefectComment({ comment_id: commentId })
  $message.success('评论已删除')
  loadComments()
}
function replyToComment(c) {
  replyTargetId.value = c.id
  newComment.value = ''
}

onMounted(() => {
  if (currentProjectId.value) {
    loadOptions()
    nextTick(() => $table.value?.handleSearch())
  }
  if (route.query.defect_id) {
    openDetailById(route.query.defect_id)
  }
})
</script>

<style scoped>
.defect-form-layout {
  display: flex;
  gap: 0;
}
.defect-form-main {
  flex: 1;
  padding-right: 16px;
  min-width: 0;
}
.defect-form-sidebar {
  width: 220px;
  flex-shrink: 0;
  padding-left: 16px;
  border-left: 1px solid var(--n-border-color);
}
.attachment-list {
  padding: 8px 10px;
  background: var(--n-color-embedded);
  border-radius: 6px;
}
.attachment-item {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 24px;
  color: var(--n-text-color-2);
}
.history-content {
  color: var(--n-text-color-2);
  font-size: 13px;
}
.history-old {
  color: var(--n-text-color-3);
}
.history-new {
  color: var(--primary-color);
}
</style>
