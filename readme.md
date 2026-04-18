# 🥔 PotatoScan — AI-Powered Potato Leaf Disease Detection

> Developed jointly by **Debarghya Sengupta** & **Ishita Das**

PotatoScan is a precision agriculture web application that automates the detection of potato leaf diseases using **Computer Vision** and **Deep Learning**. By combining a trained CNN model capable of identifying **7 distinct disease classes** with a multi-lingual interface and instant farmer alerts, it transforms traditional reactive farming into a proactive, intelligent crop protection system.

---

## 🌟 Key Features

### 🌐 Multi-lingual Support
The platform supports three languages — **English**, **Hindi**, and **Bengali** — using the Crowdsourced JSON method, making it accessible to farmers across diverse regions.

### 🧠 AI-Driven Diagnosis (97% Accuracy)
A Deep Learning model (CNN) analyzes uploaded leaf images and classifies them into **7 categories**:

| Class | Description |
|-------|-------------|
| ✅ Healthy | No disease detected |
| 🦠 Bacteria | Bacterial leaf infection |
| 🍄 Fungi | Fungal disease (e.g., blight, mold) |
| 🪱 Nematode | Root/leaf nematode infestation |
| 🐛 Pest | Pest-related leaf damage |
| 💧 Phytophthora | Late blight / water mold infection |
| 🔬 Virus | Viral disease (e.g., mosaic virus) |

Each result comes with a **confidence score** for full transparency.

### 💊 Precision Remediation
Upon disease detection, the system provides **targeted chemical or organic treatment recommendations** tailored to the identified disease class, helping farmers act quickly and effectively.

### 📧 Instant Farmer Alerts
Automated welcome and diagnostic email reports are sent via **SMTP (Nodemailer + Gmail)**, keeping farmers informed at every step of the scan process.

### 📊 Real-time Dashboard
A web-based interface allows farmers to:
- Upload leaf images for **instant AI diagnosis**
- View **past scan history**
- Track **field health** over time
- Access **treatment recommendations** per disease

### 🔒 Flexible Access
- **Registered users** get full dashboard access and scan history
- **Trial users** can scan up to **3 images** using just their name and phone number — no account required
- **Google OAuth** support for seamless sign-in

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML, CSS, EJS, JavaScript |
| Backend | Node.js, Express.js |
| ML Model | Python, Flask, TensorFlow/Keras (CNN) |
| Database | PostgreSQL |
| Auth | Passport.js (Local + Google OAuth 2.0) |
| Email | Nodemailer (Gmail SMTP) |

---

## 🚀 Getting Started

### Prerequisites
- Node.js v18+
- Python 3.9+
- PostgreSQL
- A Gmail account with App Password enabled

### 1. Clone the repository
```bash
git clone https://github.com/Debarghyasg/Potato-Leaf-Disease-prediction
cd Potato-Leaf-Disease-prediction
```

### 2. Install Node dependencies
```bash
npm install
```

### 3. Install Python dependencies
```bash
pip install flask tensorflow numpy pillow
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```env
SESSION_SECRET=your_session_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_app_password
FLASK_URL=http://localhost:5000
```

### 5. Set up PostgreSQL
```sql
CREATE DATABASE "Potato-Disease";
```
Then run the table creation queries from the project's SQL schema file.

### 6. Start the Flask ML server
```bash
python app.py
```

### 7. Start the Node server
```bash
node server.js
```

Visit `http://localhost:3000` to access the application.

---

## 📁 Project Structure

```
├── public/
│   ├── uploads/          # Uploaded leaf images
│   └── js/
│       └── i18n.js       # Multi-language support
├── views/
│   ├── Login_multilang.ejs
│   ├── signup_multilang.ejs
│   ├── index_multilang.ejs
│   └── result.ejs
├── server.js             # Express backend
├── app.py                # Flask ML server
└── .env
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

Built with 🌿 to help farmers protect their crops using the power of AI.