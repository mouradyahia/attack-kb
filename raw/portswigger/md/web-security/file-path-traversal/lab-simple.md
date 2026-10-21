# Lab: File path traversal, simple case

This lab contains a path traversal vulnerability in the display of product images.

To solve the lab, retrieve the contents of the `/etc/passwd` file.

####  Solution

-  Use Burp Suite to intercept and modify a request that fetches a product image.
-

Modify the `filename` parameter, giving it the value:

```
../../../etc/passwd
```

-  Observe that the response contains the contents of the `/etc/passwd` file.

####  Community solutions

Rana Khalil

Intigriti

z3nsh3ll

Michael Sommer
