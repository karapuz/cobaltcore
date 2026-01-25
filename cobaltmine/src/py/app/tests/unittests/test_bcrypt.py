from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "testpass123"
print(f"Testing password: {password}")
print(f"Password length: {len(password)}")
print(f"Password bytes: {len(password.encode('utf-8'))}")

try:
    hashed = pwd_context.hash(password)
    print(f"✓ Hash successful: {hashed}")
    
    verified = pwd_context.verify(password, hashed)
    print(f"✓ Verify successful: {verified}")
except Exception as e:
    print(f"✗ Error: {e}")

"""
python app/tests/unittests/test_bcrypt.py

curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123"}'
  
"""