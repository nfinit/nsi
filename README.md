![NSI logo](res/logo.gif)

NSI: the New Standard Index
---------------------------
NSI is an advanced, single-file CGI directory index that composes collections 
of hand-written HTML into a real, consistent website. Simply drop `index.cgi`
into a directory, provide your content in plain HTML according to simple rules, 
and NSI composes a page with no build step, runtime or dependencies needed 
beyond a CGI-capable web server and Perl itself.

NSI supports nesting to build more complex websites: symlink `index.cgi` into
a subdirectory and it will inherit configuration, styling and build dynamic
navigation from its parents. NSI can also enable custom server-side dynamism
through executable script fragments. 

NSI is built on progressive enhancement; its baseline output can target clients
as early as Netscape and even NCSA Mosaic, while split-path stylesheet and
script embedding can layer modern browser capabilities on top for clients
that can take advantage of them.
