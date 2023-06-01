import re
def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)
a='<p style="margin-top:6.0pt;text-align:center" align="center"><span style="font-size:10.0pt;">Số: </span><span style="font-size:10.0pt;">694/QĐ-UBND</span></p>'
a = striphtml(a)
print(a)