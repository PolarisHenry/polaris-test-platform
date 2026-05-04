import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // projects
  getProjectList: (params = {}) => request.get('/project/list', { params }),
  getProject: (params = {}) => request.get('/project/get', { params }),
  createProject: (data = {}) => request.post('/project/create', data),
  updateProject: (data = {}) => request.post('/project/update', data),
  deleteProject: (params = {}) => request.delete('/project/delete', { params }),
  getProjectMembers: (params = {}) => request.get('/project/members', { params }),
  updateProjectMembers: (params = {}) => request.post('/project/members', null, { params }),
  // modules
  getModuleTree: (params = {}) => request.get('/module/tree', { params }),
  getModule: (params = {}) => request.get('/module/get', { params }),
  createModule: (data = {}) => request.post('/module/create', data),
  updateModule: (data = {}) => request.post('/module/update', data),
  deleteModule: (params = {}) => request.delete('/module/delete', { params }),
  getModuleStats: (params = {}) => request.get('/module/stats', { params }),
  // testcases
  getTestCaseList: (params = {}) => request.get('/testcase/list', { params }),
  getTestCase: (params = {}) => request.get('/testcase/get', { params }),
  createTestCase: (data = {}) => request.post('/testcase/create', data),
  importTestCases: (data = {}) =>
    request.post('/testcase/import', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  updateTestCase: (data = {}) => request.post('/testcase/update', data),
  deleteTestCase: (params = {}) => request.delete('/testcase/delete', { params }),
  batchDeleteTestCases: (data = {}) => request.post('/testcase/batch_delete', data),
  batchReviewTestCases: (data = {}) => request.post('/testcase/batch_review', data),
  batchUpdateModuleCases: (data = {}) => request.post('/testcase/batch_update_module', data),
  updateExecResult: (data = {}) => request.post('/testcase/update_exec_result', data),
  // defects
  getDefectList: (params = {}) => request.get('/defect/list', { params }),
  getDefect: (params = {}) => request.get('/defect/get', { params }),
  createDefect: (data = {}) => request.post('/defect/create', data),
  updateDefect: (data = {}) => request.post('/defect/update', data),
  deleteDefect: (params = {}) => request.delete('/defect/delete', { params }),
  updateDefectStatus: (data = {}) => request.post('/defect/update_status', data),
  // testplans
  getTestPlanList: (params = {}) => request.get('/testplan/list', { params }),
  getTestPlan: (params = {}) => request.get('/testplan/get', { params }),
  createTestPlan: (data = {}) => request.post('/testplan/create', data),
  updateTestPlan: (data = {}) => request.post('/testplan/update', data),
  deleteTestPlan: (params = {}) => request.delete('/testplan/delete', { params }),
  executeTestPlan: (params = {}) => request.post('/testplan/execute', null, { params }),
  completeTestPlan: (data = {}) => request.post('/testplan/complete', data),
  cancelTestPlan: (data = {}) => request.post('/testplan/cancel', data),
  getPlanCaseResults: (params = {}) => request.get('/testplan/case_results', { params }),
  updatePlanCaseResult: (data = {}) => request.post('/testplan/update_case_result', data),
  createDefectFromFailure: (data = {}) => request.post('/defect/create_from_failure', data),
  // files
  getFileList: (params = {}) => request.get('/file/list', { params }),
  uploadFile: (data = {}) =>
    request.post('/file/upload', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  downloadFile: (params = {}) => request.get('/file/download', { params, responseType: 'blob' }),
  deleteFile: (params = {}) => request.delete('/file/delete', { params }),
  // msgconfig
  getMsgConfigList: (params = {}) => request.get('/msgconfig/list', { params }),
  createMsgConfig: (data = {}) => request.post('/msgconfig/create', data),
  updateMsgConfig: (data = {}) => request.post('/msgconfig/update', data),
  deleteMsgConfig: (params = {}) => request.delete('/msgconfig/delete', { params }),
  // workbench
  getWorkbenchStats: (params = {}) => request.get('/workbench/stats', { params }),
  getWorkbenchCharts: (params = {}) => request.get('/workbench/charts', { params }),
  getMyItems: (params = {}) => request.get('/workbench/my-items', { params }),
  // recycle bin
  getRecycleBin: (params = {}) => request.get('/testcase/recycle_bin', { params }),
  restoreTestCases: (data = {}) => request.post('/testcase/restore', data),
  hardDeleteTestCases: (data = {}) => request.post('/testcase/hard_delete', data),
  // review plans
  getReviewPlanList: (params = {}) => request.get('/review/list', { params }),
  getReviewPlan: (params = {}) => request.get('/review/get', { params }),
  createReviewPlan: (data = {}) => request.post('/review/create', data),
  updateReviewPlan: (data = {}) => request.post('/review/update', data),
  deleteReviewPlan: (params = {}) => request.delete('/review/delete', { params }),
  startReview: (params = {}) => request.post('/review/start', null, { params }),
  completeReview: (params = {}) => request.post('/review/complete', null, { params }),
  cancelReview: (params = {}) => request.post('/review/cancel', null, { params }),
  copyReviewPlan: (params = {}) => request.post('/review/copy', null, { params }),
  linkReviewCases: (params = {}) => request.post('/review/link_cases', null, { params }),
  unlinkReviewCases: (params = {}) => request.post('/review/unlink_cases', null, { params }),
  getReviewCaseResults: (params = {}) => request.get('/review/case_results', { params }),
  submitReviewResult: (data = {}) => request.post('/review/submit_review', data),
  batchReview: (data = {}) => request.post('/review/batch_review', data),
  // follows
  toggleFollow: (data = {}) => request.post('/follow/toggle', data),
  checkFollowStatus: (params = {}) => request.get('/follow/status', { params }),
  getMyFollowed: (params = {}) => request.get('/follow/my_followed', { params }),
  // comments
  getDefectComments: (params = {}) => request.get('/comment/list', { params }),
  createDefectComment: (data = {}) => request.post('/comment/create', data),
  deleteDefectComment: (params = {}) => request.delete('/comment/delete', { params }),
  getChangeHistory: (params = {}) => request.get('/change_history/list', { params }),
  // testplan manual execution & report
  submitManualExec: (data = {}) => request.post('/testplan/submit_manual_exec', data),
  getExecutionDetail: (params = {}) => request.get('/testplan/execution_detail', { params }),
  batchExecutePlan: (data = {}) => request.post('/testplan/batch_execute', data),
  batchChangeExecutor: (params = {}) =>
    request.post('/testplan/batch_change_executor', null, { params }),
  batchUnlinkPlanCases: (params = {}) => request.post('/testplan/batch_unlink', null, { params }),
  getTestReport: (params = {}) => request.get('/testplan/report', { params }),
}
