"""Static, learning-only data served by the mock Organization workspace API."""

from copy import deepcopy


MOCK_ORGANIZATION_SNAPSHOT: dict = {
    "organization": {
        "id": "skillsync-demo-organization",
        "name": "SkillSync Demo Organization",
        "learning_focus": "Practical digital and customer experience skills",
    },
    "totals": {
        "active_courses": 2,
        "active_learners": 128,
        "completion_rate": 72,
        "verified_skills": 246,
        "average_improvement": 29,
    },
    "courses": [
        {
            "id": "digital-marketing-foundations",
            "title": "Digital Marketing Foundations",
            "status": "published",
            "updated_at": "Updated today",
            "owner_name": "Creator Demo",
            "analytics": {
                "course_id": "digital-marketing-foundations",
                "title": "Digital Marketing Foundations",
                "status": "published",
                "learner_count": 164,
                "active_learners": 128,
                "course_starts": 164,
                "completions": 118,
                "completion_rate": 72,
                "average_assessment_score": 78,
                "practical_pass_rate": 69,
                "verified_skills": 246,
                "funnel": [
                    {"id": "started", "label": "Started course", "value": 164},
                    {"id": "onboarding", "label": "Completed onboarding", "value": 151},
                    {"id": "pre-assessment", "label": "Completed Pre-Assessment", "value": 144},
                    {"id": "learning-path", "label": "Started Learning Path", "value": 138},
                    {"id": "learning", "label": "Completed learning", "value": 126},
                    {"id": "assessment", "label": "Completed assessment", "value": 121},
                    {"id": "practical", "label": "Completed practical", "value": 118},
                    {"id": "completed", "label": "Completed course", "value": 118},
                ],
                "assessment": {
                    "pre_assessment_average": 52,
                    "post_assessment_average": 78,
                    "average_improvement": 26,
                    "practical_pass_rate": 69,
                },
                "skills": [
                    {"skill_id": "skill-customer-journey", "name": "Customer Journey", "pre_score": 40, "post_score": 82, "improvement": 42, "practical_pass_rate": 72, "retry_rate": 8, "common_challenge": "Connecting touchpoints to a measurable next action."},
                    {"skill_id": "skill-campaign-measurement", "name": "Campaign Measurement", "pre_score": 30, "post_score": 70, "improvement": 40, "practical_pass_rate": 54, "retry_rate": 22, "common_challenge": "Selecting outcome metrics instead of activity-only metrics."},
                    {"skill_id": "skill-channel-strategy", "name": "Channel Strategy", "pre_score": 60, "post_score": 78, "improvement": 18, "practical_pass_rate": 68, "retry_rate": 13, "common_challenge": "Explaining why a channel fits both audience and objective."},
                    {"skill_id": "skill-marketing-fundamentals", "name": "Marketing Fundamentals", "pre_score": 75, "post_score": 90, "improvement": 15, "practical_pass_rate": 81, "retry_rate": 5, "common_challenge": "Distinguishing funnel stages in less familiar scenarios."},
                ],
                "content": [
                    {"id": "content-metrics", "title": "Choosing the Right KPIs", "content_type": "Lesson", "completion_rate": 61, "quiz_score": 58, "retry_rate": 22},
                    {"id": "content-journey", "title": "Mapping the Customer Journey", "content_type": "Lesson", "completion_rate": 84, "quiz_score": 81, "retry_rate": 9},
                    {"id": "content-channels", "title": "Selecting Channels for Campaign Goals", "content_type": "Practice", "completion_rate": 76, "quiz_score": 74, "retry_rate": 14},
                    {"id": "content-funnel", "title": "Marketing Funnel Refresher", "content_type": "Quiz", "completion_rate": 93, "quiz_score": 88, "retry_rate": 4},
                ],
            },
        },
        {
            "id": "ai-productivity-basics",
            "title": "AI Productivity Basics",
            "status": "published",
            "updated_at": "Published 8 days ago",
            "owner_name": "Creator Demo",
            "analytics": {
                "course_id": "ai-productivity-basics",
                "title": "AI Productivity Basics",
                "status": "published",
                "learner_count": 0,
                "active_learners": 0,
                "course_starts": 0,
                "completions": 0,
                "completion_rate": 0,
                "average_assessment_score": 0,
                "practical_pass_rate": 0,
                "verified_skills": 0,
                "funnel": [],
                "assessment": {"pre_assessment_average": 0, "post_assessment_average": 0, "average_improvement": 0, "practical_pass_rate": 0},
                "skills": [],
                "content": [],
            },
        },
        {"id": "customer-experience-essentials", "title": "Customer Experience Essentials", "status": "review", "updated_at": "Updated yesterday", "owner_name": "Maya Rodriguez", "analytics": None},
        {"id": "customer-interview-essentials", "title": "Customer Interview Essentials", "status": "draft", "updated_at": "Updated 3 days ago", "owner_name": "Jordan Lee", "analytics": None},
        {"id": "content-planning-workshop", "title": "Content Planning Workshop", "status": "unpublished", "updated_at": "Unpublished 12 days ago", "owner_name": "Creator Demo", "analytics": None},
    ],
    "learners": [
        {"id": "learner-maya-chen", "name": "Maya Chen", "current_learning": [{"course_id": "digital-marketing-foundations", "course_title": "Digital Marketing Foundations", "progress": 100, "status": "completed"}], "completed_courses": 1, "verified_skills": ["Customer Journey", "Marketing Fundamentals", "Channel Strategy"], "last_activity": "Completed Digital Marketing Foundations today"},
        {"id": "learner-noah-williams", "name": "Noah Williams", "current_learning": [{"course_id": "digital-marketing-foundations", "course_title": "Digital Marketing Foundations", "progress": 78, "status": "active"}], "completed_courses": 0, "verified_skills": ["Marketing Fundamentals"], "last_activity": "Submitted the practical assessment yesterday"},
        {"id": "learner-priya-shah", "name": "Priya Shah", "current_learning": [{"course_id": "digital-marketing-foundations", "course_title": "Digital Marketing Foundations", "progress": 62, "status": "active"}], "completed_courses": 0, "verified_skills": ["Customer Journey"], "last_activity": "Completed Customer Journey practice yesterday"},
        {"id": "learner-ethan-kim", "name": "Ethan Kim", "current_learning": [{"course_id": "digital-marketing-foundations", "course_title": "Digital Marketing Foundations", "progress": 44, "status": "active"}], "completed_courses": 0, "verified_skills": [], "last_activity": "Continued Channel Strategy 2 days ago"},
        {"id": "learner-sofia-martin", "name": "Sofia Martin", "current_learning": [{"course_id": "digital-marketing-foundations", "course_title": "Digital Marketing Foundations", "progress": 18, "status": "active"}], "completed_courses": 0, "verified_skills": [], "last_activity": "Completed the Pre-Assessment 3 days ago"},
        {"id": "learner-liam-brown", "name": "Liam Brown", "current_learning": [{"course_id": "ai-productivity-basics", "course_title": "AI Productivity Basics", "progress": 0, "status": "not-started"}], "completed_courses": 0, "verified_skills": [], "last_activity": "Course access assigned 4 days ago"},
    ],
    "skills": [
        {"skill_id": "skill-customer-journey", "name": "Customer Journey", "pre_score": 40, "post_score": 82, "improvement": 42, "practical_pass_rate": 72, "retry_rate": 8, "common_challenge": "Connecting touchpoints to a measurable next action.", "learner_count": 82, "coverage": "strong"},
        {"skill_id": "skill-campaign-measurement", "name": "Campaign Measurement", "pre_score": 30, "post_score": 70, "improvement": 40, "practical_pass_rate": 54, "retry_rate": 22, "common_challenge": "Selecting outcome metrics instead of activity-only metrics.", "learner_count": 64, "coverage": "needs-attention"},
        {"skill_id": "skill-channel-strategy", "name": "Channel Strategy", "pre_score": 60, "post_score": 78, "improvement": 18, "practical_pass_rate": 68, "retry_rate": 13, "common_challenge": "Explaining why a channel fits both audience and objective.", "learner_count": 68, "coverage": "developing"},
        {"skill_id": "skill-marketing-fundamentals", "name": "Marketing Fundamentals", "pre_score": 75, "post_score": 90, "improvement": 15, "practical_pass_rate": 81, "retry_rate": 5, "common_challenge": "Distinguishing funnel stages in less familiar scenarios.", "learner_count": 96, "coverage": "strong"},
    ],
    "recent_activity": [
        {"id": "activity-completion", "label": "Course completion", "detail": "Maya Chen completed Digital Marketing Foundations.", "occurred_at": "Today"},
        {"id": "activity-practical", "label": "Practical assessment", "detail": "Noah Williams submitted a Digital Campaign Plan.", "occurred_at": "Yesterday"},
        {"id": "activity-skill", "label": "Verified skill", "detail": "12 Customer Journey skill records were verified this week.", "occurred_at": "2 days ago"},
    ],
}


def organization_snapshot() -> dict:
    """Return an isolated copy so test or request code cannot mutate the fixture."""
    return deepcopy(MOCK_ORGANIZATION_SNAPSHOT)
