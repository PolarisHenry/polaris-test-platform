import { defineStore } from 'pinia'

export const useProjectStore = defineStore('project', {
  state: () => ({
    projectId: null,
    projectName: '',
    projects: [],
  }),
  getters: {
    currentProjectId: (state) => state.projectId,
    currentProjectName: (state) => state.projectName,
  },
  actions: {
    setProject(projectId, projectName) {
      this.projectId = projectId
      this.projectName = projectName
    },
    setProjects(projects) {
      this.projects = projects
    },
    clearProject() {
      this.projectId = null
      this.projectName = ''
    },
  },
  persist: {
    key: 'project-store',
    storage: localStorage,
    paths: ['projectId', 'projectName'],
  },
})
