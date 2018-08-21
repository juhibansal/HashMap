#
# Licensed to the Apache Software Foundation (ASF) under one or more
from __future__ import print_function

import sys
from operator import add
import datetime
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from pyspark.sql import Row
from pyspark.sql.types import *
from pyspark.sql import functions as func
from pyspark.sql.functions import udf,col,desc,explode,monotonically_increasing_id 
import re
import os
from os.path import isfile,isdir
from pprint import pformat
from sys import argv, exit
from glob import glob

import numpy as np
import pandas as pd
import itertools
import collections
from collections import OrderedDict
import gzip
import os
import subprocess
from pyspark.sql.window import Window
from pyspark import SparkConf
from cassandra.cluster import Cluster
import cassandra


import socket
import sys
import requests
import requests_oauthlib
import json

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: wordcount <file>", file=sys.stderr)
        exit(-1)
    
    def myfunc(line):
        tweet = json.loads(line)
        hashtag = []
        if "entities" in tweet:
            if tweet["entities"]:
                if tweet["entities"]["hashtags"]:
                    for i in range(len(tweet["entities"]["hashtags"])-1):
                        final = re.sub(r'[^a-z0-9]+', '',tweet["entities"]["hashtags"][i]["text"].lower())
                        if not final in hashtag:
                            hashtag.append(final)
        return ",".join(hashtag)

    count = 0
    def convert2arr(line):
        global count
        tweet = line.split(",")
        hashtag = []
        for x in tweet:
            hashtag.append(x)
            count = count + 1
        return count,hashtag

    def convert2rdd(line):
        tweet = line.split(",")
        tweetcount = int(tweet.pop(0))
        return tweetcount,tweet
    
    def array_to_string(my_list):
        if len(my_list) > 0:
            my_list.sort()
            return ','.join([str(elem) for elem in my_list])
        else:
            return "Nothing"
    
    spark = SparkSession\
        .builder\
        .appName("AssociationRules_Juhi")\
        .config("spark.some.config.option", "some-value")\
        .getOrCreate()

    sqlContext = SQLContext(spark)

    filelist = "s3a://juhibansal/twitter-stream/*/*/*/*.json"
    tfile = spark.sparkContext.textFile(filelist)
    devchars = tfile.map(lambda l:myfunc(l))
    filter_rdd = devchars.filter(lambda x: x is not '').distinct()
    filter_rdd1 = filter_rdd.map(lambda l:convert2arr(l))
    filter_rdd2 = filter_rdd1.map(lambda p:Row(idx=p[0], items=p[1]))

    tweets_df = spark.createDataFrame(filter_rdd2) 
    tweets_dfsl = tweets_df.select("items")
    print(filter_rdd2.collect()) 
    print(tweets_df.show(10)) 

    apirdd = spark.sparkContext.textFile("s3a://juhibansal/apitweets_processed/*")
    apirdd1 = apirdd.map(lambda l:convert2rdd(l))
    api_rdd = apirdd1.map(lambda p:Row(idx=p[0], items=p[1]))
    
    api_df = spark.createDataFrame(api_rdd)
    api_dfsl = api_df.select("items")
    print(api_dfsl.show(10)) 
    
    array_to_string_udf = udf(array_to_string,StringType())
    uniondf = tweets_dfsl.union(api_dfsl)
    uniondf = uniondf.withColumn("idx", monotonically_increasing_id())
    ml_df = uniondf.select(["idx","items"])    
    ml_df2 = ml_df.withColumn('items',array_to_string_udf(ml_df["items"]))

    #os.system("aws s3 rm --recursive s3://juhibansal/sanatized_data")
    #ml_df2.write.format('com.databricks.spark.csv').save("s3a://juhibansal/sanatized_data")
    from pyspark.ml.fpm import FPGrowth

    fpGrowth = FPGrowth(itemsCol="items", minSupport=0.001, numPartitions=10, minConfidence=0.05)
    model = fpGrowth.fit(ml_df)

    model.freqItemsets.show(100)
    dfrules = model.associationRules
    model.associationRules.show()
    model.transform(ml_df)


    dfrules = dfrules.withColumn("antecedent", explode(dfrules.antecedent))
    dfrules = dfrules.withColumn("consequent", explode(dfrules.consequent))
    print(dfrules.show())
    
    from pyspark.sql import DataFrameWriter
    url_connect = "jdbc:postgresql://<>:5432/postgresdb"
    table = "rules"
    mode = "overwrite"
    properties = {"user": "postgres","password": "insight"}
    dfrules.select(["antecedent","consequent","confidence"]).write.jdbc(url=url_connect, table="rules", mode=mode, properties=properties)

