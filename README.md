# LocalMart – Local Business E-Commerce Website

Academic full-stack project based on the supplied SRS.

## Technology
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Backend: Python Flask
- Database: MySQL

## Setup
1. Install Python 3.10+ and MySQL 8+.
2. Run `database/schema.sql` in MySQL Workbench.
3. Copy `.env.example` to `.env` and set your MySQL password.
4. Run `pip install -r requirements.txt`.
5. Run `python app.py`.
6. Open `http://127.0.0.1:5000`.

## Demo admin
Email: `admin@localmart.com`
Password: `admin123`

The application creates this demo admin automatically on first start. Change the password before real deployment.

## SRS coverage
Registration/login, product browsing/search/details, shopping cart, checkout/address, order history/status, admin authentication, product/category/stock management, customer/order management and basic sales reports.

This academic version intentionally does not include a real payment gateway or delivery API.


## Professional storefront update
This version adds a modern LocalMart storefront, responsive navigation, product catalogue cards, category browsing, richer seeded products, cart/checkout UI, customer authentication screens, order history, and an improved admin console. Existing Flask/MySQL shopping, authentication, checkout, and order-management routes are preserved.


## Full marketplace expansion
Added wishlist/saved products, customer reviews and ratings, related products, product sorting, Deals navigation, account center, coupon codes (`WELCOME10`, `LOCAL100`), payment method selection, richer checkout, and an expanded responsive storefront.


## Complete feature set
See `docs/FEATURES.md` for the full storefront, customer, checkout, wishlist/review, coupon, and admin feature list. A full multi-screen UI mockup is included at `docs/localmart_full_ui_mockup.png`.
