# 🛒 Online Shopping Management System using MongoDB

A NoSQL document-oriented **Online Shopping Management System** built with **Python, PyMongo, and MongoDB**.

This project demonstrates how MongoDB can support the core backend/database operations of an e-commerce platform, including customers, products, categories, carts, orders, payments, reviews, inventory, and analytics.

## ✨ Features

- 👤 Customer management
- 📦 Product and inventory management
- 🗂️ Category management
- 🛒 Shopping cart operations
- 📋 Order creation and tracking
- 💳 Payment and refund records
- ⭐ Product reviews and ratings
- 🔎 Text search and filtering
- ⚡ MongoDB indexes, compound indexes, and TTL indexes
- 📊 Aggregation-based business analytics
- 🔗 `$lookup` relationships between collections
- 📈 Customer segmentation and sales reports
- 🔔 Optional transactions and change streams

## 🗄️ MongoDB Collections

The database uses these collections:

`customers` · `products` · `categories` · `carts` · `orders` · `payments` · `reviews`

The schema intentionally uses a mix of **embedded documents** and **references** based on access patterns.

## 🧰 Tech Stack

- Python 3
- MongoDB
- PyMongo
- python-dotenv

## 🚀 Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Online-Shopping-Management-System
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure MongoDB

For a local MongoDB server, the default configuration works:

```text
mongodb://localhost:27017/
```

Or create a `.env` file from `.env.example`:

```bash
MONGO_URI=mongodb://localhost:27017/
DB_NAME=online_shopping_db
```

### 4. Generate sample data and run the main demo

```bash
python shopping_system.py
```

The demo creates sample categories, products, customers, and demonstrates the shopping workflow.

### 5. Run the MongoDB query demonstrations

```bash
python sample_queries.py
```

This runs CRUD examples and advanced aggregation reports.

## 📊 Example Workflow

```text
Customer
   ↓
Search Products
   ↓
Add to Cart
   ↓
Create Order
   ↓
Process Payment
   ↓
Write Review
   ↓
Update Order Status
   ↓
Generate Analytics
```

## 🧠 NoSQL Concepts Demonstrated

### Document modeling
Customer addresses and order items are embedded where they are commonly accessed together.

### References
Orders reference customers and products; payments reference orders; reviews reference customers and products.

### Indexing
The project uses unique, text, compound, category, status, date, and TTL indexes.

### Aggregation
The project demonstrates `$match`, `$lookup`, `$unwind`, `$group`, `$project`, `$sort`, `$limit`, `$switch`, and other aggregation features.

### TTL
Shopping carts use an `expiresAt` field with a TTL index.

## 📁 Project Structure

```text
Online-Shopping-Management-System/
├── shopping_system.py
├── sample_queries.py
├── schema_design.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## ⚠️ Security Note

This is an academic/demo project. Do not commit real MongoDB credentials, API keys, passwords, or `.env` files.

The payment module stores only demonstration payment metadata; it is not a real payment gateway.

## 🎓 Project Objective

The objective is to demonstrate how a NoSQL document-oriented database can store and manage the data and operations required by an online shopping platform using MongoDB.

## ⭐ If you find this useful

Star the repository, explore the aggregation examples, and feel free to fork it for learning.
