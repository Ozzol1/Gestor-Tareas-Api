"""
Servicio de envío de emails con Resend.
"""
import os
import resend


def _configurar_resend():
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("⚠️  RESEND_API_KEY no está configurada. Los emails no se enviarán.")
        return False
    resend.api_key = api_key
    return True


def enviar_email_recuperacion(email_destino, token):
    """
    Envía un email con el enlace para recuperar la contraseña.
    Devuelve True si se envió, False si falló.
    """
    if not _configurar_resend():
        return False

    app_url = os.getenv("APP_URL", "http://127.0.0.1:5000")
    enlace = f"{app_url}/reset-password/{token}"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f5f7fa; color:#2c3e50;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fa; padding:40px 20px;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:500px; background:#ffffff; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.08); overflow:hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:30px; text-align:center;">
                                <h1 style="margin:0; color:#ffffff; font-size:22px;">🚀 Gestor de Tareas</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding:40px 30px;">
                                <h2 style="color:#2c3e50; font-size:20px; margin:0 0 15px 0;">Recuperar contraseña</h2>
                                <p style="color:#7f8c8d; font-size:15px; line-height:1.6; margin:0 0 25px 0;">
                                    Recibimos una solicitud para restablecer tu contraseña. Si fuiste tú, haz clic en el siguiente botón:
                                </p>
                                <table cellpadding="0" cellspacing="0" style="margin:0 auto 25px auto;">
                                    <tr>
                                        <td style="background:#3498db; border-radius:8px;">
                                            <a href="{enlace}" style="display:inline-block; padding:14px 28px; color:#ffffff; text-decoration:none; font-weight:bold; font-size:15px;">
                                                Restablecer contraseña
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color:#95a5a6; font-size:13px; line-height:1.5; margin:0 0 15px 0;">
                                    O copia este enlace en tu navegador:
                                </p>
                                <p style="color:#3498db; font-size:12px; word-break:break-all; background:#ecf0f1; padding:10px; border-radius:6px; margin:0 0 20px 0;">
                                    {enlace}
                                </p>
                                <p style="color:#e74c3c; font-size:13px; line-height:1.5; margin:0;">
                                    ⏱️ Este enlace expira en <strong>1 hora</strong>.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8f9fa; padding:20px; text-align:center; border-top:1px solid #ecf0f1;">
                                <p style="color:#95a5a6; font-size:12px; margin:0;">
                                    Si no solicitaste este cambio, ignora este email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": email_destino,
            "subject": "Recuperar contraseña - Gestor de Tareas",
            "html": html,
        })
        return True
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
        return False