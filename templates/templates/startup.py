HELLO_MESSAGE = '<!doctypehtml><html lang=en><meta charset=UTF-8><meta content="width=device-width,initial-scale=1"name=viewport><title>Startup</title><style>#logo{font-size:35px;font-weight:700}#logo span{background:#1d1e2c;padding:5px 20px;border-radius:5px;color:#fff}</style><body style=text-align:center;margin-top:50px;font-family:sans-serif><div id=logo><span>DPanel</span></div><div dir=rtl><p>مرحبا!<p><p>شكرًا لاستخدامك DPanel لإدارة خدمات الويب الخاصة بك.<p>هذا الملف هو ملف تجريبي تم إنشاؤه تلقائيًا بواسطة DPanel لاختبار الإعدادات والتجربة بها.</div><hr><p>Welcome!<p>Thank you for using DPanel to manage your web services.<p>This file is a demo file automatically created by DPanel for testing and experimenting with your settings'
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [HELLO_MESSAGE.encode()]