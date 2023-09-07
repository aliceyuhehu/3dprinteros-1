from flask import Flask
from flask import request, abort, Blueprint

import os, pdb, json, logging

from database import db
from cloud_api import CloudPrinterOs
from printing_helpers import get_printers, printer_rows, save_printers

bp = Blueprint('printing', __name__, url_prefix='/printing')

#return a group of printers based of location and an optional rack
@bp.route('/printer_group', methods=["POST"])
def get_printer_group():
  rack = False
  request_body = request.get_json(force=True)
  location = request_body['location'].lower()

  if "rack" in request_body:
    rack = request_body['rack'].lower()
  printers = get_printers(location, rack)
  printers = printer_rows(printers)
  return {"result": printers}


@bp.route('/write_data', methods=["POST"])
def write_data():
    validate_scheduler()
    validate_api_session()
    session_id = db.api_session.find_one()['session_id']
    print_api = CloudPrinterOs(session_id=session_id, use_api=True)
    printer_group = request.get_json(force=True)['printer_group'].lower()
    printers = print_api.printer_list(printer_group=printer_group)
    save_printers(printers)
    
    return {"success": True}



#TODO how is this working????!!!?? must be using same session id for everything
### helpers ###
def validate_api_session():
    admin_session = db.api_session.find_one()
    if admin_session:
      print_api = CloudPrinterOs(session_id=admin_session['session_id'])
      valid_session = print_api.has_valid_session()
    else:
      print_api = CloudPrinterOs(session_id=None)
      valid_session = False
   
    if valid_session:
      return True
    #collection of 1, used to have redis for this but didnt make sense to have redis AND mongo
    db.api_session.drop()
    session_response = print_api.get_user_session(os.environ["PRINT_API_USERNAME"], os.environ["PRINT_API_PASSWORD"])
    if(session_response['result']):
        db.api_session.insert_one({"session_id": session_response['message']['session']}) 
    else:
      logging.error('Unable to validate api session')
      raise ValueError('Unable to validate api session')

def validate_scheduler():
  auth = request.authorization
  if not auth:
    abort(401)
  if auth['username'] == os.environ["PRINT_SCHEDULER_USER"] and auth['password'] == os.environ["PRINT_SCHEDULER_PASSWORD"]:
    return True
  else:
    abort(401)
