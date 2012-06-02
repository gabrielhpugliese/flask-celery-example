from os import path, environ
import json
from flask import Flask, Blueprint, abort, jsonify, request, session
import settings
from modules import myapi
from flask.ext.celery import Celery


app = Flask(__name__)
app.config.from_object(settings)


app.register_blueprint(myapi.blueprint)

def register_api(view, endpoint, url, pk ='id', pk_type='int'):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET',])
    app.add_url_rule(url, view_func=view_func, methods=['POST',])
    app.add_url_rule('{0}<{1}:{2}>'.format(url, pk_type, pk), view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])

register_api(myapi.MyAPI, 'my_api', '/my_api/', 'resource_tag', pk_type='string')

celery = Celery(app)

@celery.task(name="myapp.add")
def add(x, y):
    return x + y

@app.route("/test")
def hello_world(x=16, y=16):
    x = int(request.args.get("x", x))
    y = int(request.args.get("y", y))
    res = add.apply_async((x, y))
    context = {"id": res.task_id, "x": x, "y": y}
    result = "add((x){}, (y){})".format(context['x'], context['y'])
    goto = "{}".format(context['id'])
    return jsonify(result= result, goto=goto) 

@app.route("/test/result/<task_id>")
def show_result(task_id):
    retval = add.AsyncResult(task_id).get(timeout=1.0)
    return repr(retval)

print app.url_map

if __name__ == "__main__":
    port = int(environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)