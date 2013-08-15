import os

from urlparse import urlparse
from flask import Flask, request, Response
from flask import render_template, url_for, redirect, send_from_directory
from flask import send_file, make_response, abort
from flask import jsonify, json
from cloudvm.models import *
from cloudvm.dashboard import app
from cloudvm.dashboard.models import *

class WebService:
  def __init__(self):
    self.docker = Configuration.get_docker()
    self.ctx = Context(self.docker, None, State.load("dock.state"))
    self.manifest = Manifest("manifest-test.json")
    self.manifest.update(self.ctx)
    self.machine = HostMachine()

  def startManifest(self):
    self.manifest.provision(self.ctx)
    self.save()
    return self.to_status_json()

  def killManifest(self):
    self.manifest.kill(self.ctx)
    self.save()
    return self.to_status_json()

  def destroyManifest(self):
    self.manifest.destroy(self.ctx)
    self.save()
    return self.to_status_json()

  def save(self):
    self.manifest.save()
    self.ctx.state.save("dock.state")

  def to_status_json(self):
    return {
      'machine' : self.machine.to_json(),
      'manifest' : self.manifest.to_json()
    }
  
@app.route("/")
def index():
  return make_response(open('cloudvm/dashboard/templates/index.html').read())

@app.route("/status")
def status():
  web = WebService()
  return jsonify(web.to_status_json())

@app.route('/manifests/<int:id>/start', methods=['POST'])
def startManifest(id):
  web = WebService()
  return jsonify(web.startManifest())

@app.route('/manifests/<int:id>/kill', methods=['POST'])
def killManifest(id):
  web = WebService()
  return jsonify(web.killManifest())

@app.route('/manifests/<int:id>/destroy', methods=['POST'])
def destroyManifest(id):
  web = WebService()
  return jsonify(web.destroyManifest())

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico')

