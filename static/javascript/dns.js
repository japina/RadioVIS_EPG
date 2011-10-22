function displayAlertMessage(message) {
    //var timeOut = 5;
    jQuery('#msgbox').text(message).fadeIn();
    jQuery('#msgbox').css("display", "block");
   /* setTimeout(function() {
    jQuery('#messageBox').fadeOut()
    jQuery('#messageBox').css("display", "none")
    }, timeOut * 1000); */
}



function select_photo(line_no) {
	var out_data;
	$.ajax({
    	 async: false,
     	type: 'GET',
	     url: '/getmysqldbdata/'+line_no,
     	success: function(data) {
     		len = data.length;
          	out_data = data;
     	}
	});
	return out_data;
};

/*function select_text(line_no) {
	var out_data;
	$.ajax({
    	 async: false,
     	type: 'GET',
	     url: '/getmysqldbdata/'+line_no,
     	success: function(data) {
     		len = data.length;
          	out_data = data.substring(2,len-3);
     	}
	});
	return out_data;
}; */


function upload(line_no){
	$.get("/upload_data/"+line_no,function(data){
		var $dialog = $('<div></div>')
			.html(data)
			.dialog({
				autoOpen: false,
				title: 'Upload file',
				width: 500
			});
		$dialog.dialog("open");			
	});
};

/*function enter_txt(line_no){
	$.get("/upload_text/"+line_no,function(data){
		var $dialog = $('<div></div>')
			.html(data)
			.dialog({
				autoOpen: false,
				title: 'Upload text',
				width: 500
			});
		$dialog.dialog("open");			
	});
}; */


function add_or_change_function(cnt){
	// jquery (loading)
	var out_data;
	var i=0;
	while(i<cnt){
		out_data = select_photo(i).split(",");
		//document.getElementById("aoc_pic_"+(i)).innerHTML=out_data.length;		
		if (out_data.length>2){
			var data_len = out_data[0].length;	
						
			document.getElementById("aoc_pic_"+i).innerHTML=out_data[0].substr(4,data_len-5);
			data_len = out_data[1].length;						
			document.getElementById("aoc_txt_"+i).innerHTML=out_data[1].substr(3,data_len-4);
			document.getElementById("aoc_"+i).innerHTML = "<button type='button' onclick='upload("+i+")'>Change</button>";						
		}

		i+=1;
	}
	/*var len_data = out_data.length;
	var cnt = len_data/3;
	var i=0;
	while(i<cnt){
		var data_len = out_data[0+i*3].length;
		document.getElementById("aoc_pic_"+(cnt-i-1)).innerHTML=out_data[0+i*3].substr(4,data_len-5);
		data_len = out_data[1+i*3].length;
		document.getElementById("aoc_txt_"+(cnt-i-1)).innerHTML=out_data[1+i*3].substr(3,data_len-4);
		document.getElementById("aoc_"+i).innerHTML = "<button type='button' onclick='upload("+i+")'>Change</button>";						
		i+=1
	}; */
// jquery (stop)
};