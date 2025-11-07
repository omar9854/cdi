"""
Script to send password change request emails to all users
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

async def send_password_change_email(email: str, name: str):
    """Send password change request email"""
    try:
        smtp_host = 'smtp.gmail.com'
        smtp_port = 587
        smtp_user = 'medidocai@gmail.com'
        smtp_password = 'ntjtxivcqyzkeajq'
        email_from = 'medidocai@gmail.com'
        reset_link = 'https://medtechdoc-ai.preview.emergentagent.com/forgot-password'
        
        message = MIMEMultipart("alternative")
        message["From"] = email_from
        message["To"] = email
        message["Subject"] = "🔒 مطلوب: تحديث كلمة المرور - Password Update Required"
        
        html_content = f"""
        <html dir="rtl">
            <body style="font-family: Arial, sans-serif; direction: rtl;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #dc2626; text-align: center;">🔒 تحديث أمني مهم</h2>
                        <p style="font-size: 16px; color: #333;">مرحباً {name}،</p>
                        
                        <div style="background-color: #fef2f2; border-right: 4px solid #dc2626; padding: 20px; margin: 20px 0; border-radius: 4px;">
                            <h3 style="color: #991b1b; margin-top: 0;">⚠️ إجراء مطلوب</h3>
                            <p style="color: #7f1d1d; font-size: 15px; line-height: 1.8;">
                                في إطار تحسين الأمن السيبراني لنظام مركز الترميز الطبي، نطلب منك تحديث كلمة المرور الخاصة بك لتكون أكثر أماناً.
                            </p>
                        </div>
                        
                        <div style="background-color: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #1e40af; margin-top: 0;">📋 متطلبات كلمة المرور الجديدة:</h3>
                            <ul style="color: #1e3a8a; font-size: 15px; line-height: 2;">
                                <li>✓ 12 حرف على الأقل</li>
                                <li>✓ أحرف كبيرة وصغيرة (A-Z, a-z)</li>
                                <li>✓ أرقام (0-9)</li>
                                <li>✓ رموز خاصة (!@#$%^&*)</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" 
                               style="display: inline-block; padding: 15px 40px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold;">
                                تغيير كلمة المرور الآن
                            </a>
                        </div>
                        
                        <div style="background-color: #dcfce7; border: 2px solid #16a34a; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #166534; margin-top: 0;">✅ ميزات الأمان الجديدة:</h3>
                            <ul style="color: #14532d; font-size: 14px; line-height: 1.8;">
                                <li>المصادقة متعددة العوامل (MFA)</li>
                                <li>سجلات المراجعة الشاملة</li>
                                <li>حماية من الهجمات الإلكترونية</li>
                                <li>الامتثال للمعايير السعودية والأمريكية</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; color: #666; margin-top: 20px;">
                            إذا واجهت أي مشاكل، يرجى الاتصال بالدعم الفني.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        
                        <div style="text-align: center;">
                            <p style="font-size: 12px; color: #9ca3af;">
                                مركز الترميز الطبي وتحسين التوثيق السريري<br>
                                Medical Coding & Clinical Documentation Improvement Center
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, "html", "utf-8"))
        
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True
        )
        
        return True
    except Exception as e:
        print(f"❌ Error sending to {email}: {str(e)}")
        return False

async def main():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'clinical_doc_center')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Get all users
    users = await db.users.find({}, {"_id": 0, "email": 1, "full_name": 1}).to_list(100)
    
    print(f"📧 إرسال رسائل تغيير كلمة المرور إلى {len(users)} مستخدم...\n")
    
    success_count = 0
    for i, user in enumerate(users, 1):
        email = user.get('email')
        name = user.get('full_name', 'المستخدم')
        
        print(f"{i}. إرسال إلى {name} ({email})...", end=" ")
        
        success = await send_password_change_email(email, name)
        if success:
            print("✅")
            success_count += 1
        else:
            print("❌")
        
        # Small delay between emails
        await asyncio.sleep(1)
    
    print(f"\n✅ تم إرسال {success_count}/{len(users)} رسالة بنجاح")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
