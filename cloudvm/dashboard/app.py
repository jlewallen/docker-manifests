#
#
#

import json
import os
import logging

from urlparse import urlparse
from flask import Flask, request, Response, _app_ctx_stack, current_app
from flask import render_template, url_for, redirect, send_from_directory
from flask import send_file, make_response, abort
from flask import jsonify, json

from cloudvm.dashboard.web_service import WebService

log = logging.getLogger('dock')

app = Flask(__name__)
app.debug = True
app.url_map.strict_slashes = False

def get_web():
	if not hasattr(app, 'web'):
		app.web = WebService(app.options)
	current_app.web.start()
	return current_app.web

@app.route("/")
def index():
	return make_response(open('cloudvm/dashboard/templates/index.html').read())

@app.route('/manifests/<string:name>', methods=['POST'])
def addManifest(name):
	return jsonify(get_web().addManifest(name, request.data))

@app.route('/manifests/clear', methods=['POST'])
def clearManifests():
	return jsonify(get_web().clearManifests())

@app.route('/manifests/recreate', methods=['GET'])
def recreateAll():
	return jsonify(get_web().recreateAll())

@app.route("/status")
def status():
	return jsonify(get_web().to_status_json())

@app.route('/manifests/start', methods=['POST'])
def startManifests():
  return jsonify(get_web().startManifests())

@app.route('/manifests/kill', methods=['POST'])
def killManifests():
  return jsonify(get_web().killManifests())

@app.route('/manifests/destroy', methods=['POST'])
def destroyManifests():
  return jsonify(get_web().destroyManifests())

@app.route('/manifests/<int:id>/start', methods=['POST'])
def startManifest(id):
  return jsonify(get_web().startManifest(id))

@app.route('/manifests/<int:id>/kill', methods=['POST'])
def killManifest(id):
  return jsonify(get_web().killManifest(id))

@app.route('/manifests/<int:id>/destroy', methods=['POST'])
def destroyManifest(id):
  return jsonify(get_web().destroyManifest(id))

@app.route('/groups/<string:name>/start', methods=['POST'])
def startGroup(name):
  return jsonify(get_web().startGroup(name))

@app.route('/groups/<string:name>/kill', methods=['POST'])
def killGroup(name):
  return jsonify(get_web().killGroup(name))

@app.route('/groups/<string:name>/destroy', methods=['POST'])
def destroyGroup(name):
  return jsonify(get_web().destroyGroup(name))

@app.route('/groups/<string:name>/resize', methods=['POST'])
def resizeGroup(name):
	return jsonify(get_web().resizeGroup(name, int(request.args['size'])))

@app.route('/instances/<string:name>/logs', methods=['GET'])
def instanceLogs(name):
	return get_web().instanceLogs(name)

@app.route('/instances/<string:name>/<path:path>', methods=['GET'])
def instanceFileByName(name, path):
	return get_web().instanceEnv(name, path)

@app.route("/my/<path:path>")
def instanceFile(path):
	try:
		return get_web().instanceEnv(request.remote_addr, path)
	except Exception, e:
		log.warn("%s for %s/%s", e.message, request.remote_addr, path)
		return '', 404

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico')

