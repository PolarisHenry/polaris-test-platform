<template>
  <common-page :show-header="false">
    <crud-table
      ref="$table"
      :columns="columns"
      :get-data="fetchConfigs"
      :extra-params="{ project_id: currentProjectId }"
    >
      <template #queryBar>
        <project-selector style="width: 200px" @change="onProjectChange" />
      </template>

      <template #actions>
        <n-button type="primary" @click="handleAdd">
          <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
          新增配置
        </n-button>
      </template>
    </crud-table>

    <crud-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      width="600px"
      @save="handleSave"
    >
      <n-form
        ref="modalFormRef"
        :model="modalForm"
        :rules="rules"
        label-placement="left"
        label-width="100"
      >
        <n-form-item label="事件类型" path="event_type">
          <n-select
            v-model:value="modalForm.event_type"
            :options="eventTypeOptions"
            placeholder="选择事件类型"
          />
        </n-form-item>
        <n-form-item label="通知对象" path="target_type">
          <n-select
            v-model:value="modalForm.target_type"
            :options="targetTypeOptions"
            placeholder="选择通知对象"
          />
        </n-form-item>
        <n-form-item label="通知方式" path="notify_methods">
          <n-checkbox-group v-model:value="modalForm.notify_methods">
            <n-checkbox value="in_app" label="站内信" />
            <n-checkbox value="email" label="邮件" />
            <n-checkbox value="wecom_bot" label="企微机器人" />
          </n-checkbox-group>
        </n-form-item>
      </n-form>
    </crud-modal>
  </common-page>
</template>

<script setup>
import { NButton } from 'naive-ui'
import { useCRUD } from '@/composables'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import ProjectSelector from '@/components/project/ProjectSelector.vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'

const projectStore = useProjectStore()
const currentProjectId = computed(() => projectStore.currentProjectId)
const $table = ref(null)

const eventTypeOptions = [
  { label: '计划更新', value: 'plan_update' },
  { label: '执行成功', value: 'plan_exec_success' },
  { label: '执行失败', value: 'plan_exec_fail' },
]
const targetTypeOptions = [
  { label: '创建人', value: 'creator' },
  { label: '关注人', value: 'watcher' },
  { label: '处理人', value: 'handler' },
]

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '事件类型', key: 'event_type', width: 120 },
  { title: '通知对象', key: 'target_type', width: 100 },
  {
    title: '通知方式',
    key: 'notify_methods',
    width: 200,
    render: (row) => (row.notify_methods || []).join(', '),
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row) =>
      h('div', [
        h(NButton, { size: 'tiny', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
        h(
          NButton,
          {
            size: 'tiny',
            type: 'error',
            style: 'margin-left: 4px',
            onClick: () => handleDelete({ config_id: row.id }),
          },
          { default: () => '删除' }
        ),
      ]),
  },
]

const rules = {
  event_type: [{ required: true, message: '请选择事件类型', trigger: 'change' }],
  target_type: [{ required: true, message: '请选择通知对象', trigger: 'change' }],
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  modalForm,
  modalFormRef,
  handleAdd,
  handleEdit,
  handleDelete,
  handleSave,
} = useCRUD({
  name: '消息配置',
  initForm: { notify_methods: [] },
  doCreate: (data) => api.createMsgConfig({ ...data, project_id: currentProjectId.value }),
  doUpdate: api.updateMsgConfig,
  doDelete: (params) => api.deleteMsgConfig(params),
  refresh: () => $table.value?.handleSearch(),
})

async function fetchConfigs(params) {
  params.project_id = currentProjectId.value
  const res = await api.getMsgConfigList(params)
  return { data: res.data, total: res.total }
}

function onProjectChange(val) {
  if (val) $table.value?.handleSearch()
}
</script>
