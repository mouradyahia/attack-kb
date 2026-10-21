# Lab: File path traversal, traversal sequences blocked with absolute path bypass

This lab contains a path traversal vulnerability in the display of product images.

The application blocks traversal sequences but treats the supplied filename as being relative to a default working directory.

To solve the lab, retrieve the contents of the `/etc/passwd` file.

####  Solution

-  Use Burp Suite to intercept and modify a request that fetches a product image.
-  Modify the `filename` parameter, giving it the value `/etc/passwd`.
-  Observe that the response contains the contents of the `/etc/passwd` file.

####  Community solutions

Rana Khalil

z3nsh3ll

Intigriti

Michael Sommer
