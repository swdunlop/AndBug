%stylesheets=[
% 'style.css'
%]
%libs = [
% 'jquery-1.6.1.min.js',
%]
%title = 'AndBug Navi'
<?xml version='1.0'?>
<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
<html><head>
<title>{{'AndBug Navi'}}</title>
%for css in stylesheets:
<link href="/s/{{css}}" type="text/css" rel="stylesheet"></link>
%end
%for j in libs:
<script type='text/javascript' src='/s/{{j}}'></script>
%end
%for j in js:
<script type='text/javascript' src='/s/{{j}}'></script>
%end
</head><body>
