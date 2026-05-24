from app import app
from flask import session

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['role_id'] = 9999 # Fake role with no permissions
        sess['employee_id'] = 'fake'
        
    response = client.post("/employees/delete/1")
    print("Status:", response.status_code)
    print("Location:", response.headers.get("Location"))
