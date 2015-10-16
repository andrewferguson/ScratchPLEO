#Initialise all global variables to empty
scratchData, scriptArray, initCode, sensorCode, otherCode, currentFunction, variableList, motionList, soundList, broadcastList, receiveList = "", "", "", "", "", "", "", "", "", "", ""

import sys
import json

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
	
	global currentFunction, receiveList
	
	if tArray[0] == "whenGreenFlag":
		if initCode <> "":
			dError("Multiple 'When Green Flag Clicked' blocks in project. Only one is allowed.")
		currentFunction = "init"
		
	if tArray[0] == "whenIReceive":
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
	
	if tArray[0] == "doIf":
		addCode("if " + parseExpression(tArray[1]) + "\n{")
		for x in range(0, len(tArray[2])):
			translateScript(tArray[2][x])
		addCode("}")
	
	if tArray[0] == "doIfElse":
		addCode("if " + parseExpression(tArray[1]) + "\n{")
		for x in range(0, len(tArray[2])):
			translateScript(tArray[2][x])
		addCode("}\nelse\n{")
		for x in range(0, len(tArray[3])):
			translateScript(tArray[3][x])
		addCode("}")
	
	if tArray[0] == "doForever":
		addCode("while (true)\n{")
		for x in range(0, len(tArray[1])):
			translateScript(tArray[1][x])
		addCode("}")
	
	if tArray[0] == "doRepeat":
		addCode("for (new i = 1; i <= " + parseExpression(tArray[1]) + "; i++)\n{")
		for x in range(0, len(tArray[2])):
			translateScript(tArray[2][x])
		addCode("}")
	
	if tArray[0] == "doWaitUntil":
		addCode("while " = parseExpression(tArray[1]) + "\n{\nsleep;\n}"
	
	

def parseExpression(tArray):
	#takes a Scratch expression (as an array) and converts it to a PAWN expression (asn int or bool)
	
	global variableList
	
	#establish if we have reached the 'end of the expression trail', or if there are more arrays to process
	try: 
		int(tArray)
		#we have an integer
		print "int"
		
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
	print codeToAdd

def checkValidFunctionName(nameToCheck):
	print "Checking function name..."

def checkValidVariableName(nameToCheck):
	print "Checking function name..."

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
test = ["hello", "there"]
parseExpression("hi there")