# Python Web Server

The server can handle both **POST** and **GET** request. For CGI-scripts, only python scripts are handled.
Within these:
* the output can be a style sheet, html sheet, or whatever, just specify the content-type at the beginning.
* to get the URL-query, or the form data, use the cgi module.

For more specific instructions run 
``` python Server.py -h ```

## The interpreter 

In Html you can add the tag

```html
  <py-script src="path/to/script.py"> </py-script>
```

and inside it you can write all the python code you want; the ```print()``` method will be equivalent to echo in PhP.

## Routing rules

You can add a ```.htaccess``` file in your root directory, then configure routing rules. The syntax is:

* ```Document Error [ERROR TYPE]``` ```/relative/path/to/custom-error-file.html``` (to redirect errors)
* ```URL``` ```/path-to/another-url```

## Cgi-module examples

In HTML:

```html
<a href="script.py?Title="xxx"> link </a> -> a link to a python script with a query string

<form action="script.py" method="POST">  -> a form with method POST
    <input type="text" name="Input">
    <input type="submit" value="submit">
</form>
```

In the Python script:

```python
import cgi
data = cgi.FieldStorage()

title = data.getvalue('Title')
input = data.getvalue('Input')

print("Content-type: text/html\r\n\r\n") -> the content type

print("""
    <html>
    <head>
        <title> CGI Example </title>
    </head>
    <body>
        %s <br> %s
    </body>
    </html>
""" % (input, title))
```
