import airtime_data
import datetime

AIRTIME_SELECTED = 1
class epg:
	playlist_data=[]	
	def __init__(self):
		if AIRTIME_SELECTED == 1:
			airtime = airtime_data.airtime()
			self.playlist_data=airtime.get_data()
			
	def getCurrentWeek(self):
		#today_date = datetime.datetime.strftime(datetime.datetime.today(),"%Y-%m-%d %H:%M:%S.%f")
		ret = self.playlist_data
		data = lambda x: x[1]
		return map(data,ret)
		
	def program(self):
		out_data = "<epg>"
		datum_p = datetime.datetime.strptime(datum,"%Y-%m-%d %H:%M:%S")
		name = datum_p.strftime("%A")
		return data
