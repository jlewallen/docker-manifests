import os

from urlparse import urlparse
from flask import Flask, request, Response
from flask import render_template, url_for, redirect, send_from_directory
from flask import send_file, make_response, abort
from flask import jsonify, json
from cloudvm.models import *
from cloudvm.dashboard import app
from cloudvm.dashboard.models import *

@app.route("/")
def index():
  return make_response(open('cloudvm/dashboard/templates/index.html').read())

@app.route("/status")
def status():
	docker = Configuration.get_docker()
	state = State.load("dock.state")
	ctx = Context(docker, None, state)
	manifest = Manifest("manifest-test.json")
	groups = []
	return jsonify(status = {
		'groups' : []
	})

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico')

