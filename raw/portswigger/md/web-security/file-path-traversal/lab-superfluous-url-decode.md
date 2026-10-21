# Lab: File path traversal, traversal sequences stripped with superfluous URL-decode

This lab contains a path traversal vulnerability in the display of product images.

The application blocks input containing path traversal sequences. It then performs a URL-decode of the input before using it.

To solve the lab, retrieve the contents of the `/etc/passwd` file.

####  Solution

-  Use Burp Suite to intercept and modify a request that fetches a product image.
-

Modify the `filename` parameter, giving it the value:

```
..%252f..%252f..%252fetc/passwd
```

-  Observe that the response contains the contents of the `/etc/passwd` file.

####  Community solutions

Rana Khalil

Intigriti

z3nsh3ll

Michael Sommer
