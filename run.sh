#!/bin/bash

rm -rf testout
spark-submit --master local[4] src/045.mesos-spark.py data/hcl.sample testout