import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email using SMTP"""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured. Email not sent.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = to_email
            
            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Connect and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_order_confirmation(
        to_email: str,
        order_number: str,
        customer_name: str,
        items: List[dict],
        total: float,
        shipping_address: dict
    ) -> bool:
        """Send order confirmation email"""
        
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item['name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item['quantity']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₹{item['price']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₹{item['total']:.2f}</td>
            </tr>
            """
        
        address_str = f"{shipping_address.get('address_line1', '')}"
        if shipping_address.get('address_line2'):
            address_str += f", {shipping_address['address_line2']}"
        address_str += f"<br>{shipping_address.get('city', '')}, {shipping_address.get('state', '')} {shipping_address.get('pincode', '')}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0d9488, #84cc16); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .order-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .order-table th {{ background: #0d9488; color: white; padding: 12px; text-align: left; }}
                .total-row {{ font-weight: bold; font-size: 1.1em; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛒 PolluxKart</h1>
                    <h2>Order Confirmed!</h2>
                </div>
                <div class="content">
                    <p>Hi {customer_name},</p>
                    <p>Thank you for your order! We're excited to let you know that your order has been confirmed.</p>
                    
                    <h3>Order Details</h3>
                    <p><strong>Order Number:</strong> {order_number}</p>
                    
                    <table class="order-table">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th style="text-align: center;">Qty</th>
                                <th style="text-align: right;">Price</th>
                                <th style="text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                            <tr class="total-row">
                                <td colspan="3" style="padding: 15px; text-align: right;">Grand Total:</td>
                                <td style="padding: 15px; text-align: right;">₹{total:.2f}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <h3>Shipping Address</h3>
                    <p>
                        <strong>{shipping_address.get('full_name', customer_name)}</strong><br>
                        {address_str}<br>
                        Phone: {shipping_address.get('phone', 'N/A')}
                    </p>
                    
                    <p>We'll send you another email when your order ships.</p>
                    
                    <p>Thanks for shopping with us!</p>
                    <p>- The PolluxKart Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 PolluxKart. All rights reserved.</p>
                    <p>If you have any questions, contact us at support@polluxkart.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Order Confirmed!
        
        Hi {customer_name},
        
        Thank you for your order! Your order #{order_number} has been confirmed.
        
        Total: ₹{total:.2f}
        
        We'll send you another email when your order ships.
        
        Thanks for shopping with us!
        - The PolluxKart Team
        """
        
        return await EmailService.send_email(
            to_email=to_email,
            subject=f"Order Confirmed - #{order_number} | PolluxKart",
            html_content=html_content,
            text_content=text_content
        )
    
    @staticmethod
    async def send_order_shipped(
        to_email: str,
        order_number: str,
        customer_name: str,
        tracking_number: Optional[str] = None
    ) -> bool:
        """Send order shipped notification email"""
        
        tracking_info = ""
        if tracking_number:
            tracking_info = f"<p><strong>Tracking Number:</strong> {tracking_number}</p>"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0d9488, #84cc16); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚚 Your Order is On Its Way!</h1>
                </div>
                <div class="content">
                    <p>Hi {customer_name},</p>
                    <p>Great news! Your order <strong>#{order_number}</strong> has been shipped and is on its way to you.</p>
                    {tracking_info}
                    <p>You can track your package using the tracking number above.</p>
                    <p>Thanks for shopping with PolluxKart!</p>
                </div>
                <div class="footer">
                    <p>© 2025 PolluxKart. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await EmailService.send_email(
            to_email=to_email,
            subject=f"Your Order #{order_number} Has Shipped! | PolluxKart",
            html_content=html_content
        )
