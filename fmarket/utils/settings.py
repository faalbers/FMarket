import json
import pandas as pd
import smtplib
import ssl
from email.message import EmailMessage
from data.keys import KEYS

class Settings:
    def __init__(self):
        pass

    def get_ssel(self, ssel):
        with open('settings/ssel/%s.ssel' % ssel, 'r') as file:
            return self.get_ssel_file(file)
    
    def get_ssel_file(self, file):
        symbols = json.load(file)
        symbols = pd.DataFrame(symbols).T
        symbols.index.name = 'symbol'
        return symbols
    
    def set_ssel(self, ssel, data):
        with open('settings/ssel/%s.ssel' % ssel, 'w') as file:
            self.set_ssel_file(file, data)

    def set_ssel_file(self, file, data):
        data = data.T.to_dict()
        json.dump(data, file, indent=4)

    def get_filt(self, filt):
        with open('settings/filt/%s.filt' % filt, 'r') as file:
            return self.get_filt(file)
    
    def get_filt_file(self, file):
        filters = json.load(file)
        return filters
    
    def set_filt(self, filt, data):
        with open('settings/filt/%s.filt' % filt, 'w') as file:
            self.set_filt_file(file, data)

    def set_filt_file(self, file, data):
        json.dump(data, file, indent=4)

    def get_psel(self, psel):
        with open('settings/psel/%s.psel' % psel, 'r') as file:
            return self.get_psel_file(file)

    def get_psel_file(self, file):
        parmeters = json.load(file)
        return parmeters

    def set_psel(self, psel, data):
        with open('settings/psel/%s.psel' % psel, 'w') as file:
            self.set_psel_file(file, data)

    def set_psel_file(self, file, data):
        json.dump(data, file, indent=4)


    def email_ssel(self, ssel, email_adress, subject):
        main_params = ['name', 'sector', 'industry']
        data = self.get_ssel(ssel)
        email_body = ''
        for symbol, symbol_data in data.iterrows():
            email_body += '\n%s:\n' % symbol
            for param in main_params:
                email_body += '  %s: %s\n' % (param, symbol_data[param])
            other_columns = sorted(set(symbol_data.index).difference(set(main_params)))
            for param in other_columns:
                email_body += '  %s: %s\n' % (param, symbol_data[param])

        msg = EmailMessage()
        msg.set_content(email_body)
        msg['Subject'] = subject
        msg['From'] = "chalbers@gmail.com"
        msg['To'] = email_adress

        context = ssl.create_default_context()
        context.verify_flags &= ~ssl.VERIFY_X509_STRICT

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login("chalbers@gmail.com", KEYS['GMAIL']['KEY'])
            server.send_message(msg)

        print("Email sent successfully!")
