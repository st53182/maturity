"""
Performance Improvements and Database Optimization Recommendations

This file contains helper functions and recommendations for improving
database query performance in the maturity assessment application.
"""

from sqlalchemy import Index
from database import db
from models import Assessment, Team, Conflict, Employee, User


"""
-- Recommended database indexes for performance optimization
-- Run these SQL commands in your database:

CREATE INDEX idx_assessment_team_id ON assessment(team_id);
CREATE INDEX idx_assessment_user_id ON assessment(user_id);
CREATE INDEX idx_assessment_created_at ON assessment(created_at);
CREATE INDEX idx_assessment_team_user_created ON assessment(team_id, user_id, created_at);

CREATE INDEX idx_conflict_user_id ON conflict(user_id);
CREATE INDEX idx_conflict_created_at ON conflict(created_at);

CREATE INDEX idx_employee_user_id ON employee(user_id);
CREATE INDEX idx_employee_team_id ON employee(team_id);

CREATE INDEX idx_team_user_id ON team(user_id);

CREATE INDEX idx_participant_room_id ON participant(room_id);
CREATE INDEX idx_vote_room_id ON vote(room_id);
CREATE INDEX idx_vote_participant_id ON vote(participant_id);
"""

def get_teams_with_latest_assessments_optimized(user_id):
    """
    Optimized version of getting teams with their latest assessments.
    This replaces the N+1 query pattern with a single optimized query.
    
    Args:
        user_id: The user ID to filter teams for
        
    Returns:
        List of tuples (Team, latest_assessment_id)
    """
    latest_assessment_subquery = (
        db.session.query(
            Assessment.team_id,
            db.func.max(Assessment.created_at).label('max_created_at')
        )
        .filter_by(user_id=user_id)
        .group_by(Assessment.team_id)
        .subquery()
    )
    
    return (
        db.session.query(Team, Assessment.id.label('latest_assessment_id'))
        .filter_by(user_id=user_id)
        .outerjoin(
            latest_assessment_subquery,
            Team.id == latest_assessment_subquery.c.team_id
        )
        .outerjoin(
            Assessment,
            db.and_(
                Assessment.team_id == Team.id,
                Assessment.user_id == user_id,
                Assessment.created_at == latest_assessment_subquery.c.max_created_at
            )
        )
        .all()
    )

def get_team_assessments_aggregated(team_id):
    """
    Get aggregated assessment data for a team using database functions
    instead of Python processing.
    
    Args:
        team_id: The team ID to get assessments for
        
    Returns:
        Query result with aggregated assessment data
    """
    from models import Question
    
    return (
        db.session.query(
            Question.category,
            Question.subcategory,
            db.func.avg(Assessment.score).label("average_score"),
            db.func.count(Assessment.id).label("assessment_count"),
            db.func.max(Assessment.created_at).label("latest_assessment")
        )
        .join(Assessment, Question.id == Assessment.question_id)
        .filter(Assessment.team_id == team_id)
        .group_by(Question.category, Question.subcategory)
        .all()
    )

def get_employees_with_teams_optimized(user_id):
    """
    Get employees with their team information using eager loading
    to avoid N+1 queries.
    
    Args:
        user_id: The user ID to filter employees for
        
    Returns:
        List of Employee objects with eagerly loaded team relationships
    """
    from sqlalchemy.orm import joinedload
    
    return (
        Employee.query
        .options(joinedload(Employee.team))
        .filter_by(user_id=user_id)
        .all()
    )

def get_planning_participants_with_votes_optimized(room_id):
    """
    Get planning poker participants with their votes in a single query.
    
    Args:
        room_id: The room ID to get participants for
        
    Returns:
        Query result with participants and their vote information
    """
    from models import Participant, Vote
    
    return (
        db.session.query(
            Participant,
            Vote.points.label('vote_points')
        )
        .filter(Participant.room_id == room_id)
        .outerjoin(
            Vote,
            db.and_(
                Vote.participant_id == Participant.id,
                Vote.room_id == room_id
            )
        )
        .all()
    )

"""
1. Always use indexes on foreign keys and frequently filtered columns
2. Use database aggregation functions instead of Python processing
3. Combine related queries using joins instead of separate queries
4. Use eager loading (joinedload) for relationships that will be accessed
5. Consider using subqueries for complex filtering conditions
6. Limit result sets early in the query chain
7. Use database-specific optimizations when available (e.g., PostgreSQL window functions)
"""
