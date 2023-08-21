# scissors

The URL Shortener and QR Code Generator is a Flask-RESTful API that allows users to shorten long URLs and generate QR codes for them. This API provides endpoints to create short URLs, redirect the short URL to the website of their corresponding long URL, get click counts of how many visits the short URL has, as well as analytics, and generate QR codes for short URLs.

## Features

***URL Shortening:*** Convert long URLs into short, get  click counts and analytics of the shortened URL.

***URL Redirect:*** Redirect the shortl URL to the website of the long URL.

***QR Code Generation:*** Generate QR codes for short URLs.

***Error Handling:*** Proper HTTP status codes and error messages for a user-friendly experience.

***Data Validation:*** Input validation to ensure the accuracy of URLs and short codes.

## API Endpoints

### auth

***POST /auth/signup:*** Signup a new user.

***POST /auth/login:*** User login to obtain an authentication token.

***POST /auth/refresh:*** Obtain an authentication refresh token.

***POST /auth/logout:*** User logout.

### shorturl

***POST /shorturl/shorturl:*** Shorten a long URL.

***GET /shorturl/{short_url}:*** Redirect a shortened URL to it's corresponding long URL.

***GET /shorturl/link_history:*** Get the link history of current user.

***GET /shorturl/clicks/{short_url}:*** Retrieve the number of clicks for a short URL.

***GET /shorturl/delete/{short_url}:*** Delete a short URL.

### analytics

***GET /analytics/analytics/{short_url}:*** Get Analytics for a short URL.

### qrcode

***POST /qrcode/generate:*** Generate QRcode fora short URL.


***GET /qrcode/{short_url}:*** Get QRcode of short URL to download.

## Authentication

The API uses JWT-based authentication. To access protected endpoints, include the JWT token in the Authorization header as `Bearer <token>`.

## Error Handling

The API returns appropriate HTTP status codes and error messages in case of errors.
