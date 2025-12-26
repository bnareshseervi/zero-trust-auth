# API Documentation

Complete API reference for Zero-Trust Authentication System.

**Base URL:** `https://your-backend.railway.app/api`

**Authentication:** JWT Bearer Token (except for register/login endpoints)

---

## 🔐 Authentication Endpoints

### 1. Register User

Create a new user account.

**Endpoint:** `POST /auth/register`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "user_id": "uuid-string",
  "email": "user@example.com"
}
```

**Error Response (400):**
```json
{
  "error": "Email already exists"
}
```

---

### 2. Login

Authenticate user and receive JWT token.

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "uuid-string",
  "email": "user@example.com"
}
```

**Error Response (401):**
```json
{
  "error": "Invalid credentials"
}
```

---

### 3. Refresh Token

Get a new access token using refresh token.

**Endpoint:** `POST /auth/refresh`

**Headers:**
```json
{
  "Authorization": "Bearer <refresh_token>"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 4. Logout

Invalidate current session.

**Endpoint:** `POST /auth/logout`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 📊 Behavior Tracking Endpoints

### 5. Submit Behavior Data

Send behavioral telemetry data.

**Endpoint:** `POST /behavior/submit`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "typing_speed": 58.5,
  "session_hour": 14,
  "device_model": "Pixel 6",
  "device_os": "Android 13",
  "screen_width": 1080,
  "screen_height": 2400,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "session_duration": 1800
}
```

**Success Response (201):**
```json
{
  "message": "Behavior data recorded",
  "behavior_id": "uuid-string",
  "timestamp": "2025-12-26T10:30:00Z"
}
```

---

### 6. Get User Baseline

Retrieve learned behavioral baseline.

**Endpoint:** `GET /behavior/baseline`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Success Response (200):**
```json
{
  "user_id": "uuid-string",
  "avg_typing_speed": 57.8,
  "common_hours": [9, 10, 11, 14, 15, 16],
  "common_location": {
    "latitude": 12.9716,
    "longitude": 77.5946,
    "city": "Bangalore"
  },
  "common_devices": ["Pixel 6"],
  "is_ready": true,
  "samples_collected": 25
}
```

**Response when baseline not ready (200):**
```json
{
  "user_id": "uuid-string",
  "is_ready": false,
  "samples_collected": 8,
  "samples_needed": 20,
  "message": "Still learning your behavior patterns"
}
```

---

## ⚠️ Risk Assessment Endpoints

### 7. Calculate Risk Score

Get real-time risk assessment.

**Endpoint:** `POST /risk/calculate`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "typing_speed": 10.5,
  "session_hour": 3,
  "device_model": "iPhone 14",
  "latitude": 28.7041,
  "longitude": 77.1025
}
```

**Success Response (200):**
```json
{
  "risk_score": 78,
  "risk_level": "HIGH",
  "factors": {
    "typing_deviation": 82,
    "unusual_hour": true,
    "location_distance_km": 340,
    "unknown_device": true
  },
  "action": "BLOCK_ACCESS",
  "timestamp": "2025-12-26T03:15:00Z"
}
```

**Low Risk Response (200):**
```json
{
  "risk_score": 15,
  "risk_level": "LOW",
  "factors": {
    "typing_deviation": 5,
    "unusual_hour": false,
    "location_distance_km": 2,
    "unknown_device": false
  },
  "action": "ALLOW_ACCESS",
  "timestamp": "2025-12-26T10:30:00Z"
}
```

---

### 8. Get Risk History

Retrieve historical risk scores.

**Endpoint:** `GET /risk/history?limit=20&offset=0`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Query Parameters:**
- `limit` (optional): Number of records (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Success Response (200):**
```json
{
  "total_records": 150,
  "limit": 20,
  "offset": 0,
  "history": [
    {
      "risk_score": 78,
      "risk_level": "HIGH",
      "timestamp": "2025-12-26T03:15:00Z",
      "action_taken": "BLOCK_ACCESS"
    },
    {
      "risk_score": 15,
      "risk_level": "LOW",
      "timestamp": "2025-12-25T10:30:00Z",
      "action_taken": "ALLOW_ACCESS"
    }
  ]
}
```

---

### 9. Get Current Risk Status

Get latest risk score for dashboard.

**Endpoint:** `GET /risk/current`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Success Response (200):**
```json
{
  "current_risk_score": 22,
  "risk_level": "LOW",
  "last_updated": "2025-12-26T10:30:00Z",
  "session_status": "ACTIVE"
}
```

---

## 📈 Analytics Endpoints

### 10. Get User Statistics

Retrieve behavioral analytics.

**Endpoint:** `GET /analytics/stats`

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Success Response (200):**
```json
{
  "total_sessions": 45,
  "avg_risk_score": 18.5,
  "high_risk_incidents": 2,
  "blocked_attempts": 1,
  "most_active_hours": [10, 11, 14, 15],
  "devices_used": ["Pixel 6", "Pixel 7"],
  "locations": ["Bangalore", "Chennai"]
}
```

---

## 🔧 Admin Endpoints (Optional)

### 11. Get All Users (Admin Only)

**Endpoint:** `GET /admin/users`

**Headers:**
```json
{
  "Authorization": "Bearer <admin_access_token>"
}
```

---

## ❌ Error Responses

### Standard Error Format

All errors follow this structure:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-12-26T10:30:00Z"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## 🔑 Authentication Flow

1. **Register** → Get user created
2. **Login** → Receive `access_token` and `refresh_token`
3. **Use access_token** in `Authorization: Bearer <token>` header
4. **Refresh** when access_token expires (typically 15 minutes)
5. **Logout** to invalidate session

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- Risk scores range from 0-100
- Access tokens expire after 15 minutes
- Refresh tokens expire after 30 days
- All endpoints except `/auth/register` and `/auth/login` require authentication

---

## 🧪 Testing with cURL

### Register Example
```bash
curl -X POST https://your-backend.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### Login Example
```bash
curl -X POST https://your-backend.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### Get Risk Score Example
```bash
curl -X GET https://your-backend.railway.app/api/risk/current \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```