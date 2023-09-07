#!/bin/bash
gunicorn --bind 0.0.0.0:8080 "printing_backend:create_app()"