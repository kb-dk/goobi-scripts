from goobi.goobi_step import Step
import os
import shutil
import time
import traceback


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
			sleep_interval = int(self.getConfigItem('sleep_interval'))
			retries = int(self.getConfigItem('retries'))
									
			self.info_message("source_dir "+source_dir)
						
			"""
			attempt to copy all files to LIMB transit dir
			retry until all files are copied
			"""
			src_files = [[l,False] for l in os.listdir(source_dir)]			
			while files_not_copied and (retries>0):
				self.info_message("Copying files to transit dir")
				retries -= 1
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
								self.info_message("Copying file "+src_file[0])					   			
								shutil.copy2(full_file_name, transit_dir)
								src_file[1] = True
							else:
								self.warning_message(full_file_name+" is not a file ... skipping it")
				except Exception as e:
					self.warning_message("Error copying files: %s'" %e)
					files_not_copied = True
				if files_not_copied and (retries>0):
					self.warning_message("Not all files copied. Waiting to retry ...")
					time.sleep(sleep_interval)	
					print "sleep over"			
			shutil.move(transit_dir,hotfolder_dir)
		except Exception as e:
			self.error_message("An error happened %s" %e)	
			traceback.format_exc()
			self.error_message("Script Failed !!!!")
		if files_not_copied and retries <= 0:
			self.error_message("Maximum number of retries exceeded. Script Stopped")	
		return None

if __name__ == '__main__':	
	CopyToLimb().begin()
