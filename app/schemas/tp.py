from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    CaseStatus,
    DefectSeverity,
    DefectStatus,
    ExecResult,
    FileCategory,
    PlanStatus,
    ReviewResult,
    TestCaseLevel,
)


# ============== Project Schemas ==============
class BaseProject(BaseModel):
    id: int
    name: str
    organization: Optional[str] = None
    desc: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    members: Optional[list] = []


class ProjectCreate(BaseModel):
    name: str = Field(example="北极星后台管理系统")
    organization: Optional[str] = Field(None, example="质量保障部")
    desc: Optional[str] = Field("", example="项目描述")


class ProjectUpdate(BaseModel):
    id: int
    name: str = Field(example="北极星后台管理系统")
    organization: Optional[str] = Field(None)
    desc: Optional[str] = Field("")
    member_ids: Optional[List[int]] = []


class ProjectMemberSchema(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str = "tester"
    username: Optional[str] = None
    email: Optional[str] = None


# ============== Module Schemas ==============
class ModuleSchema(BaseModel):
    id: int
    name: str
    desc: Optional[str] = None
    order: int = 0
    parent_id: int = 0
    project_id: int
    is_deleted: bool = False
    children: Optional[List["ModuleSchema"]] = []


class ModuleCreate(BaseModel):
    name: str = Field(example="内容模块")
    desc: Optional[str] = Field("")
    order: int = Field(0)
    parent_id: int = Field(0)
    project_id: int = Field(..., description="所属项目ID")


class ModuleUpdate(ModuleCreate):
    id: int


class ModuleMove(BaseModel):
    id: int
    parent_id: int = Field(0, description="新父模块ID")
    order: int = Field(0, description="排序")


# ============== TestCase Schemas ==============
class TestCaseStepSchema(BaseModel):
    id: int
    step_number: int
    action: str
    expected_result: str
    sort_order: int


class TestCaseStepCreate(BaseModel):
    step_number: int = Field(..., description="步骤序号")
    action: str = Field(..., description="测试步骤")
    expected_result: str = Field(..., description="预期结果")
    sort_order: int = Field(0, description="排序")


class BaseTestCase(BaseModel):
    id: int
    name: str
    module_id: Optional[int] = None
    project_id: int
    level: TestCaseLevel = TestCaseLevel.P2
    precondition: Optional[str] = None
    remark: Optional[str] = None
    tags: List[str] = []
    review_result: Optional[ReviewResult] = None
    exec_result: ExecResult = ExecResult.PENDING
    status: CaseStatus = CaseStatus.DRAFT
    creator_id: int
    reviewer_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: Optional[List[TestCaseStepSchema]] = []


class TestCaseCreate(BaseModel):
    name: str = Field(example="登录功能测试")
    module_id: Optional[int] = None
    project_id: int = Field(..., description="所属项目ID")
    level: TestCaseLevel = TestCaseLevel.P2
    precondition: Optional[str] = ""
    remark: Optional[str] = ""
    tags: List[str] = []
    reviewer_id: Optional[int] = None
    steps: List[TestCaseStepCreate] = []


class TestCaseUpdate(BaseModel):
    id: int
    name: str = Field(example="登录功能测试")
    module_id: Optional[int] = None
    project_id: int = Field(..., description="所属项目ID")
    level: TestCaseLevel = TestCaseLevel.P2
    precondition: Optional[str] = ""
    remark: Optional[str] = ""
    tags: List[str] = []
    steps: Optional[List[TestCaseStepCreate]] = None
    reviewer_id: Optional[int] = None
    review_result: Optional[ReviewResult] = None
    exec_result: Optional[ExecResult] = None


class BatchDeleteRequest(BaseModel):
    ids: List[int] = Field(..., description="要删除的ID列表")


class BatchReviewRequest(BaseModel):
    ids: List[int] = Field(..., description="要评审的ID列表")
    review_result: ReviewResult = Field(..., description="评审结果")


class BatchUpdateModuleRequest(BaseModel):
    ids: List[int] = Field(..., description="要更新的用例ID列表")
    module_id: int = Field(..., description="目标模块ID")


class ExecResultUpdate(BaseModel):
    case_id: int = Field(..., description="用例ID")
    exec_result: ExecResult = Field(..., description="执行结果")


# ============== Defect Schemas ==============
class BaseDefect(BaseModel):
    id: int
    name: str
    status: DefectStatus
    severity: DefectSeverity
    handler_id: Optional[int] = None
    creator_id: int
    project_id: int
    content: Optional[str] = None
    related_case_ids: List[int] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DefectCreate(BaseModel):
    name: str = Field(example="登录按钮无响应")
    status: DefectStatus = DefectStatus.NEW
    severity: DefectSeverity = DefectSeverity.MINOR
    handler_id: Optional[int] = None
    project_id: int = Field(..., description="所属项目ID")
    content: Optional[str] = ""
    related_case_ids: List[int] = []
    plan_id: Optional[int] = None


class DefectUpdate(BaseModel):
    id: int
    name: str = Field(example="登录按钮无响应")
    status: DefectStatus = DefectStatus.NEW
    severity: DefectSeverity = DefectSeverity.MINOR
    handler_id: Optional[int] = None
    project_id: int = Field(..., description="所属项目ID")
    content: Optional[str] = ""
    related_case_ids: List[int] = []
    plan_id: Optional[int] = None


class DefectStatusUpdate(BaseModel):
    defect_id: int = Field(..., description="缺陷ID")
    status: DefectStatus = Field(..., description="新状态")


class DefectCreateFromFailure(BaseModel):
    plan_id: int = Field(..., description="测试计划ID")
    case_id: int = Field(..., description="失败的用例ID")
    name: str = Field(..., description="缺陷名称")


# ============== TestPlan Schemas ==============
class BaseTestPlan(BaseModel):
    id: int
    name: str
    status: PlanStatus
    project_id: int
    creator_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    desc: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TestPlanCreate(BaseModel):
    name: str = Field(example="V2.0回归测试计划")
    project_id: int = Field(..., description="所属项目ID")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    desc: Optional[str] = ""
    case_ids: List[int] = []


class TestPlanUpdate(BaseModel):
    id: int
    name: str = Field(example="V2.0回归测试计划")
    project_id: int = Field(..., description="所属项目ID")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    desc: Optional[str] = ""
    case_ids: List[int] = []


class PlanCaseResult(BaseModel):
    id: int
    plan_id: int
    case_id: int
    case_name: Optional[str] = None
    exec_result: ExecResult = ExecResult.PENDING
    executed_at: Optional[datetime] = None
    executor_id: Optional[int] = None


class PlanCaseResultUpdate(BaseModel):
    plan_case_id: int = Field(..., description="计划-用例关联ID")
    exec_result: ExecResult = Field(..., description="执行结果")
    executor_id: Optional[int] = None


class PlanStatusUpdate(BaseModel):
    plan_id: int = Field(..., description="计划ID")


class PlanProgress(BaseModel):
    total: int = 0
    pending: int = 0
    success: int = 0
    fail: int = 0
    blocked: int = 0
    percent: float = 0.0


# ============== File Schemas ==============
class BaseFile(BaseModel):
    id: int
    name: str
    path: str
    size: int
    file_type: Optional[str] = None
    project_id: Optional[int] = None
    uploader_id: int
    category: FileCategory
    created_at: Optional[datetime] = None


# ============== Workbench Schemas ==============
class WorkbenchStats(BaseModel):
    case_count: int = 0
    review_count: int = 0
    plan_count: int = 0
    defect_count: int = 0


class ChartDataItem(BaseModel):
    label: str
    value: int


class WorkbenchCharts(BaseModel):
    case_by_level: List[ChartDataItem] = []
    defect_by_status: List[ChartDataItem] = []
    case_by_week: List[ChartDataItem] = []
    defect_by_severity: List[ChartDataItem] = []


class MyItem(BaseModel):
    id: int
    name: str
    type: str  # plan / review / defect
    status: str
    progress: Optional[float] = None
    created_at: Optional[datetime] = None


# ============== MessageConfig Schemas ==============
class BaseMessageConfig(BaseModel):
    id: int
    event_type: str
    target_type: str
    notify_methods: List[str]
    project_id: int


class MessageConfigCreate(BaseModel):
    event_type: str = Field(example="plan_exec_success")
    target_type: str = Field(example="creator")
    notify_methods: List[str] = Field(example=["in_app", "email"])
    project_id: int = Field(..., description="所属项目ID")


class MessageConfigUpdate(BaseModel):
    id: int
    event_type: str = Field(example="plan_exec_success")
    target_type: str = Field(example="creator")
    notify_methods: List[str] = Field(example=["in_app", "email"])
    project_id: int = Field(..., description="所属项目ID")


# ============== ReviewPlan Schemas ==============
class ReviewPlanCreate(BaseModel):
    name: str = Field(example="v1.0 版本用例评审")
    review_mode: str = Field("single", description="评审模式(single/multi)")
    project_id: int = Field(..., description="所属项目ID")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    desc: Optional[str] = ""
    tags: List[str] = []
    reviewer_ids: List[int] = []
    case_ids: List[int] = []


class ReviewPlanUpdate(BaseModel):
    id: int
    name: str = Field(example="v1.0 版本用例评审")
    review_mode: str = Field("single", description="评审模式(single/multi)")
    project_id: int = Field(..., description="所属项目ID")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    desc: Optional[str] = ""
    tags: List[str] = []
    reviewer_ids: List[int] = []
    case_ids: List[int] = []


class ReviewPlanCaseResult(BaseModel):
    id: int
    plan_id: int
    case_id: int
    case_name: Optional[str] = None
    review_result: Optional[ReviewResult] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None


class ReviewPlanCaseSubmit(BaseModel):
    plan_case_id: int = Field(..., description="评审计划-用例关联ID")
    review_result: ReviewResult = Field(..., description="评审结果")


class ReviewPlanProgress(BaseModel):
    total: int = 0
    unreviewed: int = 0
    pass_count: int = 0
    unpass_count: int = 0
    suggest: int = 0
    resubmit: int = 0
    percent: float = 0.0


# ============== Follow Schemas ==============
class FollowCreate(BaseModel):
    target_type: str = Field(..., description="目标类型(testcase/defect/plan/review_plan)")
    target_id: int = Field(..., description="目标ID")


class FollowItem(BaseModel):
    id: int
    target_type: str
    target_id: int
    name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


# ============== DefectComment Schemas ==============
class DefectCommentCreate(BaseModel):
    defect_id: int = Field(..., description="缺陷ID")
    content: str = Field(..., description="评论内容")
    parent_id: int = Field(0, description="父评论ID")


class DefectCommentSchema(BaseModel):
    id: int
    defect_id: int
    user_id: int
    username: Optional[str] = None
    content: str
    parent_id: int = 0
    created_at: Optional[datetime] = None
    replies: Optional[List["DefectCommentSchema"]] = []


# ============== ChangeHistory Schemas ==============
class ChangeHistorySchema(BaseModel):
    id: int
    target_type: str
    target_id: int
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by_id: int
    changed_by_name: Optional[str] = None
    changed_at: Optional[datetime] = None


# ============== TestPlan Manual Execution Schemas ==============
class StepResultCreate(BaseModel):
    step_number: int = Field(..., description="步骤序号")
    actual_result: Optional[str] = Field("", description="实际结果")
    step_exec_result: ExecResult = Field(ExecResult.PENDING, description="步骤执行结果")


class ManualExecSubmit(BaseModel):
    plan_case_id: int = Field(..., description="计划-用例关联ID")
    exec_result: ExecResult = Field(..., description="执行结果")
    step_results: List[StepResultCreate] = []
    comment: Optional[str] = Field("", description="评论")


# ============== Recycle Bin Schemas ==============
class RecycleBinItem(BaseModel):
    id: int
    name: str
    type: str  # testcase / module
    deleted_at: Optional[datetime] = None
    module_name: Optional[str] = None
    level: Optional[str] = None


# ============== Test Report Schemas ==============
class TestReportData(BaseModel):
    plan_id: int
    plan_name: str
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0
    pending: int = 0
    pass_rate: float = 0.0
    completion_rate: float = 0.0
    defect_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    case_details: List[dict] = []
