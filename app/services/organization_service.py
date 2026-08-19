"""Read-only access to the learning-focused Organization mock fixture."""

from fastapi import HTTPException, status

from app.data.mock_organization import organization_snapshot


class MockOrganizationService:
    """Expose the isolated organization fixture without mutating it."""

    def snapshot(self) -> dict:
        return organization_snapshot()

    def course(self, course_id: str) -> dict:
        for course in self.snapshot()["courses"]:
            if course["id"] == course_id:
                return course
        self._not_found("ORGANIZATION_COURSE_NOT_FOUND", "This course is not in the organization workspace")

    def learner(self, learner_id: str) -> dict:
        for learner in self.snapshot()["learners"]:
            if learner["id"] == learner_id:
                return learner
        self._not_found("ORGANIZATION_LEARNER_NOT_FOUND", "This learner is not in the organization workspace")

    @staticmethod
    def _not_found(code: str, message: str) -> None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": code, "message": message})


mock_organization_service = MockOrganizationService()
