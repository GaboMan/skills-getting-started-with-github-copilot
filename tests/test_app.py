"""
Tests for the High School Management System API
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
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Soccer Team": {
            "description": "Join the school soccer team and compete in inter-school matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["alex@mergington.edu", "ryan@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Practice basketball skills and participate in tournaments",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore various art techniques including painting, drawing, and sculpture",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["emily@mergington.edu", "sarah@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Soccer Team" in data
        assert "Basketball Club" in data
        assert "Art Club" in data
    
    def test_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Soccer Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post("/activities/Soccer Team/signup?email=newstudent@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newstudent@mergington.edu for Soccer Team" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Soccer Team"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post("/activities/NonExistent Club/signup?email=student@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_already_registered(self, client):
        """Test signup when student is already registered"""
        response = client.post("/activities/Soccer Team/signup?email=alex@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is already signed up"
    
    def test_signup_with_special_characters(self, client):
        """Test signup with activity name containing special characters"""
        response = client.post("/activities/Art%20Club/signup?email=newartist@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newartist@mergington.edu for Art Club" in data["message"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete("/activities/Soccer Team/unregister?email=alex@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered alex@mergington.edu from Soccer Team" in data["message"]
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alex@mergington.edu" not in activities_data["Soccer Team"]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete("/activities/NonExistent Club/unregister?email=student@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_registered(self, client):
        """Test unregister when student is not registered"""
        response = client.delete("/activities/Soccer Team/unregister?email=notregistered@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"
    
    def test_unregister_and_signup_again(self, client):
        """Test unregistering and then signing up again"""
        # Unregister
        response = client.delete("/activities/Basketball Club/unregister?email=james@mergington.edu")
        assert response.status_code == 200
        
        # Sign up again
        response = client.post("/activities/Basketball Club/signup?email=james@mergington.edu")
        assert response.status_code == 200
        
        # Verify
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "james@mergington.edu" in activities_data["Basketball Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete user scenarios"""
    
    def test_full_signup_flow(self, client):
        """Test complete signup flow for a new student"""
        email = "newstudent@mergington.edu"
        
        # Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        
        # Sign up for multiple activities
        response = client.post(f"/activities/Soccer Team/signup?email={email}")
        assert response.status_code == 200
        
        response = client.post(f"/activities/Art Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify registrations
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Soccer Team"]["participants"]
        assert email in activities_data["Art Club"]["participants"]
    
    def test_participant_count_consistency(self, client):
        """Test that participant counts remain consistent"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Soccer Team"]["participants"])
        
        # Add a participant
        client.post("/activities/Soccer Team/signup?email=new@mergington.edu")
        response = client.get("/activities")
        assert len(response.json()["Soccer Team"]["participants"]) == initial_count + 1
        
        # Remove a participant
        client.delete("/activities/Soccer Team/unregister?email=new@mergington.edu")
        response = client.get("/activities")
        assert len(response.json()["Soccer Team"]["participants"]) == initial_count
