# Smart Traffic Violation Logger

A lightweight, realistic web application developed using Flask, intended for use by traffic police authorities to digitally manage and track traffic violations. 

## Features
- **Public Portal:** Citizens can search for their vehicle number to check for any pending traffic violations.
- **Admin/Officer Dashboard:** Secure login for officers to log new violations (Vehicle Number, Violation Type, Location, Fine Amount).
- **Dynamic QR Code Generation:** Automatically generates a QR code for every logged challan (receipt), which links directly to the fine's payment/status page.
- **Realistic UI:** Designed to mimic a government web portal with accessibility features (font resizing), emergency helpline modals, and dual-language safety instructions.
- **Status Tracking:** Officers can update fine statuses from `Unpaid` to `Paid`.

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite & SQLAlchemy
- **Frontend:** HTML, CSS, Bootstrap 5
- **Libraries:** `qrcode`, `pillow`, `flask-login`

## How to Run Locally
1. Clone this repository:
   ```bash
   git clone <your-repository-url>
   cd traffic_logger
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```
5. Open your browser and go to `http://127.0.0.1:5000`.

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`
