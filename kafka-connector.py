#!/usr/bin/env python

import sys, requests, yaml, atexit, cStringIO, time, io, os
import xml.etree.cElementTree as ET
import avro.schema
from avro.io import DatumWriter

from optparse import OptionParser
from confluent_kafka import Producer
from events import MovementEvent

def update_last_offset(n):
    global _last_offset
    _last_offset = n


def producer_callback(eventid):
    eventid = eventid
    def inner_callback(err, msg):
        if err:
            sys.stderr.write("%% Message failed delivery: %s\n" % msg)
        else:
            update_last_offset(eventid)
        
    return inner_callback


if __name__ == '__main__':
    filename = "LastEvent"
    parser = OptionParser()
    parser.add_option("-c", "--config-file", dest="configfile", help="Config file (REQUIRED)", default="config.yaml")
    
    (options, args) = parser.parse_args()
    try:
        cf = open(options.configfile, "r")
        config = yaml.load(cf)
        cf.close()
    except yaml.YAMLError as exc:
        print exc
        print "Error loading configuration file.  Aborting."
        sys.exit()
    try:
        _last_offset = int(open(filename).read())
    except IOError:
        _last_offset = 1

    @atexit.register
    def save_last_offset():
        print "saving last offset..."
        open(filename, "w").write("%d" % _last_offset)
    
    username = None
    password = None
    try:
        if 'Auth' in config and 'Source' in config['Auth']:
            if config["Auth"]["Source"] == "Environment":
                username = os.getenv(config["Auth"]["Username"])
                password = os.getenv(config["Auth"]["Password"])
            elif config["Auth"]["Source"] == "Literal":
                username = config["Auth"]["Username"]
                password = config["Auth"]["Password"]
            else:
                print "Auth source '{}' not supported".format(config["Auth"]["Source"])
        else:
            print "Missing Auth"

    except KeyError:
        print "Invalid Auth information"
    
    if 'Interval' in config:
        interval = config['Interval']
    else:
        interval = 15.0
        
    if 'Params' in config:
        params = config['Params']
    else:
        params = {'limit': 1000}
       
    if 'Schema' in config:
        schema_path = config['Schema']
        schema = avro.schema.parse(open(schema_path).read())
        writer = avro.io.DatumWriter(schema)
    else:
        print "failed to get schema file from configuration"
        sys.exit()
    
    if 'Broker' in config:
        broker = config['Broker']
    else:
        print "Must specify Broker in configuration"
        sys.exit()

    if 'URL' in config:
        url = config['URL']
    else:
        print "Must specify API URL in configuration"
        sys.exit()
    producer_conf={'bootstrap.servers': broker}
    p = Producer(**producer_conf)
    @atexit.register
    def flush_producer():
        print "Waiting for messages to send..."
        p.flush()

    with requests.Session() as s:
        if (username is not None) and (password is not None):
            s.auth = (username, password)
        while True:
            try:
                params['startid'] = _last_offset
                r = s.get(url, params=params)
                this_count = 0
                with cStringIO.StringIO(r.text) as response_text:
                    for event, elem in ET.iterparse(response_text, events=("start", "end")):
                        if event == "start":
                            if elem.tag == "events":
                                # we want count to compare against limit
                                this_count = int(elem.get("count"))
                                
                        elif event == "end":
                            # get the values we want
                            if   elem.tag == "eventid":
                                this_id = int(elem.text)
                            elif elem.tag == "eventvalue":
                                this_value = elem.text
                            elif elem.tag == "eventtime":
                                this_timestamp = elem.text
                            elif elem.tag == "deviceid":
                                this_deviceid = int(elem.text)
                            elif elem.tag == "event":
                                # write values to kafka
                                try:
                                    me = MovementEvent.from_api(config, this_value, this_timestamp, this_deviceid)

                                    p.produce(topic, me.to_kafka(writer), 
                                              partition=me.partition(), 
                                              timestamp=me.timestamp(),
                                              callback=producer_callback(this_id))
                                except BufferError as exc:
                                    sys.stderr.write("%% Local producer queue is full.\n")

                                p.poll(0)
                                
                            # we want to clear items when we finish with them to limit memory usage
                            elem.clear()
                save_last_offset()
                if this_count < limit:
                    # we didn't hit the limit, which implies there is no more available now - sleep the interval
                    time.sleep(interval)

            except KeyboardInterrupt:
                sys.exit()
                
