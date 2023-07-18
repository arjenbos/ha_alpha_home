# Alpha Innotec Home Assistant integration

## Pre-install
1. Create a user for Home Assistant in the control box. Do not use a user that's in use by any other application. For example, the mobile app or web app.
2. Make sure Home Assistant is able to reach the control box via the local network.

## Install
1. Download the zip file from Github.
2. Upload the files into the directory `/config/custom_components`.
3. Rename the directory to `alpha`. The files should exist in the directory `/config/custom_components/alpha`.
4. Restart Home Assistant
5. Now you should be able to add the integration via UI.

## Disclaimer
I cannot say that i'm a python developer. So, if you see code that's bad practice. Please, feel free to contribute to this integration via a pull request.
