# 🧾 Bill Book – Offline Billing System for Small Shops

An offline-capable billing application designed to help small shops create customer bills, manage products, calculate discounts and taxes, generate UPI QR codes, and track daily sales.

Built using **Python, Streamlit, and SQLite** as a student portfolio project.

## 🚀 Features

- 📊 Dashboard showing total sales, daily sales, and bill count
- 🧾 Create customer bills with multiple products
- 📦 Add, edit, and manage products and prices
- 🏪 Save shop profile and contact details
- 💰 Calculate quantities, discounts, taxes, and final totals
- 📚 View saved bills in billing history
- 🖼️ Generate and download bill receipt images
- 📱 Generate UPI QR codes using the configured UPI ID and bill total
- 💬 Open WhatsApp with a prepared bill message
- 💾 Store bills locally using SQLite
- ✈️ Support local offline operation without an internet connection

## 🛠️ Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- Pillow
- qrcode

## 📁 Project Structure

```text
Bill-Book/
│
├── data/
│   └── billbook.db        # Created locally when the app runs
│
├── outputs/               # Generated bill images
│
├── src/
│   └── app.py             # Main application
│
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/fathima-luluh/Bill-Book.git
cd Bill-Book
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Run the application

```powershell
python -m streamlit run src/app.py
```

Open the application in your browser:

```text
http://localhost:8501
```

## 📖 How to Use

1. Open the application.
2. Enter your shop details in Shop Profile.
3. Add products and their prices.
4. Open New Bill.
5. Enter customer details.
6. Select products and quantities.
7. Apply discounts or taxes when required.
8. Generate and save the bill.
9. Download the bill image.
10. View previous transactions in Bill History.

## 📲 UPI and WhatsApp

- Configure your UPI ID in the shop profile.
- Generate a QR code containing the bill amount.
- Scan the QR code using a compatible UPI application to verify the payment request.
- Open WhatsApp using the prepared bill message.
- Download the bill image and attach it manually in WhatsApp before sending.

**Note:** Generating or scanning a UPI QR code does not confirm that a payment has been received. WhatsApp image attachment is manual.

## 🧪 Project Testing

The following tests were completed during development:

| Test | Result |
|---|---|
| Five bills compared with manual calculations | 5/5 passed |
| UPI QR amount verification | Passed for ₹60 |
| Offline bill creation and saved history | Passed |
| Local phone access through mobile hotspot | Passed |
| Home-screen shortcut test | Passed |
| Bill image generation | Tested |
| WhatsApp prepared message | Tested |
| WhatsApp image attachment preview | Tested |

### Five-Bill Calculation Results

| Customer | Verified Total |
|---|---:|
| Anu | ₹168 |
| Rahul | ₹150 |
| Fathima Test | ₹90 |
| Arnav | ₹135 |
| Offline Test | ₹45 |
| **Total** | **₹588** |

All five manually checked totals matched the application.

## 🌐 Phone Access

The application was tested on an Android phone through a shared mobile hotspot.

To access it on the same local network, run:

```powershell
python -m streamlit run src/app.py --server.address 0.0.0.0 --server.port 8501
```

Then open the laptop's network IP address on the phone:

```text
http://YOUR_LAPTOP_IP:8501
```

The laptop and Streamlit server must remain running, and the phone must stay connected to the same network.

**Important:** The home-screen icon is a shortcut to the locally hosted application. This project does not currently include a standalone Android APK.

## 🔒 Data and Privacy

- Billing records are stored locally in an SQLite database.
- The local database, generated images, and sensitive configuration files are excluded from Git.
- Avoid uploading real customer information or private billing records to a public repository.
- Configure your own shop details and UPI ID before using the application.

## 🎯 Project Objective

The objective is to demonstrate how Python, Streamlit, and SQLite can be combined to build a practical billing solution for small businesses, with local data storage, bill generation, QR-based payment requests, and sales tracking.

## 👩‍💻 Author

Developed as a student portfolio project.

**GitHub:** https://github.com/fathima-luluh
