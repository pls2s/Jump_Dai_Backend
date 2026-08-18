"""Function 9 Creator Dashboard endpoints."""

import csv
import json
from datetime import date
from io import StringIO
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response, Security, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.dashboard import (
    CommonErrorDashboardResponse,
    CourseImprovementInsightDashboardResponse,
    CreatorDashboardResponse,
    LearnerDashboardResponse,
    ReportExportFormat,
    SkillGapDashboardResponse,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import MockCourse, mock_course_service
from app.services.dashboard_service import mock_dashboard_service

router = APIRouter(prefix="/creator/dashboard", tags=["creator-dashboard"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep successful dashboard responses in the documented envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the request and require a creator workspace role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"

    user = mock_auth_service.current_user(authorization)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A creator workspace is required for dashboard reports",
            },
        )
    return user


def _validate_date_range(date_from: Optional[date], date_to: Optional[date]) -> None:
    """Reject an invalid reporting range before analytics are calculated."""
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_DATE_RANGE",
                "message": "date_from must be on or before date_to",
            },
        )


def _dashboard_report(
    *,
    user: MockUser,
    course_id: Optional[int],
    date_from: Optional[date],
    date_to: Optional[date],
) -> dict:
    """Load only courses owned by the caller, then build their report."""
    courses = _dashboard_courses(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    return mock_dashboard_service.build_dashboard(
        courses=courses,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )


def _dashboard_courses(
    *,
    user: MockUser,
    course_id: Optional[int],
    date_from: Optional[date],
    date_to: Optional[date],
) -> list[MockCourse]:
    """Resolve the owned Course scope shared by every dashboard section."""
    _validate_date_range(date_from, date_to)
    return (
        [mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)]
        if course_id is not None
        else mock_course_service.list_for_creator(creator_id=user.id)
    )


def _dashboard_filters(
    *,
    course_id: Optional[int],
    date_from: Optional[date],
    date_to: Optional[date],
) -> dict:
    """Build the common filter object returned by section endpoints."""
    return {
        "course_id": course_id,
        "date_from": date_from,
        "date_to": date_to,
    }


@router.get(
    "",
    response_model=SuccessResponse[CreatorDashboardResponse],
)
def read_creator_dashboard(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return learner, assessment, error, gap, and improvement analytics."""
    user = _require_creator(credentials)
    report = _dashboard_report(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    return _success(report)


def _section_response(filters: dict, items: list[dict]) -> dict:
    """Keep independently fetched sections tied to the same report filters."""
    return _success({"filters": filters, "items": items})


@router.get(
    "/learners",
    response_model=SuccessResponse[LearnerDashboardResponse],
)
def read_dashboard_learners(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return a searchable, paginated learner-progress section."""
    user = _require_creator(credentials)
    courses = _dashboard_courses(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    normalized_search = search.strip() if search else None
    learners = mock_dashboard_service.learner_progress(
        courses=courses,
        date_from=date_from,
        date_to=date_to,
    )
    if normalized_search:
        search_term = normalized_search.casefold()
        learners = [
            learner
            for learner in learners
            if search_term in learner["learner_name"].casefold()
        ]

    total_items = len(learners)
    total_pages = (total_items + page_size - 1) // page_size
    start = (page - 1) * page_size
    return _success(
        {
            "filters": {
                **_dashboard_filters(
                    course_id=course_id,
                    date_from=date_from,
                    date_to=date_to,
                ),
                "search": normalized_search,
            },
            "items": learners[start : start + page_size],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
            },
        }
    )


@router.get(
    "/errors",
    response_model=SuccessResponse[CommonErrorDashboardResponse],
)
def read_dashboard_common_errors(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return common-error analysis without loading the learner table."""
    user = _require_creator(credentials)
    courses = _dashboard_courses(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    return _section_response(
        _dashboard_filters(
            course_id=course_id,
            date_from=date_from,
            date_to=date_to,
        ),
        mock_dashboard_service.common_errors(
            courses=courses,
            date_from=date_from,
            date_to=date_to,
        ),
    )


@router.get(
    "/skill-gaps",
    response_model=SuccessResponse[SkillGapDashboardResponse],
)
def read_dashboard_skill_gaps(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return skill-gap analysis without loading other dashboard sections."""
    user = _require_creator(credentials)
    courses = _dashboard_courses(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    return _section_response(
        _dashboard_filters(
            course_id=course_id,
            date_from=date_from,
            date_to=date_to,
        ),
        mock_dashboard_service.skill_gaps(
            courses=courses,
            date_from=date_from,
            date_to=date_to,
        ),
    )


@router.get(
    "/insights",
    response_model=SuccessResponse[CourseImprovementInsightDashboardResponse],
)
def read_dashboard_insights(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return improvement recommendations without loading learner data."""
    user = _require_creator(credentials)
    courses = _dashboard_courses(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    return _section_response(
        _dashboard_filters(
            course_id=course_id,
            date_from=date_from,
            date_to=date_to,
        ),
        mock_dashboard_service.improvement_insights(
            courses=courses,
            date_from=date_from,
            date_to=date_to,
        ),
    )


@router.get("/export")
def export_creator_dashboard(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    export_format: ReportExportFormat = Query(default=ReportExportFormat.CSV, alias="format"),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Response:
    """Export the creator's filtered dashboard report as CSV, JSON, or PDF."""
    user = _require_creator(credentials)
    report = _dashboard_report(
        user=user,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )
    filename_base = "creator-dashboard-report"
    if export_format is ReportExportFormat.JSON:
        return Response(
            content=json.dumps(jsonable_encoder(report), ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_base}.json"',
            },
        )

    if export_format is ReportExportFormat.PDF:
        return Response(
            content=mock_dashboard_service.export_pdf(report),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_base}.pdf"',
            },
        )

    fieldnames = [
        "course_id",
        "course_title",
        "learner_id",
        "learner_name",
        "progress_percentage",
        "completed",
        "assessment_score",
        "last_activity_at",
        "common_errors",
        "skill_gaps",
    ]
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(mock_dashboard_service.export_rows(report))
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_base}.csv"',
        },
    )
