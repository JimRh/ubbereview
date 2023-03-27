import logging
import smtplib
from logging.handlers import TimedRotatingFileHandler, SMTPHandler  # pylint: disable=ungrouped-imports
from sys import stdout

from brain import settings

debug_file = 'logs/debug/debug.log'
info_file = 'logs/info/info.log'
error_file = 'logs/error/error.log'
warning_file = 'logs/warning/warning.log'
critical_file = 'logs/critical/critical.log'

handler_formatter = logging.Formatter('%(levelname)s %(asctime)s %(filename)s %(funcName)s %(lineno)d: %(message)s')

email_formatter = logging.Formatter(
    'Subject: ubbe API System Failure\n\n%(levelname)s\nTime: %(asctime)s\n'
    'File: %(filename)s\nFunction: %(funcName)s\nLine Number: %(lineno)d'
    '\n\nInformation: %(message)s'
)


class SSLSMTPHandler(SMTPHandler):

    def emit(self, record) -> None:
        """
            Emit a record.
        """
        port = self.mailport

        if not port:
            port = smtplib.SMTP_PORT

        try:
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)

            try:
                smtp.starttls()
            except smtplib.SMTPNotSupportedError:
                raise
            if self.username:
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (smtplib.SMTPException, ValueError):
            self.handleError(record)


def logger_setup(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create debug logging handler
    DHandler = TimedRotatingFileHandler(debug_file, when='w4')
    DHandler.setFormatter(handler_formatter)
    DHandler.setLevel(logging.DEBUG)
    logger.addHandler(DHandler)

    # Create debug stream handler
    SHandler = logging.StreamHandler(stdout)
    SHandler.setFormatter(handler_formatter)
    SHandler.setLevel(logging.DEBUG)
    logger.addHandler(SHandler)

    # Create info logger
    IHandler = TimedRotatingFileHandler(info_file, when='w4')
    IHandler.setFormatter(handler_formatter)
    IHandler.setLevel(logging.INFO)
    logger.addHandler(IHandler)

    # Create warning logger
    WHandler = TimedRotatingFileHandler(warning_file, when='w4')
    WHandler.setFormatter(handler_formatter)
    WHandler.setLevel(logging.WARNING)
    logger.addHandler(WHandler)

    # Create error logger
    EHandler = TimedRotatingFileHandler(error_file, when='w4')
    EHandler.setFormatter(handler_formatter)
    EHandler.setLevel(logging.ERROR)
    logger.addHandler(EHandler)

    # Create critical logger
    CHandler = TimedRotatingFileHandler(critical_file, when='w4')
    CHandler.setFormatter(handler_formatter)
    CHandler.setLevel(logging.CRITICAL)
    logger.addHandler(CHandler)

    mail_handler = SSLSMTPHandler(mailhost=(settings.EMAIL_HOST, settings.EMAIL_PORT),
                                  fromaddr=settings.LOGGER_FROM_EMAIL,
                                  toaddrs=settings.LOGGER_TO_EMAIL,
                                  subject='',
                                  credentials=(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD),
                                  secure=())
    mail_handler.setFormatter(email_formatter)
    mail_handler.setLevel(logging.ERROR)
    logger.addHandler(mail_handler)

    return logger
