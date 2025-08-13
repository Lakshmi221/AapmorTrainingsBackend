import mimetypes
from flask_mail import Message
from flask import render_template_string
import os

from email_services.mail_config import mail

ASSIGN_TEMPLATE = """
<html>
  <body style="font-family: Arial, sans-serif; background: #f4f7fa; padding: 20px;">
    <div style="background: white; max-width: 600px; margin: auto; padding: 20px; border-radius: 8px;">
      <img src="cid:banner" alt="Training Banner" style="width:100%; border-radius: 8px 8px 0 0;">
      <h2 style="text-align: center;">{{ heading }}</h2>
      <p>Hi {{ name }},</p>
      <p>You have been assigned a new training titled "<strong>{{ title }}</strong>".</p>
      {% if due_date %}
      <p>Please make sure to complete this training before <strong>{{ due_date }}</strong>.</p>
      {% endif %}
      <p>You can access your training portal to start learning anytime.</p>
      <br>
      <p>Thanks,<br><strong>Training Management Team</strong><br>AAPMOR Technologies</p>
      <img src="cid:logo" alt="Logo" style="width: 100px;" />
      <hr style="margin: 20px 0;">
      <p style="font-size: 12px; color: #888;">
        Please do not reply to this email. Emails sent to this address will not be answered.
      </p>
    </div>
  </body>
</html>
"""


HTML_TEMPLATE = """
<html>
  <body style="font-family: Arial, sans-serif; background: #f4f7fa; padding: 20px;">
    <div style="background: white; max-width: 600px; margin: auto; padding: 20px; border-radius: 8px;">
      <img src="cid:banner" alt="Training Banner" style="width:100%; border-radius: 8px 8px 0 0;" />
      <h2 style="text-align: center;">{{ heading }}</h2>
      <p>Hi {{ name }},</p>
      <p>This is a reminder that your training "<strong>{{ title }}</strong>" is due on <strong>{{ due_date }}</strong>. Please complete it before the deadline to stay compliant with your training requirements.</p>
      <p>If you have any questions or need help accessing the training, feel free to reach out.</p>
      <br>
      <p>Thanks,</p>
      <p><strong>Training Management Team</strong><br>AAPMOR Technologies</p>
      <img src="cid:logo" alt="AAPMOR Logo" style="width: 100px;" />
      <hr style="margin: 20px 0;">
      <p style="font-size: 12px; color: #888;">
        Please do not reply to this email. Emails sent to this address will not be answered.
      </p>
    </div>
  </body>
</html>
"""

def send_training_email(to, name, title, due_date, subject="Training Notification", heading="Training Due Soon", type="reminder"):
    if type == "assign":
        html_template = ASSIGN_TEMPLATE
    else:
        html_template = HTML_TEMPLATE

    html = render_template_string(html_template, name=name, title=title, due_date=due_date, heading=heading)
    msg = Message(subject=subject, recipients=[to])
    msg.html = html

    base_path = os.path.dirname(os.path.abspath(__file__))
    banner_path = os.path.join(base_path, '../images/banner.jpg')
    logo_path = os.path.join(base_path, '../images/logo.png')

    print("Banner exists:", os.path.exists(banner_path))
    print("Logo exists:", os.path.exists(logo_path))

    try:
        for path, cid in [(banner_path, "banner"), (logo_path, "logo")]:
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                raise ValueError(f"Could not guess MIME type for {path}")
            maintype, subtype = mime_type.split("/")

            with open(path, 'rb') as f:
                data = f.read()
                print(f"[DEBUG] {cid} image size:", len(data))
                if not data:
                    raise ValueError(f"{cid} image is empty")

                msg.attach(
                    filename=os.path.basename(path),
                    content_type=mime_type,
                    data=data,
                    disposition='inline',
                    headers={'Content-ID': f'<{cid}>'}
                )

        mail.send(msg)
        print("Mail sent successfully!")

    except Exception as e:
        print("Failed to send HTML mail:", e)
