# Cowin Slot Notifier

##### Repository Structure:
```
+ cowin_slot_notifier.py: main script to run
+ district_mapping.csv: contains the district names and it's respective district and state id
+ sensitive.py: file where you can enter your email password and directly import and use it in main file
```

First install the dependencies using the command,

    pip install -r requirements.txt

To check what arguments are needed by the script run the command,

    python cowin_slot_notifier.py -h

Script takes one required argument which is district id. You can find the id of your respective district from the district_mapping.csv file. District id of Ahmedabad Corporation is 770, so if you want to receive notifications for the slots availability in Ahmedabad Corporation area, run the script as,

    python cowin_slot_notifier.py -d 770


Note: When you use an gmail account for development, you need to turn the Less Secure App access option "ON" from your gmail account settings. An article on how to do so can be found [here](https://hotter.io/docs/email-accounts/secure-app-gmail/).

