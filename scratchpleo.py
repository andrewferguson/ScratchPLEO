#Initialise all global variables to empty
scratchData, scriptArray, initCode, sensorCode, otherCode, currentFunction, variableList, motionList, soundList, broadcastList, receiveList = "", "", "", "", "", "", "", "", "", "", ""

import sys #required for command line parameters and to exit the script in an error
import json #required to convert JSON to list
import re #required to check for valid variable and function names

def getScratchJSON():
	#get the JSON data from a Scratch file
	
	global scratchData
	scratchFile = sys.argv[1]
	scratchFile = open(scratchFile)
	scratchData = scratchFile.read()
	scratchData = json.loads(scratchData)
	scratchData = scratchData["children"][0]["scripts"]

def processScript():
	#loop through each 'main'block in the projects code
	
	for x in range(0, len(scratchData)):
		for y in range(0, len(scratchData[x][2]) ):
			translateScript(scratchData[x][2][y])
	
	
def translateScript(tArray):
	#translate the Scratch code to PAWN script
	
	global currentFunction, receiveList, soundList, motionList, broadcastList, variableList
	
	if tArray[0] == "whenGreenFlag":
		if initCode <> "":
			dError("Multiple 'When Green Flag Clicked' blocks in project. Only one is allowed.")
		currentFunction = "init"
		
	elif tArray[0] == "whenIReceive":
		if tArray[1][0:7] == "sensor_":
			#the project is trying to access one of PLEO's sensors
			validSensors = ["battery","ir","head","chin","back","left_leg","right_leg","left_arm","right_arm","tail","front_left","front_right","back_left","back_right","card_detect","write_protect","light","object","mouth","sound_dir","light_change","sound_loud","tilt","terminal","usb_detect","wakeup","battery_temp","shake","sound_loud_change","beacon","battery_current","packet","edge_in_front","edge_on_right","edge_on_left","object_in_front","object_on_left","object_on_right","touch_tap","touch_hold","touch_release","abuse_picked_up","trackabe_oject","msg_received","msg_gone"]
			if tArray[1][7:len(tArray[0])].lower() in validSensors:
				currentFunction = "sensor"
				if sensorCode <> "":
					addCode("}\n")
				addCode("if (sensor == " + tArray[1].upper() + "}\n")
			else:
				dError("Sensor: '" + tArray[1] + "' has been used when it is not supported by ScratchPLEO." )
				
		else:
			#this is a normal function call
			checkValidFunctionName(tArray[1])
			tArray[1] = tArray[1].replace(" ", "_")
			receiveList.append(tArray[1])
			if otherCode <> "":
				addCode("}\n\n")
			addCode("public pleoFunction_" + tArray[2] + "()\n{")
	
	elif tArray[0] == "doIf":
		addCode("if " + parseExpression(tArray[1]) + "\n{")
		for x in range(0, len(tArray[2])):
			translateScript(tArray[2][x])
		addCode("}")
	
	elif tArray[0] == "doIfElse":
		addCode("if " + parseExpression(tArray[1]) + "\n{")
		for x in range(0, len(tArray[2])):
			translateScript(tArray[2][x])
		addCode("}\nelse\n{")
		for x in range(0, len(tArray[3])):
			translateScript(tArray[3][x])
		addCode("}")
	
	elif tArray[0] == "doForever":
		addCode("while (true)\n{")
		for x in range(0, len(tArray[1])):
			translateScript(tArray[1][x])
		addCode("}")
	
	elif tArray[0] == "doRepeat":
		addCode("for (new i = 1; i <= " + parseExpression(tArray[1]) + "; i++)\n{")
		for x in range(0, len(tArray[2])):
			translateScript(tArray[2][x])
		addCode("}")
	
	elif tArray[0] == "doWaitUntil":
		addCode("while " + parseExpression(tArray[1]) + "\n{\nsleep;\n}")

	elif tArray[0] == "call":
		addCode("motion_play(mot_" + tArray[2].lower() + ");")
		if tArray[1][-1:len(tArray[1])] <> "%s":
			#this is a "...and wait" motion, make sure to wait until it is done
			addCode("while(motion_is_playing(mot_" + tArray[2].lower() + "))")
			addCode("{\nsleep;\n}")
		if tArray[2] not in motionList:
			motionList.append(tArray[2])
	
	elif tArray[0] == "procDef":
		#procDef is used for the custom blocks defined inside ScratchPLEO
		#the defenitions exist only to allow the blocks to be called from within Scratch
		#they should not be translated
		pass

	elif tArray[0] == "playSound":
		try:
			int(tArray)
			dError("Whoa! Something's gone real brokey... Try again, and if you see this message again, email the developer saying 'An integer was found where a string should be', along with a copy of the Scratch Project that caused this error.")
		except TypeError:
			#we have a list
			dError("Found an expression where a sound file name should be. Only sound files selected through the drop-down menus can be used.")
		except ValueError:
			#we have a non-integer thing (a.k.a a string)
			addCode("sound_play(snd_" + tArray[1].lower() + ");")
			if tArray[1] not in soundList:
				soundList.append(tArray[1])
	
	elif tArray[0] == "doPlaySoundAndWait":
		try:
			int(tArray)
			dError("Whoa! Something's gone real brokey... Try again, and if you see this message again, email the developer saying 'An integer was found where a string should be', along with a copy of the Scratch Project that caused this error.")
		except TypeError:
			#we have a list
			dError("Found an expression where a sound file name should be. Only sound files selected through the drop-down menus can be used.")
		except ValueError:
			#we have a non-integer thing (a.k.a a string)
			addCode("sound_play(snd_" + tArray[1].lower() + ");")
			addCode("while (sound_is_playing(snd_" + tArray[1].lower() + "))")
			addCode("{\nsleep;\n}")
			if tArray[1] not in soundList:
				soundList.append(tArray[1])
	
	elif tArray[0] == "doBroadcastAndWait":
		checkValidFunctionName(tArray[1])
		tArray[1] = tArray[1].replace(" ", "_")
		if tArray[1] not in broadcastList:
			broadcastList.append(tArray[1])
		tArray[1] = "pleoFunction_" + tArray[1]
		addCde(tArray[1] + ";")
	
	elif tArray[0] == "changeVar:by:":
		checkValidVariableName(tArray[1])
		tArray[1] = tArray[1].replace(" ", "_")
		tArray[1] = "pleoVar_" + tArray[1]
		if tArray[1] not in variableList:
			variableList.append(tArray[1])
		addCode(tArray[1] + " = " + tArray[1] + " + " + parseExpression(tArray[2]) + ";")
	
	elif tArray[0] == "setVar:to:":
		checkValidVariableName(tArray[1])
		tArray[1] = tArray[1].replace(" ", "_")
		tArray[1] = "pleoVar_" + tArray[1]
		if tArray[1] not in variableList:
			variableList.append(tArray[1])
		addCode(tArray[1] + " = " + parseExpression(tArray[2]) + ";")
	
	else:
		dError("Found invalid: '" + tArray[0] + "' . This is not supported.")


def parseExpression(tArray):
	#takes a Scratch expression (as an array) and converts it to a PAWN expression (asn int or bool)
	
	global variableList
	
	#establish if we have reached the 'end of the expression trail', or if there are more arrays to process
	try: 
		int(tArray)
		#we have an integer
		dError("Whoa! Something's gone real brokey... Try again, and if you see this message again, email the developer saying 'An integer was found where a string should be', along with a copy of the Scratch Project that caused this error.")
		
	except ValueError:
		#we have something not an int
		if tArray[0:7] == "sensor_":
			validSensors = ["battery","ir","head","chin","back","left_leg","right_leg","left_arm","right_arm","tail","front_left","front_right","back_left","back_right","card_detect","write_protect","light","object","mouth","sound_dir","light_change","sound_loud","tilt","terminal","usb_detect","wakeup","battery_temp","shake","sound_loud_change","beacon","battery_current","packet","edge_in_front","edge_on_right","edge_on_left","object_in_front","object_on_left","object_on_right","touch_tap","touch_hold","touch_release","abuse_picked_up","trackabe_oject","msg_received","msg_gone"]
			if tArray[7:len(tArray)].lower() in validSensors:
				#tArray is the name of a sensor
				print "sensor_get_value(sensor_name: " + tArray.upper() + " )"
		
		#we have something invalid
		dError("Found: '" + tArray + "' in expression, but only sensor names, integers and variables are allowed.")
	
	except TypeError:
		#we have a list
		#there are still more arrays to process
		if tArray[0] == "=":
			return "( " + parseExpression(tArray[1]) + " == " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "<":
			return "( " + parseExpression(tArray[1]) + " < " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == ">":
			return "( " + parseExpression(tArray[1]) + " > " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "+":
			return "( " + parseExpression(tArray[1]) + " + " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "-":
			return "( " + parseExpression(tArray[1]) + " - " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "*":
			return "( " + parseExpression(tArray[1]) + " * " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "/":
			return "( " + parseExpression(tArray[1]) + " / " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "|":
			return "( " + parseExpression(tArray[1]) + " || " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "&":
			return "( " + parseExpression(tArray[1]) + " && " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "%":
			return "( " + parseExpression(tArray[1]) + " % " + parseExpression(tArray[2]) + " )"
		elif tArray[0] == "not":
			return "(! " + parseExpression(tArray[1]) + " )"
		elif tArray[0] == "readVariable":
			checkValidVariableName(tArray[1])
			tArray[1] = tArray[1].replace(" ", "_")
			tArray[1] = "pleoVar_" + tArray[1]
			if tArray[1] not in variableList:
				variableList.append(tArray[1])
			return tArray[1]
		else:
			dError("Found '" + tArray[1] + "' in expression, yet this is not supported.")
	

def dError(error):
	#reports an error and exits the program
	print error
	sys.exit()

def addCode(codeToAdd):
	global initCode, sensorCode, otherCode
	
	if currentFunction == "init":
		#this code should be run when PLEO is first switched on
		initCode = initCode + "\n" + codeToAdd
		
	elif currentFunction == "sensor":
		#this code is linked to a sensor
		sensorCode = sensorCode + "\n" + codeToAdd
		
	elif currentFunction == "other":
		#this code is associated with a user-defined function
		otherCode = otherCode + "\n" + codeToAdd
	
	else:
		#oh, dear.
		#a block without a starting hat has been found.
		
		#alert the user and stop the script
		dError("A block has been found that has no starting block. Please ermove this block and run ScratchPLEO again.")
		#NOTE: this may change to 'alert the user, don't process this code and continue'
		#depending on the results of testing (do users have random code littering up their Scratch projects often?)

def checkValidFunctionName(nameToCheck):
	testVar = nameToCheck
	try:
		int(testVar)
	except TypeError:
		#found a list where we should have a string
		dError("Found an expression where only a broadcast name should be present. Only broadcast names selected through the drop-down menu can be used.")
	except ValueError:
		pass
	if nameToCheck == "":
		dError("Found empty broadcast name. Retry with a function name entered.")
	if re.match("^[A-Za-z0-9 ]+$", nameToCheck):
		pass
	else:
		#function name contains a non alpa-numeric or space character
		dError("Found invalid characters in broadcast name '" + nameToCheck + "' . Broadcast names can only contain letters, numbers and spaces.")

def checkValidVariableName(nameToCheck):
	testVar = nameToCheck
	try:
		int(testVar)
	except TypeError:
		#found a list where we should have a string
		dError("Found an expression where only a variable name should be present. Only variable names selected through the drop-down menu can be used.")
	except ValueError:
		pass
	if nameToCheck == "":
		dError("Found empty variable name. Retry with a variable name entered.")
	if re.match("^[A-Za-z0-9 ]+$", nameToCheck):
		pass
	else:
		#variable name contains a non alpa-numeric or space character
		dError("Found invalid characters in variable name '" + nameToCheck + "' . Variable names can only contain letters, numbers and spaces.")

def isInt(intToTest):
	try: 
		int(intToTest)
		return True
	except ValueError:
		return False
	except TypeError:
		print "list"


#getScratchJSON()
#processScript()
tt= ["hello", "world"]
checkValidFunctionName(tt)
print "457"