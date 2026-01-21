"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    # Store original participants
    original_participants = {
        name: list(details["participants"]) 
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original participants after test
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Soccer Team", "Basketball Club", "Drama Club",
            "Art Studio", "Debate Team", "Math Olympiad"
        ]
        
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        
        assert email in data["Soccer Team"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered"""
        # First signup
        client.post("/activities/Soccer Team/signup?email=duplicate@mergington.edu")
        
        # Second signup with same email
        response = client.post(
            "/activities/Soccer Team/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up"


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First signup
        email = "tounregister@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister removes the participant from the activity"""
        email = "toremove@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        
        assert email not in data["Soccer Team"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        """Test unregister when student is not signed up"""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"


class TestRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
