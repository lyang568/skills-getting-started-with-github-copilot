import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data after each test to ensure isolation."""
    # Define the original activities data
    original_data = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for intramural and league games",
            "schedule": "Tuesdays and Thursdays, 4:30 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Tennis Club": {
            "description": "Learn tennis skills and participate in friendly matches",
            "schedule": "Saturdays, 10:00 AM - 11:30 AM",
            "max_participants": 16,
            "participants": []
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and various art mediums",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": []
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills through competitive debate",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 14,
            "participants": []
        },
        "Science Club": {
            "description": "Conduct experiments and explore advanced scientific concepts",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        }
    }

    # Reset activities to original state
    activities.clear()
    activities.update(original_data)
    yield


class TestGetActivities:
    """Test the GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities

        # Check that all expected activities are present
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Drama Club", "Art Studio", "Debate Team", "Science Club"
        ]
        for activity in expected_activities:
            assert activity in data
            assert "description" in data[activity]
            assert "schedule" in data[activity]
            assert "max_participants" in data[activity]
            assert "participants" in data[activity]
            assert isinstance(data[activity]["participants"], list)

    def test_activity_data_structure(self, client):
        """Test that activity data has the correct structure."""
        response = client.get("/activities")
        data = response.json()

        # Test Chess Club structure (has participants)
        chess_club = data["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]

        # Test Basketball Team structure (no participants)
        basketball = data["Basketball Team"]
        assert basketball["description"] == "Competitive basketball team for intramural and league games"
        assert basketball["schedule"] == "Tuesdays and Thursdays, 4:30 PM - 6:00 PM"
        assert basketball["max_participants"] == 15
        assert basketball["participants"] == []


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client):
        """Test successful signup for an activity."""
        # Use an activity with no current participants
        response = client.post("/activities/Basketball%20Team/signup?email=test@mergington.edu")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Basketball Team"]["participants"]

    def test_duplicate_signup(self, client):
        """Test that signing up twice returns an error."""
        # First signup
        client.post("/activities/Basketball%20Team/signup?email=test@mergington.edu")

        # Second signup with same email
        response = client.post("/activities/Basketball%20Team/signup?email=test@mergington.edu")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self, client):
        """Test signup for non-existent activity."""
        response = client.post("/activities/NonExistent%20Activity/signup?email=test@mergington.edu")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_existing_participant(self, client):
        """Test signup with email already in Chess Club."""
        response = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]


class TestRemoveParticipant:
    """Test the DELETE /activities/{activity_name}/participants endpoint."""

    def test_successful_removal(self, client):
        """Test successful removal of a participant."""
        # First add a participant
        client.post("/activities/Basketball%20Team/signup?email=test@mergington.edu")

        # Then remove them
        response = client.delete("/activities/Basketball%20Team/participants?email=test@mergington.edu")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" not in activities_data["Basketball Team"]["participants"]

    def test_remove_nonexistent_participant(self, client):
        """Test removing a participant who is not signed up."""
        response = client.delete("/activities/Chess%20Club/participants?email=nonexistent@mergington.edu")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Participant not found" in data["detail"]

    def test_remove_from_invalid_activity(self, client):
        """Test removing from non-existent activity."""
        response = client.delete("/activities/NonExistent%20Activity/participants?email=test@mergington.edu")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_remove_existing_participant(self, client):
        """Test removing an existing participant from Chess Club."""
        initial_count = len(activities["Chess Club"]["participants"])

        response = client.delete("/activities/Chess%20Club/participants?email=michael@mergington.edu")
        assert response.status_code == 200

        # Verify count decreased
        final_count = len(activities["Chess Club"]["participants"])
        assert final_count == initial_count - 1
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_redirect(self, client):
        """Test that GET / redirects to static index.html."""
        response = client.get("/")
        assert response.status_code == 200  # FastAPI handles the redirect internally in tests
        # The redirect response should point to the static file
        # In test client, redirects are followed by default