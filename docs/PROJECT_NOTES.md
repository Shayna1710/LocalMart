# Project Notes / Viva Points

## SRS mapping
FR-01 -> registration/login
FR-02 -> product browsing/search
FR-03 -> product details
FR-04 -> cart add/update/remove
FR-05 -> checkout with delivery address
FR-06 -> order history
FR-07 -> order status
FR-08 -> admin authentication
FR-09 -> product/category/stock management
FR-10 -> customer/order management
FR-11 -> basic sales report

## Comments
The Python source contains comments around database access, authentication, cart handling, admin authorization and development-only settings.

## Academic limitations
- No real payment gateway.
- No real delivery API.
- Product images use an optional image URL/placeholder.
- CSRF protection should be added before production.
- Production should use HTTPS and a production WSGI server.
