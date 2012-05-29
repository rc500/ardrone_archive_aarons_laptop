"""
Contains the network configuration for each drone
"""
drone1 = {
				'host' : 						"192.168.1.1",	# NB - this is the IP which should be set on the drone
				'control_host' :				 "127.0.0.1",
				'at_port' : 						5556,
				'nav_port' : 						5554,
				'vid_port' : 						5555,
				'config_port' :						5559,
				'control_port' : 					5560,
				'control_data_port' :				5561,
				'video_data_port' : 				5562,
				'control_data_listening_port' :		3456,
				'video_data_listening_port' :		3457,
				'bind_host':						'192.168.1.4',
				};
				
drone2 = {
				'host' :						"192.168.2.1",	# NB - this is the IP which should be set on the drone
				'control_host' :				 "127.0.0.1",
				'at_port' :							5556,
				'nav_port' :						5554,
				'vid_port' : 						5555,
				'config_port' :						5659,
				'control_port' :					5660,
				'control_data_port' :				5661,
				'video_data_port' :					5662,
				'control_data_listening_port' :		3556,
				'video_data_listening_port' :		3557,
				'bind_host':						'192.168.2.3',
				};

