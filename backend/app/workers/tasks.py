"""
Celery background tasks.

Run worker: celery -A app.workers.celery_app worker --loglevel=info
"""
from app.workers.celery_app import celery_app


@celery_app.task(name="tasks.send_welcome_email")
def send_welcome_email(user_id: str, email: str, full_name: str) -> None:
    """Send welcome email after registration. TODO: integrate Resend."""
    print(f"[TODO] Sending welcome email to {email}")


@celery_app.task(name="tasks.compress_image")
def compress_image(file_path: str, max_width: int = 1200) -> str:
    """Compress and resize an uploaded image using Pillow."""
    from PIL import Image

    img = Image.open(file_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Convert to WebP for smaller size
    webp_path = file_path.rsplit(".", 1)[0] + ".webp"
    img.save(webp_path, "WEBP", quality=85, optimize=True)
    return webp_path


@celery_app.task(name="tasks.generate_qr_async")
def generate_qr_async(business_id: str, slug: str) -> None:
    """Async QR generation triggered after business publish. TODO: wire up."""
    print(f"[TODO] Generating QR for business {business_id} with slug {slug}")


@celery_app.task(name="tasks.send_renewal_reminder")
def send_renewal_reminder(business_id: str, email: str, days_until_expiry: int) -> None:
    """Send subscription renewal reminder. TODO: integrate Resend."""
    print(f"[TODO] Sending renewal reminder to {email}, {days_until_expiry} days left")
