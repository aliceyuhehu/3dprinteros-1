import requests
import os
import json
import urllib
import base64
import jwt #note that this is actualy pyjwt NOT the jwt library but they use the same import
import pdb


#TODO need a call to introspect to validate token
#TODO need a method to validate scheduler auth

def format_auth_string():
  string = "{}:{}".format(os.environ["OAUTH_CLIENT_ID"], os.environ["OAUTH_CLIENT_SECRET"])
  data = base64.b64encode(string.encode())
  return data.decode("utf-8")

def get_token(code):
  auth = format_auth_string()
  print("*" * 50)
  print(auth)
  print("*" * 50)
  url = "https://oauth.oit.duke.edu/oidc/token"
  payload = urllib.parse.urlencode({
    'grant_type': "authorization_code",
    'redirect_uri': os.environ["FRONTEND_OAUTH_REDIRECT_URI"],
    'code': code
  })
  headers = {
      'content-type': "application/x-www-form-urlencoded",
      'authorization': "Basic {}".format(auth)
      }

  response = requests.request("POST", url, data=payload, headers=headers)
  response = json.loads(response.text)
  print("*" * 50)
  print(response)
  print("*" * 50)

  id_token = jwt.decode(response["id_token"], verify=False)
  return {"access_token": response["access_token"], "id_token": id_token}
