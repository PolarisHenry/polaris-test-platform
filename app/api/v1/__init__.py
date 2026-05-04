from fastapi import APIRouter

from app.core.dependency import DependPermission

from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .changehistories import change_history_router
from .comments import comment_router
from .defects import defect_router
from .depts import depts_router
from .files import file_router
from .follows import follow_router
from .menus import menus_router
from .modules import module_router
from .msgconfigs import msgconfig_router
from .projects import project_router
from .reviews import review_router
from .roles import roles_router
from .testcases import testcase_router
from .testplans import testplan_router
from .users import users_router
from .workbench import workbench_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(project_router, prefix="/project", dependencies=[DependPermission])
v1_router.include_router(module_router, prefix="/module", dependencies=[DependPermission])
v1_router.include_router(testcase_router, prefix="/testcase", dependencies=[DependPermission])
v1_router.include_router(defect_router, prefix="/defect", dependencies=[DependPermission])
v1_router.include_router(testplan_router, prefix="/testplan", dependencies=[DependPermission])
v1_router.include_router(file_router, prefix="/file", dependencies=[DependPermission])
v1_router.include_router(msgconfig_router, prefix="/msgconfig", dependencies=[DependPermission])
v1_router.include_router(workbench_router, prefix="/workbench", dependencies=[DependPermission])
v1_router.include_router(review_router, prefix="/review", dependencies=[DependPermission])
v1_router.include_router(follow_router, prefix="/follow", dependencies=[DependPermission])
v1_router.include_router(comment_router, prefix="/comment", dependencies=[DependPermission])
v1_router.include_router(change_history_router, prefix="/change_history", dependencies=[DependPermission])
