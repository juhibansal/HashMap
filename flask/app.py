from flask import Flask
from flask import render_template, request, redirect
from flask import stream_with_context, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from dateutil.parser import parser
from datetime import datetime
from collections import OrderedDict
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx
import operator                             #Importing operator module

app = Flask(__name__)
db = SQLAlchemy(app)

POSTGRES = {
    'user': 'postgres',
    'pw': 'insight',
    'db': 'postgresdb',
    'host': 'XXXX',
    'port': '5432',
}

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
db.init_app(app)

@app.route('/')
def index():
	return render_template("index.html")



class Table1(db.Model):
    __tablename__ = 'rules'

    antecedent = db.Column(db.String(50), nullable=False, primary_key = True)
    consequent = db.Column(db.String(50), nullable=False, primary_key=True)
    confidence = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '{antecedent} {consequent} {confidence}'.format(consequent=self.consequent,antecedent=self.antecedent,confidence=self.confidence)

test_1 = (db.session.query(Table1).all())
#print "Test 1 = " + str( test_1 )

@app.route('/', methods=['GET','POST'])
def my_form_post():
    if request.method == 'POST':
        hashtag = request.form['hashtag_txt']
        hashtags = hashtag.strip().lower().split()
        if len(hashtags)==1: hashtags = hashtag.lower().split(",")
        DictResults = {}
        list1=[]
        for i in range(0,len(hashtags)):
            results = Table1.query.filter(Table1.antecedent==hashtags[i]).all()
            print(results)
            DictResults[hashtags[i]] = {}
            for j in range(0,len(results)):
                final = str(results[j]).split()
                if len(final)==3:
                    DictResults[hashtags[i]][final[1]] = final[2]
                    list1.append(final[1])
        counts = Counter(list1)
        create_network(DictResults)
        DictResultsCommon = {}  
        labels = []
        values = []
        
        for key, value in counts.items():
            if len(DictResults)==value:
                DictResultsCommon[key]=float("{0:.3f}".format(float(DictResults[hashtags[len(hashtags)-1]][key])))
        for key, value in sorted(DictResultsCommon.iteritems(), key=lambda (k,v): (v,k)):
            labels.append(key)
            values.append(value)
       
 
    return render_template('output.html', result=DictResultsCommon, values=values, labels=labels)

def create_network(DictResults):
    leftside = []
    rightside = []
    weights = []

    for hashtag in DictResults:
        for associate in DictResults[hashtag]:
            leftside.append(hashtag)
            rightside.append(associate)
            weights.append(DictResults[hashtag][associate])

    df = pd.DataFrame({'leftside' : leftside, 'rightside':rightside,'weights':weights})
#df = pd.DataFrame.from_dict({(i,j): DictResults[i][j] for i in DictResults.keys() for j in DictResults[i].keys()}, orient='index')
    print(df.head())
    g = nx.from_pandas_edgelist(df, 'leftside', 'rightside',edge_attr=True)
    f = plt.figure()
    g.nodes()
    g.edges()
    pos = nx.spring_layout(g)
    layout = nx.spring_layout(g,iterations=50)
    nx.draw_networkx(g,with_labels=True)
    f.savefig("static/tmp.jpg")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
