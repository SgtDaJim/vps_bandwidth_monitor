from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import smtplib
import configparser


class Email(object):
    def __init__(self, config, from_name, to_name, subject, text):
        self.email_config = configparser.ConfigParser()
        self.email_config.read(config)
        self.from_add = self.email_config.get("EmailInfo", "from")
        self.to_add = self.email_config.get("EmailInfo", "to")
        self.auth = self.email_config.get("EmailInfo", "authorization")
        self.smtp_server = self.email_config.get("EmailInfo", "smtp_server")
        self.smtp_port = self.email_config.get("EmailInfo", "smtp_port")
        self.from_name = from_name
        self.to_name = to_name
        self.subject = subject
        self.text = text

    def _format_add(self, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    def _make_email(self):
        msg = MIMEMultipart('alternative')
        # msg.attach( MIMEText(self.text, "html", "utf-8"))
        msg.attach(MIMEText(self.text, "plain", "utf-8"))
        msg['From'] = self._format_add("%s <%s>" % (self.from_name, self.from_add))
        msg['To'] = self._format_add("%s <%s>" % (self.to_name, self.to_add))
        msg['Subject'] = Header(self.subject, 'utf-8').encode()
        return msg

    def send(self):
        msg = self._make_email()
        print(msg)
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.set_debuglevel(1)
        server.login(self.from_add, self.auth)
        server.sendmail(self.from_add, [self.to_add], msg.as_string())
        server.quit()


if __name__ == "__main__":
    email = Email("text.")
    email.send()
    print("邮件已发送。")