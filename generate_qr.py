import sys
import qrcode

"""Generate a QR code PNG from a URL.

Usage:
    python generate_qr.py https://example.com/mydashboard -o dashboard_qr.png

If -o/--output is omitted the file is named qr.png in the current directory.
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_qr.py <URL> [-o output.png]")
        sys.exit(1)

    url = sys.argv[1]
    output = "qr.png"
    if len(sys.argv) >= 4 and sys.argv[2] in {"-o", "--output"}:
        output = sys.argv[3]

    img = qrcode.make(url)
    img.save(output)
    print(f"QR code saved to {output} (URL: {url})")


if __name__ == "__main__":
    main()
