<template>
  <n-select
    :value="projectStore.currentProjectId"
    :options="projectOptions"
    placeholder="选择项目"
    clearable
    filterable
    @update:value="handleChange"
  />
</template>

<script setup>
import { computed, onMounted } from 'vue'
import api from '@/api'
import { useProjectStore } from '@/store/modules/project'

const projectStore = useProjectStore()

const projectOptions = computed(() =>
  projectStore.projects.map((p) => ({ label: p.name, value: p.id }))
)

const emit = defineEmits(['change'])

function handleChange(val) {
  const project = projectStore.projects.find((p) => p.id === val)
  projectStore.setProject(val, project?.name || '')
  emit('change', val)
}

onMounted(async () => {
  try {
    const res = await api.getProjectList({ page: 1, page_size: 9999 })
    const projects = res.data || []
    projectStore.setProjects(projects)
    const currentId = projectStore.currentProjectId
    // If persisted project is still in the list, use it; otherwise default to first
    const exists = projects.some((p) => p.id === currentId)
    const targetId = currentId && exists ? currentId : projects[0]?.id ?? null
    if (targetId) {
      await nextTick()
      handleChange(targetId)
    }
  } catch {}
})
</script>
