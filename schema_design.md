# Online Shopping Management System - MongoDB Schema Design

## Overview
A NoSQL document-oriented database for managing an online shopping platform.

---

## 1. customers Collection
```json
{
  "_id": ObjectId("..."),
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "password": "hashed_password",
  "phone": "+1-555-0123",
  "dateOfBirth": ISODate("1990-05-15"),
  "createdAt": ISODate("2024-01-10T08:30:00Z"),
  "isActive": true,
  "addresses": [
    {
      "addressId": "addr_001",
      "type": "home",
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zipCode": "10001",
      "country": "USA",
      "isDefault": true
    }
  ],
  "preferences": {
    "newsletter": true,
    "notifications": {
      "email": true,
      "sms": false,
      "push": true
    },
    "currency": "USD",
    "language": "en"
  }
}
```
**Indexes:** `email` (unique), `phone`, `createdAt`

---

## 2. products Collection
```json
{
  "_id": ObjectId("..."),
  "sku": "PROD-001",
  "name": "Wireless Bluetooth Headphones",
  "description": "Premium over-ear headphones with active noise cancellation...",
  "category": "Electronics",
  "subCategory": "Audio",
  "brand": "SoundMax",
  "price": 129.99,
  "currency": "USD",
  "stock": 150,
  "attributes": {
    "color": "Black",
    "weight": "250g",
    "warranty": "2 years",
    "batteryLife": "30 hours"
  },
  "images": [
    "https://cdn.example.com/images/prod001_1.jpg",
    "https://cdn.example.com/images/prod001_2.jpg"
  ],
  "tags": ["wireless", "bluetooth", "noise-cancelling", "premium"],
  "rating": {
    "average": 4.5,
    "count": 328
  },
  "isActive": true,
  "createdAt": ISODate("2024-01-05T10:00:00Z"),
  "updatedAt": ISODate("2024-06-20T14:30:00Z")
}
```
**Indexes:** `sku` (unique), `category`, `brand`, `price`, `tags`, `isActive`

---

## 3. orders Collection
```json
{
  "_id": ObjectId("..."),
  "orderNumber": "ORD-2024-0001",
  "customerId": ObjectId("..."),
  "status": "delivered",
  "orderDate": ISODate("2024-06-15T09:00:00Z"),
  "items": [
    {
      "productId": ObjectId("..."),
      "sku": "PROD-001",
      "name": "Wireless Bluetooth Headphones",
      "quantity": 1,
      "unitPrice": 129.99,
      "discount": 10.00,
      "totalPrice": 119.99
    },
    {
      "productId": ObjectId("..."),
      "sku": "PROD-042",
      "name": "USB-C Cable 2m",
      "quantity": 2,
      "unitPrice": 15.99,
      "discount": 0,
      "totalPrice": 31.98
    }
  ],
  "shippingAddress": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zipCode": "10001",
    "country": "USA"
  },
  "billingAddress": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zipCode": "10001",
    "country": "USA"
  },
  "subtotal": 151.97,
  "shippingCost": 9.99,
  "tax": 12.16,
  "discountTotal": 10.00,
  "grandTotal": 164.12,
  "shippingMethod": "standard",
  "trackingNumber": "TRK-789456123",
  "estimatedDelivery": ISODate("2024-06-20T00:00:00Z"),
  "deliveredAt": ISODate("2024-06-19T16:45:00Z"),
  "notes": "Leave at front door"
}
```
**Indexes:** `orderNumber` (unique), `customerId`, `status`, `orderDate`

---

## 4. payments Collection
```json
{
  "_id": ObjectId("..."),
  "orderId": ObjectId("..."),
  "orderNumber": "ORD-2024-0001",
  "customerId": ObjectId("..."),
  "amount": 164.12,
  "currency": "USD",
  "method": "credit_card",
  "status": "completed",
  "transactionId": "txn_abc123xyz",
  "paymentDetails": {
    "cardLastFour": "4242",
    "cardType": "Visa",
    "expiryMonth": 12,
    "expiryYear": 2027
  },
  "processedAt": ISODate("2024-06-15T09:05:00Z"),
  "refundedAmount": 0,
  "refundHistory": []
}
```
**Indexes:** `orderId`, `customerId`, `transactionId` (unique), `status`

---

## 5. reviews Collection
```json
{
  "_id": ObjectId("..."),
  "productId": ObjectId("..."),
  "customerId": ObjectId("..."),
  "customerName": "John Doe",
  "orderId": ObjectId("..."),
  "rating": 5,
  "title": "Excellent sound quality!",
  "comment": "The noise cancellation is amazing. Battery lasts all day...",
  "images": ["https://cdn.example.com/reviews/rev001.jpg"],
  "helpful": 24,
  "verifiedPurchase": true,
  "createdAt": ISODate("2024-06-20T10:30:00Z"),
  "updatedAt": ISODate("2024-06-20T10:30:00Z")
}
```
**Indexes:** `productId`, `customerId`, `rating`, `createdAt`, `verifiedPurchase`

---

## 6. carts Collection
```json
{
  "_id": ObjectId("..."),
  "customerId": ObjectId("..."),
  "items": [
    {
      "productId": ObjectId("..."),
      "sku": "PROD-001",
      "name": "Wireless Bluetooth Headphones",
      "quantity": 1,
      "unitPrice": 129.99,
      "addedAt": ISODate("2024-06-25T14:00:00Z")
    }
  ],
  "subtotal": 129.99,
  "lastUpdated": ISODate("2024-06-25T14:00:00Z"),
  "expiresAt": ISODate("2024-07-02T14:00:00Z")
}
```
**Indexes:** `customerId` (unique), `expiresAt` (TTL)

---

## 7. categories Collection
```json
{
  "_id": ObjectId("..."),
  "name": "Electronics",
  "slug": "electronics",
  "description": "Gadgets, devices, and electronic accessories",
  "parentId": null,
  "level": 1,
  "image": "https://cdn.example.com/categories/electronics.jpg",
  "isActive": true,
  "productCount": 1250,
  "subCategories": [
    {
      "name": "Audio",
      "slug": "audio",
      "productCount": 180
    },
    {
      "name": "Computers",
      "slug": "computers",
      "productCount": 420
    }
  ]
}
```
**Indexes:** `slug` (unique), `parentId`, `isActive`

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Embedded addresses in customers** | Addresses are frequently accessed with customer data; limited in number |
| **Embedded order items in orders** | Order items are always accessed with the order; immutable after creation |
| **Separate payments collection** | Payments have independent lifecycle, audit requirements, and complex queries |
| **Separate reviews collection** | Reviews are large, frequently queried independently, and grow unbounded |
| **Separate carts collection** | Carts need TTL expiry and frequent independent updates |
| **Product rating embedded** | Frequently displayed with product; updated via aggregation pipeline |

## Relationships
- `orders.customerId` → `customers._id`
- `orders.items.productId` → `products._id`
- `payments.orderId` → `orders._id`
- `reviews.productId` → `products._id`
- `reviews.customerId` → `customers._id`
- `carts.customerId` → `customers._id`
- `categories.parentId` → `categories._id`
