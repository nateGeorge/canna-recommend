# for deployment on amazon elastic beanstalk
# can't use any graphlab dependencies
# everything is loaded from pickle

import leafly.graphlab_production as glp
import leafly.nlp_funcs as nl
import json
import cPickle as pk

from flask import Flask, request
import flask
app = Flask(__name__)

app.debug = True

# home page
@app.route('/')
def index():
    return 'get outta here!'

# returns list of words in different groups as dict
@app.route('/get_product_words', methods=['POST'])
def get_words():
    word_dict = nl.get_product_word_choices()
    resp = flask.Response(json.dumps(word_dict))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/send_words', methods=['POST', 'OPTIONS'])
def send_words():
    # print request
    # print 'motherfucker'
    # print request.form['words']
    # word_list = request.form['words']
    # print word_list
    print request.get_json()
    print request.json
    print request.mimetype
    print request.values
    words = request.form.getlist('word_list[]')
    print words
    recs, top3 = glp.get_recs(rec_engine, words, prod_group_dfs, prod_top_words, prod_user='products')
    print top3
    resp = flask.Response(json.dumps({'recs':top3.tolist()}))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == '__main__':
    rec_engine = glp.load_engine()
    prod_group_dfs, user_group_dfs = glp.load_group_dfs()
    prod_top_words, prod_word_counter = glp.load_top_words()
    app.run(host='0.0.0.0', port=10001, debug=True, threaded=True)
