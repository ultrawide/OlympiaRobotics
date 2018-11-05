# The robot will configure itself based on parameters set in file
import configparser

CONFIG_FILENAME = 'config.txt'

def create_configfile(config_filename):
	config = configparser.ConfigParser()
	config['NETWORK'] = {'server_address' : '192.168.0.1', 
						'video_port' : '8000', 
						'command_port' : '8001'}

	with open(config_filename, 'w') as configfile:
		config.write(configfile)

# 
class RobotConfig:
	NETWORK_SECTION = 'NETWORK'
	SERVER_ADDRESS_OPTION = 'server_address'
	VIDEO_PORT_OPTION = 'video_port'
	COMMAND_PORT_OPTION = 'command_port'
	
	def __init__(self, config_filename):
		self.config_filename = config_filename
		self.config = configparser.ConfigParser()
		self.config.read(config_filename)

	def get_option(self, parameter):
		value = self.config.get(self.NETWORK_SECTION, parameter, fallback=None)

		if value != None:
			print("Found '" + parameter + "' config option in " + self.config_filename + " configuration file")
		else:
			print("Warning '" + parameter + "' config option not found in " + self.config_filename + " configuration file")
		
		return value
		
if __name__ == "__main__":
	#create_configfile(CONFIG_FILENAME)

	rc = RobotConfig(CONFIG_FILENAME)
	print(rc.get_option(rc.SERVER_ADDRESS_OPTION))  # example for getting config parameters from config
	print(rc.get_option(rc.VIDEO_PORT_OPTION))
	print(rc.get_option(rc.COMMAND_PORT_OPTION))
	print(rc.get_option('nooption'))  # example for what happens when option not in config



	
