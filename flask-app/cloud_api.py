import requests, os, urllib, json, pdb, re, string, datetime, concurrent.futures
from printing_helpers import attach_filament_data, duke_ldap_search
from database import db

ENVIRONMENT = os.environ["FLASK_ENV"]
HEADERS = {'content-type': "application/x-www-form-urlencoded"}
API_GLOBAL_URL = "{}/apiglobal/".format(os.environ["PRINT_API_HOST"])

#TODO note that anything reserved i'm not getting back any sort of history or job info just "No access"
class CloudPrinterOs():
    def __init__(self, session_id=None, use_api=False):
        self.session_id = session_id
        self.use_api = use_api

    """
    NOTE: the organizational printer list used in "printer_list" seems to have 
    a more complete data, however it does not have filament data which is a 
    feature requested by Chip and company.
    """
    def accessible_printers(self):
        if(ENVIRONMENT == "production" or self.use_api):
            url =  API_GLOBAL_URL + "get_printers_list"
            payload = urllib.parse.urlencode({"session": self.session_id})
            response = requests.request("POST", url, data=payload, headers=HEADERS)
            printers =  response.json()
        else:
            f = open("{}/cloud_printer_os/mock/accessible_printers.json".format(settings.BASE_DIR))
            printers =  json.loads(f.read()) 
        return printers


    #grab the most recent job from the printer
    #TODO thhis method has gotten wayyyyy to complex, I need to simplify
    def attach_active_jobs(self, printers):
        printer_ids = [x["id"] for x in printers]
        netid_lookups = []
        errors = 0


        #multi thread to make parallel calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            #thread calls to get job history on printers
            for result in executor.map(self.printer_jobs_list, printer_ids):
              printer, netid_lookup = self.__set_history_on_printers(printers, result)
              netid_lookups.append(netid_lookup)
            
            #thread calls to query ldap for user information
            for result in executor.map(self.__get_user_identifiers, netid_lookups):
              if result:
                printer_id, ldap_data = result
                printer = next(
                    (printer for printer in printers if printer["most_recent_job"] and printer_id == printer["most_recent_job"]["id"]), None
                )
                printer["most_recent_job"]["user"] = ldap_data
        return printers

    
    #add any reservation info to the printer list
    def check_reservations(self, printers):
        work_groups = self.work_groups()
        for printer in printers:
            #24 is the ID for the EVERYONE workgroup. A printer is reserved if it is owned by a group other thatn this one
            if not printer["workgroups"]:
              print("NO GROUP")
              print(printer)
              printer["reservations"] = ["No Workgroup"]
            elif 24 not in printer["workgroups"]:
                printer["reservations"] = self.get_printer_reservations(work_groups=work_groups["message"], printer=printer)
        return printers


    #filter down a list of org printers by finding a match in printer name
    # example: get all printers with TEC in the name
    def filter_printers(self,session_id=None, printers=None, filter=None):
        remove_these = []
        timestamp = self.__epoch_timestamp(datetime.datetime.now()) #TODO rethink placement in future, makes sense now, but it's wierd.

        printers =  [printer for printer in printers['message'] if printer["name"] and filter.lower() in printer['name'].lower() ]
        #identify letter and number of printer from title so we can order
        for printer in printers:
          try:
            printer['number'] = int(re.search('\d*$', printer["name"]).group(0))
            printer['letter'] = re.search('[a-zA-Z]{1}(?=-)', printer["name"]).group(0)
            printer['location'] = re.search('^\w*', printer["name"]).group(0).lower()
            printer["last_updated"] = timestamp
          except:
              print("Error in naming convetion: " + printer["name"])
        #remove any printers that broke naming conventions chip establihsed
        return [printer for printer in printers if "letter" in printer  and "number" in printer ]


    #get the name of the group(s) that have a printer reserved
    def get_printer_reservations(self, work_groups=None, printer=None):
        reservations = []
        for res_id in printer["workgroups"]:
            reservations.append([x["name"] for x in work_groups if res_id == int(x["id"])])
        return reservations

    

    #authenticates the user into the api, returns the all important "session" token
    def get_user_session(self, username=None, password=None):
        url = API_GLOBAL_URL + "login"
        payload = urllib.parse.urlencode({'username': username, 'password': password})
        response = requests.request("POST", url, data=payload, headers=HEADERS)
        return response.json()


    # returns whether or not the user has a valid session
    def has_valid_session(self):
        url = API_GLOBAL_URL + "check_session"
        payload = urllib.parse.urlencode({"session": self.session_id})
        response = requests.request("POST", url, data=payload, headers=HEADERS)
        return response.json()['result']

    #get a list of all printers, only hit api in a live server env
    def printer_list(self, include_last_job=True, include_filament_data=True, printer_group=None):
        if(ENVIRONMENT == "production" or self.use_api):
            url =  API_GLOBAL_URL + "get_organization_printers_list"
            payload = urllib.parse.urlencode({"session": self.session_id})
            response = requests.request("POST", url, data=payload, headers=HEADERS)
            printers =  response.json()
        else:
            f = open("{}/cloud_printer_os/mock/printer_list.json".format(settings.BASE_DIR))
            printers =  json.loads(f.read())
        printers = self.filter_printers(printers=printers, filter=printer_group)

        if include_last_job:
            printers = self.attach_active_jobs(printers)
        
        if include_filament_data:
            accessible_printer_list = self.accessible_printers()
            printers = attach_filament_data(printers, accessible_printer_list)

        printers = self.check_reservations(printers)
        return printers

        

    #get the information about a specific printer job
    def printer_job(self, job_id):
        url = API_GLOBAL_URL + "get_job_info"
        payload = urllib.parse.urlencode({"session": self.session_id, "job_id": job_id})
        response = requests.request("POST", url, data=payload, headers=HEADERS)
        return response.json()

    #get a list of all the current printer jobs
    #to support multi threading this will return the printer id and the response
    def printer_jobs_list(self, printer_id):
        url = API_GLOBAL_URL + "get_printer_jobs"
        payload = urllib.parse.urlencode({"session": self.session_id, "printer_id": printer_id})
        response = requests.request("POST", url, data=payload, headers=HEADERS)
        return {"printer_id": printer_id, "response": response.json()}


    def work_groups(self):
        url = API_GLOBAL_URL + "get_workgroups_simple_list"
        payload = urllib.parse.urlencode({"session": self.session_id})
        response = requests.request("POST", url, data=payload, headers=HEADERS)
        return response.json()
    
    ### PRIVATE METHODS ### 
    #provide an epoch timestamp in case we need sorting

    def __epoch_timestamp(self, dt_object):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return (dt_object - epoch).total_seconds() * 1000.0

    def __get_user_identifiers(self, netid_lookup):
      if netid_lookup:
        printer_id, netid = netid_lookup
        identifiers = duke_ldap_search(netid)
        #returns back the printer id and the ldap result
        if printer_id == '63990':
          pdb.set_trace()
        return (printer_id, identifiers)

    def __set_history_on_printers(self, printers, result):
      status_codes = {"11": "Queued", "21": "Printing", "43": "Failed", "45": "Aborted", "77": "Complete"}
      printer = next((printer for printer in printers if result["printer_id"] == printer["id"]), None)

      try:
        all_jobs = result["response"]['message']
        most_recent_job = result["response"]['message'][0]
      except:
        most_recent_job = None
      
      #if there is no recent job, set to none, 
      #otherwise set the most recent job and job history on the printer
      if most_recent_job.__class__ != dict:
          printer["most_recent_job"] = None
          netid_lookup = None
      else:
          netid = re.search("\w*(?=\@)", most_recent_job["email"]).group(0)
          netid_lookup = (most_recent_job["id"], netid)
          printer["most_recent_job"] = most_recent_job
          printer["print_status"] = status_codes[most_recent_job["status_id"]]
          for job in all_jobs:
              job["print_status"] = status_codes[job["status_id"]]
          printer["all_jobs"] = all_jobs
      return printer, netid_lookup

     ### END PRIVATE METHODS ### 