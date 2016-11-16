import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import leafly.graphlab_production as glp
import leafly.nlp_funcs as nl
import leafly.scrape_leafly as sl
import json
import cPickle as pk
import re
from flask import Flask, request
import flask
app = Flask(__name__, static_url_path='')

app.debug = True

def clean_recs(recs):
    '''
    cleans up recommendation strains for proper presentation
    '''
    cln_recs = []
    for r in recs:
        temp = [s.capitalize() for s in r.split('-')]
        temp = ' '.join(temp)
        temp = re.sub('\ss\s', '\'s ', temp, flags=re.IGNORECASE) # replace a single s with 's
        cln_recs.append(temp)

    return cln_recs

@app.route('/')
def index():
    return app.send_static_file('app.html')

# returns list of words in different groups as dict


@app.route('/get_product_words', methods=['POST'])
def get_words():
    word_dict = nl.get_product_word_choices()
    resp = flask.Response(json.dumps(word_dict))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/send_words', methods=['POST', 'OPTIONS'])
def send_words():
    # print request.form['words']
    # word_list = request.form['words']
    # print word_list
    print request.get_json()
    print request.json
    print request.mimetype
    print request.values
    words = request.form.getlist('word_list[]')
    print words
    # get slightly more recommendations than show up on one page
    recs, top, links, toplinks = glp.get_better_recs(link_dict,
        rec_engine, words, prod_group_dfs, prod_top_words, prod_user='products', size=15)
    # convert to pretty form
    print top
    cln_recs = clean_recs(top)
    print cln_recs
    # need to convert numpy array to list so it is serializable
    toplinks = list(toplinks)
    print links
    print toplinks
    resp = flask.Response(json.dumps({'recs': cln_recs, 'links':toplinks}))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/send_leafly_user', methods=['POST', 'OPTIONS'])
def send_leafly_user():
    print request.get_json()
    print request.json
    print request.mimetype
    print request.values
    print request.form
    user = request.form.getlist('user')
    print user
    print user[0]
    k = int(request.form.getlist('k')[0])

    recs = glp.make_rec(rec_engine, user[0], users_in_rec, k)
    cln_recs = clean_recs(recs)

    print recs
    if recs is None:
        flask.Response(json.dumps({'recs':None, 'links':None}))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    links = []
    for r in recs:
        links.append(link_dict[r])

    resp = flask.Response(json.dumps({'recs':cln_recs, 'links':links}))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    # link_dict needed to get links from recommendation function
    strains = sl.load_current_strains(True)
    # make dict of names to links for sending links to rec page
    names = [s.split('/')[-1] for s in strains]
    link_dict = {}
    for i, n in enumerate(names):
        link_dict[n] = strains[i]

    latest_model = 'leafly/10groupsrec_engine.model'
    if not os.path.exists(latest_model):
        glp.train_and_save_everything(latest_model)
    else:
        rec_engine = glp.load_engine(filename=latest_model)

    prod_group_dfs, user_group_dfs = glp.load_group_dfs()
    prod_top_words, prod_word_counter = glp.load_top_words()
    users_in_rec = pk.load(open('leafly/users_in_rec.pk'))
    app.run(host='0.0.0.0', port=10001, debug=True, threaded=True)
