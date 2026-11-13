
# 🧾 Bill Book – Offline Billing System for Small Shops

A simple and user-friendly offline billing application designed to help small shops create bills, manage products, and track sales.

Built using Python, Streamlit, and SQLite.

## 🚀 Features

- 📊 Dashboard with total sales, bills, and products
- 🧾 Create and manage customer bills
- 📦 Add and manage shop products
- 📚 View previous bills and billing history
- 🏪 Save shop profile and contact details
- 💰 Calculate discounts and taxes
- 🖼️ Generate downloadable bill receipts
- 📱 Generate UPI QR codes when a UPI ID is configured
- 💾 Store billing data locally using SQLite

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
├── outputs/
├── src/
│   └── app.py
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Bill-Book
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Run the application

```powershell
python -m streamlit run src/app.py
```

The application will open in your browser, usually at:

```text
http://localhost:8501
```

## 📖 How to Use

1. Open the application.
2. Add your shop details in Shop Profile.
3. Add products and their prices.
4. Open New Bill.
5. Enter customer details and select products.
6. Generate the bill.
7. Download the receipt.
8. View previous transactions in Bill History.

## 🔒 Data and Privacy

- Billing records are stored locally in an SQLite database.
- The local database and generated output files are excluded from Git using `.gitignore`.
- Do not upload real customer information or private billing records to a public repository.
- A generated UPI QR code is a payment request; it does not confirm that payment has been received.

## 🎯 Project Objective

The goal of this project is to demonstrate how Python, Streamlit, and SQLite can be used to build a practical billing solution for small businesses.

## 👩‍💻 Author

Developed as a student portfolio project.