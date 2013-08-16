#
#
#

import os

from urlparse import urlparse
from flask import Flask, request, Response
from flask import render_template, url_for, redirect, send_from_directory
from flask import send_file, make_response, abort
from flask import jsonify, json

from cloudvm.dashboard import *
from cloudvm.dashboard.web_service import *

web = WebService()

@app.route("/")
def index():
  return make_response(open('cloudvm/dashboard/templates/index.html').read())

@app.route("/status")
def status():
  return jsonify(web.to_status_json())

@app.route('/manifests/<int:id>/start', methods=['POST'])
def startManifest(id):
  return jsonify(web.startManifest())

@app.route('/manifests/<int:id>/kill', methods=['POST'])
def killManifest(id):
  return jsonify(web.killManifest())

@app.route('/manifests/<int:id>/destroy', methods=['POST'])
def destroyManifest(id):
  return jsonify(web.destroyManifest())

@app.route('/groups/<string:name>/start', methods=['POST'])
def startGroup(name):
  return jsonify(web.startGroup(name))

@app.route('/groups/<string:name>/kill', methods=['POST'])
def killGroup(name):
  return jsonify(web.killGroup(name))

@app.route('/groups/<string:name>/destroy', methods=['POST'])
def destroyGroup(name):
  return jsonify(web.destroyGroup(name))

@app.route('/groups/<string:name>/resize', methods=['POST'])
def resizeGroup(name):
	return jsonify(web.resizeGroup(name, int(request.args['size'])))

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico')

