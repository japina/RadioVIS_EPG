#!/usr/local/bin/python
import os
#stomp part
import coilmq.start
from coilmq import *
from coilmq.server import StompConnection
from coilmq.util.concurrency import synchronized
from coilmq.queue import QueueManager
from coilmq.server.socketserver import ThreadedStompServer
from coilmq.store.memory import MemoryQueue
from coilmq.scheduler import FavorReliableSubscriberScheduler, RandomQueueScheduler
from coilmq.topic import TopicManager
import uuid

#tornado part
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import xmlrpclib

# threads
from threading import Thread
import urllib
import datetime
#from datetime import datetime
import MySQLdb

#airtime imports
import airtime_data


DB_SERVER = "10.0.0.10"
WEB_SERVER = "localhost"

AIRTIME_SELECTED = 1


#get next data according to last_id
def dbGetNextId(radio_station,timestamp,last_id):
	#correct - just copy from FirstId
	got_id = 1
	if last_id!="":
		got_id=int(last_id.split("_")[1])	
	db=MySQLdb.connect(passwd="csndoidar",db="radiodns_client",user="radiodnsc",use_unicode=True,charset="utf8",host=DB_SERVER,port=3306)		
	c = db.cursor()
	c.execute("select datetime_id from radiodns_client.radiodns_client where radio_station=%s",(radio_station))
	data_rows = c.fetchall()
	last_datetime_id = int(data_rows[-1][0])-1
	if got_id==last_datetime_id:
		got_id = 1
	else:
		got_id +=1
	c.close()
	return str(timestamp)+"_"+str(got_id)


def dbGetData(radio_station,last_id,date_val,datetime_id,type):
	next_id = 0
	db=MySQLdb.connect(passwd="csndoidar",db="radiodns_client",user="radiodnsc",use_unicode=True,charset="utf8",host=DB_SERVER,port=3306)		
	c = db.cursor()
	dt_id = datetime_id.split("_")[1]
	if last_id!="":
		next_id=int(last_id.split("_")[1])+1
	c.execute("select url_field,text_field from radiodns_client.radiodns_client where datetime_id=%s",next_id) #get image and text data for the radiodns
	data_row = c.fetchone()
	if data_row==None:
		next_id = 1
		c.execute("select url_field,text_field from radiodns_client.radiodns_client where datetime_id=%s",next_id)		
		data_row = c.fetchone()		
	c.execute("select datetime_id,id from radiodns_client.radiodns_client where start_time<%s and end_time>%s and radio_station=%s",(date_val,date_val,radio_station))
	lista = c.fetchall()
	c.execute("select datetime_id,id from radiodns_client.radiodns_client where end_time<%s and radio_station=%s",(date_val,radio_station))	
	listb = c.fetchall()
	sizeb = len(listb)
	cntb = 0
	if sizeb>0:
		for i in lista:
			if i[0]==None:
				i[0]=listb[cntb]
				cntb+=1
	c.close()
	return data_row

# get pics according to start_time and end_time	
def dbGetTimes(start_time,end_time):
	if (start_time.find(".")!=-1):
		ms_start_time = datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S.%f") #- datetime.timedelta(microseconds=100000)
	else:
		ms_start_time = datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S") #- datetime.timedelta(microseconds=100000)
	if (end_time.find(".")!=-1):
		ms_end_time = datetime.datetime.strptime(end_time,"%Y-%m-%d %H:%M:%S.%f") #+ datetime.timedelta(microseconds=100000)
	else:
		ms_end_time = datetime.datetime.strptime(end_time,"%Y-%m-%d %H:%M:%S") #+ datetime.timedelta(microseconds=100000)
		
	db=MySQLdb.connect(passwd="csndoidar",db="radiodns_client",user="radiodnsc",use_unicode=True,charset="utf8",host=DB_SERVER,port=3306)		
	c = db.cursor()
	c.execute("select url_field,text_field,datetime_id from radiodns_client.radiodns_client where start_time>=%s and end_time<=%s",(ms_start_time,ms_end_time))	
	ret = c.fetchall()
	c.close()
	return list(ret)

define("port", default=8890, help="run on the given port", type=int)

# RadioEPG
class EpgHandler(tornado.web.RequestHandler):
	def get(self,indata):
		playlist_data=[]
		if AIRTIME_SELECTED == 1:
			airtime = airtime_data.airtime()
			playlist_data=airtime.get_data()
			start_time = playlist_data[int(line_no)][0]
			end_time = playlist_data[int(line_no)][3]
		self.set_header("Content-Type","text/xml")		
		self.write(xml_data)



# curently only one topic at the time !!!
class VisHandler(tornado.web.RequestHandler):
	def get(self,indata):
		part_indata = indata.split("?")
		parsed_indata = part_indata[1].split("&")
		topics=[]
		last_id=""
		for i in parsed_indata:
			if i.find("topic=")==0:
				topics.append(i.replace("topic=",""))
			try:
				if i.find("last_id")==0:
					last_id=i.replace("last_id=","")
			except:
				pass

		#currently only one topic
		topic = topics[0]
		radio_station = topic.split("/")[0]
				
		# need to parse indata
		# if parse(indata) == true then select 
		# get current time
		#read fom the pic database where start is lower or the same and end is larger or the same as current time
		# show pic or TEXT
		timestamp = datetime.datetime.now().strftime("%d%H%M%S%f")
		date_val = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")	

		dt_id = 1
		datetime_data = str(timestamp)+"_2"
		if last_id!="":
			dt_id = int(last_id.split("_")[1])
			datetime_data = dbGetNextId(radio_station,timestamp,last_id)
		headers = ["X-RadioVIS-Message-ID:"+urllib.quote(datetime_data), 
		"X-RadioVIS-Destination:"+urllib.quote(topic)]
		#"X-RadioVIS-Trigger-Time: NOW",
		#"X-RadioVIS-Link:"+urllib.quote("http://www.puppetz.si")]
		for header in headers:
			argum = header.split(":")
			self.set_header(argum[0],argum[1])
		
		outdata=""
		[show_url,text_text] = dbGetData(radio_station,last_id,date_val,datetime_data,"")
		parsed_topic = topic.split("/")
		if parsed_topic[-1]=="image":
			outdata="SHOW /static/music/"+show_url

		if parsed_topic[-1]=="text":
			outdata = "TEXT "+text_text
		self.render("templates/index.html", title="RadioVIS", outdata = outdata)			

# entering RadioVIS data
class SettingHandler(tornado.web.RequestHandler):
	def get(self):
		airtime = airtime_data.airtime()
		playlist_data=airtime.get_data()
		cnt = len(playlist_data)
		self.render("templates/settings.html", title="Settings", outdata = playlist_data, cnt = cnt)		
		
#get data from mysql according to no of clicked line
class GetMySQLDataHandler(tornado.web.RequestHandler):
	def get(self,data):
		airtime = airtime_data.airtime()
		playlist_data=airtime.get_data()
		start_time = playlist_data[int(data.split("/")[1])][0]
		end_time = playlist_data[int(data.split("/")[1])][3]
		outdata = dbGetTimes(start_time,end_time)

		self.render("templates/getmysqldbdata.html",data = outdata)			
	
class UploadDataHandler(tornado.web.RequestHandler):
	def get(self,data):
		line_no = data.split("/")[1]
		if AIRTIME_SELECTED == 1:
			airtime = airtime_data.airtime()
			playlist_data=airtime.get_data()
			description = playlist_data[int(line_no)][2]
		
		self.render("templates/upload_data.html",line_no = line_no, image_list_url=image_list_url)					

#uploading text data
class UptextHandler(tornado.web.RequestHandler):
	def post(self):
		received_data = self.request
		line_no = 1	
		boundary = received_data.headers["Content-Type"].split(";")[1].replace("boundary=","")
		name_pos = received_data.body.find('name="text"\r\n\r\n')+15
		end_data_pos = received_data.body[name_pos:].find("\r\n")+name_pos
		entered_text = received_data.body[name_pos:end_data_pos]

		line_no_pos = received_data.body.find('name="line_no"')+18
		line_no_end_pos = received_data.body[line_no_pos:].find("\r\n")+line_no_pos
		line_no = received_data.body[line_no_pos:line_no_end_pos]
		
		
		db=MySQLdb.connect(passwd="csndoidar",db="radiodns_client",user="radiodnsc",use_unicode=True,charset="utf8",host=DB_SERVER,port=3306)		
		c = db.cursor()
		if AIRTIME_SELECTED == 1:
			airtime = airtime_data.airtime()
			playlist_data=airtime.get_data()
			start_time = playlist_data[int(line_no)][0]
			end_time = playlist_data[int(line_no)][3]
		
		ret = dbGetTimes(start_time,end_time)
		list_of_ids =[]
		for i in ret:
			list_of_ids.append(i[3])
		if len(list_of_ids)>0:
			last_id = max(list_of_ids)+1
		else:
			last_id = 1
		c.execute("insert into radiodns_client.radiodns_client (radio_station,text_field,start_time,end_time,datetime_id) values (%s,%s,%s,%s,%s,%s)",("www.val202.si",entered_text,start_time,end_time,str(last_id)))
		
		
		self.render("templates/uptext.html",received_data = received_data.body[name_pos:end_data_pos])	


#insert entered data while setting to mysql
class UploadHandler(tornado.web.RequestHandler):
	def post(self):
		received_data = self.request	
		line_no = 1	
		boundary = received_data.headers["Content-Type"].split(";")[1].replace("boundary=","")
		content_type_pos = received_data.body.find("Content-Type:")
		end_header_pos = received_data.body[content_type_pos:].find("\r\n")+content_type_pos
		file_data = received_data.body[end_header_pos:].replace(boundary,"")
		file_name_pos = received_data.body.find("filename") 
		file_name_end_pos = received_data.body[file_name_pos:].replace('filename="','').find('"')+file_name_pos
		file_name = received_data.body[file_name_pos+10:file_name_end_pos+10]

		name_pos = received_data.body.find('name="text"\r\n\r\n')+15
		end_data_pos = received_data.body[name_pos:].find("\r\n")+name_pos
		entered_text = received_data.body[name_pos:end_data_pos]

		
		line_no_pos = received_data.body[end_header_pos:].find('name="line_no"')+end_header_pos+18
		line_no_end_pos = received_data.body[line_no_pos:].find("\r\n")+line_no_pos
		line_no = received_data.body[line_no_pos:line_no_end_pos]
		
		fopen = open("static/music/"+file_name,"wb")
		fopen.write(file_data)
		fopen.close()
		db=MySQLdb.connect(passwd="csndoidar",db="radiodns_client",user="radiodnsc",use_unicode=True,charset="utf8",host=DB_SERVER,port=3306)		
		c = db.cursor()
		if AIRTIME_SELECTED == 1:
			airtime = airtime_data.airtime()
			playlist_data=airtime.get_data()
			start_time = playlist_data[int(line_no)][0]
			end_time = playlist_data[int(line_no)][3]
			description = playlist_data[int(line_no)][2]
		
		ret = dbGetTimes(start_time,end_time)
		list_of_ids =[]
		for i in ret:
			list_of_ids.append(i[3])
		if len(list_of_ids)>0:
			last_id = max(list_of_ids)+1
		else:
			last_id = 1
		c.execute("insert into radiodns_client.radiodns_client (radio_station,url_field,text_field,start_time,end_time,datetime_id) values (%s,%s,%s,%s,%s,%s)",("www.val202.si",file_name,entered_text,start_time,end_time,str(last_id)))
		self.redirect("/setting")		
			

# stomp server seting
class TopicM(TopicManager):

	def send(self, message):
		"""
		Sends a message to all subscribers of destination.
		
		@param message: The message frame.	(The frame will be modified to set command 
							to MESSAGE and set a message id.)
		@type message: L{stompclient.frame.Frame}
		"""
		print message # poslji sporocilo na web server
		dest = message.destination
		if not dest:
			raise ValueError("Cannot send frame with no destination: %s" % message)
		
		message.command = 'MESSAGE'
		
		if not 'message-id' in message.headers:
			message.headers['message-id'] = str(uuid.uuid4())
			
		for subscriber in self._topics[dest]:
			subscriber.send_frame(message)	
			
#thread class
class stormt(Thread):
	def __init__(self,server):
		Thread.__init__(self)
		self.server = server
	def run(self):
		self.server.serve_forever()
		
if __name__ == '__main__':

#stomp
	class DumbContext(object):
		def __enter__(self):
			pass
		def __exit__(self, type, value, traceback):
			pass

	def context_serve(context):
		server = ThreadedStompServer((WEB_SERVER,61613),
									 queue_manager=QueueManager(store=MemoryQueue,
									subscriber_scheduler=FavorReliableSubscriberScheduler,
									queue_scheduler=RandomQueueScheduler),
									 topic_manager=TopicM(),
									 authenticator=None)
		stomp_server = stormt(server)
		stomp_server.start()

	context_serve(DumbContext())

#tornado
	settings = {
		"static_path": os.path.join(os.path.dirname(__file__), "static"),
		"login_url" : "login",
		"cookie_secret" : "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo="		
		}

	application = tornado.web.Application([
		(r"/(vis[A-Za-z0-9%=&\._]+)", VisHandler),
		(r"/(epg[A-Za-z0-9%=&\._]+)", EpgHandler),					
		(r"/setting", SettingHandler),
		(r"/(getmysqldbdata/[0-9]+)", GetMySQLDataHandler),		
		(r"/(upload_data/[0-9]+)", UploadDataHandler),			
		(r"/upload", UploadHandler),	
		(r"/uptext",UptextHandler)
		], **settings
	)

	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
