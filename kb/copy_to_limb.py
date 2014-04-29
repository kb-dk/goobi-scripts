from goobi.goobi_step import Step
import os
import shutil
import time


class CopyToLimb( Step ):

	def setup(self):
		self.name = 'Copy to LIMB'
		self.config_main_section = 'copy_to_limb'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			"process_id" : "number",
			"source" : "folder",
		}

	def step(self):
		try:
			files_not_copied  = True
			source_dir = self.command_line.source
			transit_dir = os.path.join(self.getConfigItem('limb_transit'),os.path.basename(source_dir))
			hotfolder_dir = self.getConfigItem('limb_hotfolder')
			sleep_interval = self.getConfigItem('sleep_interval')
									
			self.info_message("source_dir "+source_dir)
						
			"""
			attempt to copy all files to LIMB transit dir
			retry until all files are copied
			"""
			src_files = [[l,False] for l in os.listdir(source_dir)]			
			while (files_not_copied):
				files_not_copied = False
				try: 
					"""
					create transit dir
					"""
					if not os.path.exists(transit_dir):
						os.makedirs(transit_dir)

					for src_file in src_files:
						self.info_message("starting copy")
						if (not src_file[1]):
			    				full_file_name = os.path.join(source_dir, src_file[0])
			    				if (os.path.isfile(full_file_name)):					   			
								shutil.copy2(full_file_name, transit_dir)
								src_file[1] = True
							else:
								self.info_message(full_file_name+" is not af file")
				except Exception as e:
					self.info_message("Error copying files: %s'" %e)
					files_not_copied = True
				if (files_not_copied):
					self.info_messages("Not all files copied. Sleeping ...")
					time.sleep(sleep_interval)				
			shutil.move(transit_dir,hotfolder_dir)
		except Exception as e:
			self.info_message("An error happened %s" %e)			
		return None

if __name__ == '__main__':	
	CopyToLimb().begin()