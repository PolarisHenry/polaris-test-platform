# 测试用例模块菜单优化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复测试用例模块树设计问题、支持含子模块的用例计数、批量更新用例模块、调整所有测试管理页面的筛选/操作布局

**Architecture:** 后端修改 module stats 统计逻辑为递归计数、新增 batch_update_module 和 module/move 接口；前端修改 testcase 页面树组件行为、添加拖拽支持、新增批量操作选项，统一调整 testplan/defect/file/msgconfig 页面布局

**Tech Stack:** FastAPI + Tortoise ORM + Vue3 + Naive UI

---

### Task 1: Backend - 模块统计改为递归计数（含子模块）

**Files:**
- Modify: `app/controllers/module.py:74-82`
- Modify: `app/api/v1/modules/modules.py:43-46`

- [ ] **Step 1: 修改 get_module_stats 方法**

修改 `app/controllers/module.py` 的 `get_module_stats` 方法，使用 ModuleClosure 查询每个模块的所有后代用例：

```python
async def get_module_stats(self, project_id: int):
    modules = await self.model.filter(is_deleted=False, project_id=project_id).order_by("order")
    result = []
    for m in modules:
        descendants = await ModuleClosure.filter(ancestor=m.id).values_list("descendant", flat=True)
        count = await TestCase.filter(module_id__in=descendants).count()
        result.append({"id": m.id, "name": m.name, "case_count": count})
    # 统计未规划用例
    unplanned_count = await TestCase.filter(
        Q(project_id=project_id), Q(module_id__isnull=True) | Q(module_id=0)
    ).count()
    return {"modules": result, "unplanned_count": unplanned_count}
```

注意：需要在文件顶部确保 `from tortoise.expressions import Q` 已导入（第1行已有）。

- [ ] **Step 2: 修改 stats 路由返回新格式**

修改 `app/api/v1/modules/modules.py` 的 `get_module_stats` 路由：

```python
@router.get("/stats", summary="模块用例统计")
async def get_module_stats(project_id: int = Query(..., description="项目ID")):
    data = await module_controller.get_module_stats(project_id=project_id)
    return Success(data=data)
```

原代码不变——因为 controller 现在返回 dict 而非 list，Success 直接包裹。

---

### Task 2: Backend - 批量更新用例所属模块

**Files:**
- Modify: `app/schemas/tp.py:133-140` (batch schema 区域)
- Modify: `app/controllers/testcase.py:65-74`
- Modify: `app/api/v1/testcases/testcases.py:68-85`

- [ ] **Step 1: 新增 BatchUpdateModuleRequest schema**

在 `app/schemas/tp.py` 的 batch 相关 schema 区域（`BatchReviewRequest` 之后）添加：

```python
class BatchUpdateModuleRequest(BaseModel):
    ids: List[int] = Field(..., description="要更新的用例ID列表")
    module_id: int = Field(..., description="目标模块ID")
```

- [ ] **Step 2: 新增 batch_update_module 方法**

在 `app/controllers/testcase.py` 的 `batch_review` 方法之后添加：

```python
async def batch_update_module(self, ids: List[int], module_id: int):
    await self.model.filter(id__in=ids).update(module_id=module_id)
```

- [ ] **Step 3: 新增 API 路由**

在 `app/api/v1/testcases/testcases.py` 的 `batch_review` 路由之后添加：

```python
from app.schemas.tp import BatchDeleteRequest, BatchReviewRequest, BatchUpdateModuleRequest, ExecResultUpdate, TestCaseCreate, TestCaseUpdate

@router.post("/batch_update_module", summary="批量更新用例模块")
async def batch_update_module(batch_in: BatchUpdateModuleRequest):
    await test_case_controller.batch_update_module(ids=batch_in.ids, module_id=batch_in.module_id)
    return Success(msg="Updated Successfully")
```

- [ ] **Step 4: 确认 import 行已更新**

确认 `app/api/v1/testcases/testcases.py` 的 import 行包含 `BatchUpdateModuleRequest`。

---

### Task 3: Backend - 模块拖动接口

**Files:**
- Modify: `app/schemas/tp.py`
- Modify: `app/controllers/module.py:56-65`
- Modify: `app/api/v1/modules/modules.py:37-46`

- [ ] **Step 1: 新增 ModuleMove schema**

在 `app/schemas/tp.py` 的 ModuleUpdate 之后添加：

```python
class ModuleMove(BaseModel):
    id: int
    parent_id: int = Field(0, description="新父模块ID")
    order: int = Field(0, description="排序")
```

- [ ] **Step 2: 新增 move_module 方法**

在 `app/controllers/module.py` 的 `delete_module` 之前添加：

```python
async def move_module(self, id: int, parent_id: int, order: int = 0):
    module_obj = await self.get(id=id)
    parent_changed = module_obj.parent_id != parent_id
    module_obj.parent_id = parent_id
    module_obj.order = order
    await module_obj.save()
    if parent_changed:
        await ModuleClosure.filter(ancestor=module_obj.id).delete()
        await ModuleClosure.filter(descendant=module_obj.id).delete()
        await self.update_module_closure(module_obj)
```

- [ ] **Step 3: 新增 move 路由**

在 `app/api/v1/modules/modules.py` 的 delete_module 之后添加：

```python
from app.schemas.tp import ModuleCreate, ModuleMove, ModuleUpdate

@router.post("/move", summary="移动模块（拖拽）")
async def move_module(move_in: ModuleMove):
    await module_controller.move_module(id=move_in.id, parent_id=move_in.parent_id, order=move_in.order)
    return Success(msg="Moved Successfully")
```

---

### Task 4: Frontend - CrudTable 增加 actions 插槽

**Files:**
- Modify: `web/src/components/table/CrudTable.vue`

- [ ] **Step 1: 在 QueryBar 和 n-data-table 之间添加 actions 插槽**

修改 `web/src/components/table/CrudTable.vue` 模板，在 QueryBar 和 n-data-table 之间插入 actions 区域：

```html
    <QueryBar v-if="$slots.queryBar" mb-30 @search="handleSearch" @reset="handleReset">
      <slot name="queryBar" />
    </QueryBar>

    <div v-if="$slots.actions" mb-15 flex items-center gap-8>
      <slot name="actions" />
    </div>

    <n-data-table
```

---

### Task 5: Frontend - API 新增

**Files:**
- Modify: `web/src/api/index.js`

- [ ] **Step 1: 在 testcases 区域添加 batchUpdateModule API**

在 `web/src/api/index.js` 的 `batchReviewTestCases` 之后添加：

```js
  batchUpdateModuleCases: (data = {}) => request.post('/testcase/batch_update_module', data),
```

---

### Task 6: Frontend - 测试用例页面改造

**Files:**
- Modify: `web/src/views/testplatform/testcase/index.vue`

这是最大的改动，包含：模块树点击修复、展开收起行为、拖拽、用例计数新格式、批量操作UI、页面布局。

- [ ] **Step 1: 修复模块树点击与展开收起分离**

移除 `nodeProps` 中的 `onClick` 处理，改用 n-tree 的 `@update:selected-keys` 事件：

找到并修改：

```js
// 删除 nodeProps 函数（约第 290-292 行）
// 原来：
// const nodeProps = ({ option }) => ({
//   onClick() { onTreeSelect([option.id]) },
// })

// 改为空对象
const nodeProps = () => ({})
```

在 `<n-tree>` 标签上修改：

```html
          <n-tree
            :data="moduleTreeData"
            :node-props="nodeProps"
            :expanded-keys="expandedKeys"
            key-field="id"
            label-field="name"
            children-field="children"
            block-line
            selectable
            @update:selected-keys="onTreeSelect"
          >
```

- [ ] **Step 2: 添加拖拽支持**

在 `<n-tree>` 标签上添加 draggable 属性和 drop 事件处理：

```html
          <n-tree
            :data="moduleTreeData"
            :node-props="nodeProps"
            :expanded-keys="expandedKeys"
            key-field="id"
            label-field="name"
            children-field="children"
            block-line
            selectable
            draggable
            @update:selected-keys="onTreeSelect"
            @drop="handleTreeDrop"
          >
```

在 `onMounted` 之前添加拖拽处理函数：

```js
async function handleTreeDrop({ node, dragNode, dropPosition }) {
  // 不允许拖动 'all' 'unplanned' 'recycle' 特殊节点
  if (dragNode.id === 'all' || dragNode.id === 'unplanned' || dragNode.id === 'recycle') {
    return
  }
  // 不允许拖到 'unplanned' 下
  if (dropPosition === 'inner' && (node.id === 'all' || node.id === 'unplanned')) {
    $message.warning('不能将模块拖放到此位置')
    return
  }
  try {
    if (dropPosition === 'inner') {
      // 成为目标节点的子模块
      await api.updateModule({ id: dragNode.id, parent_id: node.id, name: dragNode.name, project_id: currentProjectId.value, desc: '', order: 0 })
    } else {
      // 成为目标节点的平级模块（parent_id 与目标节点相同）
      const targetParentId = node.id === 'all' || node.id === 'unplanned' ? 0 : (node.parent_id || 0)
      await api.updateModule({ id: dragNode.id, parent_id: targetParentId, name: dragNode.name, project_id: currentProjectId.value, desc: '', order: 0 })
    }
    $message.success('模块已移动')
    await loadModuleTree()
  } catch (err) {
    $message.error('移动失败')
  }
}
```

- [ ] **Step 3: 优化展开收起行为**

修改 `toggleExpand` 函数，收起时保留顶层级模块展开状态：

```js
function toggleExpand() {
  if (treeExpanded.value) {
    // 收起：只展开顶层级模块（直接子模块）
    const topIds = []
    for (const node of moduleTreeData.value) {
      // all 和 unplanned 没有 children，跳过
      if (node.children?.length) {
        topIds.push(node.id)
      }
    }
    expandedKeys.value = topIds
    treeExpanded.value = false
  } else {
    // 展开：递归展开所有
    const ids = []
    collectNodeIds(moduleTreeData.value, ids)
    expandedKeys.value = ids
    treeExpanded.value = true
  }
}
```

- [ ] **Step 4: 修改 loadModuleTree 处理新 stats 格式和无规划用例计数**

更新 `loadModuleTree` 函数：

```js
async function loadModuleTree() {
  if (!currentProjectId.value) return
  const res = await api.getModuleTree({ project_id: currentProjectId.value })
  moduleTreeRaw.value = res.data || []
  const statsRes = await api.getModuleStats({ project_id: currentProjectId.value })
  const statsData = statsRes.data || {}
  const statsList = statsData.modules || []
  const unplannedCount = statsData.unplanned_count || 0
  const total = mergeCaseCounts(moduleTreeRaw.value, statsList)
  totalCaseCount.value = total + unplannedCount
  recycleCount.value = 0
  moduleTreeData.value = [
    { id: 'all', name: '全部用例', children: [], caseCount: total + unplannedCount },
    { id: 'unplanned', name: '未规划用例', children: [], caseCount: unplannedCount },
    ...moduleTreeRaw.value,
  ]
}
```

- [ ] **Step 5: 添加批量更新模块 UI**

在 `batchOptions` 中添加新选项：

```js
const batchOptions = [
  { label: '批量评审', key: 'review' },
  { label: '批量修改模块', key: 'module' },
  { label: '批量删除', key: 'delete' },
]
```

在 `onBatchSelect` 中添加处理：

```js
function onBatchSelect(key) {
  if (key === 'review') handleBatchReview()
  else if (key === 'module') handleBatchModule()
  else if (key === 'delete') handleBatchDelete()
}
```

在 `handleBatchReview` 之后添加批量模块更新逻辑：

```js
const batchModuleVisible = ref(false)
const batchModuleId = ref(null)

function handleBatchModule() {
  if (!checkedRowKeys.value.length) { $message.warning('请先勾选用例'); return }
  batchModuleId.value = null
  batchModuleVisible.value = true
}

async function doBatchUpdateModule() {
  if (!batchModuleId.value) { $message.warning('请选择目标模块'); return }
  await api.batchUpdateModuleCases({ ids: checkedRowKeys.value, module_id: batchModuleId.value })
  $message.success('批量修改模块成功')
  batchModuleVisible.value = false
  $table.value?.handleSearch()
  loadModuleTree()
}
```

在模板的闭包 meta 标签之后、`</common-page>` 之前添加批量更新模块的对话框：

```html
        <n-modal v-model:show="batchModuleVisible" title="批量修改模块" preset="card" style="width: 400px" :mask-closable="false">
          <n-form label-placement="left" label-width="80">
            <n-form-item label="目标模块">
              <n-tree-select
                v-model:value="batchModuleId"
                :options="moduleTreeRaw"
                placeholder="请选择目标模块"
                clearable
                key-field="id"
                label-field="name"
                children-field="children"
              />
            </n-form-item>
          </n-form>
          <template #footer>
            <n-button @click="batchModuleVisible = false">取消</n-button>
            <n-button ml-12 type="primary" @click="doBatchUpdateModule">确定</n-button>
          </template>
        </n-modal>
```

- [ ] **Step 6: 调整页面布局——项目选择器移入 queryBar，操作按钮下移**

修改 `<template>` 区域：

```html
      <common-page>
        <!-- 移除 #action 区域 -->

        <crud-table
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="fetchCases"
          :extra-params="{ project_id: currentProjectId, module_id: selectedModuleId }"
          @on-checked="onChecked"
        >
          <template #queryBar>
            <project-selector style="width: 200px" @change="onProjectChange" />
            <n-input v-model:value="queryItems.name" placeholder="通过 ID/名称/标签搜索" clearable style="width: 260px" />
            <n-select v-model:value="queryItems.level" placeholder="用例等级" clearable :options="levelOptions" style="width: 120px" />
            <n-select v-model:value="queryItems.status" placeholder="状态" clearable :options="statusOptions" style="width: 120px" />
          </template>

          <template #actions>
            <n-button type="primary" v-permission="'post/api/v1/testcase/create'" @click="handleAdd">
              <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
              新建
            </n-button>
            <n-button ml-8>
              <template #icon><the-icon icon="material-symbols:upload" :size="18" /></template>
              导入
            </n-button>
            <n-dropdown trigger="hover" :options="batchOptions" @select="onBatchSelect" ml-8>
              <n-button>批量操作</n-button>
            </n-dropdown>
          </template>
        </crud-table>
```

- [ ] **Step 7: 修复 ProjectSelector 事件传递**

由于 `project-selector` 现在在 `#queryBar` 中而不是 `#action`，需要确保其 `onProjectChange` 能正确触发。移除 `onProjectChange` 中的 `loadModuleTree()` 和 `loadUsers()` 去重调用，保持逻辑不变：

```js
function onProjectChange(val) {
  if (val) {
    loadModuleTree()
    loadUsers()
    $table.value?.handleSearch()
  }
}
```

---

### Task 7: Frontend - 测试计划页面布局调整

**Files:**
- Modify: `web/src/views/testplatform/testplan/index.vue`

- [ ] **Step 1: 将 project-selector 移入 queryBar，新建计划按钮移入 actions**

```html
      <common-page>
        <crud-table
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="fetchPlans"
          :extra-params="{ project_id: currentProjectId }"
        >
          <template #queryBar>
            <project-selector style="width: 200px" @change="onProjectChange" />
            <n-input v-model:value="queryItems.name" placeholder="计划名称" clearable />
            <n-select v-model:value="queryItems.status" placeholder="状态" clearable :options="statusOptions" style="width: 140px" />
          </template>

          <template #actions>
            <n-button type="primary" v-permission="'post/api/v1/testplan/create'" @click="handleAdd">
              <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
              新建计划
            </n-button>
          </template>
        </crud-table>
```

---

### Task 8: Frontend - 缺陷页面布局调整

**Files:**
- Modify: `web/src/views/testplatform/defect/index.vue`

- [ ] **Step 1: 将 project-selector 移入 queryBar，新建缺陷按钮移入 actions**

```html
      <common-page>
        <crud-table
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="fetchDefects"
          :extra-params="{ project_id: currentProjectId }"
        >
          <template #queryBar>
            <project-selector style="width: 200px" @change="onProjectChange" />
            <n-input v-model:value="queryItems.name" placeholder="缺陷名称" clearable />
            <n-select v-model:value="queryItems.status" placeholder="状态" clearable :options="statusOpts" style="width: 120px" />
            <n-select v-model:value="queryItems.severity" placeholder="严重程度" clearable :options="severityOpts" style="width: 120px" />
          </template>

          <template #actions>
            <n-button type="primary" v-permission="'post/api/v1/defect/create'" @click="handleAdd">
              <template #icon><the-icon icon="material-symbols:add" :size="18" /></template>
              新建缺陷
            </n-button>
          </template>
        </crud-table>
```

---

### Task 9: Frontend - 文件页面布局调整

**Files:**
- Modify: `web/src/views/testplatform/file/index.vue`

- [ ] **Step 1: 将 project-selector 移入 queryBar，上传按钮移入 actions**

```html
      <common-page>
        <n-tabs v-model:value="activeTab" mb-12 @update:value="onTabChange">
          <n-tab-pane name="all" tab="全部文件" />
          <n-tab-pane name="common" tab="普通文件" />
          <n-tab-pane name="test_case" tab="用例附件" />
          <n-tab-pane name="defect" tab="缺陷附件" />
          <n-tab-pane name="template" tab="模板文件" />
        </n-tabs>

        <crud-table ref="$table" :columns="columns" :get-data="fetchFiles" :extra-params="{ project_id: currentProjectId, category: activeTab === 'all' ? '' : activeTab }">
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
```

---

### Task 10: Frontend - 消息配置页面布局调整

**Files:**
- Modify: `web/src/views/testplatform/msgconfig/index.vue`

- [ ] **Step 1: 将 project-selector 移入 queryBar，新增配置按钮移入 actions**

```html
      <common-page>
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
```

---

### 验证清单

- [ ] `ruff check app/` — 无 lint 错误
- [ ] 启动后端，测试 `POST /module/stats` 返回含 `modules` 和 `unplanned_count` 的新格式
- [ ] 启动后端，测试 `POST /testcase/batch_update_module` 批量更新模块
- [ ] 启动前端，验证模块树：
  - [ ] 点击模块名选中筛选（不触发展开收起）
  - [ ] 点击箭头独立展开收起子模块
  - [ ] 「全部用例」展开/收起按钮行为正确
  - [ ] 拖拽模块到另一模块上成为子模块
- [ ] 验证每个模块显示含子模块用例总数
- [ ] 验证「未规划用例」显示正确计数
- [ ] 验证批量操作→修改模块功能
- [ ] 验证各页面布局正确（testcase, testplan, defect, file, msgconfig）
