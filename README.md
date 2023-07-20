# Alpha Innotec Home Assistant integration
A custom integration which will add your thermostats to Home Assistant.

## Pre-install
1. Create a user for Home Assistant in the control box. Do not use a user that's in use by any other application. For example, the mobile app or web app.
2. Make sure Home Assistant is able to reach the control box via the local network.
2. Make sure Home Assistant is able to reach the gateway via the local network.
3. You need to have the password for the gateway.

## Install
1. Download the latest version release from Github.
2. Upload the files into the directory `/config/custom_components`.
3. Rename the directory to `alpha`. The files should exist in the directory `/config/custom_components/alpha`.
4. Restart Home Assistant
5. Now you should be able to add the integration via UI.
6. Required information:
   1. Gateway IP
   2. Gateway password
   3. Control box IP
   4. Control box username
   5. Control box password

## Disclaimer
- I cannot say that i'm a python developer. So, if you see code that's bad practice. Please, feel free to contribute to this integration via a pull request. 
- I do not own an Alpha Innotect heat pump. If you have an issue, please provide sample data and information about your installation because I can't easily test changes.