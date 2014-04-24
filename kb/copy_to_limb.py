from goobi.goobi_step import Step
import os
import shutil
import time


class CopyToLimb( Step ):

	def setup(self):
		self.name = 'Copy to LIMB'
		self.config_main_section = 'test'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			"process_id" : "number",
			"source" : "folder",
		}

	def step(self):
		try:
			print "hello"
			files_not_copied  = True
			transit_dir = self.getConfigItem('limb_transit') + '/' + os.path.basename(self.command_line.source)
			print "transit: "+transit_dir
			os.makedirs(transit_dir)
			
			src_files = [[l,False] for l in os.listdir(self.command_line.source)]
			
			while (files_not_copied):
				files_not_copied = False
				for src_file in src_files:
					print "starting copy"
					if (not src_file[1]):
		    				full_file_name = os.path.join(self.command_line.source, src_file[0])
		    				if (os.path.isfile(full_file_name)):
					   		try:	
								shutil.copy2(full_file_name, transit_dir)
								src_file[1] = True
					   		except Exception:
								self.info_message("Error copying file '"+full_file_name)
								files_not_copied = True
						else:
							self.info_message(full_file_name+" is not af file")
				if (files_not_copied):
					self.info_messages("Not all files copied. Sleeping ...")
					time.sleep				
			shutil.move(transit_dir,self.getConfigItem('limb_hotfolder'))
		except Exception as e:
			print e
			self.info_message("An error happened")			
		return None

if __name__ == '__main__':	
	CopyToLimb().begin()
