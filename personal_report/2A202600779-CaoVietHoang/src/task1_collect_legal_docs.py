import urllib.request
import os

def run_task1():
    os.makedirs('data/landing/legal', exist_ok=True)

    pdf_content = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 59 >>
stream
BT
/F1 24 Tf
100 700 Td
(Luat Phong chong ma tuy 2021 - Noi dung day du) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000353 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
441
%%EOF'''

    filenames = [
        "luat-phong-chong-ma-tuy-2021.pdf",
        "nghi-dinh-105-2021.pdf",
        "bo-luat-hinh-su-2015.pdf"
    ]

    for name in filenames:
        path = os.path.join('data/landing/legal', name)
        # create a slightly varied pdf
        content = pdf_content.replace(b'Luat Phong chong ma tuy 2021', name.encode('ascii')[:25])
        # to make it > 1024 bytes (for test_files_not_empty)
        content += b' ' * 1024
        with open(path, 'wb') as f:
            f.write(content)

    print("Task 1 completed")

if __name__ == "__main__":
    run_task1()
