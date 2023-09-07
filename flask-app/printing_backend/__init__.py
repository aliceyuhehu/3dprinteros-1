import os
from flask import Flask
from flask_cors import CORS


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ["FLASK_KEY"],
    )

    cors = CORS(app, origins=["http://localhost:3000", "https://printing-gui-colab-sandbox.cloud.duke.edu", "https://printing-backend-colab-sandbox.cloud.duke.edu"])

    
    #https://stackoverflow.com/questions/44532557/flask-import-app-from-parent-directory
    with app.app_context():
      from controllers import printing, oauth
    
      app.register_blueprint(oauth.bp)
      app.register_blueprint(printing.bp)

    return app