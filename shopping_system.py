"""
Online Shopping Management System using MongoDB
===============================================
A complete NoSQL implementation with CRUD operations, aggregations,
and business logic for an e-commerce platform.

Requirements: pymongo, python-dotenv
Install: pip install pymongo python-dotenv
"""

import os
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bson import ObjectId
from bson.decimal128 import Decimal128
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure
from pymongo.collection import Collection


# ============================================================================
# CONFIGURATION
# ============================================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "online_shopping_db")


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class DatabaseConnection:
    """Manages MongoDB connection and provides collection access."""

    _instance = None

    def __new__(cls, uri: str = MONGO_URI, db_name: str = DB_NAME):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = MongoClient(uri)
            cls._instance.db = cls._instance.client[db_name]
        return cls._instance

    @property
    def customers(self) -> Collection:
        return self.db["customers"]

    @property
    def products(self) -> Collection:
        return self.db["products"]

    @property
    def orders(self) -> Collection:
        return self.db["orders"]

    @property
    def payments(self) -> Collection:
        return self.db["payments"]

    @property
    def reviews(self) -> Collection:
        return self.db["reviews"]

    @property
    def carts(self) -> Collection:
        return self.db["carts"]

    @property
    def categories(self) -> Collection:
        return self.db["categories"]

    def close(self):
        self.client.close()
        DatabaseConnection._instance = None


def get_db() -> DatabaseConnection:
    """Get database connection instance."""
    return DatabaseConnection()


# ============================================================================
# INDEX SETUP
# ============================================================================

def setup_indexes():
    """Create all necessary indexes for optimal query performance."""
    db = get_db()

    # Customers indexes
    db.customers.create_index("email", unique=True)
    db.customers.create_index("phone")
    db.customers.create_index("createdAt")
    db.customers.create_index("addresses.zipCode")

    # Products indexes
    db.products.create_index("sku", unique=True)
    db.products.create_index("category")
    db.products.create_index("subCategory")
    db.products.create_index("brand")
    db.products.create_index("price")
    db.products.create_index("tags")
    db.products.create_index("isActive")
    db.products.create_index([("name", "text"), ("description", "text")])
    db.products.create_index("rating.average")

    # Orders indexes
    db.orders.create_index("orderNumber", unique=True)
    db.orders.create_index("customerId")
    db.orders.create_index("status")
    db.orders.create_index("orderDate")
    db.orders.create_index([("customerId", ASCENDING), ("orderDate", DESCENDING)])

    # Payments indexes
    db.payments.create_index("orderId")
    db.payments.create_index("customerId")
    db.payments.create_index("transactionId", unique=True)
    db.payments.create_index("status")
    db.payments.create_index("processedAt")

    # Reviews indexes
    db.reviews.create_index("productId")
    db.reviews.create_index("customerId")
    db.reviews.create_index("rating")
    db.reviews.create_index("createdAt")
    db.reviews.create_index([("productId", ASCENDING), ("createdAt", DESCENDING)])
    db.reviews.create_index("verifiedPurchase")

    # Carts indexes
    db.carts.create_index("customerId", unique=True)
    db.carts.create_index("expiresAt", expireAfterSeconds=0)  # TTL index

    # Categories indexes
    db.categories.create_index("slug", unique=True)
    db.categories.create_index("parentId")
    db.categories.create_index("isActive")

    print("✅ All indexes created successfully!")


# ============================================================================
# CUSTOMER MANAGEMENT
# ============================================================================

class CustomerManager:
    """Handles all customer-related operations."""

    def __init__(self):
        self.collection = get_db().customers

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (use bcrypt in production)."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[str]:
        """Register a new customer."""
        customer_data["password"] = self.hash_password(customer_data["password"])
        customer_data["createdAt"] = datetime.utcnow()
        customer_data["isActive"] = True
        customer_data.setdefault("addresses", [])
        customer_data.setdefault("preferences", {
            "newsletter": True,
            "notifications": {"email": True, "sms": False, "push": True},
            "currency": "USD",
            "language": "en"
        })

        try:
            result = self.collection.insert_one(customer_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print("❌ Customer with this email already exists!")
            return None

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID."""
        return self.collection.find_one({"_id": ObjectId(customer_id)})

    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """Get customer by email."""
        return self.collection.find_one({"email": email})

    def update_customer(self, customer_id: str, updates: Dict) -> bool:
        """Update customer information."""
        updates["updatedAt"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(customer_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def add_address(self, customer_id: str, address: Dict) -> bool:
        """Add a new address to customer."""
        address["addressId"] = f"addr_{ObjectId()}"
        result = self.collection.update_one(
            {"_id": ObjectId(customer_id)},
            {"$push": {"addresses": address}}
        )
        return result.modified_count > 0

    def set_default_address(self, customer_id: str, address_id: str) -> bool:
        """Set an address as default."""
        # First, unset all defaults
        self.collection.update_one(
            {"_id": ObjectId(customer_id)},
            {"$set": {"addresses.$[].isDefault": False}}
        )
        # Then set the specified one
        result = self.collection.update_one(
            {"_id": ObjectId(customer_id), "addresses.addressId": address_id},
            {"$set": {"addresses.$.isDefault": True}}
        )
        return result.modified_count > 0

    def delete_customer(self, customer_id: str) -> bool:
        """Soft delete a customer."""
        result = self.collection.update_one(
            {"_id": ObjectId(customer_id)},
            {"$set": {"isActive": False, "deletedAt": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def search_customers(self, query: str, limit: int = 20) -> List[Dict]:
        """Search customers by name or email."""
        return list(self.collection.find({
            "$or": [
                {"firstName": {"$regex": query, "$options": "i"}},
                {"lastName": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ]
        }).limit(limit))

    def get_customer_order_history(self, customer_id: str) -> List[Dict]:
        """Get complete order history for a customer using aggregation."""
        pipeline = [
            {"$match": {"_id": ObjectId(customer_id)}},
            {
                "$lookup": {
                    "from": "orders",
                    "localField": "_id",
                    "foreignField": "customerId",
                    "as": "orders"
                }
            },
            {
                "$project": {
                    "firstName": 1,
                    "lastName": 1,
                    "email": 1,
                    "totalOrders": {"$size": "$orders"},
                    "totalSpent": {"$sum": "$orders.grandTotal"},
                    "orders": {
                        "$sortArray": {
                            "input": "$orders",
                            "sortBy": {"orderDate": -1}
                        }
                    }
                }
            }
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}


# ============================================================================
# PRODUCT MANAGEMENT
# ============================================================================

class ProductManager:
    """Handles all product-related operations."""

    def __init__(self):
        self.collection = get_db().products

    def create_product(self, product_data: Dict[str, Any]) -> Optional[str]:
        """Add a new product to catalog."""
        product_data["rating"] = {"average": 0, "count": 0}
        product_data["isActive"] = True
        product_data["createdAt"] = datetime.utcnow()
        product_data["updatedAt"] = datetime.utcnow()

        try:
            result = self.collection.insert_one(product_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print("❌ Product with this SKU already exists!")
            return None

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product by ID."""
        return self.collection.find_one({"_id": ObjectId(product_id)})

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get product by SKU."""
        return self.collection.find_one({"sku": sku})

    def update_product(self, product_id: str, updates: Dict) -> bool:
        """Update product details."""
        updates["updatedAt"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def update_stock(self, product_id: str, quantity_change: int) -> bool:
        """Update product stock (positive to add, negative to subtract)."""
        result = self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {"stock": quantity_change},
                "$set": {"updatedAt": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def search_products(self, query: str = None, category: str = None,
                       min_price: float = None, max_price: float = None,
                       tags: List[str] = None, brand: str = None,
                       sort_by: str = "createdAt", sort_order: int = -1,
                       limit: int = 20, skip: int = 0) -> Dict:
        """Advanced product search with filters."""
        filter_query = {"isActive": True}

        if query:
            filter_query["$text"] = {"$search": query}
        if category:
            filter_query["category"] = category
        if brand:
            filter_query["brand"] = brand
        if tags:
            filter_query["tags"] = {"$in": tags}
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filter_query["price"] = price_filter

        total = self.collection.count_documents(filter_query)

        cursor = self.collection.find(filter_query)

        if query:
            cursor = cursor.sort([("score", {"$meta": "textScore"})])
        else:
            cursor = cursor.sort(sort_by, sort_order)

        products = list(cursor.skip(skip).limit(limit))

        return {
            "products": products,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    def get_products_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """Get products by category."""
        return list(self.collection.find(
            {"category": category, "isActive": True}
        ).limit(limit))

    def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        """Get products with low stock."""
        return list(self.collection.find(
            {"stock": {"$lte": threshold}, "isActive": True}
        ).sort("stock", ASCENDING))

    def delete_product(self, product_id: str) -> bool:
        """Soft delete a product."""
        result = self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"isActive": False, "updatedAt": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_top_rated_products(self, limit: int = 10) -> List[Dict]:
        """Get top-rated products."""
        return list(self.collection.find(
            {"isActive": True, "rating.count": {"$gt": 0}}
        ).sort("rating.average", DESCENDING).limit(limit))


# ============================================================================
# ORDER MANAGEMENT
# ============================================================================

class OrderManager:
    """Handles all order-related operations."""

    def __init__(self):
        self.collection = get_db().orders
        self.products = get_db().products

    def generate_order_number(self) -> str:
        """Generate unique order number."""
        prefix = "ORD"
        year = datetime.utcnow().year
        count = self.collection.count_documents({}) + 1
        return f"{prefix}-{year}-{count:06d}"

    def create_order(self, customer_id: str, items: List[Dict],
                    shipping_address: Dict, billing_address: Dict,
                    shipping_method: str = "standard", notes: str = "") -> Optional[Dict]:
        """Create a new order with inventory check and stock deduction."""

        # Validate stock and calculate totals
        order_items = []
        subtotal = 0

        for item in items:
            product = self.products.find_one({"_id": ObjectId(item["productId"])})
            if not product:
                print(f"❌ Product {item['productId']} not found!")
                return None

            if product["stock"] < item["quantity"]:
                print(f"❌ Insufficient stock for {product['name']}! Available: {product['stock']}")
                return None

            unit_price = product["price"]
            discount = item.get("discount", 0)
            item_total = (unit_price - discount) * item["quantity"]

            order_items.append({
                "productId": product["_id"],
                "sku": product["sku"],
                "name": product["name"],
                "quantity": item["quantity"],
                "unitPrice": unit_price,
                "discount": discount,
                "totalPrice": round(item_total, 2)
            })

            subtotal += item_total

        # Calculate costs
        shipping_cost = 9.99 if shipping_method == "standard" else 19.99
        tax_rate = 0.08
        tax = round(subtotal * tax_rate, 2)
        discount_total = sum(item["discount"] * item["quantity"] for item in order_items)
        grand_total = round(subtotal + shipping_cost + tax, 2)

        order = {
            "orderNumber": self.generate_order_number(),
            "customerId": ObjectId(customer_id),
            "status": "pending",
            "orderDate": datetime.utcnow(),
            "items": order_items,
            "shippingAddress": shipping_address,
            "billingAddress": billing_address,
            "subtotal": round(subtotal, 2),
            "shippingCost": shipping_cost,
            "tax": tax,
            "discountTotal": round(discount_total, 2),
            "grandTotal": grand_total,
            "shippingMethod": shipping_method,
            "notes": notes
        }

        # Insert order
        result = self.collection.insert_one(order)
        order_id = result.inserted_id

        # Deduct stock
        for item in items:
            self.products.update_one(
                {"_id": ObjectId(item["productId"])},
                {"$inc": {"stock": -item["quantity"]}}
            )

        print(f"✅ Order created: {order['orderNumber']} (Total: ${grand_total})")
        return {"orderId": str(order_id), "orderNumber": order["orderNumber"], "total": grand_total}

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Get order by ID."""
        return self.collection.find_one({"_id": ObjectId(order_id)})

    def get_order_by_number(self, order_number: str) -> Optional[Dict]:
        """Get order by order number."""
        return self.collection.find_one({"orderNumber": order_number})

    def update_order_status(self, order_id: str, status: str,
                           tracking_number: str = None,
                           estimated_delivery: datetime = None) -> bool:
        """Update order status."""
        valid_statuses = ["pending", "confirmed", "processing", "shipped",
                         "out_for_delivery", "delivered", "cancelled", "returned"]

        if status not in valid_statuses:
            print(f"❌ Invalid status! Must be one of: {valid_statuses}")
            return False

        updates = {"status": status, "updatedAt": datetime.utcnow()}

        if tracking_number:
            updates["trackingNumber"] = tracking_number
        if estimated_delivery:
            updates["estimatedDelivery"] = estimated_delivery
        if status == "delivered":
            updates["deliveredAt"] = datetime.utcnow()

        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order and restore stock."""
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        if order["status"] in ["delivered", "returned", "cancelled"]:
            print("❌ Cannot cancel this order!")
            return False

        # Restore stock
        for item in order["items"]:
            self.products.update_one(
                {"_id": item["productId"]},
                {"$inc": {"stock": item["quantity"]}}
            )

        result = self.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "cancelled", "cancelledAt": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_customer_orders(self, customer_id: str, limit: int = 20) -> List[Dict]:
        """Get all orders for a customer."""
        return list(self.collection.find(
            {"customerId": ObjectId(customer_id)}
        ).sort("orderDate", DESCENDING).limit(limit))

    def get_orders_by_status(self, status: str, limit: int = 50) -> List[Dict]:
        """Get orders by status."""
        return list(self.collection.find(
            {"status": status}
        ).sort("orderDate", DESCENDING).limit(limit))


# ============================================================================
# PAYMENT MANAGEMENT
# ============================================================================

class PaymentManager:
    """Handles all payment-related operations."""

    def __init__(self):
        self.collection = get_db().payments

    def process_payment(self, order_id: str, customer_id: str,
                       amount: float, method: str,
                       payment_details: Dict) -> Optional[str]:
        """Process a payment for an order."""

        transaction_id = f"txn_{ObjectId()}"

        payment = {
            "orderId": ObjectId(order_id),
            "orderNumber": payment_details.get("orderNumber", ""),
            "customerId": ObjectId(customer_id),
            "amount": amount,
            "currency": payment_details.get("currency", "USD"),
            "method": method,
            "status": "completed",
            "transactionId": transaction_id,
            "paymentDetails": {
                "cardLastFour": payment_details.get("cardLastFour", ""),
                "cardType": payment_details.get("cardType", ""),
                "expiryMonth": payment_details.get("expiryMonth"),
                "expiryYear": payment_details.get("expiryYear")
            },
            "processedAt": datetime.utcnow(),
            "refundedAmount": 0,
            "refundHistory": []
        }

        try:
            result = self.collection.insert_one(payment)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Payment processing failed: {e}")
            return None

    def get_payment_by_order(self, order_id: str) -> Optional[Dict]:
        """Get payment by order ID."""
        return self.collection.find_one({"orderId": ObjectId(order_id)})

    def process_refund(self, payment_id: str, amount: float, reason: str) -> bool:
        """Process a partial or full refund."""
        payment = self.collection.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            return False

        available = payment["amount"] - payment["refundedAmount"]
        if amount > available:
            print(f"❌ Refund amount exceeds available amount! Available: ${available}")
            return False

        refund_record = {
            "refundId": f"ref_{ObjectId()}",
            "amount": amount,
            "reason": reason,
            "processedAt": datetime.utcnow()
        }

        result = self.collection.update_one(
            {"_id": ObjectId(payment_id)},
            {
                "$inc": {"refundedAmount": amount},
                "$push": {"refundHistory": refund_record},
                "$set": {
                    "status": "refunded" if amount == available else "partially_refunded",
                    "updatedAt": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    def get_customer_payments(self, customer_id: str) -> List[Dict]:
        """Get all payments for a customer."""
        return list(self.collection.find(
            {"customerId": ObjectId(customer_id)}
        ).sort("processedAt", DESCENDING))


# ============================================================================
# REVIEW MANAGEMENT
# ============================================================================

class ReviewManager:
    """Handles all review-related operations."""

    def __init__(self):
        self.collection = get_db().reviews
        self.products = get_db().products

    def create_review(self, product_id: str, customer_id: str,
                     customer_name: str, order_id: str,
                     rating: int, title: str, comment: str,
                     images: List[str] = None) -> Optional[str]:
        """Create a product review and update product rating."""

        if not 1 <= rating <= 5:
            print("❌ Rating must be between 1 and 5!")
            return None

        review = {
            "productId": ObjectId(product_id),
            "customerId": ObjectId(customer_id),
            "customerName": customer_name,
            "orderId": ObjectId(order_id),
            "rating": rating,
            "title": title,
            "comment": comment,
            "images": images or [],
            "helpful": 0,
            "verifiedPurchase": True,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = self.collection.insert_one(review)

        # Update product rating using aggregation
        self._update_product_rating(product_id)

        return str(result.inserted_id)

    def _update_product_rating(self, product_id: str):
        """Recalculate and update product average rating."""
        pipeline = [
            {"$match": {"productId": ObjectId(product_id)}},
            {
                "$group": {
                    "_id": "$productId",
                    "averageRating": {"$avg": "$rating"},
                    "reviewCount": {"$sum": 1}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            avg_rating = round(result[0]["averageRating"], 1)
            count = result[0]["reviewCount"]

            self.products.update_one(
                {"_id": ObjectId(product_id)},
                {
                    "$set": {
                        "rating.average": avg_rating,
                        "rating.count": count,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )

    def get_product_reviews(self, product_id: str, limit: int = 20,
                           sort_by: str = "helpful") -> List[Dict]:
        """Get reviews for a product."""
        sort_field = "helpful" if sort_by == "helpful" else "createdAt"
        sort_order = DESCENDING if sort_by == "helpful" else DESCENDING

        return list(self.collection.find(
            {"productId": ObjectId(product_id)}
        ).sort(sort_field, sort_order).limit(limit))

    def mark_helpful(self, review_id: str) -> bool:
        """Mark a review as helpful."""
        result = self.collection.update_one(
            {"_id": ObjectId(review_id)},
            {"$inc": {"helpful": 1}}
        )
        return result.modified_count > 0

    def get_review_summary(self, product_id: str) -> Dict:
        """Get rating distribution for a product."""
        pipeline = [
            {"$match": {"productId": ObjectId(product_id)}},
            {
                "$group": {
                    "_id": "$rating",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": -1}}
        ]

        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for doc in self.collection.aggregate(pipeline):
            distribution[doc["_id"]] = doc["count"]

        total = sum(distribution.values())
        product = self.products.find_one({"_id": ObjectId(product_id)})

        return {
            "productId": product_id,
            "averageRating": product["rating"]["average"] if product else 0,
            "totalReviews": total,
            "distribution": distribution
        }


# ============================================================================
# CART MANAGEMENT
# ============================================================================

class CartManager:
    """Handles shopping cart operations."""

    def __init__(self):
        self.collection = get_db().carts
        self.products = get_db().products

    def get_cart(self, customer_id: str) -> Optional[Dict]:
        """Get customer's cart."""
        return self.collection.find_one({"customerId": ObjectId(customer_id)})

    def add_to_cart(self, customer_id: str, product_id: str,
                   quantity: int = 1) -> bool:
        """Add item to cart."""
        product = self.products.find_one({"_id": ObjectId(product_id)})
        if not product or not product["isActive"]:
            print("❌ Product not found or inactive!")
            return False

        if product["stock"] < quantity:
            print(f"❌ Only {product['stock']} items available!")
            return False

        cart_item = {
            "productId": product["_id"],
            "sku": product["sku"],
            "name": product["name"],
            "quantity": quantity,
            "unitPrice": product["price"],
            "addedAt": datetime.utcnow()
        }

        # Check if item already in cart
        existing = self.collection.find_one({
            "customerId": ObjectId(customer_id),
            "items.productId": ObjectId(product_id)
        })

        if existing:
            result = self.collection.update_one(
                {
                    "customerId": ObjectId(customer_id),
                    "items.productId": ObjectId(product_id)
                },
                {
                    "$inc": {"items.$.quantity": quantity},
                    "$set": {"lastUpdated": datetime.utcnow()}
                }
            )
        else:
            result = self.collection.update_one(
                {"customerId": ObjectId(customer_id)},
                {
                    "$push": {"items": cart_item},
                    "$set": {"lastUpdated": datetime.utcnow()}
                },
                upsert=True
            )

        self._recalculate_cart(customer_id)
        return result.modified_count > 0 or result.upserted_id is not None

    def update_cart_item(self, customer_id: str, product_id: str,
                        quantity: int) -> bool:
        """Update item quantity in cart."""
        if quantity <= 0:
            return self.remove_from_cart(customer_id, product_id)

        product = self.products.find_one({"_id": ObjectId(product_id)})
        if product and product["stock"] < quantity:
            print(f"❌ Only {product['stock']} items available!")
            return False

        result = self.collection.update_one(
            {
                "customerId": ObjectId(customer_id),
                "items.productId": ObjectId(product_id)
            },
            {
                "$set": {
                    "items.$.quantity": quantity,
                    "lastUpdated": datetime.utcnow()
                }
            }
        )

        self._recalculate_cart(customer_id)
        return result.modified_count > 0

    def remove_from_cart(self, customer_id: str, product_id: str) -> bool:
        """Remove item from cart."""
        result = self.collection.update_one(
            {"customerId": ObjectId(customer_id)},
            {
                "$pull": {"items": {"productId": ObjectId(product_id)}},
                "$set": {"lastUpdated": datetime.utcnow()}
            }
        )

        self._recalculate_cart(customer_id)
        return result.modified_count > 0

    def clear_cart(self, customer_id: str) -> bool:
        """Clear entire cart."""
        result = self.collection.update_one(
            {"customerId": ObjectId(customer_id)},
            {
                "$set": {
                    "items": [],
                    "subtotal": 0,
                    "lastUpdated": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    def _recalculate_cart(self, customer_id: str):
        """Recalculate cart subtotal."""
        cart = self.get_cart(customer_id)
        if not cart:
            return

        subtotal = sum(
            item["unitPrice"] * item["quantity"]
            for item in cart.get("items", [])
        )

        self.collection.update_one(
            {"customerId": ObjectId(customer_id)},
            {
                "$set": {
                    "subtotal": round(subtotal, 2),
                    "expiresAt": datetime.utcnow() + timedelta(days=7)
                }
            }
        )


# ============================================================================
# CATEGORY MANAGEMENT
# ============================================================================

class CategoryManager:
    """Handles category operations."""

    def __init__(self):
        self.collection = get_db().categories

    def create_category(self, name: str, slug: str, description: str = "",
                       parent_id: str = None, image: str = "") -> Optional[str]:
        """Create a new category."""
        category = {
            "name": name,
            "slug": slug,
            "description": description,
            "parentId": ObjectId(parent_id) if parent_id else None,
            "level": 1 if not parent_id else 2,
            "image": image,
            "isActive": True,
            "productCount": 0,
            "subCategories": []
        }

        try:
            result = self.collection.insert_one(category)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print("❌ Category with this slug already exists!")
            return None

    def get_all_categories(self) -> List[Dict]:
        """Get all active categories."""
        return list(self.collection.find({"isActive": True}).sort("name", ASCENDING))

    def get_category_tree(self) -> List[Dict]:
        """Get hierarchical category tree."""
        pipeline = [
            {"$match": {"isActive": True, "parentId": None}},
            {
                "$graphLookup": {
                    "from": "categories",
                    "startWith": "$_id",
                    "connectFromField": "_id",
                    "connectToField": "parentId",
                    "as": "children",
                    "depthField": "level"
                }
            }
        ]
        return list(self.collection.aggregate(pipeline))


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

class AnalyticsManager:
    """Provides business analytics and reporting."""

    def __init__(self):
        self.db = get_db().db

    def sales_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Generate sales report for date range."""
        pipeline = [
            {
                "$match": {
                    "orderDate": {"$gte": start_date, "$lte": end_date},
                    "status": {"$nin": ["cancelled"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "totalOrders": {"$sum": 1},
                    "totalRevenue": {"$sum": "$grandTotal"},
                    "totalItems": {"$sum": {"$size": "$items"}},
                    "avgOrderValue": {"$avg": "$grandTotal"},
                    "totalDiscount": {"$sum": "$discountTotal"}
                }
            }
        ]

        result = list(self.db.orders.aggregate(pipeline))
        return result[0] if result else {}

    def top_selling_products(self, limit: int = 10) -> List[Dict]:
        """Get top selling products."""
        pipeline = [
            {"$match": {"status": {"$nin": ["cancelled"]}}},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.productId",
                    "productName": {"$first": "$items.name"},
                    "sku": {"$first": "$items.sku"},
                    "totalSold": {"$sum": "$items.quantity"},
                    "totalRevenue": {"$sum": "$items.totalPrice"}
                }
            },
            {"$sort": {"totalSold": -1}},
            {"$limit": limit}
        ]
        return list(self.db.orders.aggregate(pipeline))

    def customer_analytics(self) -> Dict:
        """Get customer analytics."""
        pipeline = [
            {
                "$lookup": {
                    "from": "orders",
                    "localField": "_id",
                    "foreignField": "customerId",
                    "as": "orders"
                }
            },
            {
                "$project": {
                    "totalSpent": {"$sum": "$orders.grandTotal"},
                    "orderCount": {"$size": "$orders"}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "totalCustomers": {"$sum": 1},
                    "activeCustomers": {
                        "$sum": {"$cond": [{"$gt": ["$orderCount", 0]}, 1, 0]}
                    },
                    "avgLifetimeValue": {"$avg": "$totalSpent"},
                    "totalRevenue": {"$sum": "$totalSpent"}
                }
            }
        ]

        result = list(self.db.customers.aggregate(pipeline))
        return result[0] if result else {}

    def revenue_by_category(self) -> List[Dict]:
        """Get revenue breakdown by category."""
        pipeline = [
            {"$match": {"status": {"$nin": ["cancelled"]}}},
            {"$unwind": "$items"},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.productId",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$group": {
                    "_id": "$product.category",
                    "revenue": {"$sum": "$items.totalPrice"},
                    "itemsSold": {"$sum": "$items.quantity"}
                }
            },
            {"$sort": {"revenue": -1}}
        ]
        return list(self.db.orders.aggregate(pipeline))

    def monthly_sales_trend(self, months: int = 12) -> List[Dict]:
        """Get monthly sales trend."""
        pipeline = [
            {"$match": {"status": {"$nin": ["cancelled"]}}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$orderDate"},
                        "month": {"$month": "$orderDate"}
                    },
                    "orders": {"$sum": 1},
                    "revenue": {"$sum": "$grandTotal"},
                    "avgOrderValue": {"$avg": "$grandTotal"}
                }
            },
            {"$sort": {"_id.year": -1, "_id.month": -1}},
            {"$limit": months}
        ]
        return list(self.db.orders.aggregate(pipeline))


# ============================================================================
# SAMPLE DATA GENERATOR
# ============================================================================

def generate_sample_data():
    """Generate sample data for testing."""
    db = get_db()

    # Clear existing data
    db.customers.delete_many({})
    db.products.delete_many({})
    db.orders.delete_many({})
    db.payments.delete_many({})
    db.reviews.delete_many({})
    db.carts.delete_many({})
    db.categories.delete_many({})

    print("🗑️  Cleared existing data")

    # Categories
    categories_data = [
        {"name": "Electronics", "slug": "electronics", "description": "Gadgets and devices", "productCount": 0},
        {"name": "Clothing", "slug": "clothing", "description": "Apparel and accessories", "productCount": 0},
        {"name": "Home & Kitchen", "slug": "home-kitchen", "description": "Home essentials", "productCount": 0},
        {"name": "Books", "slug": "books", "description": "Physical and digital books", "productCount": 0},
        {"name": "Sports", "slug": "sports", "description": "Sports equipment", "productCount": 0}
    ]
    db.categories.insert_many(categories_data)
    print("✅ Categories created")

    # Products
    products_data = [
        {"sku": "ELEC-001", "name": "Wireless Bluetooth Headphones", "description": "Premium noise-cancelling headphones", "category": "Electronics", "subCategory": "Audio", "brand": "SoundMax", "price": 129.99, "stock": 150, "attributes": {"color": "Black", "batteryLife": "30h"}, "tags": ["wireless", "bluetooth", "premium"]},
        {"sku": "ELEC-002", "name": "Smart Watch Pro", "description": "Fitness tracking smartwatch", "category": "Electronics", "subCategory": "Wearables", "brand": "TechGear", "price": 249.99, "stock": 80, "attributes": {"color": "Silver", "waterResistant": "Yes"}, "tags": ["smart", "fitness", "wearable"]},
        {"sku": "ELEC-003", "name": "4K Webcam", "description": "Ultra HD webcam for streaming", "category": "Electronics", "subCategory": "Cameras", "brand": "VisionCam", "price": 89.99, "stock": 200, "attributes": {"resolution": "4K", "fps": "60"}, "tags": ["webcam", "streaming", "4k"]},
        {"sku": "CLTH-001", "name": "Cotton T-Shirt", "description": "100% organic cotton tee", "category": "Clothing", "subCategory": "Tops", "brand": "EcoWear", "price": 24.99, "stock": 500, "attributes": {"color": "White", "size": "M"}, "tags": ["cotton", "organic", "casual"]},
        {"sku": "CLTH-002", "name": "Running Shoes", "description": "Lightweight running shoes", "category": "Clothing", "subCategory": "Footwear", "brand": "RunFast", "price": 89.99, "stock": 120, "attributes": {"color": "Blue", "size": "10"}, "tags": ["running", "sports", "lightweight"]},
        {"sku": "HOME-001", "name": "Coffee Maker", "description": "Programmable drip coffee maker", "category": "Home & Kitchen", "subCategory": "Appliances", "brand": "BrewMaster", "price": 79.99, "stock": 60, "attributes": {"capacity": "12 cups", "color": "Black"}, "tags": ["coffee", "kitchen", "appliance"]},
        {"sku": "HOME-002", "name": "LED Desk Lamp", "description": "Adjustable LED desk lamp", "category": "Home & Kitchen", "subCategory": "Lighting", "brand": "BrightLight", "price": 34.99, "stock": 300, "attributes": {"color": "White", "brightness": "1000 lumens"}, "tags": ["led", "desk", "lighting"]},
        {"sku": "BOOK-001", "name": "Python Programming", "description": "Complete Python guide", "category": "Books", "subCategory": "Programming", "brand": "TechPress", "price": 39.99, "stock": 100, "attributes": {"pages": 450, "format": "Paperback"}, "tags": ["python", "programming", "coding"]},
        {"sku": "BOOK-002", "name": "The Art of Design", "description": "Design principles book", "category": "Books", "subCategory": "Design", "brand": "CreativePress", "price": 29.99, "stock": 75, "attributes": {"pages": 320, "format": "Hardcover"}, "tags": ["design", "art", "creative"]},
        {"sku": "SPRT-001", "name": "Yoga Mat", "description": "Non-slip exercise yoga mat", "category": "Sports", "subCategory": "Fitness", "brand": "FlexFit", "price": 29.99, "stock": 250, "attributes": {"color": "Purple", "thickness": "6mm"}, "tags": ["yoga", "fitness", "exercise"]}
    ]

    for p in products_data:
        p["rating"] = {"average": round(random.uniform(3.5, 5.0), 1), "count": random.randint(50, 500)}
        p["isActive"] = True
        p["createdAt"] = datetime.utcnow() - timedelta(days=random.randint(30, 365))
        p["updatedAt"] = datetime.utcnow()
        p["images"] = [f"https://cdn.example.com/images/{p['sku'].lower()}.jpg"]

    db.products.insert_many(products_data)
    print("✅ Products created")

    # Customers
    customers_data = [
        {"firstName": "John", "lastName": "Doe", "email": "john.doe@example.com", "password": "hashed_pass", "phone": "+1-555-0101", "addresses": [{"addressId": "addr_1", "type": "home", "street": "123 Main St", "city": "New York", "state": "NY", "zipCode": "10001", "country": "USA", "isDefault": True}]},
        {"firstName": "Jane", "lastName": "Smith", "email": "jane.smith@example.com", "password": "hashed_pass", "phone": "+1-555-0102", "addresses": [{"addressId": "addr_2", "type": "home", "street": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zipCode": "90001", "country": "USA", "isDefault": True}]},
        {"firstName": "Bob", "lastName": "Johnson", "email": "bob.j@example.com", "password": "hashed_pass", "phone": "+1-555-0103", "addresses": [{"addressId": "addr_3", "type": "home", "street": "789 Pine Rd", "city": "Chicago", "state": "IL", "zipCode": "60601", "country": "USA", "isDefault": True}]},
        {"firstName": "Alice", "lastName": "Williams", "email": "alice.w@example.com", "password": "hashed_pass", "phone": "+1-555-0104", "addresses": [{"addressId": "addr_4", "type": "home", "street": "321 Elm St", "city": "Houston", "state": "TX", "zipCode": "77001", "country": "USA", "isDefault": True}]},
        {"firstName": "Charlie", "lastName": "Brown", "email": "charlie.b@example.com", "password": "hashed_pass", "phone": "+1-555-0105", "addresses": [{"addressId": "addr_5", "type": "home", "street": "654 Maple Dr", "city": "Phoenix", "state": "AZ", "zipCode": "85001", "country": "USA", "isDefault": True}]}
    ]

    for c in customers_data:
        c["createdAt"] = datetime.utcnow() - timedelta(days=random.randint(30, 180))
        c["isActive"] = True
        c["preferences"] = {"newsletter": True, "notifications": {"email": True, "sms": False, "push": True}, "currency": "USD", "language": "en"}

    db.customers.insert_many(customers_data)
    print("✅ Customers created")

    print("\n🎉 Sample data generation complete!")
    print(f"   Categories: {db.categories.count_documents({})}")
    print(f"   Products: {db.products.count_documents({})}")
    print(f"   Customers: {db.customers.count_documents({})}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Online Shopping Management System - MongoDB")
    print("=" * 60)

    # Setup
    setup_indexes()
    generate_sample_data()

    # Initialize managers
    customer_mgr = CustomerManager()
    product_mgr = ProductManager()
    order_mgr = OrderManager()
    payment_mgr = PaymentManager()
    review_mgr = ReviewManager()
    cart_mgr = CartManager()
    analytics_mgr = AnalyticsManager()

    # Demo operations
    print("\n" + "=" * 60)
    print("  DEMO OPERATIONS")
    print("=" * 60)

    # 1. Search products
    print("\n📦 Product Search (Electronics):")
    results = product_mgr.search_products(category="Electronics", limit=3)
    for p in results["products"]:
        print(f"   - {p['name']} | ${p['price']} | Stock: {p['stock']} | ⭐ {p['rating']['average']}")

    # 2. Add to cart
    customer = customer_mgr.get_customer_by_email("john.doe@example.com")
    product = product_mgr.get_product_by_sku("ELEC-001")

    print(f"\n🛒 Adding to cart: {product['name']}")
    cart_mgr.add_to_cart(str(customer["_id"]), str(product["_id"]), 2)
    cart = cart_mgr.get_cart(str(customer["_id"]))
    print(f"   Cart subtotal: ${cart['subtotal']}")

    # 3. Create order
    print("\n📋 Creating order...")
    shipping = customer["addresses"][0].copy()
    del shipping["addressId"], shipping["type"], shipping["isDefault"]

    order_result = order_mgr.create_order(
        str(customer["_id"]),
        [{"productId": str(product["_id"]), "quantity": 1, "discount": 10}],
        shipping, shipping,
        shipping_method="standard"
    )

    if order_result:
        # 4. Process payment
        print("\n💳 Processing payment...")
        payment_id = payment_mgr.process_payment(
            order_result["orderId"],
            str(customer["_id"]),
            order_result["total"],
            "credit_card",
            {"orderNumber": order_result["orderNumber"], "cardLastFour": "4242", "cardType": "Visa", "expiryMonth": 12, "expiryYear": 2027}
        )
        print(f"   Payment ID: {payment_id}")

        # 5. Add review
        print("\n⭐ Adding review...")
        review_id = review_mgr.create_review(
            str(product["_id"]),
            str(customer["_id"]),
            f"{customer['firstName']} {customer['lastName']}",
            order_result["orderId"],
            5,
            "Excellent product!",
            "Best headphones I've ever owned. Great sound quality."
        )
        print(f"   Review ID: {review_id}")

        # 6. Update order status
        print("\n🚚 Updating order status...")
        order_mgr.update_order_status(
            order_result["orderId"],
            "shipped",
            tracking_number="TRK-123456789",
            estimated_delivery=datetime.utcnow() + timedelta(days=3)
        )
        print("   Status: shipped")

    # 7. Analytics
    print("\n📊 Analytics:")

    # Top selling products
    top_products = analytics_mgr.top_selling_products(3)
    print("\n   Top Selling Products:")
    for p in top_products:
        print(f"   - {p['productName']}: {p['totalSold']} sold, ${p['totalRevenue']:.2f} revenue")

    # Customer analytics
    cust_stats = analytics_mgr.customer_analytics()
    print(f"\n   Customer Stats:")
    print(f"   - Total Customers: {cust_stats.get('totalCustomers', 0)}")
    print(f"   - Active Customers: {cust_stats.get('activeCustomers', 0)}")
    print(f"   - Avg Lifetime Value: ${cust_stats.get('avgLifetimeValue', 0):.2f}")

    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
