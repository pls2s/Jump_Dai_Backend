"""Function 9 Creator Dashboard endpoints."""

import csv
import json
from datetime import date
from io import StringIO
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response, Security, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.dashboard import CreatorDashboardResponse, ReportExportFormat
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service
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
    _validate_date_range(date_from, date_to)
    courses = (
        [mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)]
        if course_id is not None
        else mock_course_service.list_for_creator(creator_id=user.id)
    )
    return mock_dashboard_service.build_dashboard(
        courses=courses,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
    )


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


@router.get("/export")
def export_creator_dashboard(
    course_id: Optional[int] = Query(default=None, ge=1),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    export_format: ReportExportFormat = Query(default=ReportExportFormat.CSV, alias="format"),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Response:
    """Export the creator's filtered dashboard report as CSV or JSON."""
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
