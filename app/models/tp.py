from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import (
    CaseStatus,
    DefectSeverity,
    DefectStatus,
    ExecResult,
    FileCategory,
    PlanStatus,
    ReviewResult,
    TestCaseLevel,
)


class Project(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=100, unique=True, description="项目名称", index=True)
    organization = fields.CharField(max_length=100, null=True, description="所属组织")
    desc = fields.CharField(max_length=500, null=True, description="项目描述")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)

    class Meta:
        table = "project"


class ProjectMember(BaseModel, TimestampMixin):
    project = fields.ForeignKeyField("models.Project", related_name="members", description="项目")
    user = fields.ForeignKeyField("models.User", related_name="project_memberships", description="成员")
    role = fields.CharField(max_length=20, default="tester", description="项目角色(admin/tester/developer)")

    class Meta:
        table = "project_member"


class Module(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=100, description="模块名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="备注")
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, description="父模块ID", index=True)
    project = fields.ForeignKeyField("models.Project", related_name="modules", description="所属项目")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)

    class Meta:
        table = "module"


class ModuleClosure(BaseModel, TimestampMixin):
    ancestor = fields.IntField(description="祖先模块ID", index=True)
    descendant = fields.IntField(description="后代模块ID", index=True)
    level = fields.IntField(default=0, description="深度", index=True)

    class Meta:
        table = "module_closure"


class TestCase(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=200, description="用例名称", index=True)
    module = fields.ForeignKeyField("models.Module", related_name="test_cases", null=True, description="所属模块")
    project = fields.ForeignKeyField("models.Project", related_name="test_cases", description="所属项目")
    level = fields.CharEnumField(TestCaseLevel, default=TestCaseLevel.P2, description="用例等级", index=True)
    precondition = fields.TextField(null=True, description="前置条件（富文本）")
    remark = fields.TextField(null=True, description="备注（富文本）")
    tags = fields.JSONField(null=True, default=[], description="标签列表")
    review_result = fields.CharEnumField(ReviewResult, null=True, description="评审结果")
    exec_result = fields.CharEnumField(ExecResult, default=ExecResult.PENDING, description="执行结果")
    status = fields.CharEnumField(CaseStatus, default=CaseStatus.DRAFT, description="用例状态", index=True)
    creator = fields.ForeignKeyField("models.User", related_name="created_cases", description="创建人")
    reviewer = fields.ForeignKeyField("models.User", related_name="reviewed_cases", null=True, description="评审人")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        table = "test_case"


class TestCaseStep(BaseModel, TimestampMixin):
    test_case = fields.ForeignKeyField("models.TestCase", related_name="steps", description="所属用例")
    step_number = fields.IntField(description="步骤序号")
    action = fields.TextField(description="测试步骤")
    expected_result = fields.TextField(description="预期结果")
    sort_order = fields.IntField(default=0, description="排序")

    class Meta:
        table = "test_case_step"
        ordering = ["sort_order"]


class Defect(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=200, description="缺陷名称", index=True)
    status = fields.CharEnumField(DefectStatus, default=DefectStatus.NEW, description="缺陷状态", index=True)
    severity = fields.CharEnumField(DefectSeverity, default=DefectSeverity.MINOR, description="严重程度", index=True)
    handler = fields.ForeignKeyField("models.User", related_name="handled_defects", null=True, description="处理人")
    creator = fields.ForeignKeyField("models.User", related_name="created_defects", description="创建人")
    project = fields.ForeignKeyField("models.Project", related_name="defects", description="所属项目")
    plan = fields.ForeignKeyField("models.TestPlan", related_name="defects", null=True, description="关联测试计划")
    content = fields.TextField(null=True, description="缺陷内容（富文本）")

    class Meta:
        table = "defect"


class DefectCase(BaseModel):
    defect = fields.ForeignKeyField("models.Defect", related_name="defect_cases", description="缺陷")
    case = fields.ForeignKeyField("models.TestCase", related_name="defect_refs", description="关联用例")

    class Meta:
        table = "defect_case"


class TestPlan(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=200, description="计划名称", index=True)
    status = fields.CharEnumField(PlanStatus, default=PlanStatus.DRAFT, description="计划状态", index=True)
    project = fields.ForeignKeyField("models.Project", related_name="test_plans", description="所属项目")
    creator = fields.ForeignKeyField("models.User", related_name="created_plans", description="创建人")
    start_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    desc = fields.CharField(max_length=500, null=True, description="计划描述")

    class Meta:
        table = "test_plan"


class TestPlanCase(BaseModel):
    plan = fields.ForeignKeyField("models.TestPlan", related_name="plan_cases", description="测试计划")
    case = fields.ForeignKeyField("models.TestCase", related_name="plan_refs", description="测试用例")
    exec_result = fields.CharEnumField(ExecResult, default=ExecResult.PENDING, description="执行结果")
    executed_at = fields.DatetimeField(null=True, description="执行时间")
    executor = fields.ForeignKeyField("models.User", related_name="executed_cases", null=True, description="执行人")

    class Meta:
        table = "test_plan_case"


class File(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=255, description="文件名")
    path = fields.CharField(max_length=500, description="文件路径")
    size = fields.BigIntField(description="文件大小(字节)")
    file_type = fields.CharField(max_length=50, null=True, description="文件MIME类型")
    project = fields.ForeignKeyField("models.Project", related_name="files", null=True, description="所属项目")
    uploader = fields.ForeignKeyField("models.User", related_name="uploaded_files", description="上传人")
    category = fields.CharEnumField(FileCategory, default=FileCategory.COMMON, description="文件分类")

    class Meta:
        table = "file"


class MessageConfig(BaseModel, TimestampMixin):
    event_type = fields.CharField(max_length=50, description="事件类型", index=True)
    target_type = fields.CharField(max_length=50, description="通知对象", index=True)
    notify_methods = fields.JSONField(default=[], description="通知方式")
    project = fields.ForeignKeyField("models.Project", related_name="message_configs", description="所属项目")

    class Meta:
        table = "message_config"


class ReviewPlan(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=200, description="评审名称", index=True)
    status = fields.CharEnumField(PlanStatus, default=PlanStatus.DRAFT, description="评审状态", index=True)
    review_mode = fields.CharField(max_length=20, default="single", description="评审模式(single/multi)")
    project = fields.ForeignKeyField("models.Project", related_name="review_plans", description="所属项目")
    creator = fields.ForeignKeyField("models.User", related_name="created_reviews", description="创建人")
    start_time = fields.DatetimeField(null=True, description="评审开始时间")
    end_time = fields.DatetimeField(null=True, description="评审截止时间")
    desc = fields.CharField(max_length=500, null=True, description="评审描述")
    tags = fields.JSONField(null=True, default=[], description="标签列表")

    class Meta:
        table = "review_plan"


class ReviewPlanCase(BaseModel, TimestampMixin):
    plan = fields.ForeignKeyField("models.ReviewPlan", related_name="plan_cases", description="评审计划")
    case = fields.ForeignKeyField("models.TestCase", related_name="review_refs", description="测试用例")
    review_result = fields.CharEnumField(ReviewResult, null=True, description="评审结果")
    reviewed_at = fields.DatetimeField(null=True, description="评审时间")
    reviewer = fields.ForeignKeyField("models.User", related_name="review_records", null=True, description="评审人")

    class Meta:
        table = "review_plan_case"


class ReviewPlanReviewer(BaseModel, TimestampMixin):
    plan = fields.ForeignKeyField("models.ReviewPlan", related_name="reviewers", description="评审计划")
    user = fields.ForeignKeyField("models.User", related_name="review_assignments", description="评审人")

    class Meta:
        table = "review_plan_reviewer"


class DefectComment(BaseModel, TimestampMixin):
    defect = fields.ForeignKeyField("models.Defect", related_name="comments", description="缺陷")
    user = fields.ForeignKeyField("models.User", related_name="defect_comments", description="评论人")
    content = fields.TextField(description="评论内容")
    parent_id = fields.IntField(default=0, description="父评论ID(用于回复)")

    class Meta:
        table = "defect_comment"


class ChangeHistory(BaseModel):
    target_type = fields.CharField(max_length=50, description="目标类型(testcase/defect/plan)")
    target_id = fields.IntField(description="目标ID", index=True)
    field_name = fields.CharField(max_length=100, description="变更字段")
    old_value = fields.TextField(null=True, description="旧值")
    new_value = fields.TextField(null=True, description="新值")
    changed_by = fields.ForeignKeyField("models.User", related_name="changes", description="变更人")
    changed_at = fields.DatetimeField(auto_now_add=True, description="变更时间")

    class Meta:
        table = "change_history"


class Follow(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="follows", description="关注人")
    target_type = fields.CharField(max_length=50, description="目标类型(testcase/defect/plan/review_plan)")
    target_id = fields.IntField(description="目标ID", index=True)
    created_at = fields.DatetimeField(auto_now_add=True, description="关注时间")

    class Meta:
        table = "follow"


class TestPlanCaseStepResult(BaseModel, TimestampMixin):
    plan_case = fields.ForeignKeyField("models.TestPlanCase", related_name="step_results", description="计划用例")
    step_number = fields.IntField(description="步骤序号")
    actual_result = fields.TextField(null=True, description="实际结果")
    step_exec_result = fields.CharEnumField(ExecResult, default=ExecResult.PENDING, description="步骤执行结果")

    class Meta:
        table = "test_plan_case_step_result"
