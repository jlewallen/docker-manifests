import os
from flask import Flask, request, Response
from flask import render_template, url_for, redirect, send_from_directory
from flask import send_file, make_response, abort
from flask import jsonify, json
from cloudvm.dashboard import app
from cloudvm.dashboard.models import *

@app.route("/")
def index():
  return make_response(open('dashboard/templates/index.html').read())

@app.route("/status")
def status():
  return jsonify(running = True)

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico')

