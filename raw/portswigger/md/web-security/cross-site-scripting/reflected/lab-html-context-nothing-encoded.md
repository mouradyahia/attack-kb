# Lab: Reflected XSS into HTML context with nothing encoded

This lab contains a simple reflected cross-site scripting vulnerability in the search functionality.

To solve the lab, perform a cross-site scripting attack that calls the `alert` function.

####  Solution

-

Copy and paste the following into the search box:

```
<script>alert(1)</script>
```

-  Click "Search".

####  Community solutions

z3nsh3ll

Michael Sommer
