'''
Author: Monil Shah
Date: 23/05/2021
'''

from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from copy import deepcopy
import os
import json
import argparse
import smtplib
import ssl
import requests
import pandas as pd
from fake_useragent import UserAgent
from pretty_html_table import build_table
from sensitive import development_email_pwd

class VaccineSlotAvailabilityNotifier:
    '''
    Class based implementation of VaccineSlot Notifier
    '''

    # intialize the constructor
    def __init__(self):
        self.temp_user_agent = UserAgent()
        self.header = {'User-Agent': self.temp_user_agent.random}
        self.production_server_url = "https://cdn-api.co-vin.in/api"
        self.find_by_district_api_url = "/v2/appointment/sessions/public/calendarByDistrict"
        self.development_email = "<development_email_here>" # example: userserver@gmail.com, For now the script is made for gmail only.
        self.port = 465 # For SSL


    def get_vaccination_session_by_district(self, udf_district_id, slot_date):
        """
        Function to check for slot availability using district_id.
        """
        if self.production_server_url and self.find_by_district_api_url:
            get_vaccination_session_by_district_url = self.production_server_url + \
                        self.find_by_district_api_url + "?district_id=" + \
                        udf_district_id + "&date=" + slot_date

            response = requests.get(get_vaccination_session_by_district_url, headers=self.header)

            if (response.ok) and ('centers' in json.loads(response.text)):
                response_json = json.loads(response.text)['centers']
                if response_json:
                    return response_json
            else:
                return response.content.decode(response.encoding)

        else:
            return "Please enter a valid API URLs."

    def send_email_notification(self, district_name_based_on_id, receiver_email, slots_data):
        """
        support function for sending slot availability emails.
        """
        if receiver_email:

            # Try block
            try:
                email_success_flag = False

                msg = MIMEMultipart()
                msg['Subject'] = 'New vaccine slots available around \
                                 {}'.format(district_name_based_on_id)
                msg['From'] = self.development_email
                msg['To'] = receiver_email

                body_content = slots_data
                msg.attach(MIMEText(body_content, "html"))
                msg_body = msg.as_string()

                # Create a secure SSL context
                context = ssl.create_default_context()

                # setup the server
                with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=context) as server:
                    server.login(self.development_email, development_email_pwd)
                    server.sendmail(msg['From'], msg['To'], msg_body)
                    email_success_flag = True

                return email_success_flag

            # Exception Handling
            except Exception as error:
                return str(error)

        else:
            return "Please enter a valid receiver email."


# Main Function
if __name__ == "__main__":

    try:

        # construct the argument parser
        ap = argparse.ArgumentParser()

        ap.add_argument("-d", "--DistrictId", required=True,
            help="District where you want to find slots. \
                    For district id's, kindly check district_mapping.csv")
        ap.add_argument("-a", "--Age", type=int,
            help="Minimum Age Limit for vaccine beneficiary.")
        ap.add_argument("-n", "--Numberofdays", type=int,
            default=1,
            help="Time Range to check for the slots availability from current date.")

        # parse the arguments
        args = vars(ap.parse_args())

        # Create a list for the pincodes (atleast one pincode shall be given)
        district_id = args["DistrictId"]

        # create an object of class VaccineSlotAvailabilityNotifier
        API_obj = VaccineSlotAvailabilityNotifier()

        # load mapping from csv
        csv_abs_path = os.getcwd() + "/district_mapping.csv"
        mapping_df = pd.read_csv(csv_abs_path)

        district_name = mapping_df.loc[mapping_df['district id'] == int(district_id), 'district name'].iloc[0]

        rename_mapping = {
            'date': 'Date',
            'min_age_limit': 'Minimum Age Limit',
            'available_capacity_dose1': 'Available Capacity Dose 1',
            'available_capacity_dose2': 'Available Capacity Dose 2',
            'vaccine': 'Vaccine',
            'pincode': 'Pincode',
            'name': 'Center Name',
            'state_name' : 'State',
            'district_name' : 'District',
            'block_name': 'Block Name',
            'fee_type' : 'Fees'
            }


        # create a list of date range from today upto the number of days passed in the argument
        current_date = datetime.today()
        list_format = [current_date + timedelta(days=i) for i in range(args["Numberofdays"])]
        actual_dates = [i.strftime("%d-%m-%Y") for i in list_format]

        available_slot_list = list()

        for date in actual_dates:
            json_response = API_obj.get_vaccination_session_by_district(district_id, date)

            if json_response:
                for data in json_response:
                    if data['sessions'][0]['available_capacity_dose1'] > 0 or data['sessions'][0]['available_capacity_dose2'] > 0:
                        available_slot_list.append(data)
            else:
                pass

        if len(available_slot_list) > 0:
            df = pd.DataFrame(available_slot_list)
            if len(df):
                df = df.explode("sessions")
                df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                df['available_capacity_dose1'] = df.sessions.apply(lambda x: x['available_capacity_dose1'])
                df['available_capacity_dose2'] = df.sessions.apply(lambda x: x['available_capacity_dose2'])
                df['date'] = df.sessions.apply(lambda x: x['date'])
                df = df[["date", "available_capacity_dose1", "available_capacity_dose2", "vaccine", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type"]]
                final_df = deepcopy(df)

                if len(final_df) > 0:
                    final_df.drop_duplicates(inplace=True)
                    final_df.rename(columns=rename_mapping, inplace=True)

                    if args["Age"] is not None:
                        filtered_df = final_df.loc[final_df['Minimum Age Limit'] <= args["Age"]]
                        filtered_df.reset_index(inplace=True)
                        filtered_df.drop_duplicates(inplace=True)

                        if len(filtered_df) > 0:
                            output = build_table(filtered_df[["Date", "Available Capacity Dose 1", "Available Capacity Dose 2", "Vaccine", "Minimum Age Limit", "Center Name", "Pincode", "Fees"]], 'blue_light')
                            email_status = API_obj.send_email_notification(district_name, 'moniltshah98@gmail.com', output)

                            if email_status:
                                print("Email Sent Successfully.")
                            else:
                                print("Some error occured while sending email.")

                        else:
                            print("Slots Found! But not for the mentioned age of the vaccine beneficiary.")
                        
                    else:
                        output = build_table(final_df[["Date", "Available Capacity Dose 1", "Available Capacity Dose 2", "Vaccine", "Minimum Age Limit", "Center Name", "Pincode", "Fees"]], 'blue_light')
                        email_status = API_obj.send_email_notification(district_name, "<receiver_email_here>", output)

                        if email_status:
                            print("Email Sent Successfully.")
                        else:
                            print("Some error occured while sending email.")
        else:
            print("No slots availabile")

    except Exception as error:
        print(str(error))
