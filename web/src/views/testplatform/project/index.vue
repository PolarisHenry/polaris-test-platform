<template>
  <common-page>
    <template #action>
      <n-button type="primary" @click="handleAdd">
        <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
        新建项目
      </n-button>
    </template>

    <crud-table ref="$table" :columns="columns" :get-data="api.getProjectList">
      <template #queryBar>
        <n-input v-model:value="queryItems.name" placeholder="项目名称" clearable />
      </template>
    </crud-table>

    <crud-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      width="700px"
      @save="handleSave"
    >
      <n-form
        ref="modalFormRef"
        :model="modalForm"
        :rules="rules"
        label-placement="left"
        label-width="100"
      >
        <n-form-item label="项目名称" path="name">
          <n-input v-model:value="modalForm.name" placeholder="请输入项目名称" />
        </n-form-item>
        <n-form-item label="所属组织">
          <n-input v-model:value="modalForm.organization" placeholder="请输入所属组织" />
        </n-form-item>
        <n-form-item label="项目描述">
          <n-input v-model:value="modalForm.desc" type="textarea" placeholder="请输入项目描述" />
        </n-form-item>
      </n-form>
    </crud-modal>
  </common-page>
</template>

<script setup>
import { NButton, NPopconfirm } from 'naive-ui'
import { useCRUD } from '@/composables'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import api from '@/api'

const $table = ref(null)
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '项目名称', key: 'name', ellipsis: { tooltip: true } },
  { title: '所属组织', key: 'organization', width: 120 },
  { title: '描述', key: 'desc', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    render: (row) =>
      h('div', [
        h(NButton, { size: 'tiny', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete({ project_id: row.id }) },
          {
            trigger: () =>
              h(
                NButton,
                { size: 'tiny', type: 'error', style: 'margin-left: 4px' },
                { default: () => '删除' }
              ),
            default: () => '确认删除?',
          }
        ),
      ]),
  },
]

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
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
  name: '项目',
  initForm: {},
  doCreate: api.createProject,
  doUpdate: api.updateProject,
  doDelete: api.deleteProject,
  refresh: () => $table.value?.handleSearch(),
})
</script>
