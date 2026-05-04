from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class TestCaseLevel(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ReviewResult(StrEnum):
    PASS = "pass"
    RESUBMIT = "resubmit"
    FAIL = "fail"
    # 与《功能细节交互》中「通过 / 失败 / 建议」的建议项对应
    SUGGEST = "suggest"


class ExecResult(StrEnum):
    SUCCESS = "success"
    FAIL = "fail"
    PENDING = "pending"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class CaseStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DefectStatus(StrEnum):
    NEW = "new"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    CLOSED = "closed"


class DefectSeverity(StrEnum):
    TRIVIAL = "trivial"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FileCategory(StrEnum):
    COMMON = "common"
    TEST_CASE = "test_case"
    DEFECT = "defect"
    TEMPLATE = "template"
