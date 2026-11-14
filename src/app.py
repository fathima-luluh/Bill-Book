
import streamlit as st
import sqlite3
import pandas as pd
import json
import qrcode
import os

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from urllib.parse import urlencode


# ==================================================
# 1. APP CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Bill Book",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Bill Book")
st.caption("Simple Offline Billing System for Small Shops")

DB_PATH = os.path.join("data", "billbook.db")

os.makedirs("data", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


# ==================================================
# 2. DATABASE CONNECTION
# ==================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ==================================================
# 3. DATABASE MIGRATION
# ==================================================

def ensure_columns(conn, table, columns):

    existing = {
        row[1]
        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

    for column_name, column_type in columns.items():

        if column_name not in existing:

            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN "
                f"{column_name} {column_type}"
            )


def initialize_database():

    conn = get_connection()

    # Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    """)

    # Bills table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            subtotal REAL,
            discount REAL,
            tax_rate REAL,
            tax_amount REAL,
            total REAL,
            items_json TEXT
        )
    """)

    # Shop settings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shop_settings (
            id INTEGER PRIMARY KEY,
            shop_name TEXT,
            address TEXT,
            phone TEXT,
            upi_id TEXT
        )
    """)

    # Add missing columns to older databases.
    ensure_columns(conn, "products", {
        "id": "INTEGER",
        "name": "TEXT",
        "price": "REAL"
    })

    ensure_columns(conn, "bills", {
        "id": "INTEGER",
        "created_at": "TEXT",
        "customer_name": "TEXT",
        "customer_phone": "TEXT",
        "subtotal": "REAL DEFAULT 0",
        "discount": "REAL DEFAULT 0",
        "tax_rate": "REAL DEFAULT 0",
        "tax_amount": "REAL DEFAULT 0",
        "total": "REAL DEFAULT 0",
        "items_json": "TEXT"
    })

    # Fix the old shop_settings table.
    ensure_columns(conn, "shop_settings", {
        "id": "INTEGER",
        "shop_name": "TEXT",
        "address": "TEXT",
        "phone": "TEXT",
        "upi_id": "TEXT"
    })

    # Fill missing IDs in old products and bills.
    for table in ["products", "bills"]:

        rows = conn.execute(
            f"SELECT rowid FROM {table} WHERE id IS NULL"
        ).fetchall()

        for row in rows:

            next_id = conn.execute(
                f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}"
            ).fetchone()[0]

            conn.execute(
                f"UPDATE {table} SET id = ? WHERE rowid = ?",
                (next_id, row[0])
            )

    # Assign an ID to existing shop settings rows.
    settings_rows = conn.execute(
        "SELECT rowid, id FROM shop_settings ORDER BY rowid"
    ).fetchall()

    for index, row in enumerate(settings_rows, start=1):

        if row[1] is None:

            conn.execute(
                "UPDATE shop_settings SET id = ? WHERE rowid = ?",
                (index, row[0])
            )

    # Ensure a default shop profile exists.
    shop = conn.execute(
        "SELECT rowid FROM shop_settings WHERE id = 1 LIMIT 1"
    ).fetchone()

    if shop is None:

        conn.execute("""
            INSERT INTO shop_settings
            (id, shop_name, address, phone, upi_id)
            VALUES (1, 'My Shop', '', '', '')
        """)

    conn.commit()
    conn.close()


initialize_database()


# ==================================================
# 4. DATA RETRIEVAL
# ==================================================

def get_products():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT id, name, price FROM products ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def get_bills():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM bills ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def get_shop_settings():

    conn = get_connection()

    row = conn.execute("""
        SELECT shop_name, address, phone, upi_id
        FROM shop_settings
        WHERE id = 1
        LIMIT 1
    """).fetchone()

    conn.close()

    if row:

        return {
            "shop_name": row[0] or "My Shop",
            "address": row[1] or "",
            "phone": row[2] or "",
            "upi_id": row[3] or ""
        }

    return {
        "shop_name": "My Shop",
        "address": "",
        "phone": "",
        "upi_id": ""
    }


# ==================================================
# 5. PROFESSIONAL BILL IMAGE GENERATOR
# ==================================================

def create_bill_image(bill, shop):

    items = bill["items"]

    width = 760

    has_upi = bool(shop.get("upi_id", "").strip())

    height = (
        950
        + len(items) * 55
        + (260 if has_upi else 0)
    )

    image = Image.new(
        "RGB",
        (width, height),
        "#FFFFFF"
    )

    draw = ImageDraw.Draw(image)

    # Load fonts
    try:

        regular = ImageFont.truetype(
            "arial.ttf", 21
        )

        small = ImageFont.truetype(
            "arial.ttf", 17
        )

        bold = ImageFont.truetype(
            "arialbd.ttf", 22
        )

        heading = ImageFont.truetype(
            "arialbd.ttf", 36
        )

        large = ImageFont.truetype(
            "arialbd.ttf", 38
        )

    except OSError:

        regular = ImageFont.load_default()
        small = regular
        bold = regular
        heading = regular
        large = regular

    # Drawing helpers
    def left(text, x, y, font=regular, fill="#222222"):

        draw.text(
            (x, y),
            str(text),
            font=font,
            fill=fill
        )

    def right(text, x, y, font=regular, fill="#222222"):

        draw.text(
            (x, y),
            str(text),
            font=font,
            fill=fill,
            anchor="ra"
        )

    def center(text, y, font=regular, fill="#222222"):

        draw.text(
            (width // 2, y),
            str(text),
            font=font,
            fill=fill,
            anchor="mt"
        )

    def separator(y):

        draw.line(
            (40, y, width - 40, y),
            fill="#CCCCCC",
            width=2
        )

    # Outer border
    draw.rounded_rectangle(
        (20, 20, width - 20, height - 20),
        radius=16,
        outline="#DDDDDD",
        width=2
    )

    y = 40

    # Shop name
    center(
        shop.get("shop_name") or "My Shop",
        y,
        heading,
        "#172554"
    )

    y += 60

    if shop.get("address"):

        center(
            shop["address"][:65],
            y,
            small,
            "#555555"
        )

        y += 30

    if shop.get("phone"):

        center(
            "Phone: " + shop["phone"],
            y,
            small,
            "#555555"
        )

        y += 35

    separator(y)

    y += 25

    # Invoice information
    left(
        "INVOICE",
        45,
        y,
        bold,
        "#172554"
    )

    right(
        "BILL NO: " + str(bill["id"]),
        width - 45,
        y,
        bold
    )

    y += 42

    left(
        "Date: " + str(bill["created_at"]),
        45,
        y,
        small
    )

    y += 35

    left(
        "Customer: " + str(bill["customer_name"]),
        45,
        y
    )

    y += 35

    if bill.get("customer_phone"):

        left(
            "Phone: " + str(bill["customer_phone"]),
            45,
            y,
            small
        )

        y += 35

    separator(y)

    y += 22

    # Product table header
    left("ITEM", 45, y, bold)
    right("QTY", 450, y, bold)
    right("PRICE", 585, y, bold)
    right("TOTAL", 710, y, bold)

    y += 42

    separator(y)

    y += 18

    # Product rows
    for item in items:

        name = str(item["name"])

        if len(name) > 25:
            name = name[:22] + "..."

        left(name, 45, y)

        right(
            str(item["quantity"]),
            450,
            y
        )

        right(
            f'Rs. {float(item["price"]):.2f}',
            585,
            y,
            small
        )

        right(
            f'Rs. {float(item["amount"]):.2f}',
            710,
            y,
            small
        )

        y += 55

    separator(y)

    y += 25

    # Amount summary
    left(
        f'Subtotal: Rs. {float(bill["subtotal"]):.2f}',
        45,
        y
    )

    y += 42

    left(
        f'Discount: Rs. {float(bill["discount"]):.2f}',
        45,
        y
    )

    y += 42

    left(
        f'Tax ({bill["tax_rate"]}%): Rs. '
        f'{float(bill["tax_amount"]):.2f}',
        45,
        y
    )

    y += 55

    separator(y)

    y += 25

    # Grand total
    left(
        "GRAND TOTAL",
        45,
        y,
        bold,
        "#172554"
    )

    right(
        f'Rs. {float(bill["total"]):.2f}',
        width - 45,
        y - 8,
        large,
        "#15803D"
    )

    y += 75

    # UPI QR code
    if has_upi:

        separator(y)

        y += 25

        center(
            "SCAN TO PAY",
            y,
            bold,
            "#172554"
        )

        y += 45

        upi_data = urlencode({
            "pa": shop["upi_id"],
            "pn": shop.get("shop_name", "My Shop"),
            "am": f'{float(bill["total"]):.2f}',
            "cu": "INR"
        })

        upi_link = "upi://pay?" + upi_data

        qr = qrcode.make(upi_link).convert("RGB")

        qr = qr.resize((170, 170))

        image.paste(
            qr,
            (width // 2 - 85, y)
        )

        y += 180

        center(
            "UPI ID: " + shop["upi_id"],
            y,
            small,
            "#555555"
        )

        y += 45

    # Footer
    separator(y)

    y += 25

    center(
        "Thank you for shopping with us!",
        y,
        bold,
        "#172554"
    )

    y += 38

    center(
        "Please visit again.",
        y,
        small,
        "#666666"
    )

    y += 50

    return image.crop(
        (0, 0, width, y)
    )


# ==================================================
# 6. SAVE BILL
# ==================================================

def create_whatsapp_share_url(bill):
    """Create a WhatsApp message link for a saved bill.

    The bill image must still be attached manually after downloading it.
    """
    shop = get_shop_settings()
    message = (
        f"{shop.get('shop_name') or 'My Shop'}\n"
        f"Bill No: {bill['id']}\n"
        f"Customer: {bill['customer_name']}\n"
        f"Date: {bill['created_at']}\n"
        f"Total: Rs. {float(bill['total']):.2f}\n\n"
        "Please find the bill image attached."
    )
    return "https://wa.me/?" + urlencode({"text": message})


def save_bill(bill):

    conn = get_connection()

    next_id = conn.execute(
        "SELECT COALESCE(MAX(id), 0) + 1 FROM bills"
    ).fetchone()[0]

    conn.execute("""
        INSERT INTO bills (
            id,
            created_at,
            customer_name,
            customer_phone,
            subtotal,
            discount,
            tax_rate,
            tax_amount,
            total,
            items_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        next_id,
        bill["created_at"],
        bill["customer_name"],
        bill["customer_phone"],
        bill["subtotal"],
        bill["discount"],
        bill["tax_rate"],
        bill["tax_amount"],
        bill["total"],
        json.dumps(bill["items"])
    ))

    conn.commit()
    conn.close()

    bill["id"] = next_id

    return bill


# ==================================================
# 7. SESSION STATE
# ==================================================

if "cart" not in st.session_state:

    st.session_state.cart = []

if "last_bill" not in st.session_state:

    st.session_state.last_bill = None


# ==================================================
# 8. NAVIGATION TABS
# ==================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🧾 New Bill",
    "📦 Products",
    "📚 Bill History",
    "⚙️ Shop Profile"
])


# ==================================================
# 9. DASHBOARD
# ==================================================

with tab1:

    st.header("Dashboard")

    bills_df = get_bills()

    products_df = get_products()

    total_sales = (
        float(bills_df["total"].fillna(0).sum())
        if not bills_df.empty else 0
    )

    # Calculate today's sales using the date stored in each bill.
    today = datetime.now().strftime("%d-%m-%Y")

    if not bills_df.empty:
        today_bills = bills_df[
            bills_df["created_at"].astype(str).str.startswith(today)
        ]
        today_sales = float(
            today_bills["total"].fillna(0).sum()
        )
        today_bill_count = len(today_bills)
    else:
        today_sales = 0.0
        today_bill_count = 0

    total_bills = len(bills_df)
    total_products = len(products_df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Sales",
        f"₹{total_sales:,.2f}"
    )

    col2.metric(
        "Today's Sales",
        f"₹{today_sales:,.2f}"
    )

    col3.metric(
        "Total Bills",
        total_bills
    )

    col4.metric(
        "Total Products",
        total_products
    )

    st.metric(
        "Bills Created Today",
        today_bill_count
    )

    st.divider()

    st.subheader("Recent Bills")

    if not bills_df.empty:

        recent = bills_df.head(10).copy()

        recent["total"] = recent["total"].apply(
            lambda x: f"₹{x:,.2f}"
        )

        st.dataframe(
            recent[
                ["id", "created_at", "customer_name", "total"]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No bills created yet.")


# ==================================================
# 10. NEW BILL
# ==================================================

with tab2:

    st.header("Create New Bill")

    products_df = get_products()

    if products_df.empty:

        st.warning(
            "Please add products before creating a bill."
        )

    else:

        st.subheader("Customer Details")

        customer_name = st.text_input(
            "Customer Name",
            key="bill_customer_name"
        )

        customer_phone = st.text_input(
            "Customer Phone",
            key="bill_customer_phone"
        )

        st.divider()

        st.subheader("Add Products")

        product_options = {
            (
                f'{row["name"]} - '
                f'₹{float(row["price"]):.2f}'
            ): row
            for _, row in products_df.iterrows()
        }

        selected_product = st.selectbox(
            "Select Product",
            list(product_options.keys())
        )

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            step=1
        )

        if st.button("➕ Add to Bill"):

            product = product_options[selected_product]

            existing = next(
                (
                    item for item in st.session_state.cart
                    if item["product_id"] == int(product["id"])
                ),
                None
            )

            if existing:

                existing["quantity"] += int(quantity)

                existing["amount"] = (
                    existing["quantity"] * existing["price"]
                )

            else:

                st.session_state.cart.append({
                    "product_id": int(product["id"]),
                    "name": product["name"],
                    "price": float(product["price"]),
                    "quantity": int(quantity),
                    "amount": (
                        float(product["price"]) * int(quantity)
                    )
                })

            st.success("Product added successfully!")

        st.divider()

        st.subheader("Bill Items")

        if st.session_state.cart:

            cart_df = pd.DataFrame(
                st.session_state.cart
            )

            st.dataframe(
                cart_df[
                    ["name", "quantity", "price", "amount"]
                ],
                use_container_width=True,
                hide_index=True
            )

            if st.button("🗑️ Clear Cart"):

                st.session_state.cart = []

                st.rerun()

            subtotal = sum(
                item["amount"]
                for item in st.session_state.cart
            )

            discount = st.number_input(
                "Discount (₹)",
                min_value=0.0,
                max_value=float(subtotal),
                value=0.0,
                step=1.0
            )

            tax_rate = st.number_input(
                "Tax (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5
            )

            taxable_amount = max(
                0,
                subtotal - discount
            )

            tax_amount = (
                taxable_amount * tax_rate / 100
            )

            total = taxable_amount + tax_amount

            st.divider()

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Subtotal",
                f"₹{subtotal:.2f}"
            )

            col2.metric(
                "Tax",
                f"₹{tax_amount:.2f}"
            )

            col3.metric(
                "Grand Total",
                f"₹{total:.2f}"
            )

            if st.button(
                "✅ Save Bill",
                type="primary"
            ):

                if not customer_name.strip():

                    st.error(
                        "Please enter the customer name."
                    )

                else:

                    bill = {
                        "created_at": datetime.now().strftime(
                            "%d-%m-%Y %I:%M %p"
                        ),
                        "customer_name": customer_name.strip(),
                        "customer_phone": customer_phone.strip(),
                        "subtotal": subtotal,
                        "discount": discount,
                        "tax_rate": tax_rate,
                        "tax_amount": tax_amount,
                        "total": total,
                        "items": st.session_state.cart.copy()
                    }

                    bill = save_bill(bill)

                    bill_image = create_bill_image(
                        bill,
                        get_shop_settings()
                    )

                    st.session_state.last_bill = {
                        "bill": bill,
                        "image": bill_image
                    }

                    st.session_state.cart = []

                    st.success(
                        f'Bill #{bill["id"]} saved successfully!'
                    )

                    st.rerun()

        else:

            st.info(
                "Your bill is empty. Add products above."
            )

    # Display most recently generated bill.
    if st.session_state.last_bill:

        st.divider()

        st.subheader("Latest Saved Bill")

        saved = st.session_state.last_bill

        bill_image = saved["image"]

        st.image(
            bill_image,
            caption="Generated Bill",
            use_container_width=True
        )

        image_buffer = BytesIO()

        bill_image.save(
            image_buffer,
            format="PNG"
        )

        st.download_button(
            "⬇️ Download Bill PNG",
            data=image_buffer.getvalue(),
            file_name=(
                f'bill_{saved["bill"]["id"]}.png'
            ),
            mime="image/png"
        )

        st.link_button(
            "📲 Share on WhatsApp",
            create_whatsapp_share_url(saved["bill"])
        )
        st.caption(
            "First download the bill image. WhatsApp will open with a "
            "prepared message; attach the downloaded PNG before sending."
        )


# ==================================================
# 11. PRODUCT MANAGEMENT
# ==================================================

with tab3:

    st.header("Product Management")

    with st.form("add_product_form"):

        product_name = st.text_input(
            "Product Name"
        )

        product_price = st.number_input(
            "Product Price (₹)",
            min_value=0.01,
            value=10.0,
            step=1.0
        )

        submitted = st.form_submit_button(
            "➕ Add Product"
        )

        if submitted:

            if not product_name.strip():

                st.error("Please enter a product name.")

            else:

                conn = get_connection()

                next_id = conn.execute(
                    "SELECT COALESCE(MAX(id), 0) + 1 FROM products"
                ).fetchone()[0]

                conn.execute("""
                    INSERT INTO products (id, name, price)
                    VALUES (?, ?, ?)
                """, (
                    next_id,
                    product_name.strip(),
                    product_price
                ))

                conn.commit()
                conn.close()

                st.success("Product added successfully!")

                st.rerun()

    st.divider()

    st.subheader("Available Products")

    products_df = get_products()

    if not products_df.empty:

        st.dataframe(
            products_df,
            use_container_width=True,
            hide_index=True
        )

        product_to_delete = st.selectbox(
            "Select Product to Delete",
            products_df["id"].tolist(),
            format_func=lambda x: (
                f'{products_df.loc[products_df["id"] == x, "name"].iloc[0]} '
                f'(ID: {x})'
            )
        )

        if st.button("❌ Delete Selected Product"):

            conn = get_connection()

            conn.execute(
                "DELETE FROM products WHERE id = ?",
                (int(product_to_delete),)
            )

            conn.commit()
            conn.close()

            st.success("Product deleted successfully!")

            st.rerun()

    else:

        st.info("No products added yet.")


# ==================================================
# 12. BILL HISTORY
# ==================================================

with tab4:

    st.header("Bill History")

    bills_df = get_bills()

    if not bills_df.empty:

        display_df = bills_df.copy()

        display_df["total"] = display_df["total"].apply(
            lambda x: f"₹{x:,.2f}"
        )

        st.dataframe(
            display_df[
                [
                    "id",
                    "created_at",
                    "customer_name",
                    "customer_phone",
                    "total"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("View and Download Bill")

        bill_ids = bills_df["id"].tolist()

        selected_bill_id = st.selectbox(
            "Select Bill Number",
            bill_ids
        )

        selected_bill = bills_df[
            bills_df["id"] == selected_bill_id
        ].iloc[0]

        st.write(
            "Customer:",
            selected_bill["customer_name"]
        )

        st.write(
            "Date:",
            selected_bill["created_at"]
        )

        st.write(
            "Phone:",
            selected_bill["customer_phone"]
        )

        st.write(
            "Subtotal:",
            f'₹{selected_bill["subtotal"]:.2f}'
        )

        st.write(
            "Discount:",
            f'₹{selected_bill["discount"]:.2f}'
        )

        st.write(
            "Tax:",
            f'₹{selected_bill["tax_amount"]:.2f}'
        )

        st.write(
            "**Total:**",
            f'₹{selected_bill["total"]:.2f}'
        )

        try:

            items = json.loads(
                selected_bill["items_json"] or "[]"
            )

            st.write("Items:")

            st.dataframe(
                pd.DataFrame(items),
                use_container_width=True,
                hide_index=True
            )

            history_bill = {
                "id": int(selected_bill["id"]),
                "created_at": selected_bill["created_at"],
                "customer_name": selected_bill["customer_name"],
                "customer_phone": (
                    selected_bill["customer_phone"] or ""
                ),
                "subtotal": float(selected_bill["subtotal"] or 0),
                "discount": float(selected_bill["discount"] or 0),
                "tax_rate": float(selected_bill["tax_rate"] or 0),
                "tax_amount": float(selected_bill["tax_amount"] or 0),
                "total": float(selected_bill["total"] or 0),
                "items": items
            }

            history_image = create_bill_image(
                history_bill,
                get_shop_settings()
            )

            buffer = BytesIO()

            history_image.save(
                buffer,
                format="PNG"
            )

            st.download_button(
                "⬇️ Download Selected Bill",
                data=buffer.getvalue(),
                file_name=f"bill_{selected_bill_id}.png",
                mime="image/png"
            )

            st.link_button(
                "📲 Share Selected Bill on WhatsApp",
                create_whatsapp_share_url(history_bill)
            )
            st.caption(
                "Download the image first, then attach that PNG in "
                "WhatsApp before sending."
            )

        except (ValueError, TypeError, KeyError) as error:

            st.error(
                f"Could not display bill items: {error}"
            )

    else:

        st.info("No bills found.")


# ==================================================
# 13. SHOP PROFILE
# ==================================================

with tab5:

    st.header("Shop Profile")

    shop = get_shop_settings()

    with st.form("shop_profile_form"):

        shop_name = st.text_input(
            "Shop Name",
            value=shop["shop_name"]
        )

        address = st.text_area(
            "Shop Address",
            value=shop["address"]
        )

        phone = st.text_input(
            "Shop Phone Number",
            value=shop["phone"]
        )

        upi_id = st.text_input(
            "UPI ID",
            value=shop["upi_id"],
            placeholder="yourname@upi"
        )

        save_profile = st.form_submit_button(
            "💾 Save Shop Profile"
        )

        if save_profile:

            conn = get_connection()

            existing = conn.execute(
                "SELECT rowid FROM shop_settings WHERE id = 1 LIMIT 1"
            ).fetchone()

            if existing:

                conn.execute("""
                    UPDATE shop_settings
                    SET shop_name = ?,
                        address = ?,
                        phone = ?,
                        upi_id = ?
                    WHERE id = 1
                """, (
                    shop_name.strip(),
                    address.strip(),
                    phone.strip(),
                    upi_id.strip()
                ))

            else:

                conn.execute("""
                    INSERT INTO shop_settings
                    (id, shop_name, address, phone, upi_id)
                    VALUES (1, ?, ?, ?, ?)
                """, (
                    shop_name.strip(),
                    address.strip(),
                    phone.strip(),
                    upi_id.strip()
                ))

            conn.commit()
            conn.close()

            st.success(
                "Shop profile saved successfully!"
            )

            st.rerun()

    st.info(
        "Your UPI ID is used to generate a payment QR code "
        "on new bills. Always verify payments in your UPI app."
    )


# ==================================================
# 14. FOOTER
# ==================================================

st.divider()

st.caption(
    "🧾 Bill Book | Version 1.1 | "
    "Offline billing system for small shops"
)
