import leafly.graphlab_production as glp
import leafly.nlp_funcs as nl
import json

from flask import Flask, request
import flask
app = Flask(__name__)

app.debug = True

# home page
@app.route('/')
def index():
    return 'bullshit!'

# returns list of words in different groups as dict
@app.route('/get_product_words', methods=['POST'])
def get_words():
    #word_dict = nl.get_product_word_choices()
    word_dict = nl.get_product_word_choices()
    resp = flask.Response(json.dumps(word_dict))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/send_words', methods=['POST'])
def send_words(data):
    word_dict = request.json
    word_dict = nl.get_product_word_choices()
    resp = flask.Response(json.dumps(word_dict))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == '__main__':
    rec_engine = glp.load_engine()
    app.run(host='0.0.0.0', port=8080, debug=True)
