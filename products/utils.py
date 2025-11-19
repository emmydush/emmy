import qrcode
import qrcode.constants
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
import os


def generate_product_qr_code(product):
    """
    Generate a QR code for a product and return the image URL
    """
    # Generate the product detail URL
    # In a real application, you would use the request object to get the full URL
    # For now, we'll create a relative URL
    product_url = reverse("products:detail", kwargs={"pk": product.pk})

    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Add product URL to QR code
    qr.add_data(product_url)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to BytesIO object
    buffer = BytesIO()
    img.save(buffer, "PNG")

    # Return the image data
    buffer.seek(0)
    return buffer


def generate_product_barcode_image(product):
    """
    Generate a barcode image for a product with improved quality for scanning
    """
    if not product.barcode:
        return None

    try:
        # Import the barcode module
        from barcode import get_barcode_class
        from barcode.writer import ImageWriter

        # Map format names to barcode classes
        format_map = {
            "code128": "code128",
            "ean13": "ean13",
            "upca": "upca",
        }

        # Get the appropriate barcode class
        barcode_format = format_map.get(product.barcode_format, "code128")
        barcode_class = get_barcode_class(barcode_format)

        # Create barcode instance with improved options for scanning
        options = {
            "module_width": 0.2,  # Default: 0.2
            "module_height": 15.0,  # Default: 15.0 - Increase height for better scanning
            "quiet_zone": 6.5,  # Default: 6.5 - Quiet zone for scanners
            "font_size": 10,  # Default: 10
            "text_distance": 5.0,  # Default: 5.0
            "background": "white",  # Default: 'white'
            "foreground": "black",  # Default: 'black'
            "write_text": True,  # Default: True - Include text under barcode
            "text": product.barcode,  # Text to display under barcode
        }

        # Create barcode instance
        barcode_instance = barcode_class(product.barcode, writer=ImageWriter())

        # Save to BytesIO object
        buffer = BytesIO()
        barcode_instance.write(buffer, options)

        # Return the image data
        buffer.seek(0)
        return buffer
    except ImportError as e:
        print(f"Barcode module import error: {e}")
        return None
    except Exception as e:
        print(f"Error generating barcode: {e}")
        return None


def get_product_qr_code_url(product):
    """
    Get the URL for a product's QR code
    """
    # In a real implementation, you would generate and save the QR code
    # For now, we'll return a placeholder
    return f"/media/qr/product_{product.pk}.png"


def get_product_barcode_url(product):
    """
    Get the URL for a product's barcode
    """
    if not product.barcode:
        return None
    return f"/media/barcode/product_{product.pk}.png"
