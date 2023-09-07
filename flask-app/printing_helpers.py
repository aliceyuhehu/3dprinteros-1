from database import db
from ldap3 import Server, Connection, ALL

import string, json, pdb

LDAP_SERVER = Server('ldap.duke.edu', port=636, use_ssl=True)
LDAP_CONNECTION = Connection(LDAP_SERVER)

#add filament data to printers. we do this by using the accessible_printers call
def attach_filament_data(printers, accessible_printer_list):
  data = accessible_printer_list["message"]
  for printer in printers:
      printer_data = next((item for item in data if item["printer_id"] == printer["id"]), None)
      if printer_data and printer_data["filaments"]:
          printer["filament_info"] = json.loads(printer_data["filaments"])
      else:
          printer["filament_info"] = None
  return printers

#run an anonymous ldap query
def duke_ldap_search(netid):
  attributes=["uid","cn", "title", "eduPersonPrimaryAffiliation","eduPersonPrincipalName", "duDirJobDesc","mail","telephonenumber","givenname","cn","sn","displayname","edupersonaffiliation","duDukeId"]
  search = "({}={})".format('uid', netid)
  ldap_connection = Connection(LDAP_SERVER)
  ldap_connection.bind()
  ldap_connection.search('dc=duke,dc=edu', search, attributes=attributes)
  result = ldap_connection.entries
  ldap_connection.unbind()
  if result:
      return json.loads(result[0].entry_to_json())


def get_printers(location, rack):
  printers = []

  for printer in db.printers.find({"location": location}):
    del printer["_id"]
    printers.append(printer)
  if rack:
    rack_printers = db.printer_racks.find_one({"name": rack})["printers"]
    printers =  [printer for printer in printers if printer["id"] in rack_printers]
    #order the printers as they appear on the wall,, A-2, A-2, B-1, B-2, etc.
  return sorted(printers, key=lambda k: (k['letter'].lower(), k['number']))



def printer_rows(printers):
  rows = []
  alphabet = list(string.ascii_lowercase)
  for letter in alphabet:
      row = [x for x in printers if x['letter'].lower() == letter] #get all printers with same letter(which means row) and put in a list together
      if row: 
          rows.append(row)
  return rows


def save_printers(printers):
  for printer in printers:
    previous_data = db.printers.find_one({"id": printer["id"]})
    if previous_data:
      #note that when I was just updating the printer dict, it was not removing the previous
      #reservation from the dict, instead I am deleting and re-creating to ensure that accuracy
      db.printers.delete_one({"id": printer["id"]})
      db.printers.insert_one(printer)

    else:
      db.printers.insert_one(printer)
