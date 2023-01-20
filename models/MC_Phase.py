#### Imports
import json


#### Statics
enum_var = {}


#### Class
class MC_Phase:
	
	#### Properties
	var = 0

	#### Structors
	def __init__(self):
		pass

	def __del__(self):
		pass

	#### Methods


#### Phase Types
class Phase_Swiss(MC_Phase):
	
	#### Properties
	var = 0

	#### Structors
	def __init__(self):
		super().__init__()
	
	def __del__(self):
		super().__del__()

class MC_Phase_Bracket(MC_Phase):
	
	#### Properties
	var = 0

	#### Structors
	def __init__(self):
		super().__init__()
	
	def __del__(self):
		super().__del__()

	#### Methods

class Phase_Bracket_Single_Elimination(MC_Phase_Bracket):
	
	#### Properties
	var = 0

	#### Structors
	def __init__(self):
		super().__init__()
	
	def __del__(self):
		super().__del__()

	#### Methods

class Phase_Bracket_Double_Elimination(MC_Phase_Bracket):
	
	#### Properties
	var = 0

	#### Structors
	def __init__(self):
		super().__init__()
	
	def __del__(self):
		super().__del__()

	#### Methods


#### End of File