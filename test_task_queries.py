import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_KEY = "localtest"

def test_task(name, message):
    """Test task creation queries"""
    print(f"\n{'='*60}")
    print(f"TASK TEST: {name}")
    print(f"{'='*60}")
    print(f"Query: {message}")
    
    payload = {
        "version": "3.0.0",
        "input": {"message": message},
        "context": {"platform": "web"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/assistant",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            print(f"\nResponse Type: {result.get('type')}")
            print(f"Response: {result.get('response', '')[:150]}")
            
            # Task details
            task = result.get('task', {})
            if task:
                print(f"\n[TASK DETAILS]")
                print(f"  Type: {task.get('task_type')}")
                print(f"  Status: {task.get('status')}")
                
                execution = task.get('execution', {})
                if execution:
                    print(f"\n[EXECUTION]")
                    for key, value in execution.items():
                        if key not in ['trace_id', 'timestamp']:
                            print(f"  {key}: {value}")
                
                error = task.get('error')
                if error:
                    print(f"  Error: {error}")
                
                print(f"\n[PASS] Task created successfully")
            else:
                print(f"\n[INFO] No task created (passive response)")
                
        else:
            print(f"[FAIL] Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TASK CREATION QUERY TESTS")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}")
    
    # Email task queries
    test_task(
        "Email - Simple",
        "Send an email to john@example.com saying hello"
    )
    
    test_task(
        "Email - With Subject",
        "Send an email to sarah@test.com with subject Meeting Tomorrow and body Let's meet at 3pm"
    )
    
    test_task(
        "Email - Detailed",
        "Email alice@company.com about the project update with details about the new features"
    )
    
    test_task(
        "Email - Multiple Recipients",
        "Send email to team@company.com and manager@company.com about the quarterly report"
    )
    
    # WhatsApp task queries
    test_task(
        "WhatsApp - Simple",
        "Send a WhatsApp message to +1234567890 saying hello"
    )
    
    test_task(
        "WhatsApp - Detailed",
        "WhatsApp John at +1234567890 to remind him about tomorrow's meeting at 10am"
    )
    
    test_task(
        "WhatsApp - Casual",
        "Message +9876543210 on WhatsApp: Hey, are you free this weekend?"
    )
    
    # Reminder/Schedule tasks
    test_task(
        "Reminder - Simple",
        "Remind me to call mom tomorrow at 5pm"
    )
    
    test_task(
        "Schedule - Meeting",
        "Schedule a meeting with the team next Monday at 2pm"
    )
    
    test_task(
        "Schedule - Personal",
        "Add gym session to my calendar for Wednesday 6am"
    )
    
    # Task creation queries
    test_task(
        "Task - Simple",
        "Create a task to finish the report by Friday"
    )
    
    test_task(
        "Task - Detailed",
        "Add task: Review code changes and submit pull request before end of day"
    )
    
    # Mixed/Complex queries
    test_task(
        "Complex - Multi-action",
        "Send email to boss@company.com about project completion and schedule follow-up meeting"
    )
    
    test_task(
        "Complex - With Context",
        "Email the client at client@business.com with the proposal document and CC my manager"
    )
    
    print("\n" + "="*60)
    print("ALL TASK TESTS COMPLETED")
    print("="*60)
