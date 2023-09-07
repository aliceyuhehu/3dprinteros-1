#!/usr/local/bin/python

import schedule
import time
import requests
import os
import logging
import base64

logging.basicConfig(filename="scheduler.log",
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)


PRINT_BACKEND_HOST = os.environ["PRINT_BACKEND_HOST"]
string = "{}:{}".format(os.environ["PRINT_SCHEDULER_USER"], os.environ["PRINT_SCHEDULER_PASSWORD"])
data = base64.b64encode(string.encode())
PRINT_BACKEND_AUTH = data.decode("utf-8")

def job():
  #TODO validate response and log success or failures
  #TODO REMEMBER: Container must be rebuilt for this to take effect
  logging.info("writing lilly")

  url = "{}/printing/write_data".format(PRINT_BACKEND_HOST)
  payload = "{\"printer_group\": \"lilly\"}"
  headers = {'content-type': 'application/json', 'authorization': "Basic {}".format(PRINT_BACKEND_AUTH)}
  response = requests.request("POST", url, data=payload, headers=headers)
  print(response.text)

  logging.info("writing ruby")
  url = "{}/printing/write_data".format(PRINT_BACKEND_HOST)
  payload = "{\"printer_group\": \"ruby\"}"
  headers = {'content-type': 'application/json', 'authorization': "Basic {}".format(PRINT_BACKEND_AUTH)}
  response = requests.request("POST", url, data=payload, headers=headers)
  print(response.text)

  logging.info("writing tec")
  url = "{}/printing/write_data".format(PRINT_BACKEND_HOST)
  payload = "{\"printer_group\": \"tec\"}"
  headers = {'content-type': 'application/json', 'authorization': "Basic {}".format(PRINT_BACKEND_AUTH)}
  response = requests.request("POST", url, data=payload, headers=headers)
  print(response.text)

schedule.every(2).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
