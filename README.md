# front

Getting from python objects to UIs exposing them.
Note the absence of the G in front of UI. 
This is because a UI (User Interface) is not necessarily graphical.
Though graphical interfaces will be our main focus, we are concerned here 
will the slightly more general problem of UIs, that could take the form of 
web-services, command-line interfaces, could be web-based or not, etc.

To install:	```pip install front```

# Note about major changes

This package used to be what [py2dash](https://github.com/i2mint/py2dash/), 
but using `streamlit` instead of `dash` as its backend. 
This has since been moved to [streamlitfront](https://github.com/i2mint/streamlitfront/), 
making way for `front` to (yet) become the common set of tools to be used in both.
