from app import app
from flask import session

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['employee_id'] = 'admin'
        sess['user_id'] = 'admin'
        sess['role_id'] = 1
        sess['_user_id'] = '1'  # Flask-Login requires this
        
    response = client.post("/estimation/categories/delete/1")
    print("Status:", response.status_code)
    print("Headers:", response.headers)
    if response.status_code == 302:
        res2 = client.get(response.headers['Location'])
        print("Redirect HTML snippet:")
        print(res2.data.decode('utf-8')[:1000])
        if "Không thể thực hiện" in res2.data.decode('utf-8'):
            print("FOUND FLASH MESSAGE!")
        else:
            print("FLASH MESSAGE NOT FOUND!")
