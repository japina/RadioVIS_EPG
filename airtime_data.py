PGSQL_SERVER = "10.0.0.10"
class airtime:
	outdata = []
	def get_data(self):	
		import bpgsql
		import datetime
		conn = bpgsql.connect(username="airtime",host=PGSQL_SERVER,password="airtime", dbname="airtime")
		cur = conn.cursor()
		cur.execute("select * from cc_show_instances")
		ret = cur.fetchall()
		start_time = ""
		end_time = ""
		cnt = len(ret)
		i = 0
		while (i<cnt):
			show_id = ret[i][0]
			start_time =  ret[i][1]
			#self.outdata.append(start_time)
			cur.execute("select * from cc_schedule where instance_id='"+str(show_id)+"'")
			ret2 = cur.fetchall()
			cnt_j = len(ret2)
			j = 0
			#if (cnt_j>0):
			#	playlist_id = ret2[0][1]
			#	cur.execute ("select * from cc_playlist where id='"+str(playlist_id)+"'")
			#	ret21 = cur.fetchall()
			while(j<cnt_j):
				cur.execute("select * from cc_files where id='"+str(ret2[j][5])+"'")
				ret3 = cur.fetchall()
				if (j+1==cnt_j):
					end_time =  str(ret[i][2])
				element_len = ret3[0][16]
				element_desc = ret3[0][19]
				element_name = str(ret3[0][2])
				element_len_timedelta = datetime.timedelta(0,element_len.second,element_len.microsecond,0, element_len.minute, element_len.hour,0)
				element_end_time = start_time + element_len_timedelta
				self.outdata.append([str(start_time),element_name,element_desc,str(element_end_time)])
				start_time = element_end_time					
				j+=1
			i+=1
		#self.outdata.append(end_time)
		return self.outdata
