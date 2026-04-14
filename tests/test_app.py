import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestActivitiesEndpoint:
    """Test GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Should return all activities from the database"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activities_have_required_fields(self):
        """Each activity should have required fields"""
        response = client.get("/activities")
        activities = response.json()
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test POST /activities/{activity_name}/signup endpoint"""

    def test_signup_student_for_activity(self):
        """Should successfully sign up a student for an activity"""
        test_email = "test_student@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={test_email}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert test_email in result["message"]

    def test_signup_student_already_registered(self):
        """Should return 400 if student is already signed up"""
        test_email = "michael@mergington.edu"  # Already registered for Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={test_email}"
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"].lower()

    def test_signup_for_nonexistent_activity(self):
        """Should return 404 for non-existent activity"""
        test_email = "test@mergington.edu"
        response = client.post(
            f"/activities/Nonexistent Club/signup?email={test_email}"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_signup_adds_participant_to_activity(self):
        """Verify that signup actually adds the participant to the activity"""
        test_email = "new_student@mergington.edu"
        # First, get initial state
        response = client.get("/activities")
        initial_activities = response.json()
        initial_count = len(initial_activities["Programming Class"]["participants"])

        # Sign up
        signup_response = client.post(
            f"/activities/Programming Class/signup?email={test_email}"
        )
        assert signup_response.status_code == 200

        # Verify participant was added
        response = client.get("/activities")
        updated_activities = response.json()
        final_count = len(updated_activities["Programming Class"]["participants"])
        assert final_count == initial_count + 1
        assert test_email in updated_activities["Programming Class"]["participants"]


class TestRemoveParticipantEndpoint:
    """Test DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_from_activity(self):
        """Should successfully unregister a student from an activity"""
        test_email = "daniel@mergington.edu"  # Registered for Chess Club
        response = client.delete(
            f"/activities/Chess Club/participants?email={test_email}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_remove_nonexistent_participant(self):
        """Should return 404 if participant is not registered"""
        response = client.delete(
            f"/activities/Chess Club/participants?email=notexist@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_remove_participant_from_nonexistent_activity(self):
        """Should return 404 if activity does not exist"""
        response = client.delete(
            f"/activities/Nonexistent Club/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_remove_reduces_participant_count(self):
        """Verify that removing a participant reduces the count"""
        test_email = "emma@mergington.edu"  # Registered for Programming Class
        # Get initial state
        response = client.get("/activities")
        initial_activities = response.json()
        initial_count = len(initial_activities["Programming Class"]["participants"])

        # Remove participant
        remove_response = client.delete(
            f"/activities/Programming Class/participants?email={test_email}"
        )
        assert remove_response.status_code == 200

        # Verify participant was removed
        response = client.get("/activities")
        updated_activities = response.json()
        final_count = len(updated_activities["Programming Class"]["participants"])
        assert final_count == initial_count - 1
        assert test_email not in updated_activities["Programming Class"]["participants"]


class TestRootEndpoint:
    """Test GET / endpoint"""

    def test_root_redirects_to_index(self):
        """Root endpoint should redirect to static index page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
