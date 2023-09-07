from flask import Flask
from flask import request, abort, Blueprint

import os, pdb, json, logging
from oauth import get_token

app = Flask(__name__)
bp = Blueprint('oauth', __name__, url_prefix='/oauth')


@bp.route('', methods=["GET"])
def oauth():
  return get_token(request.args.get('code'))