# Zero-Trust Authentication with Behavioral Security Analysis

> A continuous authentication system that monitors user behavior in real-time and dynamically adjusts access based on risk scores, implementing zero-trust security principles.

## 📖 Overview

Traditional authentication systems trust users completely after a single login event. This project reimagines security by **never trusting permanently and always verifying continuously**.

The system learns your normal behavior patterns and detects anomalies using rule-based logic combined with machine learning, automatically blocking suspicious access attempts.

### 🎯 Key Innovation

**Continuous Behavioral Verification** - Authentication doesn't stop at login. Every action is monitored, analyzed, and scored for risk.

## 🚨 Problem We're Solving

Current authentication systems face critical vulnerabilities:

- **Credential theft** - Stolen passwords grant full access
- **Session hijacking** - No detection after initial login
- **Shared devices** - Can't distinguish between authorized and unauthorized users
- **Compromised accounts** - Attackers look like legitimate users

## ✨ Solution Approach

Our zero-trust model continuously monitors:

- **Typing speed** - Characteristic patterns per user
- **Login timing** - Usual activity hours
- **Geolocation** - Expected access locations
- **Device fingerprints** - Known vs unknown devices
- **Session patterns** - Duration and interaction behaviors

### Real-World Example

**Normal Behavior:**
```
User: John
Typing Speed: 55-60 WPM
Login Time: 9 AM - 5 PM
Location: Bangalore
Device: Android Pixel 6
```

**Detected Anomaly:**
```
Typing Speed: 5 WPM (90% deviation)
Login Time: 3:47 AM (unusual)
Location: Delhi (340 km away)
Device: Unknown iOS device
→ Risk Score: 78/100 → Access BLOCKED
```

## 🏗️ Architecture

```
┌─────────────────────┐
│   Flutter Mobile    │
│   - Behavior Track  │
│   - Risk Dashboard  │
└──────────┬──────────┘
           │ HTTPS/JSON
           ↓
┌─────────────────────┐
│   Flask Backend     │
│   - JWT Auth        │
│   - Risk Engine     │
│   - ML Detection    │
└─────┬───────┬───────┘
      │       │
      ↓       ↓
┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Redis   │
│- Users   │ │- Sessions│
│- Behavior│ │- Cache   │
└──────────┘ └──────────┘
```

## 🎯 Core Features

### 1. Secure Authentication
- Email/password registration and login
- Bcrypt password hashing
- JWT token-based sessions
- Automatic token refresh

### 2. Behavioral Profiling
Real-time capture of:
- Typing speed (WPM)
- Session timing patterns
- Device information (model, OS, screen)
- GPS coordinates
- Session duration

### 3. Adaptive Baseline Learning
- Collects initial behavioral data
- Computes personalized baselines
- Continuously updates with new patterns
- Marks profiles as "learning" until sufficient data

### 4. Dynamic Risk Scoring

| Risk Level | Score | Action |
|-----------|-------|--------|
| 🟢 Low | 0-30 | Full access granted |
| 🟡 Medium | 31-60 | Warning + MFA prompt |
| 🔴 High | 61-100 | Access blocked |

### 5. ML-Powered Anomaly Detection
- **Isolation Forest** algorithm
- Trained on user-specific behavior
- Detects outlier patterns
- Contributes to overall risk score

### 6. Risk Monitoring Dashboard
- Real-time risk score display
- Historical risk trends
- Behavioral deviation alerts
- Audit trail for security events

## 🚀 Quick Start

### Prerequisites

```bash
# Backend
Python 3.9+

# Frontend
Flutter 3.0+
Android Studio / Xcode
```

### Backend Setup

```bash
# Clone repository
git clone https://github.com/bnareshseervi/zero-trust-auth.git
cd zero-trust-auth/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
flask db upgrade

# Run development server
flask run
```

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
flutter pub get

# Configure API endpoint
# Edit lib/config/api_config.dart

# Run on emulator/device
flutter run
```

## 🔧 Configuration

### Environment Variables (Backend)

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/zerotrustdb
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### API Configuration (Frontend)

```dart
// lib/config/api_config.dart
class ApiConfig {
  static const String baseUrl = 'https://your-backend.railway.app';
}
```

## 📦 Deployment

### Railway Deployment (Backend)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Android APK Build (Frontend)

```bash
flutter build apk --release
# APK location: build/app/outputs/flutter-apk/app-release.apk
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Zero-trust security principles inspired by Google's BeyondCorp
- Behavioral biometrics research from NIST
- scikit-learn community for ML algorithms


---

⭐ **Star this repo if you find it helpful!**
